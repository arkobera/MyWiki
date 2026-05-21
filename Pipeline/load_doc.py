from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT_DIR = Path(__file__).resolve().parent.parent
PATH_RAW = ROOT_DIR / "raw"
CHROMA_DIR = ROOT_DIR / "chromadb"
COLLECTION_NAME = "pdf_docs"


class LoadDoc:
    def __init__(self, file_name: str, raw_dir: Path = PATH_RAW) -> None:
        self.file_path = raw_dir / file_name

    def load(self) -> list[Any]:
        from langchain_community.document_loaders import PyPDFLoader

        loader = PyPDFLoader(str(self.file_path))
        return loader.load()


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
        return text_splitter.split_documents(self.documents)


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name

    def embed(self) -> Any:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=self.model_name)


class VectorStore:
    def __init__(
        self,
        chunks: list[Any],
        embeddings: Any,
        persist_directory: Path = CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self.chunks = chunks
        self.embeddings = embeddings
        self.persist_directory = persist_directory
        self.collection_name = collection_name

    def store(self) -> Any:
        from langchain_community.vectorstores import Chroma

        vectorstore = Chroma(
            persist_directory=str(self.persist_directory),
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )

        ids = [str(uuid4()) for _ in self.chunks]
        vectorstore.add_documents(documents=self.chunks, ids=ids)
        vectorstore.persist()
        return vectorstore
