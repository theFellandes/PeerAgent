# DataAnalysisAgent - CSV/Excel data analysis
"""
Agent specialized in analyzing tabular data from CSV/Excel files.
"""
from typing import Any, Dict, Optional, List
import json
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base import BaseAgent
from src.utils.logger import log_agent_call


class DataAnalysisAgent(BaseAgent):
    """
    Agent specialized in analyzing tabular data.
    
    Handles:
    - CSV/Excel data interpretation
    - Statistical summaries
    - Data pattern identification
    - Trend analysis
    - Data quality assessment
    """

    @property
    def agent_type(self) -> str:
        return "data_analysis_agent"

    @property
    def system_prompt(self) -> str:
        return """You are an expert data analyst.

## Analysis Guidelines:

1. **Data Understanding**: First understand the structure and content
2. **Statistical Summary**: Provide key statistics when applicable
3. **Pattern Recognition**: Identify trends, outliers, correlations
4. **Clear Insights**: Present findings in business-friendly language
5. **Actionable Recommendations**: Suggest next steps based on data

## Analysis Capabilities:
- Summary statistics (mean, median, mode, std dev)
- Distribution analysis
- Trend identification
- Correlation analysis
- Anomaly detection
- Data quality assessment

Always explain findings in plain language, not just numbers."""

    @log_agent_call("data_analysis_agent")
    async def execute(
            self,
            task: str,
            data: Optional[str] = None,
            session_id: Optional[str] = None,
            task_id: Optional[str] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze the provided data or data description.
        
        Args:
            task: Analysis request or data description
            data: Optional raw data (CSV format, table, etc.)
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            
        Returns:
            Dictionary with analysis results
        """
        self.logger.info(f"DataAnalysisAgent processing: {task[:50]}...")

        # Combine task and data if both provided
        analysis_content = task
        if data:
            analysis_content = f"{task}\n\nData:\n{data}"

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""Analyze the following data or data description:

---
{analysis_content}
---

Provide a JSON response with:
- "data_overview": brief description of the data
- "key_statistics": important metrics (if applicable)
- "patterns_found": array of identified patterns or trends
- "insights": array of key insights
- "recommendations": array of recommended actions
- "data_quality": assessment of data quality (good/fair/poor)
- "visualization_suggestions": what charts would help visualize this data""")
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
                data_result = json.loads(content.strip())
                return {
                    "type": "data_analysis",
                    "data_overview": data_result.get("data_overview", ""),
                    "key_statistics": data_result.get("key_statistics", {}),
                    "patterns_found": data_result.get("patterns_found", []),
                    "insights": data_result.get("insights", []),
                    "recommendations": data_result.get("recommendations", []),
                    "data_quality": data_result.get("data_quality", "unknown"),
                    "visualization_suggestions": data_result.get("visualization_suggestions", [])
                }
            except json.JSONDecodeError:
                return {
                    "type": "data_analysis",
                    "data_overview": content,
                    "insights": [content],
                    "recommendations": []
                }
                
        except Exception as e:
            self.logger.error(f"DataAnalysisAgent failed: {e}")
            return {
                "type": "error",
                "error": str(e)
            }
