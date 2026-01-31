"""
Advanced Features - Reflection, Bias, Groundedness, LLM Judge

Set your API key:
  export LYZR_API_KEY="your-api-key"

Get your API key: https://studio.lyzr.ai
"""

from lyzr import Studio


studio = Studio(
    env="dev"  # Set LYZR_API_KEY environment variable, log="debug"
)  # Uses LYZR_API_KEY env var

# Create agent with all advanced features
agent = studio.create_agent(
    name="Advanced Assistant",
    provider="openai/gpt-4o",
    role="Advanced assistant with quality checks",
    goal="Provide high-quality, unbiased responses",
    instructions="Be helpful, factual, and unbiased",
    # Advanced evaluation features
    reflection=True,  # Self-critique
    bias_check=True,  # Bias detection
    llm_judge=True,  # Quality evaluation
    groundedness_facts=[  # Fact validation
        "Our company was founded in 2020",
        "We have 50,000+ users worldwide",
        "Headquarters in San Francisco",
    ],
)

print("Agent created with advanced features:")
print(f"  Reflection: {agent.has_reflection()}")
print(f"  Bias Check: {agent.has_bias_check()}")
print(f"  LLM Judge: {agent.has_llm_judge()}")
print(f"  Groundedness: {agent.has_groundedness()}")

# Use agent - features work automatically
response = agent.run("Tell me about your company")
print(f"\nResponse: {response.response}")

# Toggle features
agent = agent.disable_reflection()
print(f"\nReflection after disable: {agent.has_reflection()}")

agent = agent.enable_reflection()
print(f"Reflection after enable: {agent.has_reflection()}")

# Update groundedness facts
agent = agent.add_groundedness_facts(
    ["Company founded in 2020", "Headquarters in San Francisco", "Serving enterprise clients"]
)

# Remove features
agent = agent.disable_llm_judge()
agent = agent.remove_groundedness()

print(f"\nLLM Judge: {agent.has_llm_judge()}")
print(f"Groundedness: {agent.has_groundedness()}")

agent.delete()

print("\n" + "=" * 70)
print("Advanced Features:")
print("  • Reflection - Agent self-critique and improvement")
print("  • Bias Check - Fairness and bias detection")
print("  • LLM Judge - Quality evaluation")
print("  • Groundedness - Fact-based validation")
print("=" * 70)
