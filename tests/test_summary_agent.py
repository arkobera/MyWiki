from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from Pipeline.summary_agent import SummaryAgent, SummaryResult, update_document_index


def build_result(document_name: str, embedding_id: str) -> SummaryResult:
    return SummaryResult(
        document_name=document_name,
        summary="A concise summary.",
        keywords=["keyword-a", "keyword-b", "keyword-c"],
        tags=["tag-a", "tag-b"],
        category="Research Paper",
        file_path=f"raw/{document_name}",
        embedding_id=embedding_id,
        main_topics=["topic-a"],
        technical_concepts=["concept-a"],
        important_entities=["entity-a"],
        frameworks=["framework-a"],
        algorithms=["algorithm-a"],
        libraries=["library-a"],
        research_areas=["research-a"],
        related_technologies=["technology-a"],
    )


def test_update_document_index_creates_expected_structure(tmp_path: Path) -> None:
    index_path = tmp_path / "index.md"

    update_document_index(build_result("sample.pdf", "embed-1"), index_path=index_path)

    content = index_path.read_text(encoding="utf-8")
    assert content.startswith("# Document Index")
    assert "## sample.pdf" in content
    assert "Embedding ID:\nembed-1" in content
    assert "- keyword-a" in content


def test_update_document_index_replaces_existing_entry_without_duplication(tmp_path: Path) -> None:
    index_path = tmp_path / "index.md"
    update_document_index(build_result("sample.pdf", "embed-1"), index_path=index_path)
    update_document_index(build_result("sample.pdf", "embed-2"), index_path=index_path)

    content = index_path.read_text(encoding="utf-8")
    assert content.count("## sample.pdf") == 1
    assert "embed-2" in content
    assert "embed-1" not in content


def test_build_batches_trims_large_documents_to_lightweight_context() -> None:
    agent = SummaryAgent()
    documents = [
        Document(page_content=" ".join([f"Page content token {index}" for index in range(150)]), metadata={"page": index})
        for index in range(20)
    ]

    batches = agent._build_batches(documents)

    assert len(batches) <= 2
    assert sum(len(batch) for batch in batches) <= 3000
