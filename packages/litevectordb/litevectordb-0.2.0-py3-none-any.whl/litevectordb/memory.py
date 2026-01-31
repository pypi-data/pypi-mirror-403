# litevectordb/memory.py
from __future__ import annotations

from datetime import datetime
import numpy as np

from .vector_store import VectorStore
from .embeddings import fake_embed  # troque depois por openai/ollama


class MemoryDB:
    """
    Camada de alto nível: memória estilo Chroma.
    Usa o VectorStore por baixo.
    """

    def __init__(self, db_path: str, dim: int = 64):
        self.store = VectorStore(db_path, dim=dim)
        self.dim = dim

    # ============================================================
    # Gravar memória
    # ============================================================
    def store_memory(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict = None,
    ) -> int:
        """
        Gera embedding do conteúdo e salva como memória.
        """
        vec = fake_embed(content, dim=self.dim)

        key = f"{session_id}:{datetime.utcnow().isoformat()}"
        metadata = metadata or {}
        metadata.update({"session_id": session_id, "role": role})

        return self.store.add(
            vector=vec,
            content=content,
            metadata=metadata,
            key=key,
        )

    # ============================================================
    # Recuperar memórias relevantes
    # ============================================================
    def retrieve_memory(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.2,
    ):
        """
        Busca vetorial + filtro por sessão.
        """
        q_vec = fake_embed(query, dim=self.dim)
        results = self.store.search(q_vec, top_k=top_k, min_score=min_score)

        # filtrar por sessão (como faria o Chroma com "where")
        filtered = [
            r for r in results
            if r["metadata"].get("session_id") == session_id
        ]

        return filtered

    # ============================================================
    # Utilidades
    # ============================================================
    def count(self):
        return self.store.count()

    def close(self):
        self.store.close()
