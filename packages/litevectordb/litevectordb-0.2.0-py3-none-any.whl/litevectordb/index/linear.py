import numpy as np
from typing import List, Tuple
from .base import VectorIndex


class LinearIndex(VectorIndex):
    def __init__(self, dim: int):
        super().__init__(dim)
        self._vectors = {}

    def add(self, ids: List[str], vectors: np.ndarray):
        for _id, vec in zip(ids, vectors):
            self._vectors[_id] = vec

    def remove(self, ids: List[str]):
        for _id in ids:
            self._vectors.pop(_id, None)

    def search(self, query: np.ndarray, k: int) -> List[Tuple[str, float]]:
        results = []

        for _id, vec in self._vectors.items():
            score = float(np.dot(query, vec))
            results.append((_id, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
