"""
Data models for Knowledge Base query results and documents
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class QueryResult(BaseModel):
    """Result from knowledge base query"""
    text: str = Field(..., description="Retrieved text chunk")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score (0-1)")
    source: Optional[str] = Field(None, description="Source document name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Optional fields
    id: Optional[str] = Field(None, description="Document/chunk ID")
    page: Optional[int] = Field(None, description="Page number (for PDFs)")
    chunk_index: Optional[int] = Field(None, description="Chunk index in document")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump(exclude_none=True)


class Document(BaseModel):
    """Document in knowledge base"""
    id: str = Field(..., description="Document ID")
    source: str = Field(..., description="Source identifier")
    text: Optional[str] = Field(None, description="Document text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump(exclude_none=True)
