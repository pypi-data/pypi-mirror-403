"""
Set your API key:
  export LYZR_API_KEY="your-api-key"
Or pass directly:
  Studio(api_key="your-api-key")

Get your API key: https://studio.lyzr.ai

Local Tools - Advanced Examples

Demonstrates: Multiple tools, parallel execution, complex workflows
"""

from lyzr import Studio
import json


# Define local tools
def get_weather(city: str) -> str:
    """Get current weather for a city"""
    weather_db = {
        "San Francisco": {"temp": "72°F", "condition": "Sunny"},
        "New York": {"temp": "65°F", "condition": "Cloudy"},
        "Seattle": {"temp": "58°F", "condition": "Rainy"},
        "Miami": {"temp": "85°F", "condition": "Hot and Humid"},
    }
    data = weather_db.get(city, {"temp": "Unknown", "condition": "No data"})
    return json.dumps(data)


def calculate_price(quantity: int, unit_price: float, tax_rate: float = 8.5) -> str:
    """Calculate total price including tax"""
    subtotal = quantity * unit_price
    tax = subtotal * (tax_rate / 100)
    total = subtotal + tax
    return json.dumps(
        {
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
            "tax": tax,
            "tax_rate": tax_rate,
            "total": total,
        }
    )


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert between currencies"""
    rates = {("USD", "EUR"): 0.92, ("USD", "GBP"): 0.79, ("EUR", "USD"): 1.09, ("GBP", "USD"): 1.27}
    rate = rates.get((from_currency, to_currency), 1.0)
    converted = amount * rate
    return json.dumps(
        {
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": round(converted, 2),
            "rate": rate,
        }
    )


def get_business_hours(location: str) -> str:
    """Get business hours for different locations"""
    hours = {"US": "9 AM - 5 PM EST", "UK": "9 AM - 5 PM GMT", "Asia": "9 AM - 5 PM JST"}
    return hours.get(location, "9 AM - 5 PM Local Time")


studio = Studio(
    env="dev"  # Set LYZR_API_KEY environment variable, log="debug"
)  # Uses LYZR_API_KEY env var

agent = studio.create_agent(
    name="Multi-Tool Assistant",
    provider="openai/gpt-4o-mini",
    role="Multi-purpose assistant",
    goal="Help with weather, pricing, currency, and business info",
    instructions="Use available tools to provide accurate information. You can use multiple tools in one response.",
)

# Add all tools
agent.add_tool(get_weather)
agent.add_tool(calculate_price)
agent.add_tool(convert_currency)
agent.add_tool(get_business_hours)

# Example 1: Single tool call
print("=" * 70)
print("Example 1: Single Tool Call")
print("=" * 70)
response = agent.run("What's the weather in Seattle?")
print(f"Response: {response.response}\n")

# Example 2: Multiple sequential tool calls
print("=" * 70)
print("Example 2: Multiple Tool Calls")
print("=" * 70)
response = agent.run(
    "Check weather in San Francisco, New York, and Miami. "
    "Tell me which city has the best weather."
)
print(f"Response: {response.response}\n")

# Example 3: Complex calculation with multiple tools
print("=" * 70)
print("Example 3: Complex Multi-Tool Workflow")
print("=" * 70)
response = agent.run(
    "Calculate price for 10 items at $49.99 each with 7.5% tax, "
    "then convert the total to EUR and GBP. "
    "Present the results in a clear format."
)
print(f"Response: {response.response}\n")

# Example 4: Combining different tool types
print("=" * 70)
print("Example 4: Combining Multiple Tools")
print("=" * 70)
response = agent.run(
    "I need to know: "
    "1) Weather in New York, "
    "2) Your business hours in UK, "
    "3) Price for 3 items at $25 each, "
    "4) Convert $75 to EUR"
)
print(f"Response: {response.response}\n")

# Example 5: Tool chaining
print("=" * 70)
print("Example 5: Tool Chaining")
print("=" * 70)
response = agent.run(
    "Calculate total cost for 5 units at $100 each with 10% tax. "
    "Then convert that total amount from USD to EUR and GBP. "
    "Show me both converted amounts."
)
print(f"Response: {response.response}\n")

agent.delete()

print("=" * 70)
print("Key Insights:")
print("  • Multiple tools can be called in one request")
print("  • Tools execute in parallel when possible")
print("  • Results can chain (output of one → input to another)")
print("  • Agent orchestrates complex multi-tool workflows")
print("=" * 70)
