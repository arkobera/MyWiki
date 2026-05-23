from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from Pipeline.logging_utils import log_workflow

ROOT_DIR = Path(__file__).resolve().parent.parent
PATH_RAW = ROOT_DIR / "raw"
EMBEDDINGS_DIR = ROOT_DIR / "embeddings"
DEFAULT_COLLECTION_NAME = "document_chunks"


def build_embedding_id(file_name: str) -> str:
    stem = Path(file_name).stem.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "document"
    digest = hashlib.sha1(file_name.encode("utf-8")).hexdigest()[:10]
    return f"{normalized}-{digest}"


class LoadDoc:
    def __init__(self, file_name: str, raw_dir: Path = PATH_RAW) -> None:
        self.file_path = raw_dir / file_name

    def load(self) -> list[Any]:
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(str(self.file_path))
        documents = loader.load()
        log_workflow(
            "load_document",
            "Loaded source document pages.",
            file_name=self.file_path.name,
            pages=len(documents),
        )
        return documents


class Chunker:
    def __init__(
        self,
        documents: list[Any],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        self.documents = documents
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self) -> list[Any]:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        chunks = text_splitter.split_documents(self.documents)
        log_workflow(
            "chunk_document",
            "Split document into semantic chunks.",
            chunk_count=len(chunks),
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        return chunks


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name

    def embed(self) -> Any:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        log_workflow(
            "embedder_ready",
            "Initialized embedding model.",
            model_name=self.model_name,
        )
        return HuggingFaceEmbeddings(model_name=self.model_name)


class VectorStore:
    def __init__(
        self,
        file_name: str,
        chunks: list[Any],
        embeddings: Any,
        embeddings_root: Path = EMBEDDINGS_DIR,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        self.file_name = file_name
        self.embedding_id = build_embedding_id(file_name)
        self.chunks = chunks
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.persist_directory = embeddings_root / self.embedding_id

    def _prepare_chunks(self) -> list[Any]:
        prepared_chunks: list[Any] = []
        for index, chunk in enumerate(self.chunks, start=1):
            metadata = dict(getattr(chunk, "metadata", {}))
            metadata.update(
                {
                    "file_name": self.file_name,
                    "embedding_id": self.embedding_id,
                    "chunk_index": index,
                }
            )
            chunk.metadata = metadata
            prepared_chunks.append(chunk)
        return prepared_chunks

    def store(self) -> dict[str, Any]:
        from langchain_community.vectorstores import Chroma

        if self.persist_directory.exists():
            shutil.rmtree(self.persist_directory)
            log_workflow(
                "reset_embeddings",
                "Removed previous embedding directory before re-indexing.",
                embedding_id=self.embedding_id,
                persist_directory=str(self.persist_directory),
            )

        self.persist_directory.mkdir(parents=True, exist_ok=True)
        prepared_chunks = self._prepare_chunks()

        vectorstore = Chroma(
            persist_directory=str(self.persist_directory),
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )

        ids = [f"{self.embedding_id}-chunk-{index:04d}-{uuid4().hex[:8]}" for index, _ in enumerate(prepared_chunks, start=1)]
        vectorstore.add_documents(documents=prepared_chunks, ids=ids)

        log_workflow(
            "store_embeddings",
            "Stored document chunks in a dedicated Chroma collection.",
            file_name=self.file_name,
            embedding_id=self.embedding_id,
            collection_name=self.collection_name,
            chunk_count=len(prepared_chunks),
            persist_directory=str(self.persist_directory),
        )

        return {
            "vectorstore": vectorstore,
            "embedding_id": self.embedding_id,
            "chunk_ids": ids,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
        }
