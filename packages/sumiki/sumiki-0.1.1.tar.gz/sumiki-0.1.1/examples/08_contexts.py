"""
Contexts - Background Information for Agents

Set your API key:
  export LYZR_API_KEY="your-api-key"

Get your API key: https://studio.lyzr.ai
"""

from lyzr import Studio


studio = Studio(
    env="dev"  # Set LYZR_API_KEY environment variable, log="debug"
)  # Uses LYZR_API_KEY env var

# Create contexts
company = studio.create_context(
    name="company_info", value="Lyzr - AI agent infrastructure provider with 50k+ developers"
)

support = studio.create_context(
    name="support_info", value="Support hours: 9am-5pm EST, Email: support@lyzr.ai"
)

# Create agent with contexts
agent = studio.create_agent(
    name="Company Assistant",
    provider="openai/gpt-4o-mini",
    role="Company assistant",
    goal="Answer questions about the company",
    instructions="Use the provided context to answer accurately",
    contexts=[company, support],
)

# Agent uses contexts automatically
response = agent.run("What company am I talking to?")
print(response.response)

response = agent.run("What are your support hours?")
print(response.response)

# Update context
company = company.update(value="Lyzr - Leading AI agent platform with enterprise features")

# Add more contexts after creation
pricing = studio.create_context(
    name="pricing", value="Pro plan: $99/month, Enterprise: Custom pricing"
)

agent.add_context(pricing)

response = agent.run("What are your pricing plans?")
print(response.response)

# Cleanup
company.delete()
support.delete()
pricing.delete()
agent.delete()
