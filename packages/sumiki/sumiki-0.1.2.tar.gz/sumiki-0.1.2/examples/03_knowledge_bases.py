"""
Set your API key:
  export LYZR_API_KEY="your-api-key"
Or pass directly:
  Studio(api_key="your-api-key")

Get your API key: https://studio.lyzr.ai
"""

from lyzr import Studio


studio = Studio(
    env="dev"  # Set LYZR_API_KEY environment variable
)  # Uses LYZR_API_KEY env var

# Create knowledge base
kb = studio.create_knowledge_base(name="company_docs", vector_store="qdrant")  # need enums

# Add documents
kb.add_text("Company hours: 9am-5pm EST", source="hours.txt")
kb.add_text("Refund policy: 30-day guarantee", source="policy.txt")


# Query knowledge base
results = kb.query("What are the hours?", top_k=3)
for result in results:
    print(f"Score {result.score:.2f}: {result.text}")

# Use with agent
agent = studio.create_agent(
    name="Support Bot",
    provider="openai/gpt-4o-mini",
    role="Customer support agent",
    goal="Answer customer questions",
    instructions="Use knowledge base to answer accurately",
)

# Pass KB at runtime
response = agent.run("What are your business hours?", knowledge_bases=[kb])
print(f"\nAgent: {response.response}")

# Cleanup
kb.delete()
agent.delete()
