"""
Set your API key:
  export LYZR_API_KEY="your-api-key"
Or pass directly:
  Studio(api_key="your-api-key")

Get your API key: https://studio.lyzr.ai
"""

from lyzr import Studio
from lyzr.tools import HubSpot, Gmail, Stripe


studio = Studio(
    env="dev"  # Set LYZR_API_KEY environment variable
)  # Uses LYZR_API_KEY env var

# Create agent
agent = studio.create_agent(
    name="CRM Agent",
    provider="openai/gpt-4o-mini",
    role="CRM assistant",
    goal="Manage customer relationships",
    instructions="Use HubSpot and Gmail for customer management",
)

# Add backend tools - typed with autocomplete!
agent.add_tool(HubSpot.CREATE_CONTACT)
agent.add_tool(Gmail.SEND_EMAIL)

# Tools execute on backend automatically
response = agent.run("Create contact for john@example.com and send welcome email")
print(response.response)

# Add more tools - type-safe!
agent.add_tool(Stripe.CREATE_CUSTOMER)
agent.add_tool(HubSpot.GET_DEAL)

response = agent.run("Create Stripe customer and get HubSpot deal info")
print(response.response)

agent.delete()
