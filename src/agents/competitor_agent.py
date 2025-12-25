# CompetitorAgent - Competitor research and analysis
"""
Agent specialized in researching and analyzing competitors.
"""
from typing import Any, Dict, Optional, List
import json
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base import BaseAgent
from src.utils.logger import log_agent_call

try:
    from langchain_community.tools import DuckDuckGoSearchResults
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False


class CompetitorAgent(BaseAgent):
    """
    Agent specialized in competitor analysis.
    
    Handles:
    - Competitor identification
    - Market position analysis
    - Feature comparison
    - SWOT analysis
    - Competitive intelligence
    """

    def __init__(self):
        super().__init__()
        self.search_tool = None
        if SEARCH_AVAILABLE:
            try:
                self.search_tool = DuckDuckGoSearchResults(max_results=5)
            except Exception as e:
                self.logger.warning(f"Search tool initialization failed: {e}")

    @property
    def agent_type(self) -> str:
        return "competitor_agent"

    @property
    def system_prompt(self) -> str:
        return """You are an expert competitive intelligence analyst.

## Analysis Framework:

1. **Market Position**: Where does each competitor stand?
2. **Product/Service Comparison**: Key differentiators
3. **Pricing Strategy**: How do prices compare?
4. **Strengths & Weaknesses**: SWOT-style analysis
5. **Market Share**: Estimated market presence
6. **Strategic Recommendations**: How to compete effectively

## Deliverables:
- Competitor overview
- Feature comparison matrix
- Strengths and weaknesses
- Market positioning
- Strategic recommendations

Always cite sources when using research data."""

    async def _search_competitor(self, query: str) -> str:
        """Search for competitor information."""
        if not self.search_tool:
            return "Search not available - providing analysis based on general knowledge."
        
        try:
            results = self.search_tool.invoke(query)
            return results if results else "No results found."
        except Exception as e:
            self.logger.warning(f"Search failed: {e}")
            return f"Search failed: {str(e)}"

    @log_agent_call("competitor_agent")
    async def execute(
            self,
            task: str,
            competitors: Optional[List[str]] = None,
            session_id: Optional[str] = None,
            task_id: Optional[str] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze competitors based on the request.
        
        Args:
            task: Analysis request describing what to analyze
            competitors: Optional list of competitor names
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            
        Returns:
            Dictionary with competitor analysis
        """
        self.logger.info(f"CompetitorAgent analyzing: {task[:50]}...")

        # Search for competitor information if available
        search_context = ""
        if self.search_tool:
            search_results = await self._search_competitor(f"competitor analysis {task}")
            search_context = f"\n\nResearch Results:\n{search_results}"

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""Analyze the competitive landscape based on this request:

---
{task}
{search_context}
---

Provide a JSON response with:
- "market_overview": brief market summary
- "competitors": array of competitor objects with name, description, strengths, weaknesses
- "comparison_matrix": key features/aspects compared across competitors
- "market_positioning": how competitors are positioned
- "opportunities": gaps or opportunities identified
- "threats": competitive threats to be aware of
- "recommendations": strategic recommendations
- "sources": any sources used for research""")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            # Try to parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            try:
                data = json.loads(content.strip())
                return {
                    "type": "competitor_analysis",
                    "market_overview": data.get("market_overview", ""),
                    "competitors": data.get("competitors", []),
                    "comparison_matrix": data.get("comparison_matrix", {}),
                    "market_positioning": data.get("market_positioning", ""),
                    "opportunities": data.get("opportunities", []),
                    "threats": data.get("threats", []),
                    "recommendations": data.get("recommendations", []),
                    "sources": data.get("sources", [])
                }
            except json.JSONDecodeError:
                return {
                    "type": "competitor_analysis",
                    "market_overview": content,
                    "competitors": [],
                    "recommendations": []
                }
                
        except Exception as e:
            self.logger.error(f"CompetitorAgent failed: {e}")
            return {
                "type": "error",
                "error": str(e)
            }
