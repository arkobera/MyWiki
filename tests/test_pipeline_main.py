from __future__ import annotations

from Pipeline import main as pipeline_main


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

    def __init__(self, chunks: list[str], embeddings: str) -> None:
        self.chunks = chunks
        self.embeddings = embeddings
        self.collection_name = "pdf_docs"
        self.persist_directory = "chromadb"

    def store(self) -> "FakeVectorStore":
        FakeVectorStore.stored = True
        return self


def test_run_pipeline_returns_indexing_summary(monkeypatch, tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "sample.pdf").write_bytes(b"%PDF-1.4 sample")
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(pipeline_main, "LoadDoc", FakeLoader)
    monkeypatch.setattr(pipeline_main, "Chunker", FakeChunker)
    monkeypatch.setattr(pipeline_main, "Embedder", FakeEmbedder)
    monkeypatch.setattr(pipeline_main, "VectorStore", FakeVectorStore)

    result = pipeline_main.run_pipeline("sample.pdf")

    assert result["file_name"] == "sample.pdf"
    assert result["documents"] == 2
    assert result["chunks"] == 3
    assert result["vector_collection"] == "pdf_docs"
    assert FakeVectorStore.stored is True


def test_main_invokes_pipeline_and_prints_summary(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        pipeline_main,
        "run_pipeline",
        lambda file_name: {
            "file_name": file_name,
            "documents": 1,
            "chunks": 4,
        },
    )

    exit_code = pipeline_main.main(["sample.pdf"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Indexed sample.pdf" in output
    assert "4 chunk(s)" in output
