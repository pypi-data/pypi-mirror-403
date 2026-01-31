# litevectordb/vector_store.py
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

import numpy as np

from litevectordb.index.linear import LinearIndex


class VectorStore:
    """
    Mini banco vetorial local baseado em SQLite + NumPy.
    Estilo Chroma, mas bem leve.
    """

    def __init__(self, path: str, dim: int):
        """
        path: caminho do arquivo .db (ex: "memories.db")
        dim: dimensão dos vetores (ex: 1536)
        """
        self.path = path
        self.dim = dim
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA journal_mode=WAL;")  # melhor p/ concorrência leve
        self._create_schema()

        self.index = LinearIndex(dim=self.dim)
        self._load_index()

    def _load_index(self):
        """Carrega vetores do disco para a memória no startup"""
        cur = self._conn.cursor()
        cur.execute("SELECT id, vector FROM documents")
        rows = cur.fetchall()
        
        if not rows:
            return

        ids = []
        vectors = []
        for doc_id, blob in rows:
            ids.append(str(doc_id))
            vectors.append(self._decode_vector(blob))
        
        if ids:
            self.index.add(ids, np.array(vectors))

    # ---------- setup ----------

    def _create_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                content TEXT,
                metadata TEXT,
                vector BLOB NOT NULL,
                dim INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )
        self._conn.commit()

    # ---------- helpers de encode/decode ----------

    def _encode_vector(self, v: np.ndarray) -> bytes:
        v = np.asarray(v, dtype=np.float32)
        if v.shape != (self.dim,):
            raise ValueError(
                f"expected vector of shape ({self.dim},), got {v.shape}"
            )
        return v.tobytes()

    def _decode_vector(self, blob: bytes) -> np.ndarray:
        return np.frombuffer(blob, dtype=np.float32)

    # ---------- operações básicas ----------

    def add(
        self,
        vector: np.ndarray,
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        key: Optional[str] = None,
    ) -> int:
        """
        Insere um novo documento vetorial.
        Retorna o id (int) gerado pelo banco.
        """
        blob = self._encode_vector(vector)
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)

        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO documents (key, content, metadata, vector, dim)
            VALUES (?, ?, ?, ?, ?)
            """,
            (key, content, meta_json, blob, self.dim),
        )
        self._conn.commit()
        
        doc_id = cur.lastrowid
        self.index.add([str(doc_id)], np.array([vector]))
        
        return doc_id

    def upsert(
        self,
        vector: np.ndarray,
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        key: Optional[str] = None,
    ) -> int:
        """
        Insere ou atualiza por 'key'.
        Se key existir: atualiza content/metadata/vector.
        Se não existir: insere novo registro.
        """
        if key is None:
            # sem key, cai no add normal
            return self.add(vector, content, metadata, key=None)

        blob = self._encode_vector(vector)
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)

        cur = self._conn.cursor()
        cur.execute("SELECT id FROM documents WHERE key = ?", (key,))
        row = cur.fetchone()

        if row:
            doc_id = row[0]
            cur.execute(
                """
                UPDATE documents
                SET content = ?, metadata = ?, vector = ?, dim = ?
                WHERE id = ?
                """,
                (content, meta_json, blob, self.dim, doc_id),
            )
            self._conn.commit()
            
            # Atualiza índice
            self.index.add([str(doc_id)], np.array([vector]))
            
            return doc_id
        else:
            return self.add(vector, content, metadata, key=key)

    def get(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um documento por id.
        """
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT id, key, content, metadata, vector
            FROM documents WHERE id = ?
            """,
            (doc_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        _id, key, content, meta_json, blob = row
        return {
            "id": _id,
            "key": key,
            "content": content,
            "metadata": json.loads(meta_json or "{}"),
            "vector": self._decode_vector(blob),
        }

    def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT id, key, content, metadata, vector
            FROM documents WHERE key = ?
            """,
            (key,),
        )
        row = cur.fetchone()
        if not row:
            return None

        _id, key, content, meta_json, blob = row
        return {
            "id": _id,
            "key": key,
            "content": content,
            "metadata": json.loads(meta_json or "{}"),
            "vector": self._decode_vector(blob),
        }

    def delete(self, doc_id: int) -> None:
        self.index.remove([str(doc_id)])
        cur = self._conn.cursor()
        cur.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        self._conn.commit()

    def delete_by_key(self, key: str) -> None:
        cur = self._conn.cursor()
        # Precisa buscar ID antes de deletar p/ atualizar índice
        cur.execute("SELECT id FROM documents WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            doc_id = row[0]
            self.index.remove([str(doc_id)])
            cur.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            self._conn.commit()

    # ---------- busca vetorial (cosine) ----------

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        min_score: float = -1.0,
    ) -> List[Dict[str, Any]]:
        """
        Busca usando o índice vetorial interno.
        """
        results_index = self.index.search(query_vector, k=top_k)
        
        # Filtra por score min
        results_index = [r for r in results_index if r[1] >= min_score]
        
        if not results_index:
            return []

        # Recupera metadados do SQLite
        # ids no índice são strings, precisamos de ints
        ids_map = {int(r[0]): r[1] for r in results_index}
        ids_list = list(ids_map.keys())
        
        if not ids_list:
            return []

        placeholders = ",".join(["?"] * len(ids_list))
        cur = self._conn.cursor()
        query_sql = f"""
            SELECT id, key, content, metadata
            FROM documents 
            WHERE id IN ({placeholders})
        """
        cur.execute(query_sql, ids_list)
        rows = cur.fetchall()

        final_results = []
        for _id, key, content, meta_json in rows:
            score = ids_map.get(_id, 0.0)
            final_results.append({
                "id": _id,
                "key": key,
                "content": content,
                "metadata": json.loads(meta_json or "{}"),
                "score": score,
            })

        # Reordena porque SQL IN não garante ordem
        final_results.sort(key=lambda r: r["score"], reverse=True)
        return final_results

    # ---------- utilidades ----------

    def count(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documents")
        return int(cur.fetchone()[0])

    def close(self) -> None:
        self._conn.close()
