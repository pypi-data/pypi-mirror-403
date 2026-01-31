from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np


class VectorIndex(ABC):
    def __init__(self, dim: int):
        self.dim = dim

    @abstractmethod
    def add(self, ids: List[str], vectors: np.ndarray):
        pass

    @abstractmethod
    def remove(self, ids: List[str]):
        pass

    @abstractmethod
    def search(
        self,
        query: np.ndarray,
        k: int
    ) -> List[Tuple[str, float]]:
        """
        Returns a list of (id, score)
        """
        pass
