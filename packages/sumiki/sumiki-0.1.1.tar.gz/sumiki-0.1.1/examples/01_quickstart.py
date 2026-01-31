"""
Quickstart - Basic Agent Operations

Set your API key:
  export LYZR_API_KEY="your-api-key"

Get your API key: https://studio.lyzr.ai
"""

from lyzr import Studio


studio = Studio(
    env="dev"  # Set LYZR_API_KEY environment variable
)  # Uses LYZR_API_KEY env var

# Create agent
agent = studio.create_agent(
    name="Assistant",
    provider="openai/gpt-4o-mini",
    role="You are a helpful assistant",
    goal="Help users with their questions",
    instructions="Be concise and friendly",
)

# Run agent
response = agent.run("What is 2+2?")
print(response.response)

# Streaming
for chunk in agent.run("Count to 5", stream=True):
    print(chunk.content, end="", flush=True)
print()

# Update
agent = agent.update(temperature=0.3)

# Clone
clone = agent.clone("Assistant V2")

# Cleanup
agent.delete()
clone.delete()
