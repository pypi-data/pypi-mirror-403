"""
RAI Guardrails - Responsible AI Safety

Set your API key:
  export LYZR_API_KEY="your-api-key"

Get your API key: https://studio.lyzr.ai
"""

from lyzr import Studio
from lyzr.rai import PIIType, PIIAction, SecretsAction


studio = Studio(
    env="dev"  # Set LYZR_API_KEY environment variable, log="debug"
)  # Uses LYZR_API_KEY env var

# Create RAI policy with typed enums
policy = studio.create_rai_policy(
    name="SafetyPolicy",
    description="Comprehensive safety guardrails",
    toxicity_threshold=0.3,
    prompt_injection=True,
    secrets_detection=SecretsAction.MASK,
    pii_detection={
        PIIType.CREDIT_CARD: PIIAction.BLOCK,
        PIIType.EMAIL: PIIAction.REDACT,
        PIIType.PHONE: PIIAction.REDACT,
        PIIType.SSN: PIIAction.BLOCK,
    },
    banned_topics=["politics", "religion"],
    nsfw_check=True,
    nsfw_threshold=0.8,
)

print(f"Created policy: {policy.name}")
print(f"  ID: {policy.id}")
print(f"  Toxicity enabled: {policy.toxicity_check.get('enabled')}")
print(f"  PII enabled: {policy.pii_detection.get('enabled')}")

# Create agent with RAI
agent = studio.create_agent(
    name="Safe Assistant",
    provider="openai/gpt-4o-mini",
    role="Safe and helpful assistant",
    goal="Help users responsibly",
    instructions="Be helpful while respecting safety guidelines",
    rai_policy=policy,  # Add guardrails
)

print(f"\nAgent created with RAI: {agent.has_rai_policy()}")

# Normal usage works
response = agent.run("Tell me about machine learning")
print(f"\nResponse: {response.response[:100]}...")


response = agent.run("Say my email back to me pradipta@lyzr.ai")
print(f"\nResponse with rai stuff: {response.response}...")

# Streaming is blocked with RAI
print("\nTrying to stream with RAI enabled:")
try:
    agent.run("Hello", stream=True)
except RuntimeError as e:
    print(f"  Error (expected): {e}")

# Add RAI to existing agent
agent2 = studio.create_agent(
    name="Regular Bot",
    provider="gpt-4o-mini",
    role="Assistant",
    goal="Help users",
    instructions="Be helpful",
)

print(f"\nAgent2 has RAI: {agent2.has_rai_policy()}")
agent2 = agent2.add_rai_policy(policy)
print(f"After adding RAI: {agent2.has_rai_policy()}")

# Remove RAI
agent2 = agent2.remove_rai_policy()
print(f"After removing RAI: {agent2.has_rai_policy()}")

# List all policies
policies = studio.list_rai_policies()
print(f"\nTotal RAI policies: {len(policies)}")

# Cleanup
policy.delete()
agent.delete()
agent2.delete()

print("\n" + "=" * 70)
print("RAI Features:")
print("  • Toxicity detection")
print("  • PII protection (block/redact)")
print("  • Secrets masking")
print("  • Topic filtering")
print("  • NSFW detection")
print("  • Prompt injection prevention")
print("  • Streaming disabled for safety")
print("=" * 70)
