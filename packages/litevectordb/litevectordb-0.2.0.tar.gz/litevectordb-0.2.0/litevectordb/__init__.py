# litevectordb/__init__.py
"""
LiteVectorDB - Banco de dados vetorial local, leve e simples.

Uso básico:
    >>> from litevectordb import LocalVectorDB
    >>> db = LocalVectorDB(path="meu_banco.db", dim=64)
    >>> db.add_texts(["Python é uma linguagem popular"])
    >>> resultados = db.similarity_search("linguagem de programação")
"""

from .client import LocalVectorDB, DocumentResult
from .vector_store import VectorStore
from .memory import MemoryDB
from .embeddings import fake_embed

__version__ = "0.2.0"

__all__ = [
    "LocalVectorDB",
    "VectorStore",
    "MemoryDB",
    "DocumentResult",
    "fake_embed",
    "__version__",
]
