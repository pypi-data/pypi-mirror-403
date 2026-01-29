"""
Knowledge ingestion and management module for AiCippy.

Provides:
- Feed crawling and parsing
- Content summarization
- S3 storage management
- Knowledge Base indexing
- Semantic search
"""

from __future__ import annotations

from aicippy.knowledge.crawler import FeedCrawler
from aicippy.knowledge.summarizer import ContentSummarizer
from aicippy.knowledge.indexer import KnowledgeIndexer
from aicippy.knowledge.project_scanner import ProjectScanner, ProjectInfo

__all__ = [
    "FeedCrawler",
    "ContentSummarizer",
    "KnowledgeIndexer",
    "ProjectScanner",
    "ProjectInfo",
]
