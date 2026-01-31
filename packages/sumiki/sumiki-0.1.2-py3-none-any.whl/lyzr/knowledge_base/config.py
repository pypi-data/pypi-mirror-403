"""
Configuration classes for Knowledge Base creation and runtime
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field, model_validator, ConfigDict
import re
import random
import string
from lyzr.vector_stores import VectorStoreResolver

if TYPE_CHECKING:
    from lyzr.knowledge_base.entity import KnowledgeBase


class KnowledgeBaseConfig(BaseModel):
    """Configuration for creating a knowledge base"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Knowledge base name (lowercase, numbers, underscores only)"
    )
    collection_name: Optional[str] = Field(
        None,
        description="Vector DB collection name (auto-generated if not provided)"
    )
    description: Optional[str] = Field(None, max_length=1000, description="KB description")

    # Vector store configuration
    vector_store: str = Field("qdrant", description="Vector store type (qdrant, weaviate, etc.)")
    vector_db_credential_id: Optional[str] = Field(None, description="Custom vector DB credential ID")
    vector_store_provider: Optional[str] = Field(None, description="Provider display name")

    # Model configuration
    embedding_model: str = Field("text-embedding-3-large", description="Embedding model name")
    embedding_credential_id: str = Field("lyzr_openai", description="Embedding credential ID")
    llm_model: str = Field("gpt-4o", description="LLM model for query processing")
    llm_credential_id: str = Field("lyzr_openai", description="LLM credential ID")

    # Advanced settings
    semantic_data_model: bool = Field(False, description="Enable semantic data modeling")
    user_id: Optional[str] = Field(None, description="User ID")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    model_config = ConfigDict(validate_assignment=True)

    @model_validator(mode='before')
    @classmethod
    def process_config(cls, data: Any) -> Any:
        """Process and validate configuration"""
        if isinstance(data, dict):
            # Validate name format
            if 'name' in data:
                name = data['name']
                if not re.match(r'^[a-z0-9_]+$', name):
                    raise ValueError(
                        "Knowledge base name must contain only lowercase letters, numbers, and underscores. "
                        f"Invalid: '{name}'. Examples: 'customer_support', 'product_docs_2024', 'faq_kb'"
                    )

            # Auto-generate collection_name if not provided
            if 'collection_name' not in data or not data['collection_name']:
                if 'name' in data:
                    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                    data['collection_name'] = f"{data['name']}{suffix}"

            # Resolve vector store credentials
            if 'vector_store' in data:
                try:
                    provider = VectorStoreResolver.resolve(data['vector_store'])

                    # Set credential and display name if not explicitly provided
                    if 'vector_db_credential_id' not in data or not data['vector_db_credential_id']:
                        data['vector_db_credential_id'] = provider.credential_id
                    if 'vector_store_provider' not in data or not data['vector_store_provider']:
                        data['vector_store_provider'] = provider.display_name
                except ValueError as e:
                    raise ValueError(f"Invalid vector store: {str(e)}")

        return data

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to API request format"""
        data = {
            "name": self.name,
            "collection_name": self.collection_name,
            "vector_db_credential_id": self.vector_db_credential_id,
            "vector_store_provider": self.vector_store_provider,
            "embedding_model": self.embedding_model,
            "embedding_credential_id": self.embedding_credential_id,
            "llm_model": self.llm_model,
            "llm_credential_id": self.llm_credential_id,
            "semantic_data_model": self.semantic_data_model,
        }

        # Only include optional fields if they have values
        if self.description is not None:
            data["description"] = self.description
        if self.user_id is not None:
            data["user_id"] = self.user_id
        if self.meta_data is not None:
            data["meta_data"] = self.meta_data

        return data


class KnowledgeBaseRuntimeConfig:
    """
    Runtime configuration for KB when passed to agent.run()

    Allows customizing retrieval parameters per-call.
    """

    def __init__(
        self,
        kb: 'KnowledgeBase',
        top_k: int = 10,
        retrieval_type: str = "basic",
        score_threshold: float = 0.0,
        time_decay_factor: float = 0.4,
        **kwargs
    ):
        self.kb = kb
        self.top_k = top_k
        self.retrieval_type = retrieval_type
        self.score_threshold = score_threshold
        self.time_decay_factor = time_decay_factor
        self.extra_config = kwargs

    def to_agentic_config(self) -> Dict[str, Any]:
        """Convert to agentic_rag config format"""
        return self.kb.to_agentic_config(
            top_k=self.top_k,
            retrieval_type=self.retrieval_type,
            score_threshold=self.score_threshold,
            time_decay_factor=self.time_decay_factor,
            **self.extra_config
        )
