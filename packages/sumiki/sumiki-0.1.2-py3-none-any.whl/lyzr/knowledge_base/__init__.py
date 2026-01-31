"""
Knowledge Base module for managing RAG configurations

This module provides tools for creating, managing, and querying knowledge bases
for Retrieval-Augmented Generation (RAG).

Main Classes:
    - KnowledgeBase: Smart KB object with methods for adding documents and querying
    - KnowledgeBaseConfig: Configuration for creating a new KB
    - KnowledgeBaseModule: Module for managing KB lifecycle (create, list, delete)
    - QueryResult: Result from a KB query
    - Document: Document metadata in a KB
"""

from lyzr.knowledge_base.models import QueryResult, Document
from lyzr.knowledge_base.config import KnowledgeBaseConfig, KnowledgeBaseRuntimeConfig
from lyzr.knowledge_base.entity import KnowledgeBase, KnowledgeBaseList
from lyzr.knowledge_base.module import KnowledgeBaseModule

__all__ = [
    "KnowledgeBase",
    "KnowledgeBaseConfig",
    "KnowledgeBaseRuntimeConfig",
    "KnowledgeBaseList",
    "KnowledgeBaseModule",
    "QueryResult",
    "Document",
]
