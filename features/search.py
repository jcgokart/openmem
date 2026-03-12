"""
Enhanced Search
Chinese tokenization using jieba with FTS5 + BM25 ranking
"""

import sqlite3
import json
import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import jieba

from data.vocabularies import STOPWORDS, TECH_WORDS


class ChineseTokenizer:
    """Chinese tokenizer for FTS5"""
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenize Chinese text using jieba"""
        words = jieba.cut(text)
        
        tokens = []
        for word in words:
            word = word.strip()
            if len(word) > 0 and word not in STOPWORDS:
                if re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9\-._]+$', word):
                    tokens.append(word.lower())
        
        return tokens
    
    @staticmethod
    def tokenize_for_fts(text: str) -> str:
        """Tokenize for FTS5 (space-separated string)"""
        tokens = ChineseTokenizer.tokenize(text)
        return ' '.join(tokens)


class EnhancedSearch:
    """Enhanced search with Chinese tokenization"""
    
    def __init__(self, storage):
        self.storage = storage
    
    def _highlight_text(self, content: str, tokens: List[str], 
                       max_length: int = 200) -> str:
        """Highlight matched keywords"""
        if not tokens:
            return content[:max_length] + ('...' if len(content) > max_length else '')
        
        import re
        pattern = '|'.join([re.escape(t) for t in tokens])
        
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        if not matches:
            return content[:max_length] + ('...' if len(content) > max_length else '')
        
        start = max(0, matches[0].start() - 50)
        end = min(len(content), matches[-1].end() + 50)
        
        snippet = content[start:end]
        snippet = re.sub(f'({pattern})', r'<mark>\1</mark>', snippet, flags=re.IGNORECASE)
        
        if start > 0:
            snippet = '...' + snippet
        if end < len(content):
            snippet = snippet + '...'
        
        return snippet
    
    def search(self, query: str, limit: int = 10, use_chinese_tokenizer: bool = True,
              highlight: bool = True) -> List[Dict[str, Any]]:
        """Enhanced search with Chinese tokenization"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            if use_chinese_tokenizer:
                tokens = ChineseTokenizer.tokenize(query)
                fts_query = ' AND '.join(tokens)
            else:
                tokens = query.split()
                fts_query = query
            
            cursor.execute("""
                SELECT m.id, m.type, m.content, m.metadata, m.tags, m.priority, 
                       m.created_at, m.updated_at, m.expires_at, m.version,
                       bm25(memories_fts) as score
                FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE memories_fts MATCH ? AND bm25(memories_fts) < 0
                ORDER BY score ASC
                LIMIT ?
            """, (fts_query, limit))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = self.storage._row_to_dict(row[:10])
                result['score'] = row[10]
                
                if highlight:
                    result['highlight'] = self._highlight_text(result['content'], tokens)
                
                results.append(result)
            
            return results
            
        except Exception as e:
            return self._fallback_search(query, limit)
    
    def _fallback_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fallback search using LIKE"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, type, content, metadata, tags, priority, 
                       created_at, updated_at, expires_at, version
                FROM memories
                WHERE content LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (f'%{query}%', limit))
            
            rows = cursor.fetchall()
            return [self.storage._row_to_dict(row) for row in rows]
            
        except Exception as e:
            return []
    
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search by tags"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            conditions = ' OR '.join(['tags LIKE ?' for _ in tags])
            params = [f'%{tag}%' for tag in tags] + [limit]
            
            cursor.execute(f"""
                SELECT DISTINCT id, type, content, metadata, tags, priority, 
                       created_at, updated_at, expires_at, version
                FROM memories
                WHERE {conditions}
                ORDER BY created_at DESC
                LIMIT ?
            """, params)
            
            rows = cursor.fetchall()
            return [self.storage._row_to_dict(row) for row in rows]
            
        except Exception as e:
            return []
    
    def search_by_time_range(self, start_time: str, end_time: str, 
                             limit: int = 100) -> List[Dict[str, Any]]:
        """Search by time range"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, type, content, metadata, tags, priority, 
                       created_at, updated_at, expires_at, version
                FROM memories
                WHERE created_at BETWEEN ? AND ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (start_time, end_time, limit))
            
            rows = cursor.fetchall()
            return [self.storage._row_to_dict(row) for row in rows]
            
        except Exception as e:
            return []
    
    def search_by_type_and_content(self, type: str, content_query: str, 
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Search by type and content"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            tokens = ChineseTokenizer.tokenize(content_query)
            fts_query = ' AND '.join(tokens)
            
            cursor.execute("""
                SELECT m.id, m.type, m.content, m.metadata, m.tags, m.priority, 
                       m.created_at, m.updated_at, m.expires_at, m.version
                FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE m.type = ? AND memories_fts MATCH ?
                ORDER BY m.created_at DESC
                LIMIT ?
            """, (type, fts_query, limit))
            
            rows = cursor.fetchall()
            return [self.storage._row_to_dict(row) for row in rows]
            
        except Exception as e:
            cursor.execute("""
                SELECT id, type, content, metadata, tags, priority, 
                       created_at, updated_at, expires_at, version
                FROM memories
                WHERE type = ? AND content LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (type, f'%{content_query}%', limit))
            
            rows = cursor.fetchall()
            return [self.storage._row_to_dict(row) for row in rows]


if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced Search Test")
    print("=" * 60)
    
    print("\n[Chinese Tokenization Test]")
    text = "Decided to use microservices architecture"
    tokens = ChineseTokenizer.tokenize(text)
    print(f"Text: {text}")
    print(f"Tokens: {tokens}")
    
    text = "Decided to use monolithic architecture"
    tokens = ChineseTokenizer.tokenize(text)
    print(f"Text: {text}")
    print(f"Tokens: {tokens}")
    
    print("\n[FTS5 Format Test]")
    fts_text = ChineseTokenizer.tokenize_for_fts("Decided to use microservices architecture")
    print(f"FTS5 Format: {fts_text}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
