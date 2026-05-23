from __future__ import annotations

from Pipeline import main as pipeline_main
from Pipeline.summary_agent import SummaryResult


class FakeLoader:
    def __init__(self, file_name: str) -> None:
        self.file_name = file_name

    def load(self) -> list[str]:
        return ["doc-1", "doc-2"]


class FakeChunker:
    def __init__(self, documents: list[str]) -> None:
        self.documents = documents

    def chunk(self) -> list[str]:
        return ["chunk-1", "chunk-2", "chunk-3"]


class FakeEmbedder:
    def embed(self) -> str:
        return "embeddings"


class FakeVectorStore:
    stored = False

    def __init__(self, file_name: str, chunks: list[str], embeddings: str) -> None:
        self.file_name = file_name
        self.chunks = chunks
        self.embeddings = embeddings

    def store(self) -> dict[str, object]:
        FakeVectorStore.stored = True
        return {
            "embedding_id": "sample-embedding",
            "chunk_ids": ["chunk-a", "chunk-b", "chunk-c"],
            "collection_name": "document_chunks",
            "persist_directory": "embeddings/sample-embedding",
        }


class FakeSummaryAgent:
    def summarize(
        self,
        document_name: str,
        file_path: str,
        embedding_id: str,
        documents: list[str],
    ) -> SummaryResult:
        return SummaryResult(
            document_name=document_name,
            summary="A concise technical summary.",
            keywords=["transformer attention", "sequence modeling", "self-attention"],
            tags=["transformers", "nlp"],
            category="Machine Learning Research",
            file_path=file_path,
            embedding_id=embedding_id,
            main_topics=["transformers"],
            technical_concepts=["self-attention"],
            important_entities=["encoder"],
            frameworks=[],
            algorithms=["scaled dot-product attention"],
            libraries=[],
            research_areas=["natural language processing"],
            related_technologies=["large language models"],
        )


def test_run_pipeline_returns_indexing_summary(monkeypatch, tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "sample.pdf").write_bytes(b"%PDF-1.4 sample")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pipeline_main, "ROOT_DIR", tmp_path)

    captured_index_update: dict[str, object] = {}

    monkeypatch.setattr(pipeline_main, "LoadDoc", FakeLoader)
    monkeypatch.setattr(pipeline_main, "Chunker", FakeChunker)
    monkeypatch.setattr(pipeline_main, "Embedder", FakeEmbedder)
    monkeypatch.setattr(pipeline_main, "VectorStore", FakeVectorStore)
    monkeypatch.setattr(pipeline_main, "SummaryAgent", FakeSummaryAgent)
    monkeypatch.setattr(
        pipeline_main,
        "update_document_index",
        lambda result: captured_index_update.update({"document_name": result.document_name}),
    )

    FakeVectorStore.stored = False
    result = pipeline_main.run_pipeline("sample.pdf")

    assert result["file_name"] == "sample.pdf"
    assert result["documents"] == 2
    assert result["chunks"] == 3
    assert result["vector_collection"] == "document_chunks"
    assert result["embedding_id"] == "sample-embedding"
    assert result["keywords"][0] == "transformer attention"
    assert captured_index_update["document_name"] == "sample.pdf"
    assert FakeVectorStore.stored is True


def test_run_pipeline_uses_project_root_when_cwd_is_nested(monkeypatch, tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "sample.pdf").write_bytes(b"%PDF-1.4 sample")
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    monkeypatch.chdir(backend_dir)
    monkeypatch.setattr(pipeline_main, "ROOT_DIR", tmp_path)

    monkeypatch.setattr(pipeline_main, "LoadDoc", FakeLoader)
    monkeypatch.setattr(pipeline_main, "Chunker", FakeChunker)
    monkeypatch.setattr(pipeline_main, "Embedder", FakeEmbedder)
    monkeypatch.setattr(pipeline_main, "VectorStore", FakeVectorStore)
    monkeypatch.setattr(pipeline_main, "SummaryAgent", FakeSummaryAgent)
    monkeypatch.setattr(pipeline_main, "update_document_index", lambda result: None)

    FakeVectorStore.stored = False
    result = pipeline_main.run_pipeline("sample.pdf")

    assert result["file_name"] == "sample.pdf"
    assert result["chunks"] == 3
    assert result["embedding_id"] == "sample-embedding"
    assert FakeVectorStore.stored is True


def test_main_invokes_pipeline_and_prints_summary(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        pipeline_main,
        "run_pipeline",
        lambda file_name: {
            "file_name": file_name,
            "documents": 1,
            "chunks": 4,
            "embedding_id": "sample-embedding",
        },
    )

    exit_code = pipeline_main.main(["sample.pdf"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Indexed sample.pdf" in output
    assert "embedding ID sample-embedding" in output
