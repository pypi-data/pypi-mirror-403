"""
KnowledgeBase entity class with smart object methods
"""

from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr

if TYPE_CHECKING:
    from lyzr.http import HTTPClient
    from lyzr.knowledge_base.models import QueryResult, Document
    from lyzr.knowledge_base.config import KnowledgeBaseRuntimeConfig


class KnowledgeBase(BaseModel):
    """
    Smart KnowledgeBase - both data and behavior

    Represents a RAG configuration that can store and query documents.
    """

    id: str = Field(..., alias="_id", description="Knowledge base ID")
    name: Optional[str] = Field(None, description="Knowledge base name (not returned by API)")
    collection_name: str = Field(..., description="Vector DB collection name")
    description: Optional[str] = Field(None, description="KB description")

    # Provider configuration
    vector_db_credential_id: str = Field(..., description="Vector DB credential ID")
    vector_store_provider: str = Field(..., description="Vector store provider display name")
    embedding_model: str = Field(..., description="Embedding model name")
    embedding_credential_id: str = Field(..., description="Embedding credential ID")
    llm_model: str = Field(..., description="LLM model name")
    llm_credential_id: str = Field(..., description="LLM credential ID")

    # Settings
    semantic_data_model: bool = Field(default=False, description="Semantic data modeling enabled")
    user_id: Optional[str] = Field(None, description="User ID")
    api_key: Optional[str] = Field(None, description="API key")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    # Metadata
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    # Private fields (injected by KnowledgeBaseModule)
    _http: Optional['HTTPClient'] = PrivateAttr(default=None)
    _kb_module: Optional[Any] = PrivateAttr(default=None)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    def _ensure_clients(self):
        """Ensure HTTP client is available"""
        if not self._http or not self._kb_module:
            raise RuntimeError(
                "KnowledgeBase not properly initialized. "
                "Use Studio.create_knowledge_base() or Studio.get_knowledge_base()"
            )

    def add_pdf(
        self,
        file_path: str,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        **kwargs
    ) -> bool:
        """
        Add PDF document to knowledge base

        Args:
            file_path: Path to PDF file
            chunk_size: Size of text chunks (default: 1024)
            chunk_overlap: Overlap between chunks (default: 128)
            **kwargs: Additional parameters

        Returns:
            bool: True if successful

        Example:
            >>> kb = studio.create_knowledge_base(name="docs")
            >>> kb.add_pdf("manual.pdf", chunk_size=2048)
        """
        self._ensure_clients()
        return self._kb_module._train_pdf(
            self.id, file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs
        )

    def add_docx(
        self,
        file_path: str,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        **kwargs
    ) -> bool:
        """
        Add DOCX document to knowledge base

        Args:
            file_path: Path to DOCX file
            chunk_size: Size of text chunks (default: 1024)
            chunk_overlap: Overlap between chunks (default: 128)
            **kwargs: Additional parameters

        Returns:
            bool: True if successful

        Example:
            >>> kb.add_docx("report.docx")
        """
        self._ensure_clients()
        return self._kb_module._train_docx(
            self.id, file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs
        )

    def add_txt(
        self,
        file_path: str,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        **kwargs
    ) -> bool:
        """
        Add TXT file to knowledge base

        Args:
            file_path: Path to TXT file
            chunk_size: Size of text chunks (default: 1024)
            chunk_overlap: Overlap between chunks (default: 128)
            **kwargs: Additional parameters

        Returns:
            bool: True if successful

        Example:
            >>> kb.add_txt("faq.txt")
        """
        self._ensure_clients()
        return self._kb_module._train_txt(
            self.id, file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs
        )

    def add_website(
        self,
        url: Union[str, List[str]],
        max_pages: int = 10,
        max_depth: int = 2,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        **kwargs
    ) -> bool:
        """
        Add website content to knowledge base

        Args:
            url: Website URL or list of URLs
            max_pages: Maximum pages to crawl (default: 10)
            max_depth: Maximum crawl depth (default: 2)
            chunk_size: Size of text chunks (default: 1024)
            chunk_overlap: Overlap between chunks (default: 128)
            **kwargs: Additional parameters (dynamic_content_wait_secs, etc.)

        Returns:
            bool: True if successful

        Example:
            >>> kb.add_website("https://docs.company.com", max_pages=50, max_depth=3)
            >>> kb.add_website(["https://help.com", "https://faq.com"])
        """
        self._ensure_clients()
        urls = [url] if isinstance(url, str) else url
        return self._kb_module._train_website(
            self.id,
            urls,
            max_pages=max_pages,
            max_depth=max_depth,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs
        )

    def add_text(
        self,
        text: str,
        source: str,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
        **kwargs
    ) -> bool:
        """
        Add raw text to knowledge base

        Args:
            text: Text content
            source: Source identifier
            chunk_size: Size of text chunks (default: 1024)
            chunk_overlap: Overlap between chunks (default: 128)
            **kwargs: Additional parameters

        Returns:
            bool: True if successful

        Example:
            >>> kb.add_text("FAQ: Business hours are 9am-5pm", source="faq.txt")
        """
        self._ensure_clients()
        return self._kb_module._train_text(
            self.id,
            [{"text": text, "source": source}],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs
        )

    def query(
        self,
        query: str,
        top_k: int = 5,
        retrieval_type: str = "basic",
        score_threshold: float = 0.0,
        **kwargs
    ) -> List['QueryResult']:
        """
        Query the knowledge base

        Args:
            query: Search query string
            top_k: Number of results to return (default: 5)
            retrieval_type: Type of retrieval - one of:
                - 'basic': Standard vector similarity search
                - 'mmr': Maximal Marginal Relevance (diverse results)
                - 'hyde': Hypothetical Document Embeddings
                - 'time_aware': Time-decay weighted retrieval
            score_threshold: Minimum relevance score (0.0 to 1.0)
            **kwargs: Additional parameters (lambda_param, time_decay_factor)

        Returns:
            List[QueryResult]: List of relevant results

        Example:
            >>> results = kb.query("What are business hours?", top_k=3)
            >>> for result in results:
            ...     print(f"{result.score:.2f}: {result.text}")
        """
        self._ensure_clients()
        return self._kb_module._query(
            self.id,
            query,
            top_k=top_k,
            retrieval_type=retrieval_type,
            score_threshold=score_threshold,
            **kwargs
        )

    def list_documents(self) -> List['Document']:
        """
        List all documents in knowledge base

        Returns:
            List[Document]: List of documents

        Example:
            >>> docs = kb.list_documents()
            >>> for doc in docs:
            ...     print(doc.source)
        """
        self._ensure_clients()
        return self._kb_module._list_documents(self.id)

    def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        Delete specific documents from knowledge base

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            bool: True if successful

        Example:
            >>> kb.delete_documents(["doc_123", "doc_456"])
        """
        self._ensure_clients()
        return self._kb_module._delete_documents(self.id, doc_ids)

    def reset(self) -> bool:
        """
        Clear all documents from knowledge base

        Removes all documents but keeps the KB configuration.

        Returns:
            bool: True if successful

        Example:
            >>> kb.reset()  # Removes all documents
        """
        self._ensure_clients()
        return self._kb_module._reset(self.id)

    def update(self, **kwargs) -> 'KnowledgeBase':
        """
        Update knowledge base configuration

        Args:
            **kwargs: Fields to update (description, etc.)

        Returns:
            KnowledgeBase: Updated KB instance

        Example:
            >>> kb = kb.update(description="Updated description")
        """
        self._ensure_clients()
        return self._kb_module.update(self.id, **kwargs)

    def delete(self) -> bool:
        """
        Delete this knowledge base

        Returns:
            bool: True if successful

        Example:
            >>> kb.delete()
        """
        self._ensure_clients()
        return self._kb_module.delete(self.id)

    def with_config(
        self,
        top_k: int = 10,
        retrieval_type: str = "basic",
        score_threshold: float = 0.0,
        time_decay_factor: float = 0.4,
        **kwargs
    ) -> 'KnowledgeBaseRuntimeConfig':
        """
        Create runtime config for this KB

        Used when passing KB to agent.run() with custom settings.

        Args:
            top_k: Number of results to retrieve (default: 10)
            retrieval_type: Retrieval method (basic, semantic, keyword, hybrid)
            score_threshold: Minimum relevance score (0.0 to 1.0)
            time_decay_factor: Time-based relevance decay factor
            **kwargs: Additional config parameters

        Returns:
            KnowledgeBaseRuntimeConfig: Runtime configuration wrapper

        Example:
            >>> # Pass KB with custom config to agent.run()
            >>> response = agent.run(
            ...     "Question?",
            ...     knowledge_bases=[kb.with_config(top_k=5, score_threshold=0.7)]
            ... )
        """
        from lyzr.knowledge_base.config import KnowledgeBaseRuntimeConfig
        return KnowledgeBaseRuntimeConfig(
            kb=self,
            top_k=top_k,
            retrieval_type=retrieval_type,
            score_threshold=score_threshold,
            time_decay_factor=time_decay_factor,
            **kwargs
        )

    def to_agentic_config(
        self,
        top_k: int = 10,
        retrieval_type: str = "basic",
        score_threshold: float = 0.0,
        time_decay_factor: float = 0.4
    ) -> Dict[str, Any]:
        """
        Convert to agentic_rag config format

        This is the format expected by the inference API features array.

        Args:
            top_k: Number of results to retrieve
            retrieval_type: Retrieval method
            score_threshold: Minimum relevance score
            time_decay_factor: Time-based decay factor

        Returns:
            Dict: Configuration in agentic_rag format

        Example:
            >>> config = kb.to_agentic_config(top_k=5)
            >>> # Used internally when KB is passed to agent.run()
        """
        return {
            "rag_id": self.id,
            "name": self.name,
            "description": self.description or f"Knowledge base: {self.name}",
            "top_k": top_k,
            "retrieval_type": retrieval_type,
            "score_threshold": score_threshold,
            "time_decay_factor": time_decay_factor
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excludes private fields)"""
        return self.model_dump(by_alias=False, exclude_none=True)

    def __str__(self) -> str:
        return f"KnowledgeBase(id='{self.id}', name='{self.name}', provider='{self.vector_store_provider}')"

    def __repr__(self) -> str:
        return self.__str__()


class KnowledgeBaseList(BaseModel):
    """List of knowledge bases"""
    knowledge_bases: List[KnowledgeBase] = Field(default_factory=list, description="List of KBs")
    total: Optional[int] = Field(None, description="Total count")

    def __iter__(self):
        return iter(self.knowledge_bases)

    def __len__(self):
        return len(self.knowledge_bases)

    def __getitem__(self, index):
        return self.knowledge_bases[index]
