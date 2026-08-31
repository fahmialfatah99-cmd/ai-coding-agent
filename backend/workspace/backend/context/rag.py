"""
RAG Context Engine menggunakan pgvector untuk pencarian semantik codebase.
"""
import os
from typing import List, Dict, Any
import asyncpg
from openai import AsyncOpenAI

class RAGContextEngine:
    def __init__(self, dsn: str = None):
        self.dsn = dsn or os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aicoding")
        self.client = AsyncOpenAI()

    async def get_embedding(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            input=[text.replace("\n", " ")],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    async def hybrid_search(self, project_id: str, query: str, top_k: int = 5) -> str:
        """
        Melakukan vector similarity search menggunakan pgvector (<-> cosine distance)
        """
        try:
            query_vector = await self.get_embedding(query)
            conn = await asyncpg.connect(self.dsn)
            
            # pgvector query menggunakan operator <=> (cosine distance)
            rows = await conn.fetch(
                """
                SELECT file_path, chunk_content, 1 - (embedding <=> $1::vector) AS similarity
                FROM code_embeddings
                WHERE project_id = $2
                ORDER BY embedding <=> $1::vector ASC
                LIMIT $3;
                """,
                str(query_vector), project_id, top_k
            )
            await conn.close()

            if not rows:
                return "Tidak ada chunk kode relevan ditemukan via RAG."

            result_str = ""
            for r in rows:
                result_str += f"--- File: {r['file_path']} (Similarity: {r['similarity']:.3f}) ---\n{r['chunk_content']}\n\n"
            return result_str
        except Exception as e:
            # Fallback jika database belum running/terhubung saat dev
            return f"[RAG Warning: Gagal terhubung ke database vector: {str(e)}]"
