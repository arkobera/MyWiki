from __future__ import annotations

import json
import re
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import networkx as nx

SHARED_CONCEPT_MIN_DOCUMENTS = 2
GRAPH_FILE_NAME = "graph.json"
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "based",
    "by",
    "final",
    "for",
    "from",
    "head",
    "in",
    "into",
    "is",
    "of",
    "on",
    "report",
    "or",
    "real",
    "the",
    "their",
    "time",
    "to",
    "with",
}


@dataclass(slots=True)
class IndexEntry:
    document_name: str
    summary: str
    keywords: list[str]
    category: str
    file_path: str
    embedding_id: str


def parse_index_markdown(content: str) -> list[IndexEntry]:
    sections = [section.strip() for section in content.split("\n---") if section.strip()]
    entries: list[IndexEntry] = []

    for section in sections:
        title_match = re.search(r"^##\s+(.+?)\s*$", section, flags=re.MULTILINE)
        if not title_match:
            continue

        title = title_match.group(1).strip()

        def extract(label: str) -> str:
            pattern = rf"{re.escape(label)}\n(.*?)(?:\n\n[A-Z][A-Za-z ]+:|$)"
            match = re.search(pattern, section, flags=re.DOTALL)
            if not match:
                return ""
            return match.group(1).strip()

        keywords = [
            keyword.strip()
            for keyword in re.findall(r"^-\s+(.+)$", extract("Keywords:"), flags=re.MULTILINE)
            if keyword.strip()
        ]

        entries.append(
            IndexEntry(
                document_name=title,
                summary=extract("Summary:"),
                keywords=keywords,
                category=extract("Category:") or "Uncategorized",
                file_path=extract("File:"),
                embedding_id=extract("Embedding ID:"),
            )
        )

    return entries


def derive_embedding_path(index_path: Path, embedding_id: str) -> str:
    project_root = index_path.parent.parent
    candidate = project_root / "embeddings" / embedding_id
    if candidate.exists():
        return str(candidate.relative_to(project_root))
    return f"embeddings/{embedding_id}"


def normalize_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def slugify(value: str) -> str:
    normalized = normalize_phrase(value)
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "item"


def titleize_concept(value: str) -> str:
    if value.isupper():
        return value
    return " ".join(part.upper() if len(part) <= 4 else part.capitalize() for part in value.split())


def extract_atomic_concepts(keyword: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", keyword)
    atomic: set[str] = set()
    for token in tokens:
        lowered = token.lower()
        if lowered in STOPWORDS:
            continue
        if len(lowered) <= 2 and not token.isupper():
            continue
        atomic.add(lowered)
    return atomic


def build_document_concept_map(entries: list[IndexEntry]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    document_keyword_concepts: dict[str, set[str]] = {}
    concept_documents: dict[str, set[str]] = {}

    for entry in entries:
        document_id = f"document:{entry.document_name}"
        concepts: set[str] = set()
        for keyword in entry.keywords:
            concepts.update(extract_atomic_concepts(keyword))
        document_keyword_concepts[document_id] = concepts
        for concept in concepts:
            concept_documents.setdefault(concept, set()).add(document_id)

    return document_keyword_concepts, concept_documents


def _bump_edge(
    graph: nx.Graph,
    source: str,
    target: str,
    relation: str,
    weight: float = 1.0,
    **attributes: Any,
) -> None:
    if graph.has_edge(source, target):
        graph[source][target]["weight"] = float(graph[source][target].get("weight", 0.0)) + weight
        related_documents = set(graph[source][target].get("documents", []))
        related_documents.update(attributes.get("documents", []))
        if related_documents:
            graph[source][target]["documents"] = sorted(related_documents)

        if "shared_concepts" in attributes:
            existing_shared = set(graph[source][target].get("shared_concepts", []))
            existing_shared.update(attributes["shared_concepts"])
            graph[source][target]["shared_concepts"] = sorted(existing_shared)
        return

    graph.add_edge(source, target, relation=relation, weight=weight, **attributes)


def build_knowledge_graph(index_path: Path) -> nx.Graph:
    graph = nx.Graph()

    if not index_path.exists():
        return graph

    entries = parse_index_markdown(index_path.read_text(encoding="utf-8"))
    document_concepts, concept_documents = build_document_concept_map(entries)
    shared_concepts = {
        concept
        for concept, documents in concept_documents.items()
        if len(documents) >= SHARED_CONCEPT_MIN_DOCUMENTS
    }

    document_categories: dict[str, str] = {}
    document_keywords: dict[str, set[str]] = {}
    document_shared_concepts: dict[str, set[str]] = {}

    for entry in entries:
        document_id = f"document:{entry.document_name}"
        document_categories[document_id] = entry.category or "Uncategorized"
        document_keywords[document_id] = {normalize_phrase(keyword) for keyword in entry.keywords}
        embedding_path = derive_embedding_path(index_path, entry.embedding_id)

        graph.add_node(
            document_id,
            kind="document",
            label=entry.document_name,
            summary=entry.summary,
            category=entry.category or "Uncategorized",
            type="document",
            embedding_id=entry.embedding_id,
            embedding_path=embedding_path,
            source_file=entry.file_path,
            keyword_count=len(entry.keywords),
        )

        category_id = f"category:{slugify(entry.category or 'Uncategorized')}"
        graph.add_node(
            category_id,
            kind="category",
            label=entry.category or "Uncategorized",
            type="category",
        )
        _bump_edge(graph, document_id, category_id, relation="category", weight=2.0)

        keyword_ids: list[str] = []
        shared_for_document: set[str] = set()

        for keyword in entry.keywords:
            keyword_key = normalize_phrase(keyword)
            keyword_id = f"keyword:{slugify(keyword_key)}"
            keyword_ids.append(keyword_id)
            graph.add_node(
                keyword_id,
                kind="keyword",
                label=keyword,
                type="keyword",
            )
            _bump_edge(graph, document_id, keyword_id, relation="mentions", weight=2.2)

            for concept in sorted(extract_atomic_concepts(keyword) & shared_concepts):
                shared_for_document.add(concept)
                concept_id = f"concept:{slugify(concept)}"
                graph.add_node(
                    concept_id,
                    kind="concept",
                    label=titleize_concept(concept),
                    type="concept",
                    document_count=len(concept_documents[concept]),
                )
                _bump_edge(
                    graph,
                    keyword_id,
                    concept_id,
                    relation="derived concept",
                    weight=1.6,
                    documents=[entry.document_name],
                )

        document_shared_concepts[document_id] = shared_for_document

        for source_id, target_id in combinations(sorted(set(keyword_ids)), 2):
            _bump_edge(
                graph,
                source_id,
                target_id,
                relation="contextual proximity",
                weight=1.0,
                documents=[entry.document_name],
            )

    for source_id, target_id in combinations(sorted(document_categories), 2):
        shared_keyword_labels = sorted(
            {
                graph.nodes[keyword_id]["label"]
                for keyword_id in graph.neighbors(source_id)
                if graph.nodes[keyword_id].get("kind") == "keyword"
                and graph.has_edge(target_id, keyword_id)
            }
        )
        shared_atomic_concepts = sorted(
            document_shared_concepts.get(source_id, set()) & document_shared_concepts.get(target_id, set())
        )
        same_category = document_categories[source_id] == document_categories[target_id]
        related_score = (2 * len(shared_atomic_concepts)) + len(shared_keyword_labels) + (1 if same_category else 0)

        if related_score == 0:
            continue

        relation_parts: list[str] = []
        if shared_atomic_concepts:
            relation_parts.append(f"{len(shared_atomic_concepts)} shared concepts")
        if shared_keyword_labels:
            relation_parts.append(f"{len(shared_keyword_labels)} shared keywords")
        if same_category:
            relation_parts.append("same category")

        _bump_edge(
            graph,
            source_id,
            target_id,
            relation="related documents",
            weight=2.0 + related_score,
            shared_concepts=shared_atomic_concepts,
            shared_keywords=shared_keyword_labels,
            same_category=same_category,
            label=", ".join(relation_parts) or "related documents",
        )

    return graph


def initial_position_for_node(kind: str, index: int) -> dict[str, float]:
    columns = {
        "category": (80.0, 220.0),
        "document": (520.0, 180.0),
        "keyword": (980.0, 150.0),
        "concept": (1420.0, 240.0),
    }
    origin_x, base_y = columns.get(kind, (520.0, 200.0))
    row = index % 6
    column_offset = index // 6
    return {
        "x": origin_x + (column_offset * 220.0),
        "y": base_y + (row * 170.0),
    }


def edge_style_for_relation(relation: str) -> dict[str, Any]:
    if relation == "related documents":
        return {
            "type": "straight",
            "animated": False,
            "style": {"stroke": "#38bdf8", "strokeWidth": 2.4, "opacity": 0.9},
        }
    if relation == "contextual proximity":
        return {
            "type": "smoothstep",
            "animated": False,
            "style": {"stroke": "#c084fc", "strokeWidth": 1.4, "opacity": 0.4},
        }
    if relation == "derived concept":
        return {
            "type": "smoothstep",
            "animated": False,
            "style": {"stroke": "#f59e0b", "strokeWidth": 1.5, "opacity": 0.65},
        }
    return {
        "type": "smoothstep",
        "animated": False,
        "style": {"stroke": "#94a3b8", "strokeWidth": 1.3, "opacity": 0.45},
    }


def serialize_knowledge_graph(index_path: Path) -> dict[str, Any]:
    graph = build_knowledge_graph(index_path)

    if graph.number_of_nodes() == 0:
        return {
            "meta": {"document_count": 0, "node_count": 0, "edge_count": 0},
            "nodes": [],
            "edges": [],
        }

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for index, (node_id, node_data) in enumerate(
        sorted(graph.nodes(data=True), key=lambda item: (item[1].get("kind", "default"), item[1].get("label", item[0]).lower()))
    ):
        nodes.append(
            {
                "id": node_id,
                "type": node_data.get("type", "default"),
                "position": initial_position_for_node(node_data.get("kind", "default"), index),
                "data": {
                    "label": node_data.get("label", node_id),
                    "kind": node_data.get("kind", "default"),
                    "summary": node_data.get("summary", ""),
                    "category": node_data.get("category", ""),
                    "embedding_id": node_data.get("embedding_id", ""),
                    "embedding_path": node_data.get("embedding_path", ""),
                    "source_file": node_data.get("source_file", ""),
                    "keyword_count": node_data.get("keyword_count", 0),
                    "document_count": node_data.get("document_count", 0),
                },
            }
        )

    for source, target, edge_data in sorted(graph.edges(data=True), key=lambda item: (item[0], item[1], item[2].get("relation", ""))):
        relation = edge_data.get("relation", "related")
        label = str(edge_data.get("label") or relation)
        style = edge_style_for_relation(relation)
        edges.append(
            {
                "id": f"{source}->{target}",
                "source": source,
                "target": target,
                "label": label,
                "data": {
                    "relation": relation,
                    "weight": float(edge_data.get("weight", 1.0)),
                    "documents": edge_data.get("documents", []),
                    "shared_concepts": edge_data.get("shared_concepts", []),
                    "shared_keywords": edge_data.get("shared_keywords", []),
                    "same_category": bool(edge_data.get("same_category", False)),
                },
                **style,
            }
        )

    document_count = sum(1 for _, data in graph.nodes(data=True) if data.get("kind") == "document")
    return {
        "meta": {
            "document_count": document_count,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
        },
        "nodes": nodes,
        "edges": edges,
    }


def persist_knowledge_graph(index_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    graph_payload = serialize_knowledge_graph(index_path)
    destination = output_path or index_path.parent / GRAPH_FILE_NAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(graph_payload, indent=2), encoding="utf-8")
    project_root = index_path.parent.parent
    try:
        graph_payload["graph_path"] = str(destination.relative_to(project_root))
    except ValueError:
        graph_payload["graph_path"] = str(destination)
    return graph_payload
