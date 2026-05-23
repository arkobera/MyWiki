from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Pipeline.logging_utils import log_workflow
from langchain_ollama import ChatOllama

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT_DIR / "Agents"
INDEX_PATH = AGENTS_DIR / "index.md"


@dataclass
class SummaryResult:
    document_name: str
    summary: str
    keywords: list[str]
    tags: list[str]
    category: str
    file_path: str
    embedding_id: str
    main_topics: list[str]
    technical_concepts: list[str]
    important_entities: list[str]
    frameworks: list[str]
    algorithms: list[str]
    libraries: list[str]
    research_areas: list[str]
    related_technologies: list[str]

    def to_index_entry(self) -> str:
        keywords_block = "\n".join(f"- {keyword}" for keyword in self.keywords)
        return (
            f"## {self.document_name}\n\n"
            "Summary:\n"
            f"{self.summary}\n\n"
            "Keywords:\n"
            f"{keywords_block}\n\n"
            "Category:\n"
            f"{self.category}\n\n"
            "File:\n"
            f"{self.file_path}\n\n"
            "Embedding ID:\n"
            f"{self.embedding_id}\n"
        )


class SummaryAgent:
    def __init__(
        self,
        model_name: str = "phi3:mini",
        max_chars: int = 1200,
        per_page_chars: int = 80,
        num_predict: int = 260,
    ) -> None:
        self.model_name = model_name
        self.max_chars = max_chars
        self.per_page_chars = per_page_chars
        self.num_predict = num_predict

    def summarize(
        self,
        document_name: str,
        file_path: str,
        embedding_id: str,
        documents: list[Any],
    ) -> SummaryResult:
        batches = self._build_batches(documents)
        digest = "\n\n".join(batches)
        log_workflow(
            "summary_digest",
            "Prepared condensed document context for Ollama analysis.",
            document_name=document_name,
            batch_count=len(batches),
            digest_characters=len(digest),
        )

        final_data = self._synthesize_document(document_name, digest)
        summary_text = self._coerce_summary_text(final_data.get("summary"))

        result = SummaryResult(
            document_name=document_name,
            summary=summary_text,
            keywords=self._normalize_list(final_data.get("keywords", [])),
            tags=self._normalize_list(final_data.get("tags", [])),
            category=str(final_data.get("category", "Uncategorized")).strip() or "Uncategorized",
            file_path=file_path,
            embedding_id=embedding_id,
            main_topics=self._normalize_list(final_data.get("main_topics", [])),
            technical_concepts=self._normalize_list(final_data.get("technical_concepts", [])),
            important_entities=self._normalize_list(final_data.get("important_entities", [])),
            frameworks=self._normalize_list(final_data.get("frameworks", [])),
            algorithms=self._normalize_list(final_data.get("algorithms", [])),
            libraries=self._normalize_list(final_data.get("libraries", [])),
            research_areas=self._normalize_list(final_data.get("research_areas", [])),
            related_technologies=self._normalize_list(final_data.get("related_technologies", [])),
        )

        log_workflow(
            "summary_complete",
            "Generated document summary and retrieval metadata.",
            document_name=document_name,
            category=result.category,
            keyword_count=len(result.keywords),
            tags=result.tags,
        )
        return result

    def _build_batches(
        self,
        documents: list[Any],
        max_chars: int | None = None,
        per_page_chars: int | None = None,
    ) -> list[str]:
        effective_max_chars = self.max_chars if max_chars is None else max_chars
        effective_per_page_chars = (
            self.per_page_chars if per_page_chars is None else per_page_chars
        )
        batches: list[str] = []
        current_parts: list[str] = []
        current_size = 0

        for document in documents:
            page_number = document.metadata.get("page", 0) + 1
            page_text = re.sub(r"\s+", " ", document.page_content).strip()
            if not page_text:
                continue

            segment = f"[Page {page_number}] {page_text[:effective_per_page_chars]}"
            if current_parts and current_size + len(segment) > effective_max_chars:
                batches.append("\n".join(current_parts))
                current_parts = [segment]
                current_size = len(segment)
            else:
                current_parts.append(segment)
                current_size += len(segment)

        if current_parts:
            batches.append("\n".join(current_parts))

        return batches or [""]

    def _synthesize_document(
        self,
        document_name: str,
        document_digest: str,
    ) -> dict[str, Any]:
        prompt = f"""
You are a document indexing agent for a technical wiki.
You will receive condensed excerpts spanning a full document.

Return valid JSON only. Use exactly these keys:
summary, keywords, tags, category

Rules:
- summary: 3 sentences, concise but information-dense.
- keywords: 5-8 strong retrieval terms.
- tags: 4-6 short labels.
- category: one high-quality category.
- Every list value must be an array of strings.
- Preserve technical specificity.
- Infer the deepest themes you can from the excerpts instead of repeating page phrasing.

Document name: {document_name}
Document excerpts:
{document_digest}
""".strip()

        return self._invoke_json(prompt)

    def _invoke_json(self, prompt: str) -> dict[str, Any]:

        llm = ChatOllama(
            model=self.model_name,
            temperature=0,
            num_predict=self.num_predict,
            format="json",
        )
        response = llm.invoke(prompt)
        content = self._coerce_content(response.content)

        try:
            return json.loads(self._extract_json(content))
        except json.JSONDecodeError as exc:
            log_workflow(
                "summary_parse_error",
                "Failed to parse Ollama JSON response.",
                model_name=self.model_name,
                raw_response=content[:1000],
            )
            raise ValueError("Ollama summary agent returned invalid JSON.") from exc

    @staticmethod
    def _coerce_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        return str(content)

    @staticmethod
    def _coerce_summary_text(value: Any) -> str:
        if isinstance(value, list):
            pieces = [str(item).strip() for item in value if str(item).strip()]
            return " ".join(pieces)
        if isinstance(value, str):
            return value.strip()
        return ""

    @staticmethod
    def _extract_json(content: str) -> str:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return match.group(0)
        return content

    @staticmethod
    def _normalize_list(values: Any) -> list[str]:
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            return []

        cleaned: list[str] = []
        seen: set[str] = set()
        for value in values:
            item = str(value).strip()
            if not item:
                continue
            lowered = item.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            cleaned.append(item)
        return cleaned


def update_document_index(result: SummaryResult, index_path: Path = INDEX_PATH) -> None:
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    if not index_path.exists():
        index_path.write_text("# Document Index\n", encoding="utf-8")

    current = index_path.read_text(encoding="utf-8").strip()
    sections = _parse_index_sections(current)
    sections[result.document_name] = result.to_index_entry().strip()

    ordered_entries = [sections[name] for name in sorted(sections)]
    rendered = "# Document Index\n\n" + "\n\n---\n\n".join(ordered_entries)
    rendered = rendered.rstrip() + "\n\n---\n"
    index_path.write_text(rendered, encoding="utf-8")

    log_workflow(
        "index_updated",
        "Wrote document summary into Agents/index.md.",
        document_name=result.document_name,
        index_path=str(index_path),
        embedding_id=result.embedding_id,
    )


def _parse_index_sections(content: str) -> dict[str, str]:
    if not content.strip():
        return {}

    body = content
    if body.startswith("# Document Index"):
        body = body[len("# Document Index") :].strip()

    sections: dict[str, str] = {}
    for raw_section in [section.strip() for section in body.split("\n---") if section.strip()]:
        lines = raw_section.splitlines()
        if not lines or not lines[0].startswith("## "):
            continue
        document_name = lines[0][3:].strip()
        sections[document_name] = raw_section
    return sections
