"""
Set your API key:
  export LYZR_API_KEY="your-api-key"
Or pass directly:
  Studio(api_key="your-api-key")

Get your API key: https://studio.lyzr.ai
"""

from lyzr import Studio
from pydantic import BaseModel, Field
from typing import Literal, List


studio = Studio(
    env="dev"  # Set LYZR_API_KEY environment variable
)  # Uses LYZR_API_KEY env var


# Define response structure
class SentimentAnalysis(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float
    key_points: List[str]


# Create agent with response model
agent = studio.create_agent(
    name="Sentiment Analyzer",
    provider="openai/gpt-4o",
    role="You analyze sentiment",
    goal="Analyze text sentiment accurately",
    instructions="Return sentiment, confidence, and key points",
    response_model=SentimentAnalysis,
)

# Get typed response
result: SentimentAnalysis = agent.run("I absolutely love this product! Best purchase ever!")

print(f"Sentiment: {result.sentiment}")
print(f"Confidence: {result.confidence}")
print(f"Key points: {', '.join(result.key_points)}")

agent.delete()
