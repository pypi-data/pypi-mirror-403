"""
Set your API key:
  export LYZR_API_KEY="your-api-key"
Or pass directly:
  Studio(api_key="your-api-key")

Get your API key: https://studio.lyzr.ai
"""

from pydantic import BaseModel, Field
from typing import List
import asyncio
import json

studio = Studio()  # Uses LYZR_API_KEY env var

# Knowledge Bases - Different domains
tech_kb = studio.create_knowledge_base(name="tech_research")
tech_kb.add_text(
    "AI Industry: $150B market, 40% YoY growth, transforming healthcare, finance", source="tech"
)

business_kb = studio.create_knowledge_base(name="business_research")
business_kb.add_text(
    "SaaS Metrics: 70% gross margin typical, CAC payback 12-18 months ideal", source="biz"
)


# Structured Outputs
class ResearchFindings(BaseModel):
    key_insights: List[str]
    data_points: List[str]
    sources_used: List[str]


class CritiqueResult(BaseModel):
    gaps: List[str]
    strengths: List[str]
    recommendations: List[str]


class FinalReport(BaseModel):
    title: str
    executive_summary: str
    key_findings: List[str]
    market_analysis: str
    recommendations: List[str]
    confidence_score: float = Field(ge=0, le=1)


# Agent 1: Researcher - Gathers information
researcher = studio.create_agent(
    name="Researcher",
    provider="openai/gpt-4o",
    role="Research analyst",
    goal="Gather comprehensive information",
    instructions="Search knowledge bases, extract key data, cite sources",
    memory=15,
    response_model=ResearchFindings,
)
# Agent 2: Analyst - Analyzes data
analyst = studio.create_agent(
    name="Analyst",
    provider="openai/gpt-4o",
    role="Data analyst",
    goal="Analyze findings and calculate projections",
    instructions="Use calculate_market_potential for projections, provide insights",
    memory=15,
)
analyst.add_tool(calculate_market_potential)

# Agent 3: Critic - Quality check
critic = studio.create_agent(
    name="Critic",
    provider="openai/gpt-4o-mini",
    role="Critical reviewer",
    goal="Identify gaps and validate analysis",
    instructions="Challenge assumptions, find weaknesses, suggest improvements",
    response_model=CritiqueResult,
)


# Local Tools - Data analysis
@tool()
def calculate_market_potential(market_size: float, growth_rate: float, years: int) -> str:
    """Calculate projected market size"""
    projected = market_size * ((1 + growth_rate / 100) ** years)
    return f"Year {years} projection: ${projected:.1f}B (from ${market_size}B at {growth_rate}% growth)"


@tool()
def save_report(title: str, content: str) -> str:
    """Save research report to file"""
    filename = f"{title.lower().replace(' ', '_')}.json"
    with open(filename, "w") as f:
        json.dump({"title": title, "content": content}, f, indent=2)
    return f"Saved to {filename}"


# Agent 4: Writer - Final synthesis
writer = studio.create_agent(
    name="Writer",
    provider="openai/gpt-4o",
    role="Research writer",
    goal="Create comprehensive report",
    instructions="Synthesize all inputs into polished report",
    response_model=FinalReport,
)

writer.add_tool(save_report)


async def main():
    topic = "AI Automation Market Opportunity for SaaS"

    # Step 1: Research phase
    research: ResearchFindings = researcher.run(
        f"Research: {topic}", knowledge_bases=[tech_kb, business_kb]
    )

    # Step 2: Analysis phase
    analysis = await analyst.run_with_local_tools(
        f"Analyze these findings:\n{research}\n",
        f"Calculate 5-year market projection for AI automation.",
    )

    # Step 3: Critique phase
    critique: CritiqueResult = critic.run(
        f"Review this research and analysis:\n"
        f"Research: {research}\n"
        f"Analysis: {analysis.response[:500]}"
    )

    # Step 4: Final synthesis
    report: FinalReport = await writer.run_with_local_tools(
        f"Create comprehensive report on: {topic}\n\n"
        f"Research: {research}\n"
        f"Analysis: {analysis.response}\n"
        f"Critique: {critique}\n\n"
        f"Save the report."
    )


asyncio.run(main())
