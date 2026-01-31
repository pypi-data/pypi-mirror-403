"""
Set your API key:
  export LYZR_API_KEY="your-api-key"
Or pass directly:
  Studio(api_key="your-api-key")

Get your API key: https://studio.lyzr.ai
"""

Customer Support Automation - Real-World Power Example

Features: Knowledge Base + Memory + Local Tools + Structured Outputs
"""

from lyzr import Studio, tool, get_registered_tools
from pydantic import BaseModel, Field
from typing import Literal
import asyncio

# Setup
studio = Studio()  # Uses LYZR_API_KEY env var

# 1. Knowledge Base - Company documentation
kb = studio.create_knowledge_base(name="support_docs")
kb.add_text("Refund policy: 30-day money-back guarantee", source="policy")
kb.add_text("Business hours: Mon-Fri 9am-5pm EST", source="hours")
kb.add_text("Shipping: Free over $50, standard 3-5 days", source="shipping")

# 2. Local Tool - Access customer data
@tool()
def get_customer_order(customer_id: str) -> str:
    """Get customer's order status"""
    orders = {
        "C123": "Order #789: Laptop, shipped 2 days ago, tracking: TRK123",
        "C456": "Order #790: Phone, processing, ships tomorrow"
    }
    return orders.get(customer_id, "No orders found")

# 3. Structured Output - Support ticket format
class SupportTicket(BaseModel):
    customer_id: str
    issue_type: Literal["refund", "shipping", "order_status", "general"]
    priority: Literal["high", "medium", "low"]
    resolution: str
    follow_up_needed: bool

# 4. Agent with Memory + Structured Output
agent = studio.create_agent(
    name="Support Agent",
    provider="openai/gpt-4o",
    role="Customer support specialist",
    goal="Resolve customer issues efficiently",
    instructions="Use KB for policies, get_customer_order for orders, create tickets",
    memory=20,  # Remember conversation
    response_model=SupportTicket
)

# 5. Add local tool
agent.add_tool(get_customer_order)

# 6. Complete support flow
async def main():
    session = "customer_c123_chat"

    # Customer inquiry
    print("Customer: I want to return my laptop\n")

    ticket: SupportTicket = await agent.run_with_local_tools(
        "Customer C123 wants to return their laptop. Check their order and our refund policy.",
        session_id=session,
        knowledge_bases=[kb]
    )

    print(f"Ticket Created:")
    print(f"  Customer: {ticket.customer_id}")
    print(f"  Type: {ticket.issue_type}")
    print(f"  Priority: {ticket.priority}")
    print(f"  Resolution: {ticket.resolution}")
    print(f"  Follow-up: {ticket.follow_up_needed}")

    # Cleanup
    kb.delete()
    agent.delete()

asyncio.run(main())

# This example shows:
# ✓ Knowledge base for company docs
# ✓ Local tool for customer data
# ✓ Memory for conversation context
# ✓ Structured output for ticket creation
# ✓ Type-safe results
# All in ~60 lines of clean code!
