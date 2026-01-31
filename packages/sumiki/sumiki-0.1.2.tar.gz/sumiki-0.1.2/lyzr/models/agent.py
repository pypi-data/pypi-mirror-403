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
class Agent(BaseModel):
    """Agent model representing a created agent"""

    id: str = Field(..., alias="_id", description="Agent ID")
    api_key: str = Field(..., description="API key associated with agent")
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    agent_role: Optional[str] = Field(None, description="Agent role")
    agent_goal: Optional[str] = Field(None, description="Agent goal")
    agent_instructions: Optional[str] = Field(None, description="Agent instructions")
    agent_context: Optional[str] = Field(None, description="Agent context")
    agent_output: Optional[str] = Field(None, description="Agent output format")

    # Model configuration
    provider_id: str = Field(..., description="Provider ID")
    model: str = Field(..., description="Model name")
    temperature: float = Field(..., description="Temperature setting")
    top_p: float = Field(..., description="Top-p setting")
    llm_credential_id: str = Field(default="lyzr_openai", description="LLM credential ID")

    # Features and tools
    tools: List[str] = Field(default_factory=list, description="Tool IDs")
    features: List[Any] = Field(default_factory=list, description="Features")
    managed_agents: List[Any] = Field(default_factory=list, description="Managed agents")
    tool_configs: List[Any] = Field(default_factory=list, description="Tool configurations")
    tool_usage_description: Optional[str] = Field(default="{}", description="Tool usage description")
    a2a_tools: List[Any] = Field(default_factory=list, description="Agent-to-agent tools")

    # Output configuration
    response_format: Optional[Dict[str, Any]] = Field(default={"type": "text"}, description="Response format")
    store_messages: bool = Field(default=True, description="Whether to store messages")
    file_output: bool = Field(default=False, description="Whether to output files")
    image_output_config: Optional[Dict[str, Any]] = Field(None, description="Image output config")
    voice_config: Optional[Dict[str, Any]] = Field(None, description="Voice configuration")

    # Additional params
    examples: Optional[str] = Field(None, description="Example interactions")
    additional_model_params: Optional[Dict[str, Any]] = Field(None, description="Additional model parameters")

    # Metadata
    version: str = Field(default="3", description="API version")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    # Private fields (injected by AgentModule, not serialized)
    _http: Optional['HTTPClient'] = PrivateAttr(default=None)
    _inference: Optional['InferenceModule'] = PrivateAttr(default=None)
    _agent_module: Optional[Any] = PrivateAttr(default=None)
    _response_model: Optional[Type[BaseModel]] = PrivateAttr(default=None)
    _tool_registry: Optional['ToolRegistry'] = PrivateAttr(default=None)
    _tool_executor: Optional['LocalToolExecutor'] = PrivateAttr(default=None)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    @model_validator(mode='before')
    @classmethod
    def handle_null_lists(cls, data: Any) -> Any:
        """Convert None to empty list for list fields"""
        if isinstance(data, dict):
            # Handle None values for list fields
            list_fields = ['tools', 'features', 'managed_agents', 'tool_configs', 'a2a_tools']
            for field in list_fields:
                if field in data and data[field] is None:
                    data[field] = []

            # Handle None for dict fields
            if 'response_format' in data and data['response_format'] is None:
                data['response_format'] = {"type": "text"}

            if 'tool_usage_description' in data and data['tool_usage_description'] is None:
                data['tool_usage_description'] = "{}"

        return data

    def _ensure_clients(self):
        """Ensure HTTP and inference clients are available"""
        if not self._http or not self._inference:
            raise RuntimeError(
                "Agent not properly initialized with clients. "
                "Agents should be created using Studio.create_agent() or Studio.get_agent()"
            )

    def run(
        self,
        message: str,
        session_id: Optional[str] = None,
        stream: bool = False,
        user_id: Optional[str] = None,
        knowledge_bases: Optional[List[Union['KnowledgeBase', 'KnowledgeBaseRuntimeConfig']]] = None,
        **kwargs
    ) -> Union['AgentResponse', BaseModel, Iterator['AgentStream']]:
        """
        Run the agent with a message

        Args:
            message: User message to process
            session_id: Optional session ID (auto-generated UUID if None)
            stream: Whether to stream response (default: False)
            user_id: User ID (auto-generated UUID if None)
            knowledge_bases: Knowledge bases to use for this run (passed at runtime!)
            **kwargs: Additional parameters (system_prompt_variables, features, etc.)

        Returns:
            AgentResponse: If no response_model (text response)
            BaseModel: If response_model is set (structured response - typed Pydantic instance)
            Iterator[AgentStream]: If stream=True, yields chunks (final chunk has structured_data)

        Raises:
            RuntimeError: If agent not properly initialized
            InvalidResponseError: If structured response validation fails
            APIError: If API request fails

        Example:
            >>> # Text response
            >>> agent = studio.create_agent(name="Bot", provider="gpt-4o")
            >>> response = agent.run("What is 2+2?")
            >>> print(response.response)
            >>>
            >>> # With knowledge base
            >>> kb = studio.create_knowledge_base(name="docs")
            >>> response = agent.run(
            ...     "What are business hours?",
            ...     knowledge_bases=[kb]
            ... )
            >>>
            >>> # Structured response
            >>> class Result(BaseModel):
            ...     answer: int
            >>> agent = studio.create_agent(
            ...     name="Math Bot",
            ...     provider="gpt-4o",
            ...     response_model=Result
            ... )
            >>> result: Result = agent.run("What is 2+2?")
            >>> print(result.answer)  # 4
            >>>
            >>> # Streaming
            >>> for chunk in agent.run("Tell a story", stream=True):
            ...     print(chunk.content, end="")
        """
        self._ensure_clients()

        # Check if agent has local tools - auto-detect and handle async
        has_local_tools = self._tool_registry and len(self._tool_registry) > 0

        if has_local_tools:
            logger.info(f"\n[SDK DEBUG] Agent has {len(self._tool_registry)} local tool(s) - switching to async execution")

            # Agent has local tools - run async internally
            import asyncio

            try:
                # Check if already in async context
                loop = asyncio.get_running_loop()
                # Already in async context (e.g., Jupyter/Colab)
                # Use nest_asyncio to allow nested event loops
                logger.info("[SDK DEBUG] Detected existing event loop - using nest_asyncio")
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                    return asyncio.run(self.run_with_local_tools(
                        message=message,
                        session_id=session_id,
                        stream=stream,
                        user_id=user_id,
                        knowledge_bases=knowledge_bases,
                        **kwargs
                    ))
                except ImportError:
                    # nest_asyncio not available - create task and get result
                    task = asyncio.create_task(self.run_with_local_tools(
                        message=message,
                        session_id=session_id,
                        stream=stream,
                        user_id=user_id,
                        knowledge_bases=knowledge_bases,
                        **kwargs
                    ))
                    # Wait for completion
                    return loop.run_until_complete(task)
            except RuntimeError as e:
                if "no running event loop" in str(e).lower():
                    # Not in async - create event loop and run
                    logger.info("[SDK DEBUG] Creating new event loop for local tools execution")
                    return asyncio.run(self.run_with_local_tools(
                        message=message,
                        session_id=session_id,
                        stream=stream,
                        user_id=user_id,
                        knowledge_bases=knowledge_bases,
                        **kwargs
                    ))
                # Re-raise other RuntimeErrors
                raise

        # Auto-generate session_id if not provided
        if session_id is None:
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:16]}"

        # Auto-generate user_id if not provided
        if user_id is None:
            import uuid
            user_id = f"user_{uuid.uuid4().hex[:16]}"

        # Build local_tools feature if agent has local tools
        if self._tool_registry and len(self._tool_registry) > 0:
            import json
            tools_api_format = self._tool_registry.to_api_format()
            logger.info("\n[SDK DEBUG] Building local_tools feature:")
            logger.debug("Data:", data=tools_api_format)

            local_tools_feature = {
                "type": "local_tools",
                "config": {
                    "tools": tools_api_format
                },
                "priority": 0
            }

            # Add to features
            existing_features = kwargs.get("features", [])
            kwargs["features"] = [local_tools_feature] + (existing_features if isinstance(existing_features, list) else [])
            logger.info("\n[SDK DEBUG] Complete features array:")
            logger.debug("Data:", data=kwargs["features"])

        # Build features array from knowledge_bases (runtime integration)
        if knowledge_bases:
            from lyzr.knowledge_base import KnowledgeBaseRuntimeConfig

            kb_configs = []
            for kb in knowledge_bases:
                if isinstance(kb, KnowledgeBaseRuntimeConfig):
                    kb_configs.append(kb.to_agentic_config())
                else:
                    # Plain KnowledgeBase - use defaults
                    kb_configs.append(kb.to_agentic_config())

            kb_feature = {
                "type": "KNOWLEDGE_BASE",
                "config": {
                    "lyzr_rag": {},
                    "agentic_rag": kb_configs
                },
                "priority": 0
            }

            # Add to kwargs features
            existing_features = kwargs.get("features", [])
            kwargs["features"] = [kb_feature] + (existing_features if isinstance(existing_features, list) else [])

        # Streaming
        if stream:
            return self._stream_with_validation(
                message=message,
                session_id=session_id,
                user_id=user_id,
                **kwargs
            )

        # Non-streaming
        raw_response = self._inference.chat(
            agent_id=self.id,
            message=message,
            session_id=session_id,
            user_id=user_id,
            **kwargs
        )

        # If structured response, parse and validate
        if self._response_model:
            from lyzr.structured import ResponseParser
            return ResponseParser.parse(
                raw_response.response,
                self._response_model
            )

        return raw_response

    def _stream_with_validation(
        self,
        message: str,
        session_id: str,
        user_id: str,
        **kwargs
    ) -> Iterator['AgentStream']:
        """
        Stream response with optional structured validation at the end

        Yields chunks as they arrive. If response_model is set, the final
        chunk will include the validated structured_data.
        """
        accumulated_content = []

        # Stream chunks
        for chunk in self._inference.stream(
            agent_id=self.id,
            message=message,
            session_id=session_id,
            user_id=user_id,
            **kwargs
        ):
            # Accumulate ALL content (including final chunk)
            if chunk.content:
                accumulated_content.append(chunk.content)

            # If this is the final chunk and we have a response_model
            if chunk.done and self._response_model:
                # Parse accumulated content
                from lyzr.structured import ResponseParser
                full_response = "".join(accumulated_content)

                try:
                    structured_data = ResponseParser.parse(
                        full_response,
                        self._response_model
                    )
                    # Add structured data to final chunk
                    chunk.structured_data = structured_data
                except Exception as e:
                    # Add error info to final chunk
                    chunk.metadata = chunk.metadata or {}
                    chunk.metadata["validation_error"] = str(e)
                    # Don't suppress the error - let it be visible in metadata

            yield chunk

    async def run_with_local_tools(
        self,
        message: str,
        session_id: Optional[str] = None,
        stream: bool = False,
        user_id: Optional[str] = None,
        knowledge_bases: Optional[List[Union['KnowledgeBase', 'KnowledgeBaseRuntimeConfig']]] = None,
        max_tool_iterations: int = 10,
        **kwargs
    ) -> Union['AgentResponse', BaseModel]:
        """
        Run agent with automatic local tool execution

        This method is REQUIRED when agent has local tools. It handles the
        tool execution loop automatically.

        Args:
            message: User message to process
            session_id: Optional session ID (auto-generated UUID if None)
            stream: Whether to stream response (default: False)
            user_id: User ID (auto-generated UUID if None)
            knowledge_bases: Knowledge bases to use for this run
            max_tool_iterations: Maximum tool execution loops (default: 10)
            **kwargs: Additional parameters

        Returns:
            AgentResponse or BaseModel: Agent's final response

        Raises:
            RuntimeError: If max_tool_iterations reached
            ToolNotFoundError: If required tool not found

        Example:
            >>> import asyncio
            >>> from lyzr.tools.decorators import tool, get_registered_tools
            >>>
            >>> @tool()
            >>> def read_file(file_path: str) -> str:
            ...     with open(file_path) as f:
            ...         return f.read()
            >>>
            >>> agent = studio.create_agent(name="Bot", provider="gpt-4o")
            >>> agent.add_tools(list(get_registered_tools().values()))
            >>>
            >>> async def main():
            ...     response = await agent.run_with_local_tools("Read config.json")
            ...     print(response.response)
            >>>
            >>> asyncio.run(main())
        """
        self._ensure_clients()

        # Auto-generate session_id
        if session_id is None:
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:16]}"

        # Auto-generate user_id
        if user_id is None:
            import uuid
            user_id = f"user_{uuid.uuid4().hex[:16]}"

        # Build local_tools feature if agent has local tools
        if self._tool_registry and len(self._tool_registry) > 0:
            import json
            tools_api_format = self._tool_registry.to_api_format()
            logger.info("\n[SDK DEBUG] Building local_tools feature in run_with_local_tools:")
            logger.debug("Data:", data=tools_api_format)

            local_tools_feature = {
                "type": "local_tools",
                "config": {
                    "tools": tools_api_format
                },
                "priority": 0
            }

            existing_features = kwargs.get("features", [])
            kwargs["features"] = [local_tools_feature] + (existing_features if isinstance(existing_features, list) else [])

        # Build knowledge base features
        if knowledge_bases:
            from lyzr.knowledge_base import KnowledgeBaseRuntimeConfig

            kb_configs = []
            for kb in knowledge_bases:
                if isinstance(kb, KnowledgeBaseRuntimeConfig):
                    kb_configs.append(kb.to_agentic_config())
                else:
                    kb_configs.append(kb.to_agentic_config())

            kb_feature = {
                "type": "KNOWLEDGE_BASE",
                "config": {
                    "lyzr_rag": {},
                    "agentic_rag": kb_configs
                },
                "priority": 0
            }

            existing_features = kwargs.get("features", [])
            kwargs["features"] = [kb_feature] + (existing_features if isinstance(existing_features, list) else [])

        # If no tools, use sync inference
        if not self._tool_executor:
            # No tools - use standard sync inference (but called from async)
            raw_response = self._inference.chat(
                agent_id=self.id,
                message=message,
                session_id=session_id,
                user_id=user_id,
                **kwargs
            )

            # Parse structured response if needed
            if self._response_model:
                from lyzr.structured import ResponseParser
                return ResponseParser.parse(raw_response.response, self._response_model)

            return raw_response

        # Has tools - execute tool loop
        import json
        logger.info("\n[SDK DEBUG] ===== STARTING TOOL EXECUTION LOOP =====")
        logger.info(f"Max iterations: {max_tool_iterations}")
        iteration = 0
        messages = [{"role": "user", "content": message}]

        while iteration < max_tool_iterations:
            logger.info(f"\n[SDK DEBUG] ----- ITERATION {iteration + 1} -----")
            logger.info("Messages being sent:")
            logger.debug("Data:", data=messages)

            # Call agent with current messages
            response = await self._inference.chat_async(
                agent_id=self.id,
                session_id=session_id,
                user_id=user_id,
                messages=messages,
                **kwargs
            )

            # Check if tool execution required (backend sets this flag)
            if response.get("requires_local_execution"):
                logger.debug("Backend requires local tool execution")
                # Extract tool calls from response messages
                response_messages = response.get("messages", [])

                # Find the last assistant message with tool_calls
                tool_call_message = None
                for msg in reversed(response_messages):
                    if msg.get("role") == "assistant" and "tool_calls" in msg:
                        tool_call_message = msg
                        break

                if not tool_call_message:
                    raise RuntimeError("requires_local_execution is true but no tool_calls found")

                tool_calls = tool_call_message["tool_calls"]

                logger.info(f"  Found {len(tool_calls)} tool call(s) to execute")

                # Execute all local_tool calls in parallel with asyncio.gather
                import json
                import asyncio

                async def execute_local_tool_call(tool_call):
                    """Execute a single local_tool call and return result message"""
                    tool_call_id = tool_call["id"]
                    function_info = tool_call["function"]
                    function_name = function_info["name"]  # Should be "local_tool"

                    # Parse the nested arguments (JSON string)
                    function_args_str = function_info["arguments"]
                    function_args = json.loads(function_args_str) if isinstance(function_args_str, str) else function_args_str

                    # Extract actual tool info
                    # function_args = {"tool_name": "read_file", "arguments": {"file_path": "..."}}
                    actual_tool_name = function_args["tool_name"]
                    actual_arguments = function_args.get("arguments", {})

                    logger.info(f"  [SDK DEBUG] Executing tool: {actual_tool_name}")
                    logger.info(f"    Arguments: {actual_arguments}")

                    # Execute the actual local tool
                    result = await self._tool_executor.execute(actual_tool_name, actual_arguments)

                    logger.info(f"    Result: {str(result)[:100]}...")

                    # Return in OpenAI tool result format
                    return {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": "local_tool",  # Keep as "local_tool", not actual tool name
                        "content": json.dumps({
                            "tool_name": actual_tool_name,
                            "result": result
                        })
                    }

                # Execute ALL local_tool calls in parallel
                tool_results = await asyncio.gather(
                    *[execute_local_tool_call(tc) for tc in tool_calls],
                    return_exceptions=True
                )

                logger.info(f"  [SDK DEBUG] Executed {len(tool_results)} tool(s)")

                # Add assistant message with tool_calls to history
                messages.append(tool_call_message)

                # Add all tool results
                for result in tool_results:
                    if isinstance(result, Exception):
                        # Handle execution error - still add as tool result
                        messages.append({
                            "role": "tool",
                            "tool_call_id": "error",
                            "name": "local_tool",
                            "content": json.dumps({
                                "tool_name": "unknown",
                                "result": f"Error: {str(result)}"
                            })
                        })
                    else:
                        messages.append(result)

                iteration += 1
                continue  # Loop back to agent

            else:
                # Agent completed - parse final response
                logger.debug("Agent completed after {iteration + 1} iteration(s)")

                final_response = response.get("response", "")
                logger.info("  Final response: {final_response[:100]}...")

                # Parse structured response if needed
                if self._response_model:
                    logger.info("  Parsing structured response with {self._response_model.__name__}")
                    from lyzr.structured import ResponseParser
                    return ResponseParser.parse(final_response, self._response_model)

                # Return as AgentResponse
                from lyzr.responses import AgentResponse
                return AgentResponse(
                    response=final_response,
                    session_id=session_id,
                    message_id=response.get("message_id"),
                    metadata=response.get("metadata"),
                    tool_calls=response.get("tool_calls"),
                    raw_response=response
                )

        # Max iterations reached
        raise RuntimeError(
            f"Max tool iterations ({max_tool_iterations}) reached. "
            f"Agent may be stuck in a loop."
        )

    def update(self, **kwargs) -> 'Agent':
        """
        Update agent configuration

        Args:
            **kwargs: Configuration parameters to update (name, description,
                     temperature, top_p, etc.)

        Returns:
            Agent: Updated agent instance

        Raises:
            RuntimeError: If agent not properly initialized
            ValidationError: If parameters are invalid
            APIError: If API request fails

        Example:
            >>> agent = studio.get_agent("agent_id")
            >>> agent = agent.update(temperature=0.5, description="Updated")
            >>> print(agent.temperature)  # 0.5
        """
        self._ensure_clients()

        if not self._agent_module:
            raise RuntimeError("Agent module not available")

        return self._agent_module.update(self.id, **kwargs)

    def delete(self) -> bool:
        """
        Delete this agent

        Returns:
            bool: True if deletion was successful

        Raises:
            RuntimeError: If agent not properly initialized
            NotFoundError: If agent doesn't exist
            APIError: If deletion fails

        Example:
            >>> agent = studio.get_agent("agent_id")
            >>> success = agent.delete()
            >>> print(success)  # True
        """
        self._ensure_clients()

        if not self._agent_module:
            raise RuntimeError("Agent module not available")

        return self._agent_module.delete(self.id)

    def clone(self, new_name: Optional[str] = None) -> 'Agent':
        """
        Create a copy of this agent

        Args:
            new_name: Optional name for the cloned agent (defaults to "{name} (Clone)")

        Returns:
            Agent: Cloned agent instance

        Raises:
            RuntimeError: If agent not properly initialized
            APIError: If cloning fails

        Example:
            >>> agent = studio.get_agent("agent_id")
            >>> cloned = agent.clone("My Cloned Agent")
            >>> print(cloned.id)  # Different from original
            >>> print(cloned.name)  # "My Cloned Agent"
        """
        self._ensure_clients()

        if not self._agent_module:
            raise RuntimeError("Agent module not available")

        return self._agent_module.clone(self.id, new_name)

    def add_tool(self, tool) -> 'Agent':
        """
        Add a tool (local or backend) to this agent

        Automatically detects tool type - works with local and backend tools!

        Args:
            tool: Can be:
                - Local tool from @tool decorator
                - Backend tool (HubSpot.CREATE_CONTACT, Gmail.SEND_EMAIL)
                - ToolConfig object

        Returns:
            Agent: Self for chaining

        Example:
            >>> from lyzr import tool
            >>> from lyzr.tools import HubSpot, Gmail
            >>>
            >>> @tool()
            >>> def read_file(path: str) -> str:
            ...     with open(path) as f:
            ...         return f.read()
            >>>
            >>> # All added the same way!
            >>> agent.add_tool(HubSpot.CREATE_CONTACT)  # Backend - typed!
            >>> agent.add_tool(Gmail.SEND_EMAIL)        # Backend - typed!
            >>> agent.add_tool(read_file)                # Local
        """
        from lyzr.tools.local import Tool, ToolRegistry, LocalToolExecutor
        from lyzr.tools.backend_tools import BackendToolAction
        from lyzr.tools.backend import ToolConfig

        self._ensure_clients()

        # Detect tool type and route
        if isinstance(tool, Tool):
            # Local tool
            return self._add_local_tool_internal(tool)

        elif isinstance(tool, BackendToolAction):
            # Backend tool action
            return self._add_backend_action_internal(tool)

        elif isinstance(tool, ToolConfig):
            # ToolConfig object
            return self._add_backend_config_internal(tool)

        elif callable(tool):
            # Function - create Tool from it automatically!
            tool_obj = self._function_to_tool(tool)
            return self._add_local_tool_internal(tool_obj)

        raise TypeError(f"Unknown tool type: {type(tool)}")

    def _function_to_tool(self, func) -> 'Tool':
        """Convert a function to a Tool object by inferring metadata"""
        from lyzr.tools.local import Tool
        from lyzr.tools.decorators import infer_parameters_from_function

        name = func.__name__
        description = (func.__doc__ or f"Execute {func.__name__}").strip()
        parameters = infer_parameters_from_function(func)

        return Tool(
            name=name,
            description=description,
            parameters=parameters,
            function=func
        )

    def _add_local_tool_internal(self, tool: 'Tool') -> 'Agent':
        """Internal: Add local tool to client-side registry"""
        from lyzr.tools.local import ToolRegistry, LocalToolExecutor

        if not self._tool_registry:
            self._tool_registry = ToolRegistry()
            self._tool_executor = LocalToolExecutor(self._tool_registry)

        self._tool_registry.add(tool)
        return self

    def _add_backend_action_internal(self, action: 'BackendToolAction') -> 'Agent':
        """Internal: Add backend tool action"""
        from lyzr.tools.backend import ToolConfig

        config = ToolConfig(
            tool_name=action.tool_name,
            tool_source=action.source.value,
            action_names=[action.action],
            persist_auth=True
        )
        return self._add_backend_config_internal(config)

    def _add_backend_config_internal(self, config: 'ToolConfig') -> 'Agent':
        """Internal: Add backend tool config and update agent"""
        current_configs = list(self.tool_configs) if self.tool_configs else []

        # Check if tool exists - merge actions
        for cfg in current_configs:
            if cfg.get('tool_name') == config.tool_name:
                if config.action_names:
                    cfg['action_names'].extend(config.action_names)
                return self._agent_module.update(self.id, tool_configs=current_configs)

        # New tool - add it
        current_configs.append(config.to_api_format())
        return self._agent_module.update(self.id, tool_configs=current_configs)


    def add_context(self, context: 'Context') -> 'Agent':
        """Add context to agent"""
        from lyzr.context import Context

        self._ensure_clients()
        current_features = self.features or []
        new_features = current_features + [context.to_feature_format()]
        return self._agent_module.update(self.id, features=new_features)

    def remove_context(self, context: 'Context') -> 'Agent':
        """Remove context from agent"""
        self._ensure_clients()
        current_features = self.features or []
        new_features = [
            f for f in current_features
            if not (f.get("type") == "CONTEXT" and f.get("config", {}).get("context_id") == context.id)
        ]
        return self._agent_module.update(self.id, features=new_features)

    def list_contexts(self) -> List[Dict]:
        """List contexts attached to agent"""
        if not self.features:
            return []
        return [f.get("config") for f in self.features if f.get("type") == "CONTEXT"]



    def add_rai_policy(self, policy: 'RAIPolicy') -> 'Agent':
        """Add RAI guardrails to agent"""
        self._ensure_clients()

        # Get RAI endpoint
        rai_endpoint = f"{self._agent_module._http.base_url.replace('agent-', 'srs-')}/v1/rai/inference"

        current_features = self.features or []
        new_features = current_features + [policy.to_feature_format(rai_endpoint)]
        return self._agent_module.update(self.id, features=new_features)

    def remove_rai_policy(self) -> 'Agent':
        """Remove RAI guardrails"""
        self._ensure_clients()
        current_features = self.features or []
        new_features = [f for f in current_features if f.get("type") != "RAI"]
        return self._agent_module.update(self.id, features=new_features)

    def has_rai_policy(self) -> bool:
        """Check if RAI policy is enabled"""
        if not self.features:
            return False
        return any(f.get("type") == "RAI" for f in self.features)

    def enable_file_output(self) -> 'Agent':
        """Enable file generation for this agent"""
        self._ensure_clients()
        return self._agent_module.update(self.id, file_output=True)

    def disable_file_output(self) -> 'Agent':
        """Disable file generation"""
        self._ensure_clients()
        return self._agent_module.update(self.id, file_output=False)

    def has_file_output(self) -> bool:
        """Check if file output is enabled"""
        return self.file_output


    def set_image_model(self, image_model: 'ImageModelConfig') -> 'Agent':
        """Set image generation model"""
        self._ensure_clients()
        config = {"model": image_model.model, "credential_id": image_model.credential_id}
        return self._agent_module.update(self.id, image_output_config=config)

    def disable_image_output(self) -> 'Agent':
        """Disable image generation"""
        self._ensure_clients()
        return self._agent_module.update(self.id, image_output_config=None)

    def has_image_output(self) -> bool:
        """Check if image generation enabled"""
        return self.image_output_config is not None


    def enable_reflection(self) -> 'Agent':
        """Enable self-reflection"""
        return self._update_srs_module(reflection=True)

    def disable_reflection(self) -> 'Agent':
        """Disable self-reflection"""
        return self._update_srs_module(reflection=False)

    def has_reflection(self) -> bool:
        """Check if reflection enabled"""
        return self._get_srs_module().get('reflection', False)

    def enable_bias_check(self) -> 'Agent':
        """Enable bias detection"""
        return self._update_srs_module(bias=True)

    def disable_bias_check(self) -> 'Agent':
        """Disable bias detection"""
        return self._update_srs_module(bias=False)

    def has_bias_check(self) -> bool:
        """Check if bias detection enabled"""
        return self._get_srs_module().get('bias', False)

    def _get_srs_module(self) -> Dict:
        """Get current SRS modules config"""
        if not self.features:
            return {}
        for f in self.features:
            if f.get("type") == "SRS":
                return f.get("config", {}).get("modules", {})
        return {}

    def _update_srs_module(self, **modules) -> 'Agent':
        """Update SRS modules"""
        current_features = self.features or []
        srs_modules = self._get_srs_module().copy()
        srs_modules.update(modules)

        # Remove old SRS
        features_without_srs = [f for f in current_features if f.get("type") != "SRS"]

        # Add updated SRS if any module enabled
        if any(srs_modules.values()):
            srs_feature = {
                "type": "SRS",
                "config": {"max_tries": 1, "modules": srs_modules},
                "priority": 0
            }
            new_features = features_without_srs + [srs_feature]
        else:
            new_features = features_without_srs

        return self._agent_module.update(self.id, features=new_features)

    def enable_llm_judge(self) -> 'Agent':
        """Enable LLM-as-judge"""
        current_features = self.features or []
        new_features = current_features + [{"type": "UQLM_LLM_JUDGE", "config": {}, "priority": 0}]
        return self._agent_module.update(self.id, features=new_features)

    def disable_llm_judge(self) -> 'Agent':
        """Disable LLM judge"""
        current_features = self.features or []
        new_features = [f for f in current_features if f.get("type") != "UQLM_LLM_JUDGE"]
        return self._agent_module.update(self.id, features=new_features)

    def has_llm_judge(self) -> bool:
        """Check if LLM judge enabled"""
        return self.features and any(f.get("type") == "UQLM_LLM_JUDGE" for f in self.features)

    def add_groundedness_facts(self, facts: List[str]) -> 'Agent':
        """Add facts for groundedness"""
        current_features = self.features or []
        features_without_groundedness = [f for f in current_features if f.get("type") != "GROUNDEDNESS"]
        new_features = features_without_groundedness + [{"type": "GROUNDEDNESS", "config": {"facts": facts}, "priority": 0}]
        return self._agent_module.update(self.id, features=new_features)

    def remove_groundedness(self) -> 'Agent':
        """Remove groundedness"""
        current_features = self.features or []
        new_features = [f for f in current_features if f.get("type") != "GROUNDEDNESS"]
        return self._agent_module.update(self.id, features=new_features)

    def has_groundedness(self) -> bool:
        """Check if groundedness enabled"""
        return self.features and any(f.get("type") == "GROUNDEDNESS" for f in self.features)

    def add_memory(self, max_messages: int = 10) -> 'Agent':
        """
        Enable memory for this agent

        Configures the agent to maintain conversation context across messages.

        Args:
            max_messages: Maximum messages to keep in context (default: 10, max: 200)

        Returns:
            Agent: Updated agent with memory enabled

        Example:
            >>> agent = studio.create_agent(name="Bot", provider="gpt-4o")
            >>> agent = agent.add_memory(max_messages=50)
            >>>
            >>> # Agent now maintains conversation context
            >>> agent.run("My name is John", session_id="session_1")
            >>> agent.run("What's my name?", session_id="session_1")
            >>> # "Your name is John" - remembers from context!
        """
        from lyzr.memory import MemoryConfig

        self._ensure_clients()

        memory_config = MemoryConfig(max_messages_context_count=max_messages)

        # Get current features
        current_features = self.features or []

        # Remove existing memory feature if present
        features_without_memory = [
            f for f in current_features
            if f.get("type") != "MEMORY"
        ]

        # Add new memory feature
        new_features = features_without_memory + [memory_config.to_feature_format()]

        # Update agent
        return self._agent_module.update(self.id, features=new_features)

    def remove_memory(self) -> 'Agent':
        """
        Disable memory for this agent

        Returns:
            Agent: Updated agent without memory

        Example:
            >>> agent.remove_memory()
        """
        self._ensure_clients()

        # Remove memory feature from features array
        current_features = self.features or []
        features_without_memory = [
            f for f in current_features
            if f.get("type") != "MEMORY"
        ]

        return self._agent_module.update(self.id, features=features_without_memory)

    def has_memory(self) -> bool:
        """
        Check if agent has memory enabled

        Returns:
            bool: True if memory is enabled

        Example:
            >>> if agent.has_memory():
            ...     logger.info("Memory enabled")
        """
        if not self.features:
            return False

        return any(f.get("type") == "MEMORY" for f in self.features)

    def get_memory_config(self) -> Optional[Dict[str, Any]]:
        """
        Get current memory configuration

        Returns:
            Dict or None: Memory config if enabled

        Example:
            >>> config = agent.get_memory_config()
            >>> if config:
            ...     logger.info("Max messages: {config['max_messages_context_count']}")
        """
        if not self.features:
            return None

        for feature in self.features:
            if feature.get("type") == "MEMORY":
                return feature.get("config")

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excludes private fields)"""
        return self.model_dump(by_alias=False, exclude_none=True)

    def __str__(self) -> str:
        return f"Agent(id='{self.id}', name='{self.name}', model='{self.provider_id}/{self.model}')"

    def __repr__(self) -> str:
        return self.__str__()


