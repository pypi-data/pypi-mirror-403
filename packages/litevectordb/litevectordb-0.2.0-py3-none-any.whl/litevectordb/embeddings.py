# litevectordb/embeddings.py
from __future__ import annotations

import hashlib
import numpy as np


def fake_embed(text: str, dim: int = 64) -> np.ndarray:
    """
    Exemplo de "embedding" determinístico, só p/ brincar.
    Na vida real, você pluga OpenAI, Ollama, etc.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # repete hash até preencher a dimensão
    raw = (h * ((dim // len(h)) + 1))[:dim]
    arr = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
    arr = arr / (255.0 + 1e-8)
    return arr
