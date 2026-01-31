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

# Create agent with memory
agent = studio.create_agent(
    name="Chat Bot",
    provider="openai/gpt-4o-mini",
    role="Friendly chatbot",
    goal="Have natural conversations",
    instructions="Remember what the user tells you",
    memory=20,  # Remember last 20 messages
)

session = "user_alice"

# Build conversation context
agent.run("My name is Alice", session_id=session)
agent.run("I work as a designer", session_id=session)
agent.run("I live in NYC", session_id=session)

# Test memory
response = agent.run("What's my name and job?", session_id=session)
print(response.response)

# Different session = separate memory
response = agent.run("What's my name?", session_id="different_session")
print(response.response)  # Won't know

agent.delete()
