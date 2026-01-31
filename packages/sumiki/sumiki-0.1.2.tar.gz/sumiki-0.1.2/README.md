# Sumiki - Lyzr Agent SDK

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/sumiki.svg)](https://pypi.org/project/sumiki/)

**Production-ready AI agent infrastructure for Python**

Sumiki is the official Python SDK for Lyzr's AI agent platform. Build, deploy, and manage sophisticated AI agents with enterprise features like RAG, memory, guardrails, and tool execution.

```python
from lyzr import Studio

studio = Studio()  # Uses LYZR_API_KEY env var
agent = studio.create_agent(
    name="Support Bot",
    provider="openai/gpt-4o",
    role="Customer support assistant",
    goal="Help users with technical questions",
    instructions="Be helpful, concise, and professional"
)

response = agent.run("How do I reset my password?")
print(response.response)
```

## Installation

```bash
pip install sumiki
```

**For Jupyter/Colab notebooks:**
```bash
pip install sumiki[jupyter]
```

**Get your API key**: [studio.lyzr.ai](https://studio.lyzr.ai)

```bash
export LYZR_API_KEY="your-api-key-here"
```

## Quick Start

```python
from lyzr import Studio

# Initialize SDK
studio = Studio()

# Create an agent
agent = studio.create_agent(
    name="Assistant",
    provider="openai/gpt-4o",
    role="Helpful assistant",
    goal="Answer questions accurately",
    instructions="Be concise and friendly"
)

# Run the agent
response = agent.run("What is machine learning?")
print(response.response)

# Update configuration
agent = agent.update(temperature=0.3)

# Delete when done
agent.delete()
```

## Features

### 1. Smart Agents

Create agents with automatic provider resolution and validation.

```python
# Supports 20+ models across 6 providers
agent = studio.create_agent(
    name="Bot",
    provider="openai/gpt-4o",  # or "gpt-4o", "claude-sonnet-4-5", etc.
    role="Assistant",
    goal="Help users",
    instructions="Be helpful",
    temperature=0.7,
    top_p=0.9
)

# Run
response = agent.run("Hello!")

# Update
agent = agent.update(temperature=0.5, instructions="Be very concise")

# Clone
clone = agent.clone("Bot V2")

# Delete
agent.delete()
```

### 2. Structured Outputs

Get type-safe responses using Pydantic models.

```python
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    score: float
    summary: str

agent = studio.create_agent(
    name="Analyzer",
    provider="gpt-4o",
    role="Sentiment analyzer",
    goal="Analyze text sentiment",
    instructions="Provide detailed analysis",
    response_model=Analysis
)

result: Analysis = agent.run("I love this product!")
print(result.sentiment)  # Type-safe access
print(result.score)      # IDE autocomplete works!
```

### 3. Knowledge Bases (RAG)

Add documents for retrieval-augmented generation.

```python
# Create knowledge base
kb = studio.create_knowledge_base(
    name="company_docs",
    vector_store="qdrant",  # qdrant, weaviate, pg_vector, milvus, neptune
    embedding_model="text-embedding-3-large"
)

# Add content
kb.add_pdf("manual.pdf")
kb.add_docx("report.docx")
kb.add_website("https://docs.company.com", max_pages=50)
kb.add_text("FAQ: Our hours are 9-5", source="faq")

# Query directly
results = kb.query("What are the business hours?", top_k=3)
for result in results:
    print(f"{result.score:.2f}: {result.text}")

# Use with agent
response = agent.run(
    "What does the manual say about installation?",
    knowledge_bases=[kb]
)

# Custom retrieval config
response = agent.run(
    "Question?",
    knowledge_bases=[kb.with_config(top_k=5, score_threshold=0.7)]
)

# Manage documents
docs = kb.list_documents()
kb.delete_documents(["doc_123"])
kb.reset()  # Clear all documents
kb.delete()  # Delete KB
```

### 4. Memory

Enable conversation context across messages.

```python
# Agent-level memory (simple)
agent = studio.create_agent(
    name="Bot",
    provider="gpt-4o",
    role="Assistant",
    goal="Help users",
    instructions="Be helpful",
    memory=30  # Keep last 30 messages in context
)

agent.run("My name is Alice", session_id="user_1")
agent.run("What's my name?", session_id="user_1")
# "Your name is Alice" - remembers from context!

# Or add memory to existing agent
agent = agent.add_memory(max_messages=50)
agent = agent.remove_memory()

# External memory providers
mem0 = studio.create_memory_credential(
    provider="mem0",
    name="Mem0 Memory",
    mem0_api_key="your-key"
)

# AWS AgentCore
aws_memory = studio.create_memory_credential(
    provider="aws-agentcore",
    name="AWS Memory",
    aws_access_key_id="...",
    aws_secret_access_key="...",
    aws_region="us-east-1"
)
```

### 5. Tools - Unified API

Add local Python functions or backend integrations - same simple interface!

```python
from lyzr.tools import HubSpot, Gmail, Stripe

# Define local tool - just a function!
def read_database(query: str) -> dict:
    """Query the database"""
    # Your code here
    return {"results": [...]}

# Add any tool - unified API
agent.add_tool(read_database)           # Local function - auto-async
agent.add_tool(HubSpot.CREATE_CONTACT)  # Backend - typed
agent.add_tool(Gmail.SEND_EMAIL)        # Backend - typed
agent.add_tool(Stripe.CREATE_PAYMENT)   # Backend - typed

# Single run() works for all!
response = agent.run(
    "Create a HubSpot contact, send them an email, and query the database"
)

# Available backend tools (15+):
# HubSpot, Gmail, Stripe, Shopify, Salesforce, Slack,
# GitHub, GoogleCalendar, GoogleDrive, Notion
```

**No decorators needed!** Just pass your function to `add_tool()`.

### 6. Contexts

Provide background information to agents.

```python
# Create contexts
company = studio.create_context(
    name="company_info",
    value="Acme Corp - AI solutions provider since 2020"
)

support = studio.create_context(
    name="support_hours",
    value="9am-5pm EST, support@acme.com"
)

# Add to agent
agent = studio.create_agent(
    name="Support Bot",
    provider="gpt-4o",
    role="Support assistant",
    goal="Help customers",
    instructions="Use context for accurate info",
    contexts=[company, support]
)

# Or add to existing agent
agent = agent.add_context(company)
agent = agent.remove_context(company)

# Update context value
company = company.update(value="Acme Corp - Now serving 100k+ users")
company.delete()
```

### 7. RAI Guardrails

Responsible AI with built-in safety features.

```python
from lyzr.rai import PIIType, PIIAction, SecretsAction

# Create safety policy
policy = studio.create_rai_policy(
    name="SafetyPolicy",
    description="Production guardrails",
    toxicity_threshold=0.3,
    secrets_detection=SecretsAction.MASK,
    pii_detection={
        PIIType.CREDIT_CARD: PIIAction.BLOCK,
        PIIType.EMAIL: PIIAction.REDACT,
        PIIType.PHONE: PIIAction.REDACT
    },
    banned_topics=["politics", "religion"],
    nsfw_check=True,
    nsfw_threshold=0.8,
    prompt_injection=True
)

# Add to agent
agent = studio.create_agent(
    name="Safe Bot",
    provider="gpt-4o",
    role="Assistant",
    goal="Help safely",
    instructions="Be helpful and safe",
    rai_policy=policy
)

# Or add to existing agent
agent = agent.add_rai_policy(policy)
agent = agent.remove_rai_policy()
```

**RAI Features:**
- Toxicity detection
- PII protection (block/redact/mask)
- Secrets masking
- Topic filtering (allowed/banned)
- NSFW detection
- Prompt injection prevention

### 8. File & Image Output

Generate files and images with your agents.

```python
from lyzr.image_models import Gemini, DallE, ImageProvider

# File generation
agent = studio.create_agent(
    name="Report Generator",
    provider="gpt-4o",
    role="Report writer",
    goal="Create detailed reports",
    instructions="Generate comprehensive reports",
    file_output=True  # Enable file generation
)

response = agent.run("Create a market analysis report")
for artifact in response.artifact_files:
    print(f"File: {artifact.name}")
    artifact.download(f"./downloads/{artifact.name}")

# Image generation
agent = studio.create_agent(
    name="Designer",
    provider="gpt-4o",
    role="Visual designer",
    goal="Create images",
    instructions="Generate creative visuals",
    image_model=Gemini.FLASH  # or DallE.DALL_E_3
)

response = agent.run("Create a logo for a tech startup")
for img in response.artifact_files:
    img.download(f"./images/{img.name}")

# Available image models:
# - Gemini.PRO, Gemini.FLASH
# - DallE.DALL_E_3
```

### 9. Streaming

Stream responses for real-time output.

```python
# Streaming text
for chunk in agent.run("Tell me a story", stream=True):
    print(chunk.content, end="", flush=True)

# Note: Streaming is disabled when RAI guardrails are enabled for safety
```

### 10. Environment Configuration

Switch between production, development, and local environments.

```python
# Production (default)
studio = Studio(env="prod")

# Development
studio = Studio(env="dev")

# Local development
studio = Studio(env="local")

# Custom logging
studio = Studio(log="debug")  # debug, info, warning, error, none
```

## Advanced Features

### Complete Workflow Example

```python
from lyzr import Studio
from lyzr.tools import HubSpot
from lyzr.image_models import Gemini
from lyzr.rai import PIIType, PIIAction
from pydantic import BaseModel

studio = Studio()

# Create knowledge base
kb = studio.create_knowledge_base(name="docs")
kb.add_website("https://docs.company.com")

# Create context
company = studio.create_context(
    name="company",
    value="Tech startup, 50k users"
)

# Create RAI policy
policy = studio.create_rai_policy(
    name="Safety",
    toxicity_threshold=0.3,
    pii_detection={PIIType.EMAIL: PIIAction.REDACT}
)

# Define response schema
class Report(BaseModel):
    summary: str
    action_items: list[str]
    priority: str

# Create agent with all features
agent = studio.create_agent(
    name="Enterprise Bot",
    provider="openai/gpt-4o",
    role="Business analyst",
    goal="Analyze and report",
    instructions="Provide detailed analysis",
    memory=50,
    contexts=[company],
    rai_policy=policy,
    file_output=True,
    image_model=Gemini.FLASH,
    response_model=Report
)

# Add tools
agent.add_tool(HubSpot.CREATE_CONTACT)

# Run with RAG
response = agent.run(
    "Analyze our documentation and create a report",
    knowledge_bases=[kb],
    session_id="session_1"
)

print(response.summary)  # Type-safe!
```

## Supported Providers & Models

### LLM Providers

| Provider | Models | Context |
|----------|--------|---------|
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-5, GPT-5-mini, o3, o4-mini | 128K-1M |
| **Anthropic** | Claude Sonnet 4.5, Claude Opus 4.5, Claude 3.7 | 200K |
| **Google** | Gemini 2.0/2.5/3.0 (Flash, Pro) | 1M |
| **Groq** | Llama 3.1/3.3/4, GPT-OSS, Kimi K2 | 128K-1M |
| **Perplexity** | Sonar, Sonar Pro, Sonar Reasoning, R1-1776 | 128K |
| **AWS Bedrock** | Nova (Micro/Lite/Pro), Claude, Llama, Mistral | 64K-300K |

### Vector Stores

- **Qdrant** - Fast vector similarity search
- **Weaviate** - Semantic search platform
- **PG-Vector** - PostgreSQL extension
- **Milvus** - Cloud-native vector database
- **Amazon Neptune** - Graph database with vector support

### Memory Providers

- **Lyzr** - Built-in conversation memory
- **AWS AgentCore** - AWS-native memory with strategies
- **Mem0** - Personal memory platform
- **SuperMemory** - Advanced memory management

### Backend Tools (15+)

**CRM & Sales**: HubSpot, Salesforce, Stripe
**Communication**: Gmail, Slack
**E-commerce**: Shopify
**Productivity**: Notion, Google Calendar, Google Drive
**Development**: GitHub

## SDK Architecture

### Modular Design

```
lyzr/
├── models/          # Agent configuration & entities
├── knowledge_base/  # RAG functionality
├── memory/          # Memory providers
├── tools/           # Local & backend tools
├── context.py       # Context management
├── rai.py           # Responsible AI guardrails
└── studio.py        # Main entry point
```

### Type Safety

Full type hints with `py.typed` marker for IDE support:

```python
# Enums for type safety
from lyzr.memory import MemoryProvider, MemoryStatus
from lyzr.rai import PIIType, PIIAction, SecretsAction
from lyzr.image_models import ImageProvider

# IDE autocomplete everywhere
provider = MemoryProvider.MEM0
action = PIIAction.REDACT
```

### Smart Objects

Objects have methods - intuitive API design:

```python
# Knowledge Base
kb = studio.create_knowledge_base(name="docs")
kb.add_pdf("file.pdf")
results = kb.query("question?")
kb.delete()

# Context
ctx = studio.create_context(name="info", value="data")
ctx.update(value="new data")
ctx.delete()

# Agent
agent = studio.create_agent(...)
agent.add_tool(my_function)
agent.add_memory(30)
response = agent.run("message")
agent.delete()
```

## Examples

The `examples/` directory contains comprehensive demos:

- **01_quickstart.py** - Basic agent operations
- **02_structured_outputs.py** - Type-safe Pydantic responses
- **03_knowledge_bases.py** - RAG with documents
- **04_memory.py** - Conversation context
- **05_local_tools.py** - Local Python function execution
- **06_backend_tools.py** - HubSpot, Gmail, Stripe integration
- **07_complete_workflow.py** - All features combined
- **08_contexts.py** - Background information
- **09_file_output.py** - File and image generation
- **10_rai_guardrails.py** - Safety and compliance
- **11_advanced_features.py** - Advanced patterns

Run any example:

```bash
export LYZR_API_KEY="your-api-key"
python examples/01_quickstart.py
```

## API Reference

### Studio

Main entry point for the SDK.

```python
studio = Studio(
    api_key="sk-xxx",  # Optional, reads from LYZR_API_KEY
    env="prod",        # prod, dev, local
    timeout=30,        # Request timeout in seconds
    log="warning"      # debug, info, warning, error, none
)
```

**Methods:**
- `create_agent()` - Create new agent
- `get_agent()` - Get agent by ID
- `list_agents()` - List all agents
- `create_knowledge_base()` - Create RAG config
- `get_knowledge_base()` - Get KB by ID
- `list_knowledge_bases()` - List all KBs
- `create_context()` - Create context variable
- `get_context()` - Get context by ID
- `list_contexts()` - List all contexts
- `create_rai_policy()` - Create safety policy
- `get_rai_policy()` - Get policy by ID
- `list_rai_policies()` - List all policies
- `create_memory_credential()` - Add memory provider

### Agent

Smart agent object with methods.

```python
# Core methods
agent.run(message, session_id=None, stream=False, **kwargs)
agent.update(**kwargs)
agent.clone(new_name)
agent.delete()

# Tools
agent.add_tool(tool)  # Local function or backend tool

# Memory
agent.add_memory(max_messages=10)
agent.remove_memory()
agent.has_memory()

# Context
agent.add_context(context)
agent.remove_context(context)
agent.list_contexts()

# RAI
agent.add_rai_policy(policy)
agent.remove_rai_policy()
agent.has_rai_policy()

# File output
agent.enable_file_output()
agent.disable_file_output()
agent.has_file_output()

# Image output
agent.set_image_model(image_model)
agent.disable_image_output()
agent.has_image_output()

# Evaluation features
agent.enable_reflection()
agent.disable_reflection()
agent.enable_bias_check()
agent.disable_bias_check()
agent.enable_llm_judge()
agent.disable_llm_judge()
agent.add_groundedness_facts(["fact1", "fact2"])
agent.remove_groundedness()
```

### KnowledgeBase

RAG configuration with document management.

```python
kb.add_pdf(file_path, chunk_size=1024, chunk_overlap=128)
kb.add_docx(file_path, chunk_size=1024, chunk_overlap=128)
kb.add_txt(file_path, chunk_size=1024, chunk_overlap=128)
kb.add_website(url, max_pages=10, max_depth=2)
kb.add_text(text, source)

kb.query(query, top_k=5, retrieval_type="basic", score_threshold=0.0)
kb.list_documents()
kb.delete_documents(doc_ids)
kb.reset()
kb.update(**kwargs)
kb.delete()

kb.with_config(top_k=10, retrieval_type="basic", score_threshold=0.0)
```

### Context

Key-value pairs for background information.

```python
context.update(value)
context.delete()
context.to_feature_format()
```

### RAIPolicy

Safety and compliance guardrails.

```python
policy.update(**kwargs)
policy.delete()
policy.to_feature_format(endpoint)
```

### Memory

External memory provider credentials.

```python
memory.validate()
memory.get_status()
memory.list_resources()  # AWS only
memory.use_existing(memory_id)  # AWS only
memory.delete_resource()  # AWS only
memory.delete()
```

## Best Practices

### Error Handling

```python
from lyzr.exceptions import (
    LyzrError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    APIError,
    RateLimitError,
    TimeoutError
)

try:
    agent = studio.create_agent(...)
    response = agent.run("message")
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Invalid input: {e}")
except NotFoundError:
    print("Resource not found")
except RateLimitError:
    print("Rate limit exceeded")
except APIError as e:
    print(f"API error: {e}")
```

### Session Management

```python
import uuid

# Generate unique session ID per user
session_id = str(uuid.uuid4())

# Maintain conversation context
response1 = agent.run("My name is Bob", session_id=session_id)
response2 = agent.run("What's my name?", session_id=session_id)
# Remembers "Bob" from previous message
```

### Logging

```python
# Enable debug logging to see internals
studio = Studio(log="debug")

# See tool execution details
agent.run("Use tools")  # Shows tool calls, arguments, results

# Production: use warning/error only
studio = Studio(log="warning")
```

## Requirements

- Python 3.8+
- Dependencies: `pydantic>=2.0`, `httpx`, `json-repair`

## Development

```bash
# Clone repository
git clone https://github.com/lyzr-ai/sumiki.git
cd sumiki

# Install dependencies
pip install -e ".[dev]"

# Run examples
export LYZR_API_KEY="your-key"
python examples/01_quickstart.py
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

- **Documentation**: [docs.lyzr.ai](https://docs.lyzr.ai)
- **Issues**: [GitHub Issues](https://github.com/lyzr-ai/sumiki/issues)
- **Discord**: [Join our community](https://discord.gg/lyzr)
- **Email**: support@lyzr.ai

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built by [Lyzr](https://lyzr.ai) - AI Agent Infrastructure for Production**

50,000+ developers building with Lyzr
