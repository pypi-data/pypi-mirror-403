# litevectordb/client.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import numpy as np

from .vector_store import VectorStore
from .embeddings import fake_embed  # depois você troca pelo real


class DocumentResult:
    def __init__(self, id: int, text: str, metadata: dict, score: float):
        self.id = id
        self.text = text
        self.metadata = metadata
        self.score = score


class LocalVectorDB:
    """
    Interface simples p/ usar direto, sem collections.
    """

    def __init__(self, path: str = "litevectordb.db", dim: int = 64):
        self._store = VectorStore(path, dim=dim)
        self.dim = dim

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[int]:
        metadatas = metadatas or [{} for _ in texts]
        if ids and len(ids) != len(texts):
            raise ValueError("len(ids) != len(texts)")

        inserted_ids: List[int] = []
        for i, text in enumerate(texts):
            vec = fake_embed(text, dim=self.dim)
            key = ids[i] if ids else None
            doc_id = self._store.add(
                vector=vec,
                content=text,
                metadata=metadatas[i],
                key=key,
            )
            inserted_ids.append(doc_id)
        return inserted_ids

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.2,
    ) -> List[DocumentResult]:
        q_vec = fake_embed(query, dim=self.dim)
        raw_results = self._store.search(
            query_vector=q_vec,
            top_k=top_k,
            min_score=min_score,
        )
        return [
            DocumentResult(
                id=r["id"],
                text=r["content"],
                metadata=r["metadata"],
                score=r["score"],
            )
            for r in raw_results
        ]
