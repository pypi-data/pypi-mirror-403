"""
KnowledgeBaseModule for managing knowledge base operations
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from lyzr.base import BaseModule
from lyzr.exceptions import ValidationError
from lyzr.knowledge_base.models import QueryResult, Document
from lyzr.knowledge_base.config import KnowledgeBaseConfig
from lyzr.knowledge_base.entity import KnowledgeBase, KnowledgeBaseList

if TYPE_CHECKING:
    from lyzr.http import HTTPClient
    from lyzr.urls import ServiceURLs


class KnowledgeBaseModule(BaseModule):
    """
    Module for managing knowledge bases (RAG configurations)

    Can be used standalone or through Studio client.

    Example (Standalone):
        >>> from lyzr.http import HTTPClient
        >>> from lyzr.knowledge_base import KnowledgeBaseModule
        >>> http = HTTPClient(api_key="sk-xxx", base_url="https://rag-prod.studio.lyzr.ai")
        >>> kbs = KnowledgeBaseModule(http)
        >>> kb = kbs.create(name="support_kb")

    Example (Through Studio):
        >>> from lyzr import Studio
        >>> studio = Studio(api_key="sk-xxx")
        >>> kb = studio.create_knowledge_base(name="support_kb")
    """

    def __init__(self, http_client: 'HTTPClient', env_config: 'ServiceURLs'):
        """
        Initialize KnowledgeBaseModule

        Note: Creates a separate HTTP client for RAG API (different base URL)
        Uses longer timeout (300s) for document processing and website crawling.

        Args:
            http_client: Main HTTP client (for api_key)
            env_config: Environment URL configuration
        """
        from lyzr.http import HTTPClient

        # Create new HTTP client for RAG API with longer timeout
        # Document processing and website crawling can take several minutes
        self._http = HTTPClient(
            api_key=http_client.api_key,
            base_url=env_config.rag_api,  # Use environment-specific URL
            timeout=300  # 5 minutes for RAG operations
        )

    def _make_smart_kb(self, kb_data: Dict[str, Any], name: Optional[str] = None) -> KnowledgeBase:
        """
        Create smart KnowledgeBase with injected clients

        Args:
            kb_data: Raw KB data from API
            name: Optional name to inject (API doesn't return it)

        Returns:
            KnowledgeBase: Smart KB with methods
        """
        # Normalize id field (create returns "id", list/get returns "_id")
        if "id" in kb_data and "_id" not in kb_data:
            kb_data["_id"] = kb_data["id"]

        # Inject name if provided (API doesn't return it)
        if name and "name" not in kb_data:
            kb_data["name"] = name

        kb = KnowledgeBase(**kb_data)
        kb._http = self._http
        kb._kb_module = self
        return kb

    def create(
        self,
        name: str,
        vector_store: str = "qdrant",
        embedding_model: str = "text-embedding-3-large",
        llm_model: str = "gpt-4o",
        description: Optional[str] = None,
        **kwargs
    ) -> KnowledgeBase:
        """
        Create a new knowledge base

        Args:
            name: KB name (lowercase, numbers, underscores only)
            vector_store: Vector store type (qdrant, weaviate, pg_vector, milvus, neptune)
            embedding_model: Embedding model name (default: text-embedding-3-large)
            llm_model: LLM model name (default: gpt-4o)
            description: KB description
            **kwargs: Additional configuration

        Returns:
            KnowledgeBase: Created smart KB object

        Raises:
            ValidationError: If name format is invalid
            APIError: If API request fails

        Example:
            >>> kb = kbs.create(
            ...     name="customer_support",
            ...     description="Customer support docs",
            ...     vector_store="qdrant"
            ... )
        """
        # Build configuration
        config = KnowledgeBaseConfig(
            name=name,
            vector_store=vector_store,
            embedding_model=embedding_model,
            llm_model=llm_model,
            description=description,
            **kwargs
        )

        # Make API request
        response = self._http.post("/v3/rag/", json=config.to_api_dict())

        # API returns KB data but without the name field
        # Inject the name we used for creation
        return self._make_smart_kb(response, name=name)

    def get(self, kb_id: str) -> KnowledgeBase:
        """
        Get knowledge base by ID

        Args:
            kb_id: Knowledge base ID

        Returns:
            KnowledgeBase: Smart KB object

        Raises:
            NotFoundError: If KB doesn't exist
            APIError: If API request fails

        Example:
            >>> kb = kbs.get("kb_abc123")
            >>> print(kb.name)
        """
        response = self._http.get(f"/v3/rag/{kb_id}/")
        return self._make_smart_kb(response)

    def list(self, user_id: Optional[str] = None) -> KnowledgeBaseList:
        """
        List knowledge bases

        Args:
            user_id: Optional user ID to filter by (defaults to API key)

        Returns:
            KnowledgeBaseList: List of KBs (iterable)

        Example:
            >>> all_kbs = kbs.list()
            >>> for kb in all_kbs:
            ...     print(kb.name)
        """
        # Use api_key as user_id if not provided
        if not user_id:
            # Extract from HTTP client - use the api_key value
            user_id = self._http.api_key

        response = self._http.get(f"/v3/rag/user/{user_id}/")

        # Handle response format - API returns {"configs": [...]}
        if isinstance(response, dict) and "configs" in response:
            kb_data_list = response["configs"]
            kb_list = [self._make_smart_kb(kb_data) for kb_data in kb_data_list]
            return KnowledgeBaseList(
                knowledge_bases=kb_list,
                total=len(kb_list)
            )
        elif isinstance(response, list):
            kb_list = [self._make_smart_kb(kb_data) for kb_data in response]
            return KnowledgeBaseList(knowledge_bases=kb_list, total=len(kb_list))
        elif isinstance(response, dict):
            kb_data = response.get("knowledge_bases", response.get("data", []))
            kb_list = [self._make_smart_kb(kb) for kb in kb_data]
            return KnowledgeBaseList(
                knowledge_bases=kb_list,
                total=response.get("total", len(kb_list))
            )
        else:
            return KnowledgeBaseList(knowledge_bases=[])

    def update(self, kb_id: str, **kwargs) -> KnowledgeBase:
        """
        Update knowledge base configuration

        Args:
            kb_id: Knowledge base ID
            **kwargs: Fields to update

        Returns:
            KnowledgeBase: Updated KB object

        Example:
            >>> kb = kbs.update("kb_123", description="Updated desc")
        """
        if not kwargs:
            raise ValidationError("No fields provided for update")

        response = self._http.put(f"/v3/rag/{kb_id}/", json=kwargs)

        # API returns {"success": True}, not KB data
        # Fetch updated KB
        return self.get(kb_id)

    def delete(self, kb_id: str) -> bool:
        """
        Delete a knowledge base

        Args:
            kb_id: Knowledge base ID

        Returns:
            bool: True if successful

        Example:
            >>> success = kbs.delete("kb_123")
        """
        return self._http.delete(f"/v3/rag/{kb_id}/")

    def bulk_delete(self, kb_ids: List[str]) -> bool:
        """
        Delete multiple knowledge bases

        Args:
            kb_ids: List of KB IDs to delete

        Returns:
            bool: True if successful

        Example:
            >>> kbs.bulk_delete(["kb_1", "kb_2", "kb_3"])
        """
        if not kb_ids:
            raise ValidationError("kb_ids cannot be empty")

        response = self._http.post(
            "/v3/rag/bulk-delete/",
            json={"config_ids": kb_ids}
        )
        return True

    # Internal methods (used by KnowledgeBase methods)

    def _train_pdf(self, rag_id: str, file_path: str, **kwargs) -> bool:
        """Internal: Add PDF to knowledge base"""
        return self._http.post_file(
            path="/v3/train/pdf/",
            file_path=file_path,
            file_field="file",
            params={"rag_id": rag_id},
            data={k: str(v) for k, v in kwargs.items() if k in ["chunk_size", "chunk_overlap", "data_parser"]}
        )
        return True

    def _train_docx(self, rag_id: str, file_path: str, **kwargs) -> bool:
        """Internal: Add DOCX to knowledge base"""
        self._http.post_file(
            path="/v3/train/docx/",
            file_path=file_path,
            file_field="file",
            params={"rag_id": rag_id},
            data={k: str(v) for k, v in kwargs.items() if k in ["chunk_size", "chunk_overlap", "data_parser"]}
        )
        return True

    def _train_txt(self, rag_id: str, file_path: str, **kwargs) -> bool:
        """Internal: Add TXT to knowledge base"""
        self._http.post_file(
            path="/v3/train/txt/",
            file_path=file_path,
            file_field="file",
            params={"rag_id": rag_id},
            data={k: str(v) for k, v in kwargs.items() if k in ["chunk_size", "chunk_overlap", "data_parser"]}
        )
        return True

    def _train_website(self, rag_id: str, urls: List[str], **kwargs) -> bool:
        """Internal: Add website to knowledge base"""
        payload = {
            "urls": urls,
            "source": kwargs.get("source", "website"),
            "max_crawl_pages": kwargs.get("max_pages", 10),
            "max_crawl_depth": kwargs.get("max_depth", 2),
            "chunk_size": kwargs.get("chunk_size", 1024),
            "chunk_overlap": kwargs.get("chunk_overlap", 128),
        }

        # Add optional parameters
        if "dynamic_content_wait_secs" in kwargs:
            payload["dynamic_content_wait_secs"] = kwargs["dynamic_content_wait_secs"]

        self._http.post(
            path="/v3/train/website/",
            params={"rag_id": rag_id},
            json=payload
        )
        return True

    def _train_text(self, rag_id: str, data: List[Dict[str, str]], **kwargs) -> bool:
        """Internal: Add text to knowledge base"""
        payload = {
            "data": data,
            "chunk_size": kwargs.get("chunk_size", 1024),
            "chunk_overlap": kwargs.get("chunk_overlap", 128),
        }

        self._http.post(
            path="/v3/train/text/",
            params={"rag_id": rag_id},
            json=payload
        )
        return True

    def _query(self, rag_id: str, query: str, **kwargs) -> List[QueryResult]:
        """Internal: Query knowledge base"""
        params = {
            "query": query,
            "top_k": kwargs.get("top_k", 5),
        }

        # Add optional parameters
        if "retrieval_type" in kwargs:
            params["retrieval_type"] = kwargs["retrieval_type"]
        if "score_threshold" in kwargs:
            params["score_threshold"] = kwargs["score_threshold"]
        if "lambda_param" in kwargs:
            params["lambda_param"] = kwargs["lambda_param"]
        if "time_decay_factor" in kwargs:
            params["time_decay_factor"] = kwargs["time_decay_factor"]

        response = self._http.get(f"/v3/rag/{rag_id}/retrieve/", params=params)

        # Parse results
        results = response.get("results", [])
        return [QueryResult(**result) for result in results]

    def _list_documents(self, rag_id: str) -> List[Document]:
        """Internal: List documents in KB"""
        response = self._http.get(f"/v3/rag/documents/{rag_id}/")

        # API returns a simple list of document names (strings)
        if isinstance(response, list):
            # Convert strings to Document objects
            return [
                Document(id=f"doc_{i}", source=doc_name, text=None)
                for i, doc_name in enumerate(response)
            ]
        else:
            # Fallback if format changes
            documents = response.get("documents", [])
            return [Document(**doc) if isinstance(doc, dict) else Document(id=f"doc_{i}", source=str(doc)) for i, doc in enumerate(documents)]

    def _delete_documents(self, rag_id: str, doc_ids: List[str]) -> bool:
        """Internal: Delete documents from KB"""
        self._http.delete(
            f"/v3/rag/{rag_id}/docs/",
            json_body={"document_ids": doc_ids}
        )
        return True

    def _reset(self, rag_id: str) -> bool:
        """Internal: Clear all documents from KB"""
        self._http.delete(f"/v3/rag/{rag_id}/reset/")
        return True
