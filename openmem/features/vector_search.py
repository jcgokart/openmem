"""
Semantic Search with sqlite-vec
Vector-based semantic search for better relevance
"""

import sqlite3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Search result with relevance score"""
    id: int
    type: str
    content: str
    metadata: dict
    tags: list
    priority: int
    created_at: str
    score: float


class VectorSearch:
    """Semantic search using sqlite-vec"""
    
    def __init__(self, storage, embedding_dim: int = 384):
        self.storage = storage
        self.embedding_dim = embedding_dim
        self._init_vector_table()
    
    def _init_vector_table(self):
        """Initialize vector table"""
        try:
            import sqlite_vec
            
            conn = self.storage._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_vectors
                USING vec0(
                    memory_id INTEGER PRIMARY KEY,
                    embedding FLOAT[{self.embedding_dim}]
                )
            """)
            conn.commit()
            
            self._vec_available = True
        except Exception as e:
            print(f"⚠️ sqlite-vec not available, semantic search disabled: {e}")
            self._vec_available = False
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using a simple model or API"""
        try:
            from sentence_transformers import SentenceTransformer
            if not hasattr(self, '_model'):
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = self._model.encode(text)
            return embedding.tolist()
        except ImportError:
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Simple embedding fallback using hash-based approach"""
        import hashlib
        
        words = text.lower().split()
        embedding = [0.0] * self.embedding_dim
        
        for word in words:
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % self.embedding_dim
            embedding[idx] += 1.0
        
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def add_embedding(self, memory_id: int, text: str):
        """Add embedding for a memory"""
        if not self._vec_available:
            return False
        
        try:
            import sqlite_vec
            
            conn = self.storage._get_connection()
            cursor = conn.cursor()
            
            embedding = self.get_embedding(text)
            
            cursor.execute("""
                INSERT OR REPLACE INTO memory_vectors(memory_id, embedding)
                VALUES (?, ?)
            """, (memory_id, embedding))
            conn.commit()
            
            return True
        except Exception as e:
            print(f"⚠️ Failed to add embedding: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Semantic search for similar memories"""
        if not self._vec_available:
            return []
        
        try:
            import sqlite_vec
            
            conn = self.storage._get_connection()
            cursor = conn.cursor()
            
            query_embedding = self.get_embedding(query)
            
            cursor.execute("""
                SELECT v.memory_id, v.distance
                FROM memory_vectors v
                WHERE v.embedding MATCH ?
                ORDER BY v.distance
                LIMIT ?
            """, (query_embedding, top_k))
            
            results = []
            for row in cursor.fetchall():
                memory_id, distance = row
                
                cursor.execute("""
                    SELECT id, type, content, metadata, tags, priority, created_at
                    FROM memories WHERE id = ?
                """, (memory_id,))
                
                mem_row = cursor.fetchone()
                if mem_row:
                    results.append(SearchResult(
                        id=mem_row[0],
                        type=mem_row[1],
                        content=mem_row[2],
                        metadata=mem_row[3] or {},
                        tags=mem_row[4] or [],
                        priority=mem_row[5] or 0,
                        created_at=mem_row[6],
                        score=1.0 / (1.0 + distance)
                    ))
            
            return results
        except Exception as e:
            print(f"⚠️ Semantic search failed: {e}")
            return []
    
    def hybrid_search(self, query: str, limit: int = 10,
                      fts_weight: float = 0.5, vec_weight: float = 0.5) -> List[SearchResult]:
        """Hybrid search combining FTS5 and vector search"""
        fts_results = self.storage.search(query, limit * 2)
        vec_results = self.search_similar(query, limit * 2)
        
        fts_scores = {}
        for i, r in enumerate(fts_results):
            fts_scores[r.get('id', i)] = 1.0 / (1.0 + i)
        
        vec_scores = {}
        for r in vec_results:
            vec_scores[r.id] = r.score
        
        all_ids = set(fts_scores.keys()) | set(vec_scores.keys())
        
        combined = []
        for mid in all_ids:
            fts_s = fts_scores.get(mid, 0)
            vec_s = vec_scores.get(mid, 0)
            combined_score = fts_weight * fts_s + vec_weight * vec_s
            combined.append((mid, combined_score))
        
        combined.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for mid, score in combined[:limit]:
            cursor = self.storage._get_connection().cursor()
            cursor.execute("""
                SELECT id, type, content, metadata, tags, priority, created_at
                FROM memories WHERE id = ?
            """, (mid,))
            
            row = cursor.fetchone()
            if row:
                results.append(SearchResult(
                    id=row[0],
                    type=row[1],
                    content=row[2],
                    metadata=row[3] or {},
                    tags=row[4] or [],
                    priority=row[5] or 0,
                    created_at=row[6],
                    score=score
                ))
        
        return results


if __name__ == "__main__":
    print("=" * 60)
    print("Vector Search Test")
    print("=" * 60)
    
    print("\n[Simple Embedding Test]")
    text = "Use JWT for authentication"
    embedding = VectorSearch(None, embedding_dim=384)._simple_embedding(text)
    print(f"Text: {text}")
    print(f"Embedding dim: {len(embedding)}")
    print(f"First 10 values: {embedding[:10]}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
