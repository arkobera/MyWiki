from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from Pipeline.load_doc import Chunker, Embedder, LoadDoc, VectorStore

ROOT_DIR = Path(__file__).resolve().parent.parent


def run_pipeline(file_name: str) -> dict[str, Any]:
    source_path = ROOT_DIR / "raw" / file_name
    if not source_path.exists():
        msg = f"Source file not found: {source_path}"
        raise FileNotFoundError(msg)

    loader = LoadDoc(file_name)
    documents = loader.load()

    chunker = Chunker(documents)
    chunks = chunker.chunk()

    embeddings = Embedder().embed()
    vector_store = VectorStore(chunks, embeddings)
    vector_store.store()

    return {
        "file_name": file_name,
        "documents": len(documents),
        "chunks": len(chunks),
        "vector_collection": vector_store.collection_name,
        "vector_directory": str(vector_store.persist_directory),
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
        f"{result['file_name']} with {result['documents']} document(s) "
        f"and {result['chunks']} chunk(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
