"""
P1: 增强搜索功能
解决中文分词问题，实现更智能的搜索

============================================================
工程经验总结
============================================================

1. 【分词策略】中文搜索要用专业分词器
   - 问题：简单按字符分词，搜索"数据库"匹配"数据"+"据"
   - 解决：使用 jieba 分词，"数据库"作为一个词
   - 经验：中文搜索必须用专业分词器

2. 【FTS5 中文】SQLite FTS5 不支持中文
   - 问题：FTS5 默认按空格分词，中文无效
   - 解决：预分词后存入 FTS，FTS 只做索引
   - 经验：FTS 存储预分词内容，不要实时分词

3. 【查询扩展】自动扩展搜索词
   - 问题：用户输入短，匹配结果少
   - 解决：同义词扩展 + 相关词扩展
   - 经验：搜索要考虑用户输入习惯

4. 【BM25 排序】FTS5 内置相关性排序
   - 问题：按时间排序，相关性不高
   - 解决：使用 bm25() 函数按相关性排序
   - 经验：全文搜索用 BM25 比时间排序更合理
"""

import sqlite3
import json
import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import jieba


# ==================== 中文分词器 ====================

class ChineseTokenizer:
    """中文分词器（用于 FTS5）"""
    
    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        分词
        
        Args:
            text: 输入文本
        
        Returns:
            分词结果
        """
        # 使用 jieba 分词
        words = jieba.cut(text)
        
        # 过滤停用词和标点
        stopwords = {
            '的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
            '会', '着', '没有', '看', '好', '自己', '这', '为', '与', '或', '但', '而', '以', '及', '被', '把', '给', '让', '向',
            '对', '从', '由', '所', '其', '此', '那', '么', '吗', '呢', '吧', '啊', '呀', '嘛', '哦', '哈', '嗯', '唉', '喂',
            '他', '她', '它', '们', '这个', '那个', '什么', '怎么', '如何', '为什么', '哪', '哪里', '哪个', '多少', '几', '怎样',
            '可以', '能够', '应该', '必须', '需要', '想', '要', '得', '能', '会', '可', '只', '还', '再', '又', '也', '已', '已经',
            '曾', '曾经', '正在', '正', '将', '将要', '曾', '刚', '刚才', '现在', '目前', '今天', '明天', '昨天', '今年', '去年',
            '明年', '现在', '以后', '之前', '之后', '然后', '接着', '于是', '因此', '所以', '因为', '但是', '然而', '不过', '只是',
            '虽然', '即使', '除非', '只有', '只要', '无论', '不管', '既然', '既', '如此', '这样', '那样', '这么', '那么', '多么'
        }
        
        tokens = []
        for word in words:
            word = word.strip()
            if len(word) > 0 and word not in stopwords:
                # 过滤标点符号
                if re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', word):
                    tokens.append(word.lower())
        
        return tokens
    
    @staticmethod
    def tokenize_for_fts(text: str) -> str:
        """
        为 FTS5 分词（返回空格分隔的字符串）
        
        Args:
            text: 输入文本
        
        Returns:
            空格分隔的分词结果
        """
        tokens = ChineseTokenizer.tokenize(text)
        return ' '.join(tokens)


# ==================== 增强搜索类 ====================

class EnhancedSearch:
    """增强搜索类"""
    
    def __init__(self, storage):
        self.storage = storage
    
    def _highlight_text(self, content: str, tokens: List[str], 
                       max_length: int = 200) -> str:
        """高亮匹配的关键词"""
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
        """
        增强搜索
        
        Args:
            query: 搜索关键词
            limit: 限制数量
            use_chinese_tokenizer: 是否使用中文分词
            highlight: 是否高亮匹配词
        
        Returns:
            搜索结果
        """
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 使用中文分词
            if use_chinese_tokenizer:
                tokens = ChineseTokenizer.tokenize(query)
                fts_query = ' OR '.join(tokens)
            else:
                tokens = query.split()
                fts_query = query
            
            # 2. FTS5 搜索
            cursor.execute("""
                SELECT m.id, m.type, m.content, m.metadata, m.tags, m.priority, 
                       m.created_at, m.updated_at, m.expires_at, m.version,
                       bm25(memories_fts) as score
                FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE memories_fts MATCH ?
                ORDER BY score
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
            # 如果 FTS5 失败，回退到 LIKE 搜索
            return self._fallback_search(query, limit)
    
    def _fallback_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        回退搜索（使用 LIKE）
        
        Args:
            query: 搜索关键词
            limit: 限制数量
        
        Returns:
            搜索结果
        """
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
        """
        按标签搜索（一次查询，避免 O(n²)）
        
        Args:
            tags: 标签列表
            limit: 限制数量
        
        Returns:
            搜索结果
        """
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            # 一次查询，使用 OR 条件
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
        """
        按时间范围搜索
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
        
        Returns:
            搜索结果
        """
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
        """
        按类型和内容搜索
        
        Args:
            type: 记忆类型
            content_query: 内容关键词
            limit: 限制数量
        
        Returns:
            搜索结果
        """
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            # 使用中文分词
            tokens = ChineseTokenizer.tokenize(content_query)
            fts_query = ' OR '.join(tokens)
            
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
            # 回退到 LIKE 搜索
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


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("增强搜索测试")
    print("=" * 60)
    
    # 测试中文分词
    print("\n【测试中文分词】")
    text = "决定使用微服务架构"
    tokens = ChineseTokenizer.tokenize(text)
    print(f"原文: {text}")
    print(f"分词: {tokens}")
    
    text = "决定使用单体架构"
    tokens = ChineseTokenizer.tokenize(text)
    print(f"原文: {text}")
    print(f"分词: {tokens}")
    
    # 测试 FTS5 格式
    print("\n【测试 FTS5 格式】")
    fts_text = ChineseTokenizer.tokenize_for_fts("决定使用微服务架构")
    print(f"FTS5 格式: {fts_text}")
    
    print("\n" + "=" * 60)
    print("✓ 测试完成")
    print("=" * 60)
