from __future__ import annotations

import re
from pathlib import Path

import networkx as nx


class IndexEntry:
    def __init__(
        self,
        document_name: str,
        summary: str,
        keywords: list[str],
        category: str,
        file_path: str,
        embedding_id: str,
    ) -> None:
        self.document_name = document_name
        self.summary = summary
        self.keywords = keywords
        self.category = category
        self.file_path = file_path
        self.embedding_id = embedding_id


def parse_index_markdown(content: str) -> list[IndexEntry]:
    sections = [section.strip() for section in content.split("\n---") if section.strip()]
    entries: list[IndexEntry] = []

    for section in sections:
        title_match = re.search(r"^##\s+(.+?)\s*$", section, flags=re.MULTILINE)
        if not title_match:
            continue

        title = title_match.group(1).strip()
        def extract(label: str) -> str:
            pattern = rf"{label}\n(.*?)(?:\n\n[A-Z][A-Za-z ]+:|$)"
            match = re.search(pattern, section, flags=re.DOTALL)
            if not match:
                return ""
            return re.sub(r"^\s+|\s+$", "", match.group(1)).strip()

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
                category=extract("Category:"),
                file_path=extract("File:"),
                embedding_id=extract("Embedding ID:"),
            )
        )

    return entries


def build_knowledge_graph(index_path: Path) -> nx.Graph:
    graph = nx.Graph()

    if not index_path.exists():
        return graph

    content = index_path.read_text(encoding="utf-8")
    entries = parse_index_markdown(content)

    for entry in entries:
        document_id = f"document:{entry.document_name}"
        graph.add_node(
            document_id,
            kind="document",
            label=entry.document_name,
            summary=entry.summary,
            type="document",
        )

        category = entry.category or "Uncategorized"
        category_id = f"category:{category}"
        graph.add_node(category_id, kind="category", label=category, type="category")
        graph.add_edge(document_id, category_id, relation="category")

        file_id = f"file:{entry.file_path}"
        graph.add_node(file_id, kind="file", label=entry.file_path, type="meta")
        graph.add_edge(document_id, file_id, relation="source_file")

        embedding_id = f"embedding:{entry.embedding_id}"
        graph.add_node(
            embedding_id,
            kind="embedding",
            label=entry.embedding_id,
            type="meta",
        )
        graph.add_edge(document_id, embedding_id, relation="embedding")

        for keyword in entry.keywords:
            keyword_id = f"keyword:{keyword}"
            graph.add_node(keyword_id, kind="keyword", label=keyword, type="keyword")
            graph.add_edge(document_id, keyword_id, relation="mentions")

    return graph


def serialize_knowledge_graph(index_path: Path) -> dict[str, list[dict[str, object]]]:
    graph = build_knowledge_graph(index_path)

    if graph.number_of_nodes() == 0:
        return {"nodes": [], "edges": []}

    positions = nx.spring_layout(graph, seed=42, k=1.5)
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

    for node_id, node_data in graph.nodes(data=True):
        x, y = positions[node_id]
        nodes.append(
            {
                "id": node_id,
                "type": node_data.get("type", "default"),
                "position": {"x": round(float(x) * 420 + 420, 2), "y": round(float(y) * 320 + 320, 2)},
                "data": {
                    "label": node_data.get("label", node_id),
                    "kind": node_data.get("kind", "default"),
                    "summary": node_data.get("summary", ""),
                },
            }
        )

    for source, target, edge_data in graph.edges(data=True):
        edges.append(
            {
                "id": f"{source}->{target}",
                "source": source,
                "target": target,
                "label": edge_data.get("relation", "related"),
                "animated": True,
                "type": "smoothstep",
            }
        )

    return {"nodes": nodes, "edges": edges}
