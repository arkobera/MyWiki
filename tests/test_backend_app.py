from __future__ import annotations

from fastapi.testclient import TestClient

from backend import app as backend_app


def test_pdf_upload_runs_pipeline(monkeypatch, tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    monkeypatch.setattr(backend_app, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(backend_app, "RAW_DIR", raw_dir)
    monkeypatch.setattr(
        backend_app,
        "run_pipeline",
        lambda file_name: {
            "file_name": file_name,
            "documents": 2,
            "chunks": 5,
            "vector_collection": "document_chunks",
            "vector_directory": "embeddings/sample-embedding",
            "embedding_id": "sample-embedding",
            "summary": "A concise technical summary.",
            "keywords": ["transformer attention", "sequence modeling"],
            "tags": ["transformers", "nlp"],
            "category": "Machine Learning Research",
            "index_path": "Agents/index.md",
        },
    )

    client = TestClient(backend_app.app)
    response = client.post(
        "/upload",
        files={"file": ("sample.pdf", b"%PDF-1.4 fake content", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "sample.pdf"
    assert payload["pipeline"]["status"] == "indexed"
    assert payload["pipeline"]["chunks"] == 5
    assert payload["pipeline"]["embedding_id"] == "sample-embedding"
    assert (raw_dir / "sample.pdf").exists()
