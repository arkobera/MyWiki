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


def test_knowledge_graph_endpoint_returns_serialized_graph(monkeypatch, tmp_path) -> None:
    index_path = tmp_path / "Agents" / "index.md"
    index_path.parent.mkdir()
    index_path.write_text(
        """# Document Index

## Alpha

Summary:
A model for attention.

Keywords:
- Transformer
- Attention

Category:
Artificial Intelligence

File:
raw/alpha.pdf

Embedding ID:
embed-alpha

---

## Beta

Summary:
A speech recognition report.

Keywords:
- Vision
- Attention

Category:
Computer Vision

File:
raw/beta.pdf

Embedding ID:
embed-beta
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(backend_app, "ROOT_DIR", tmp_path)

    client = TestClient(backend_app.app)
    response = client.get("/knowledge-graph")

    assert response.status_code == 200
    payload = response.json()

    assert payload["source"] == "Agents/index.md"
    assert payload["graph_path"] == "Agents/graph.json"
    assert payload["nodes"]
    assert payload["edges"]
    assert any(node["id"] == "document:Alpha" for node in payload["nodes"])
    assert any(node["id"] == "keyword:attention" for node in payload["nodes"])
    assert any(edge["source"] == "document:Alpha" and edge["target"] == "keyword:transformer" for edge in payload["edges"])
    assert any(
        {edge["source"], edge["target"]} == {"document:Alpha", "document:Beta"}
        and edge["data"]["relation"] == "related documents"
        for edge in payload["edges"]
    )
    assert any(node.get("position") for node in payload["nodes"])
    alpha_node = next(node for node in payload["nodes"] if node["id"] == "document:Alpha")
    assert alpha_node["data"]["embedding_id"] == "embed-alpha"
    assert alpha_node["data"]["embedding_path"] == "embeddings/embed-alpha"
    assert (tmp_path / "Agents" / "graph.json").exists()
