from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from backend.knowledge_graph import parse_index_markdown
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama

ROOT_DIR = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT_DIR / "Agents" / "index.md"


class RetrievalAgent:
    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model_name: str = "phi3:mini",
        llm_predict_tokens: int = 260,
        collection_name: str = "document_chunks",
    ) -> None:
        self.embedding_model_name = embedding_model_name
        self.llm_model_name = llm_model_name
        self.llm_predict_tokens = llm_predict_tokens
        self.collection_name = collection_name
        self._embeddings = None

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        return self._embeddings

    def answer(self, query: str) -> dict[str, Any]:
        query_text = query.strip()
        if not query_text:
            raise ValueError("Query text is required.")

        index_entries = parse_index_markdown(INDEX_PATH)
        if not index_entries:
            return {
                "query": query_text,
                "answer": "No indexed documents are available in Agents/index.md.",
                "document_name": None,
                "embedding_id": None,
                "confidence": 0.0,
            }

        indexed_rows = self._build_index_rows(index_entries)
        best_entry, similarity = self._find_best_index_entry(query_text, indexed_rows)

        retrieved_documents = self._retrieve_documents(best_entry.embedding_id, query_text, k=3)
        answer = self._compose_answer(query_text, best_entry, retrieved_documents)

        return {
            "query": query_text,
            "answer": answer,
            "document_name": best_entry.document_name,
            "embedding_id": best_entry.embedding_id,
            "similarity": round(similarity, 4),
            "source_file": best_entry.file_path,
            "category": best_entry.category,
            "keywords": best_entry.keywords,
        }

    def _build_index_rows(self, index_entries: list[Any]) -> list[dict[str, Any]]:
        texts = [self._build_index_text(entry) for entry in index_entries]
        vectors = self.embeddings.embed_documents(texts)
        return [
            {
                "entry": entry,
                "text": text,
                "vector": vector,
            }
            for entry, text, vector in zip(index_entries, texts, vectors)
        ]

    @staticmethod
    def _build_index_text(entry: Any) -> str:
        parts = [entry.summary or ""]
        if entry.keywords:
            parts.append("Keywords: " + ", ".join(entry.keywords))
        if entry.category:
            parts.append("Category: " + entry.category)
        return "\n".join(parts).strip()

    def _find_best_index_entry(
        self,
        query_text: str,
        rows: list[dict[str, Any]],
    ) -> tuple[Any, float]:
        query_vector = self.embeddings.embed_documents([query_text])[0]
        best_entry = None
        best_score = -1.0

        for row in rows:
            score = self._cosine_similarity(query_vector, row["vector"])
            if score > best_score:
                best_score = score
                best_entry = row["entry"]

        return best_entry, best_score if best_score >= 0 else 0.0

    @staticmethod
    def _cosine_similarity(first: list[float], second: list[float]) -> float:
        dot_product = 0.0
        sum_sq_first = 0.0
        sum_sq_second = 0.0
        for a, b in zip(first, second):
            dot_product += a * b
            sum_sq_first += a * a
            sum_sq_second += b * b
        if sum_sq_first == 0.0 or sum_sq_second == 0.0:
            return 0.0
        return dot_product / (math.sqrt(sum_sq_first) * math.sqrt(sum_sq_second))

    def _retrieve_documents(self, embedding_id: str, query_text: str, k: int = 3) -> list[Any]:
        vector_path = ROOT_DIR / "embeddings" / embedding_id
        if not vector_path.exists():
            return []

        vector_store = Chroma(
            persist_directory=str(vector_path),
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )

        try:
            return vector_store.similarity_search(query_text, k=k)
        except Exception:
            return []

    def _compose_answer(self, query_text: str, best_entry: Any, documents: list[Any]) -> str:
        if not documents:
            prompt = (
                f"You are a retrieval assistant. "
                f"Use the selected document metadata to provide the best possible answer. "
                f"If the answer is not available, reply that the information cannot be found in the indexed document.\n\n"
                f"Selected document: {best_entry.document_name}\n"
                f"Keywords: {', '.join(best_entry.keywords)}\n"
                f"Category: {best_entry.category}\n"
                f"Query: {query_text}\n\n"
                "Answer:"
            )
        else:
            context = "\n\n".join(
                f"Source chunk: {getattr(doc, 'page_content', str(doc))}" for doc in documents[:3]
            )
            prompt = (
                f"You are a retrieval-augmented assistant. "
                f"Use the retrieved document chunks to answer the user's query. "
                f"If the answer cannot be found in the retrieved text, say so clearly.\n\n"
                f"Selected document: {best_entry.document_name}\n"
                f"Keywords: {', '.join(best_entry.keywords)}\n"
                f"Category: {best_entry.category}\n\n"
                f"Query: {query_text}\n\n"
                f"Retrieved content:\n{context}\n\n"
                "Answer:"
            )

        llm = ChatOllama(
            model=self.llm_model_name,
            temperature=0,
            num_predict=self.llm_predict_tokens,
        )
        result = llm.invoke(prompt)
        content = self._coerce_content(result.content)
        return content.strip()

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
