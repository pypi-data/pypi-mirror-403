"""
Set your API key:
  export LYZR_API_KEY="your-api-key"
Or pass directly:
  Studio(api_key="your-api-key")

Get your API key: https://studio.lyzr.ai

Complete Workflow - All Features Together

Demonstrates: KB + Local Tools + Backend Tools + Memory + Structured Output
"""

from lyzr import Studio
from lyzr.tools import HubSpot
from pydantic import BaseModel

studio = Studio()  # Uses LYZR_API_KEY env var

# Knowledge Base
kb = studio.create_knowledge_base(name="product_docs")
kb.add_text("Pro plan: $99/month, includes CRM integration", source="pricing.txt")


# Local Tool - just a function!
def calculate_annual(monthly: float, discount: float = 0) -> str:
    """Calculate annual price with discount"""
    annual = monthly * 12 * (1 - discount / 100)
    return f"${annual:.2f}/year"


# Structured Output
class SalesResponse(BaseModel):
    pricing_info: str
    annual_cost: str
    recommendation: str


# Agent with everything
agent = studio.create_agent(
    name="Sales Bot",
    provider="openai/gpt-4o",
    role="Sales assistant",
    goal="Help with pricing and CRM",
    instructions="Use KB, calculate costs, recommend plans",
    memory=20,
    response_model=SalesResponse,
)

# Add tools - unified API!
agent.add_tool(calculate_annual)  # Local
agent.add_tool(HubSpot.CREATE_CONTACT)  # Backend

# Single run() - handles everything!
response: SalesResponse = agent.run(
    "What's Pro plan annual cost with 15% discount? Create CRM contact if interested.",
    knowledge_bases=[kb],
)

print(f"Pricing: {response.pricing_info}")
print(f"Annual: {response.annual_cost}")
print(f"Recommendation: {response.recommendation}")

kb.delete()
agent.delete()
