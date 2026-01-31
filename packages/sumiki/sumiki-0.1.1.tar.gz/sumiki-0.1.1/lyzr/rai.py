"""
RAI (Responsible AI) Module for Lyzr SDK

Provides guardrails for agents: toxicity detection, PII handling, content filtering, etc.
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
from enum import Enum
from lyzr.base import BaseModule

if TYPE_CHECKING:
    from lyzr.http import HTTPClient


# ============================================================================
# Typed Enums for RAI Configuration
# ============================================================================

class PIIType(str, Enum):
    """PII (Personally Identifiable Information) types"""
    CREDIT_CARD = "CREDIT_CARD"
    EMAIL = "EMAIL_ADDRESS"
    PHONE = "PHONE_NUMBER"
    SSN = "US_SSN"
    PERSON = "PERSON"
    LOCATION = "LOCATION"
    IP_ADDRESS = "IP_ADDRESS"
    URL = "URL"
    DATE_TIME = "DATE_TIME"


class PIIAction(str, Enum):
    """Actions for PII handling"""
    BLOCK = "block"        # Block the request/response
    REDACT = "redact"      # Redact/mask the PII
    DISABLED = "disabled"  # No action


class SecretsAction(str, Enum):
    """Actions for secrets detection"""
    MASK = "mask"
    BLOCK = "block"
    DISABLED = "disabled"


class ValidationMethod(str, Enum):
    """NSFW validation methods"""
    FULL = "full"
    PARTIAL = "partial"


# ============================================================================
# RAI Configuration Models
# ============================================================================

class ToxicityConfig(BaseModel):
    """Toxicity detection configuration"""
    enabled: bool = False
    threshold: float = Field(0.4, ge=0.0, le=1.0)

class PromptInjectionConfig(BaseModel):
    """Prompt injection detection configuration"""
    enabled: bool = False
    threshold: float = Field(0.3, ge=0.0, le=1.0)

class SecretsConfig(BaseModel):
    """Secrets detection configuration"""
    enabled: bool = False
    action: SecretsAction = SecretsAction.MASK

class PIIConfig(BaseModel):
    """PII detection configuration"""
    enabled: bool = False
    types: Dict[str, str] = Field(default_factory=dict)  # Will convert from PIIType enum
    custom_pii: List[str] = Field(default_factory=list)

class NSFWConfig(BaseModel):
    """NSFW content detection configuration"""
    enabled: bool = False
    threshold: float = Field(0.8, ge=0.0, le=1.0)
    validation_method: ValidationMethod = ValidationMethod.FULL


# ============================================================================
# RAI Policy Model
# ============================================================================

class RAIPolicy(BaseModel):
    """
    RAI Policy - Responsible AI guardrails configuration

    Provides content filtering, toxicity detection, PII handling, etc.
    """

    id: str = Field(..., alias="_id", description="Policy ID")
    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")

    # Detection configurations
    toxicity_check: Dict[str, Any] = Field(default_factory=dict)
    prompt_injection: Dict[str, Any] = Field(default_factory=dict)
    secrets_detection: Dict[str, Any] = Field(default_factory=dict)
    pii_detection: Dict[str, Any] = Field(default_factory=dict)
    nsfw_check: Dict[str, Any] = Field(default_factory=dict)

    # Topic controls
    allowed_topics: Dict[str, Any] = Field(default_factory=dict)
    banned_topics: Dict[str, Any] = Field(default_factory=dict)
    keywords: Dict[str, Any] = Field(default_factory=dict)

    # Advanced
    fairness_and_bias: Optional[Dict[str, Any]] = None

    # Metadata
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Private fields
    _http: Optional['HTTPClient'] = PrivateAttr(default=None)
    _rai_module: Optional[Any] = PrivateAttr(default=None)

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    def _ensure_clients(self):
        if not self._http or not self._rai_module:
            raise RuntimeError("RAIPolicy not properly initialized")

    def update(self, **kwargs) -> 'RAIPolicy':
        """Update policy configuration"""
        self._ensure_clients()
        return self._rai_module.update_policy(self.id, **kwargs)

    def delete(self) -> bool:
        """Delete this policy"""
        self._ensure_clients()
        return self._rai_module.delete_policy(self.id)

    def to_feature_format(self, rai_endpoint: str) -> Dict[str, Any]:
        """
        Convert to feature format for agent

        Args:
            rai_endpoint: RAI inference endpoint URL

        Returns:
            Dict: Feature configuration
        """
        return {
            "type": "RAI",
            "config": {
                "endpoint": rai_endpoint,
                "policy_id": self.id,
                "policy_name": self.name
            },
            "priority": 0
        }


class RAIPolicyList(BaseModel):
    """List of RAI policies"""

    policies: List[RAIPolicy] = Field(default_factory=list)
    total: Optional[int] = None

    def __iter__(self):
        return iter(self.policies)

    def __len__(self):
        return len(self.policies)

    def __getitem__(self, index):
        return self.policies[index]


# ============================================================================
# RAI Module
# ============================================================================

class RAIModule(BaseModule):
    """
    Module for managing RAI policies and guardrails

    Provides toxicity detection, PII handling, content filtering, etc.
    """

    def __init__(self, http_client: 'HTTPClient', env_config: 'ServiceURLs'):
        """
        Initialize RAI module

        Args:
            http_client: Main HTTP client (for api_key)
            env_config: Environment configuration with RAI API URL
        """
        from lyzr.http import HTTPClient

        # Create HTTP client for RAI service
        self._http = HTTPClient(
            api_key=http_client.api_key,
            base_url=env_config.rai_api,
            timeout=30
        )
        self._env_config = env_config

    def _make_smart_policy(self, policy_data: Dict[str, Any]) -> RAIPolicy:
        """Create smart RAIPolicy with injected clients"""
        policy = RAIPolicy(**policy_data)
        policy._http = self._http
        policy._rai_module = self
        return policy

    def create_policy(
        self,
        name: str,
        description: str,
        toxicity_threshold: float = 0.4,
        prompt_injection: bool = False,
        secrets_detection: SecretsAction = SecretsAction.DISABLED,
        pii_detection: Optional[Dict[PIIType, PIIAction]] = None,
        banned_topics: Optional[List[str]] = None,
        nsfw_check: bool = False,
        nsfw_threshold: float = 0.8,
        **kwargs
    ) -> RAIPolicy:
        """
        Create RAI policy with typed parameters

        Args:
            name: Policy name
            description: Policy description
            toxicity_threshold: Toxicity detection threshold (0.0-1.0)
            prompt_injection: Enable prompt injection detection
            secrets_detection: Secrets handling action (enum)
            pii_detection: PII type → action mapping (typed dict)
            banned_topics: Topics to ban
            nsfw_check: Enable NSFW detection
            nsfw_threshold: NSFW detection threshold

        Returns:
            RAIPolicy: Created policy

        Example:
            >>> from lyzr.rai import PIIType, PIIAction, SecretsAction
            >>> policy = studio.create_rai_policy(
            ...     name="SafePolicy",
            ...     description="Safety guardrails",
            ...     toxicity_threshold=0.3,
            ...     secrets_detection=SecretsAction.MASK,
            ...     pii_detection={
            ...         PIIType.CREDIT_CARD: PIIAction.BLOCK,
            ...         PIIType.EMAIL: PIIAction.REDACT
            ...     }
            ... )
        """
        # Build policy configuration
        policy_data = {
            "name": name,
            "description": description,
            "toxicity_check": {
                "enabled": toxicity_threshold < 1.0,
                "threshold": toxicity_threshold
            },
            "prompt_injection": {
                "enabled": prompt_injection,
                "threshold": 0.3
            },
            "secrets_detection": {
                "enabled": secrets_detection != SecretsAction.DISABLED,
                "action": secrets_detection.value
            },
            "pii_detection": self._build_pii_config(pii_detection),
            "allowed_topics": {"enabled": False, "topics": []},
            "banned_topics": {
                "enabled": bool(banned_topics),
                "topics": [{"name": topic} for topic in (banned_topics or [])]
            },
            "keywords": {"enabled": False, "keywords": []},
            "nsfw_check": {
                "enabled": nsfw_check,
                "threshold": nsfw_threshold,
                "validation_method": ValidationMethod.FULL.value
            }
        }

        # Merge additional kwargs
        policy_data.update(kwargs)

        response = self._http.post("/v1/rai/policies", json=policy_data)
        return self._make_smart_policy(response)

    def _build_pii_config(self, pii_detection: Optional[Dict[PIIType, PIIAction]]) -> Dict:
        """Convert typed PII dict to API format"""
        if not pii_detection:
            return {"enabled": False, "types": {}, "custom_pii": []}

        types_dict = {
            pii_type.value: action.value
            for pii_type, action in pii_detection.items()
        }

        return {
            "enabled": True,
            "types": types_dict,
            "custom_pii": []
        }

    def get_policy(self, policy_id: str) -> RAIPolicy:
        """Get RAI policy by ID"""
        response = self._http.get(f"/v1/rai/policies/{policy_id}")
        return self._make_smart_policy(response)

    def list_policies(self) -> RAIPolicyList:
        """
        List all RAI policies for the authenticated user

        Returns:
            RAIPolicyList: List of RAI policies

        Example:
            >>> policies = rai.list_policies()
            >>> for policy in policies:
            ...     print(policy.name)
        """
        response = self._http.get("/v1/rai/policies")

        if isinstance(response, list):
            policies = [self._make_smart_policy(p) for p in response]
            return RAIPolicyList(policies=policies, total=len(policies))
        elif isinstance(response, dict) and "policies" in response:
            policies = [self._make_smart_policy(p) for p in response["policies"]]
            return RAIPolicyList(policies=policies, total=len(policies))

        return RAIPolicyList(policies=[])

    def update_policy(self, policy_id: str, **kwargs) -> RAIPolicy:
        """Update RAI policy"""
        response = self._http.put(f"/v1/rai/policies/{policy_id}", json=kwargs)
        # PUT returns success, fetch updated policy
        return self.get_policy(policy_id)

    def delete_policy(self, policy_id: str) -> bool:
        """Delete RAI policy"""
        self._http.delete(f"/v1/rai/policies/{policy_id}")
        return True
