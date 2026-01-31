"""
Context Module for Lyzr SDK

Manages context variables - key-value pairs that provide background information to agents.
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
from lyzr.base import BaseModule

if TYPE_CHECKING:
    from lyzr.http import HTTPClient


class Context(BaseModel):
    """
    Smart Context object

    Represents a context variable (key-value pair) that provides
    background information to agents.
    """

    id: str = Field(..., alias="_id", description="Context ID")
    name: str = Field(..., description="Context name (key)")
    value: str = Field(..., description="Context value")
    api_key: str = Field(..., description="Associated API key")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    # Private fields
    _http: Optional['HTTPClient'] = PrivateAttr(default=None)
    _context_module: Optional[Any] = PrivateAttr(default=None)

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    def _ensure_clients(self):
        if not self._http or not self._context_module:
            raise RuntimeError("Context not properly initialized")

    def update(self, value: str) -> 'Context':
        """
        Update context value

        Args:
            value: New value

        Returns:
            Context: Updated context

        Example:
            >>> ctx = ctx.update("New value")
        """
        self._ensure_clients()
        return self._context_module.update(self.id, value=value)

    def delete(self) -> bool:
        """
        Delete this context

        Returns:
            bool: True if successful
        """
        self._ensure_clients()
        return self._context_module.delete(self.id)

    def to_feature_format(self) -> Dict[str, Any]:
        """
        Convert to feature format for agent

        Returns:
            Dict: Feature configuration
        """
        return {
            "type": "CONTEXT",
            "config": {
                "context_id": self.id,
                "context_name": self.name
            },
            "priority": 10
        }


class ContextList(BaseModel):
    """List of contexts"""

    contexts: List[Context] = Field(default_factory=list)
    total: Optional[int] = None

    def __iter__(self):
        return iter(self.contexts)

    def __len__(self):
        return len(self.contexts)

    def __getitem__(self, index):
        return self.contexts[index]


class ContextModule(BaseModule):
    """Module for managing contexts"""

    def _make_smart_context(self, context_data: Dict[str, Any]) -> Context:
        """Create smart Context with injected clients"""
        # Normalize field names - API may return context_id or _id
        if "context_id" in context_data and "_id" not in context_data:
            context_data["_id"] = context_data.pop("context_id")

        context = Context(**context_data)
        context._http = self._http
        context._context_module = self
        return context

    def create(self, name: str, value: str) -> Context:
        """
        Create a new context

        Args:
            name: Context name
            value: Context value

        Returns:
            Context: Created context

        Example:
            >>> ctx = contexts.create(name="company", value="Lyzr Inc")
        """
        response = self._http.post(
            "/v3/contexts/",
            json={"name": name, "value": value}
        )

        # API returns {"context_id": "...", "message": "..."}
        # Need to fetch full context details
        context_id = response.get("context_id")
        if not context_id:
            raise ValueError("API did not return context_id")

        return self.get(context_id)

    def get(self, context_id: str) -> Context:
        """
        Get context by ID

        Args:
            context_id: Context ID

        Returns:
            Context: Context object
        """
        response = self._http.get(f"/v3/contexts/{context_id}")
        return self._make_smart_context(response)

    def list(self, skip: int = 0, limit: int = 100) -> ContextList:
        """
        List all contexts

        Args:
            skip: Number to skip
            limit: Maximum to return

        Returns:
            ContextList: List of contexts
        """
        response = self._http.get(f"/v3/contexts/?skip={skip}&limit={limit}")

        if isinstance(response, list):
            contexts = [self._make_smart_context(c) for c in response]
            return ContextList(contexts=contexts, total=len(contexts))

        return ContextList(contexts=[])

    def update(self, context_id: str, value: str) -> Context:
        """
        Update context value

        Args:
            context_id: Context ID
            value: New value

        Returns:
            Context: Updated context
        """
        response = self._http.put(
            f"/v3/contexts/{context_id}",
            json={"value": value}
        )

        # API returns {"message": "Context updated successfully"}
        # Need to fetch full context details
        return self.get(context_id)

    def delete(self, context_id: str) -> bool:
        """
        Delete context

        Args:
            context_id: Context ID

        Returns:
            bool: True if successful
        """
        self._http.delete(f"/v3/contexts/{context_id}")
        return True
