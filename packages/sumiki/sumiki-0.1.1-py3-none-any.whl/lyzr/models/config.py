"""
Pydantic models for Lyzr Agent SDK
"""

from typing import Optional, List, Dict, Any, Literal, Union, Iterator, TYPE_CHECKING, Type
from pydantic import BaseModel, Field, validator, model_validator, ConfigDict, PrivateAttr
from lyzr.providers import ProviderName, ModelResolver

# Import at runtime (needed for field annotations)
from lyzr.tools.backend import ToolConfig
from lyzr.memory import MemoryConfig
from lyzr.logger import get_logger
logger = get_logger()

if TYPE_CHECKING:
    from lyzr.http import HTTPClient
    from lyzr.inference import InferenceModule
    from lyzr.responses import AgentResponse, AgentStream
    from lyzr.knowledge_base import KnowledgeBase, KnowledgeBaseRuntimeConfig
    from lyzr.tools.local import Tool, ToolRegistry, LocalToolExecutor
class AgentConfig(BaseModel):
    """Configuration for creating an agent"""

    name: str = Field(..., min_length=1, max_length=200, description="Agent name")
    description: Optional[str] = Field(None, max_length=1000, description="Agent description")

    # Required fields (user-facing: role, goal, instructions)
    role: str = Field(..., description="Agent's role/persona")
    goal: str = Field(..., description="Agent's primary goal")
    instructions: str = Field(..., description="Detailed instructions for the agent")

    # Model configuration
    provider: str = Field(..., description="Provider and model (e.g., 'openai/gpt-4o' or 'gpt-4o')")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")

    # Optional configurations
    examples: Optional[str] = Field(None, description="Example interactions")
    tools: List[str] = Field(default_factory=list, description="List of tool IDs")
    tool_usage_description: str = Field("{}", description="Tool usage description JSON")
    tool_configs: List[Any] = Field(default_factory=list, description="Tool configurations")

    # Advanced settings
    llm_credential_id: str = Field("lyzr_openai", description="LLM credential ID")
    features: List[Any] = Field(default_factory=list, description="Enabled features")
    managed_agents: List[Any] = Field(default_factory=list, description="Managed sub-agents")
    a2a_tools: List[Any] = Field(default_factory=list, description="Agent-to-agent tools")
    additional_model_params: Optional[Dict[str, Any]] = Field(None, description="Additional model parameters")
    response_format: Dict[str, Any] = Field({"type": "text"}, description="Response format configuration")
    store_messages: bool = Field(True, description="Whether to store conversation messages")
    file_output: bool = Field(False, description="Whether agent can output files")
    image_output_config: Optional[Dict[str, Any]] = Field(None, description="Image output configuration")

    # Structured response support
    response_model: Optional[Type[BaseModel]] = Field(
        None,
        exclude=True,
        description="Pydantic model for structured responses (not sent to API)"
    )

    # Backend tools support (ACI, Composio, OpenAPI)
    backend_tools: Optional[List[Union[ToolConfig, Dict[str, Any]]]] = Field(
        None,
        exclude=True,
        description="Backend tools (ACI/Composio/OpenAPI) - converted to tool_configs"
    )

    # Context support
    contexts: Optional[List['Context']] = Field(
        None,
        exclude=True,
        description="Contexts to add to agent (converted to features)"
    )

    # Advanced evaluation features
    reflection: bool = Field(False, description="Enable self-reflection")
    bias_check: bool = Field(False, description="Enable bias detection")
    llm_judge: bool = Field(False, description="Enable LLM-as-judge")
    groundedness_facts: Optional[List[str]] = Field(None, description="Facts for validation")

    # RAI guardrails support
    rai_policy: Optional['RAIPolicy'] = Field(
        None,
        exclude=True,
        description="RAI policy for guardrails (converted to features)"
    )

    # Image generation support
    image_model: Optional['ImageModelConfig'] = Field(
        None,
        exclude=True,
        description="Image model configuration (converted to image_output_config)"
    )

    # Memory support
    memory: Optional[Union[MemoryConfig, int]] = Field(
        None,
        exclude=True,
        description="Memory configuration (converted to features). Can be int (shorthand) or MemoryConfig"
    )

    # Internal fields (populated after parsing)
    provider_id: Optional[str] = Field(None, description="Resolved provider ID")
    model: Optional[str] = Field(None, description="Resolved model name")

    class Config:
        validate_assignment = True

    @validator("name")
    def validate_name(cls, v):
        """Validate agent name"""
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")
        return v.strip()

    @model_validator(mode='before')
    @classmethod
    def parse_provider_and_build_features(cls, data: Any) -> Any:
        """Parse provider string and build response_format"""
        if isinstance(data, dict):
            # Parse provider if present
            if 'provider' in data:
                try:
                    provider_str = data['provider']
                    provider, model, model_info = ModelResolver.parse(provider_str)

                    # Set resolved values
                    data['provider_id'] = provider.value
                    data['model'] = model
                    data['llm_credential_id'] = ModelResolver.get_credential_id(provider)
                except ValueError as e:
                    raise ValueError(f"Invalid provider/model: {str(e)}")

            # Build response_format from response_model if present
            if 'response_model' in data and data['response_model']:
                from lyzr.structured import ResponseSchemaBuilder
                data['response_format'] = ResponseSchemaBuilder.to_json_schema(data['response_model'])
            elif 'response_format' not in data or not data['response_format']:
                data['response_format'] = {"type": "text"}

            # Convert backend_tools to tool_configs
            if 'backend_tools' in data and data['backend_tools']:
                tool_configs = []
                for tool in data['backend_tools']:
                    if isinstance(tool, dict):
                        tool_configs.append(tool)
                    else:
                        # Assume it's a ToolConfig object
                        tool_configs.append(tool.to_api_format())

                # Merge with existing tool_configs
                existing_configs = data.get('tool_configs', [])
                data['tool_configs'] = existing_configs + tool_configs

            # Convert contexts to features
            if 'contexts' in data and data['contexts']:
                for ctx in data['contexts']:
                    if hasattr(ctx, 'to_feature_format'):
                        feature = ctx.to_feature_format()
                    elif isinstance(ctx, dict) and 'type' in ctx:
                        feature = ctx
                    else:
                        continue

                    existing_features = data.get('features', [])
                    data['features'] = existing_features + [feature]

            # Build SRS feature (reflection + bias)
            if data.get('reflection') or data.get('bias_check'):
                srs_feature = {
                    "type": "SRS",
                    "config": {
                        "max_tries": 1,
                        "modules": {
                            "reflection": data.get('reflection', False),
                            "bias": data.get('bias_check', False)
                        }
                    },
                    "priority": 0
                }
                existing_features = data.get('features', [])
                data['features'] = existing_features + [srs_feature]

            # Build LLM Judge feature
            if data.get('llm_judge'):
                existing_features = data.get('features', [])
                data['features'] = existing_features + [{
                    "type": "UQLM_LLM_JUDGE", "config": {}, "priority": 0
                }]

            # Build Groundedness feature
            if data.get('groundedness_facts'):
                existing_features = data.get('features', [])
                data['features'] = existing_features + [{
                    "type": "GROUNDEDNESS",
                    "config": {"facts": data['groundedness_facts']},
                    "priority": 0
                }]

            # Convert rai_policy to features
            if 'rai_policy' in data and data['rai_policy']:
                from lyzr.rai import RAIPolicy
                rai_policy = data['rai_policy']
                if isinstance(rai_policy, RAIPolicy):
                    # RAI endpoint will be constructed in create method
                    # For now, store it to be processed later
                    data['_rai_policy_temp'] = rai_policy

            # Convert image_model to image_output_config
            if 'image_model' in data and data['image_model']:
                img_config = data['image_model']
                data['image_output_config'] = {
                    "model": img_config.model,
                    "credential_id": img_config.credential_id
                }

            # Convert memory to features
            if 'memory' in data and data['memory']:
                from lyzr.memory import MemoryConfig

                # Handle different input formats
                if isinstance(data['memory'], int):
                    # Shorthand: just max_messages
                    memory_config = MemoryConfig(max_messages_context_count=data['memory'])
                elif isinstance(data['memory'], dict):
                    memory_config = MemoryConfig(**data['memory'])
                else:
                    # Assume it's already a MemoryConfig
                    memory_config = data['memory']

                # Convert to feature format
                memory_feature = memory_config.to_feature_format()

                # Add to features array
                existing_features = data.get('features', [])
                data['features'] = existing_features + [memory_feature]

        return data

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to API request format"""
        return {
            "name": self.name,
            "description": self.description,
            "agent_role": self.role,
            "agent_goal": self.goal,
            "agent_instructions": self.instructions,
            "examples": self.examples,
            "tools": self.tools,
            "tool_usage_description": self.tool_usage_description,
            "tool_configs": self.tool_configs,
            "provider_id": self.provider_id,
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "llm_credential_id": self.llm_credential_id,
            "features": self.features,
            "managed_agents": self.managed_agents,
            "a2a_tools": self.a2a_tools,
            "additional_model_params": self.additional_model_params,
            "response_format": self.response_format,
            "store_messages": self.store_messages,
            "file_output": self.file_output,
            "image_output_config": self.image_output_config,
        }


