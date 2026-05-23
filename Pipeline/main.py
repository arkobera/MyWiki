from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from Pipeline.load_doc import Chunker, Embedder, LoadDoc, VectorStore
from Pipeline.logging_utils import log_workflow
from Pipeline.summary_agent import SummaryAgent, update_document_index

ROOT_DIR = Path(__file__).resolve().parent.parent


def run_pipeline(file_name: str) -> dict[str, Any]:
    source_path = ROOT_DIR / "raw" / file_name
    if not source_path.exists():
        msg = f"Source file not found: {source_path}"
        raise FileNotFoundError(msg)

    log_workflow(
        "pipeline_start",
        "Started full indexing pipeline for uploaded document.",
        file_name=file_name,
        source_path=str(source_path),
    )

    loader = LoadDoc(file_name)
    documents = loader.load()

    chunker = Chunker(documents)
    chunks = chunker.chunk()

    embeddings = Embedder().embed()
    vector_store = VectorStore(file_name=file_name, chunks=chunks, embeddings=embeddings)
    vector_store_result = vector_store.store()

    summary_agent = SummaryAgent()
    summary_result = summary_agent.summarize(
        document_name=file_name,
        file_path=str(Path("raw") / file_name),
        embedding_id=vector_store_result["embedding_id"],
        documents=documents,
    )
    update_document_index(summary_result)

    log_workflow(
        "pipeline_complete",
        "Completed embeddings and agent indexing workflow.",
        file_name=file_name,
        embedding_id=vector_store_result["embedding_id"],
        chunk_count=len(chunks),
        index_path="Agents/index.md",
    )

    return {
        "file_name": file_name,
        "documents": len(documents),
        "chunks": len(chunks),
        "vector_collection": vector_store_result["collection_name"],
        "vector_directory": str(vector_store_result["persist_directory"]),
        "embedding_id": vector_store_result["embedding_id"],
        "chunk_ids": vector_store_result["chunk_ids"],
        "summary": summary_result.summary,
        "keywords": summary_result.keywords,
        "tags": summary_result.tags,
        "category": summary_result.category,
        "index_path": "Agents/index.md",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process a PDF into the vector store.")
    parser.add_argument("file_name", help="File name inside raw/")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_pipeline(args.file_name)
    print(
        "Indexed "
        f"{result['file_name']} with {result['documents']} document(s), "
        f"{result['chunks']} chunk(s), and embedding ID {result['embedding_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
