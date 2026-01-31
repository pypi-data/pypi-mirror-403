# Changelog

All notable changes to Sumiki (Lyzr SDK) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-01-29

### Fixed
- Agent clone method field mapping (agent_role → role, agent_goal → goal, agent_instructions → instructions)
- Jupyter/Colab async event loop handling with nest-asyncio support

### Added
- Optional jupyter dependency for notebook compatibility

## [0.1.1] - 2026-01-29

### Fixed
- Critical bug fixes for production readiness
- Clone method now uses create endpoint instead of broken clone API
- RAI policy banned_topics format (dict with "name" key)
- Context and KnowledgeBase API response parsing
- Debug log f-string formatting for proper variable interpolation
- Forward reference resolution in Pydantic models
- Jupyter/Colab compatibility - handle existing event loops gracefully

### Changed
- Refactored codebase into modular packages for better maintainability
- Removed all hardcoded API keys from examples
- Enhanced README with comprehensive feature documentation

### Added
- MANIFEST.in for proper package distribution
- CHANGELOG.md for version tracking
- Jupyter support with nest-asyncio (optional dependency)
- Better async event loop handling for notebooks

## [0.1.0] - 2026-01-29

### Added

#### Core Features
- **Smart Agents** - Create, run, update, clone, and delete AI agents
- **Structured Outputs** - Type-safe responses using Pydantic models
- **Streaming** - Real-time response streaming
- **Multi-provider Support** - OpenAI, Anthropic, Google, Groq, Perplexity, AWS Bedrock

#### Knowledge Base (RAG)
- Create and manage knowledge bases with multiple vector stores
- Support for Qdrant, Weaviate, PG-Vector, Milvus, Amazon Neptune
- Add documents: PDF, DOCX, TXT, websites, raw text
- Query with configurable retrieval (basic, MMR, HyDE, time-aware)
- Runtime configuration for per-call customization
- Document management (list, delete, reset)

#### Memory
- Agent-level conversation memory (last N messages)
- External memory providers: AWS AgentCore, Mem0, SuperMemory
- Memory credential management with validation
- AWS-specific resource management

#### Tools - Unified API
- **Local Tools** - Add Python functions without decorators
- **Backend Tools** - Type-safe integrations (15+ services)
  - CRM: HubSpot, Salesforce
  - Communication: Gmail, Slack
  - E-commerce: Shopify, Stripe
  - Productivity: Notion, Google Calendar, Google Drive
  - Development: GitHub
- Automatic async execution for local tools
- Parallel tool execution with asyncio

#### Context
- Key-value pairs for background information
- Add contexts to agents at creation or runtime
- Update and delete context values

#### RAI Guardrails
- Toxicity detection with configurable thresholds
- PII protection (block, redact, mask)
- Secrets detection and masking
- Topic filtering (allowed/banned lists)
- NSFW content detection
- Prompt injection prevention
- Type-safe enums (PIIType, PIIAction, SecretsAction)

#### File & Image Output
- File generation capability
- Image generation with Gemini and DALL-E models
- Artifact download support

#### Evaluation Features
- Self-reflection
- Bias detection
- LLM-as-judge evaluation
- Groundedness checking with facts

#### SDK Infrastructure
- **Modular Architecture** - Clean package structure
  - `models/` - Agent configuration and entities
  - `knowledge_base/` - RAG functionality
  - `memory/` - Memory providers
  - `tools/` - Local and backend tools
- **Type Safety** - Full type hints with `py.typed` marker
- **Smart Objects** - Objects with methods (kb.query(), agent.run(), etc.)
- **Environment Support** - prod, dev, local configurations
- **Logging System** - Configurable log levels (debug, info, warning, error)
- **Error Handling** - Custom exception hierarchy
- **Version Management** - Centralized version in `__version__.py`

### Fixed
- Critical indentation bugs in inference.py and models.py
- Circular import issues in models package
- Forward reference resolution with Pydantic v2
- API response parsing for contexts and knowledge bases
- Clone method to use create endpoint instead of broken clone endpoint
- RAI policy banned_topics format (list of dicts with "name" key)
- Debug log f-string formatting

### Changed
- Refactored large files into modular packages
  - `models.py` (1,318 lines) → `models/` package (3 files)
  - `knowledge_base.py` (950 lines) → `knowledge_base/` package (4 files)
  - `memory.py` (668 lines) → `memory/` package (4 files)
- Improved developer experience with better file organization
- Enhanced type safety with enums and type hints

### Developer Experience
- No decorators required for local tools
- Unified API for local and backend tools
- Auto-async detection for local tools
- Type-safe backend tool classes
- Comprehensive examples (11 demos)
- Full IDE autocomplete support

## [Unreleased]

### Planned
- Unit tests for all modules
- Integration tests
- Type stub files (.pyi)
- Performance optimizations
- Additional backend tool integrations
- Advanced RAG features

---

## Version History

- **0.1.0** (2026-01-29) - Initial public release
