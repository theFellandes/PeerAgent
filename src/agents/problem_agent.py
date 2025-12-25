# ProblemStructuringAgent - Problem Tree construction
from typing import Any, Dict, List, Optional
import json
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base import BaseAgent
from src.models.agents import ProblemTree, ProblemCause, BusinessDiagnosis
from src.utils.logger import log_agent_call


class ProblemStructuringAgent(BaseAgent):
    """
    Agent specialized in structuring business problems into Problem Trees.

    Takes input from BusinessSenseAgent and creates structured analysis:
    - Problem type classification
    - Main problem statement
    - Root causes with sub-causes (Issue Tree)
    """

    @property
    def agent_type(self) -> str:
        return "problem_structuring_agent"

    @property
    def system_prompt(self) -> str:
        return """You are an expert business analyst specializing in problem structuring and root cause analysis.

Your role is to take a business problem diagnosis and create a structured Problem Tree (Issue Tree).

PROBLEM CLASSIFICATION:
Classify each problem into ONE of these categories:
- Growth: Revenue, sales, market share, customer acquisition problems
- Cost: Expense management, operational cost, efficiency problems
- Operational: Process, workflow, delivery, quality problems
- Technology: IT infrastructure, software, digital transformation problems
- Regulation: Compliance, legal, regulatory problems
- Organizational: HR, culture, structure, leadership problems

PROBLEM TREE STRUCTURE:
For each problem, identify:
1. Main Problem: Clear, concise statement of the core issue
2. Root Causes: 3-5 major causes contributing to the problem
3. Sub-Causes: 2-3 specific factors under each root cause

BEST PRACTICES:
- Be MECE (Mutually Exclusive, Collectively Exhaustive)
- Use actionable language
- Focus on causes, not symptoms
- Prioritize based on impact
- Consider interdependencies between causes"""

    def _get_json_format_prompt(self) -> str:
        """Return the JSON format instructions as plain text (avoiding template issues)."""
        return """You must respond with ONLY a valid JSON object in this exact format:
{
    "problem_type": "Growth" | "Cost" | "Operational" | "Technology" | "Regulation" | "Organizational",
    "main_problem": "Clear statement of the core problem",
    "root_causes": [
        {
            "cause": "First root cause",
            "sub_causes": ["Sub-cause 1.1", "Sub-cause 1.2", "Sub-cause 1.3"]
        },
        {
            "cause": "Second root cause",
            "sub_causes": ["Sub-cause 2.1", "Sub-cause 2.2"]
        },
        {
            "cause": "Third root cause",
            "sub_causes": ["Sub-cause 3.1", "Sub-cause 3.2"]
        }
    ]
}

Include 3-5 root causes, each with 2-3 sub-causes. Output ONLY the JSON, no other text."""

    @log_agent_call("problem_structuring_agent")
    async def execute(
            self,
            diagnosis: BusinessDiagnosis,
            additional_context: Optional[str] = None,
            session_id: Optional[str] = None,
            task_id: Optional[str] = None,
            **kwargs
    ) -> ProblemTree:
        """
        Structure a business problem into a Problem Tree.

        Args:
            diagnosis: BusinessDiagnosis from BusinessSenseAgent
            additional_context: Any additional context from the conversation
            session_id: Session ID for tracking
            task_id: Task ID for tracking

        Returns:
            ProblemTree with structured analysis
        """
        self.logger.info(f"ProblemStructuringAgent processing diagnosis: {diagnosis.customer_stated_problem[:50]}...")

        # Build comprehensive prompt content
        context = f"""Business Diagnosis:
- Customer Stated Problem: {diagnosis.customer_stated_problem}
- Identified Business Problem: {diagnosis.identified_business_problem}
- Hidden Root Risk: {diagnosis.hidden_root_risk}
- Urgency Level: {diagnosis.urgency_level}"""
        
        if additional_context:
            context += f"\n\nAdditional Context:\n{additional_context}"

        # Use direct messages to avoid template variable issues with JSON braces
        messages = [
            SystemMessage(content=self.system_prompt),
            SystemMessage(content=self._get_json_format_prompt()),
            HumanMessage(content=f"Create a Problem Tree for this diagnosis:\n\n{context}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            # Parse JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            # Build ProblemTree from parsed data
            root_causes = []
            for cause_data in data.get("root_causes", []):
                root_causes.append(ProblemCause(
                    cause=cause_data.get("cause", "Unknown cause"),
                    sub_causes=cause_data.get("sub_causes", [])
                ))
            
            result = ProblemTree(
                problem_type=data.get("problem_type", "Operational"),
                main_problem=data.get("main_problem", diagnosis.identified_business_problem),
                root_causes=root_causes
            )
            
            self.logger.info(f"ProblemTree created: {result.problem_type} - {len(result.root_causes)} causes")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            return ProblemTree(
                problem_type="Operational",
                main_problem=diagnosis.identified_business_problem,
                root_causes=[
                    ProblemCause(
                        cause="Analysis requires manual review",
                        sub_causes=["JSON parsing error", "Please retry the analysis"]
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"ProblemStructuringAgent failed: {e}")
            return ProblemTree(
                problem_type="Operational",
                main_problem=diagnosis.identified_business_problem,
                root_causes=[
                    ProblemCause(
                        cause="Analysis incomplete",
                        sub_causes=["Unable to fully structure the problem", str(e)]
                    )
                ]
            )

    async def structure_from_text(
            self,
            problem_description: str,
            session_id: Optional[str] = None,
            task_id: Optional[str] = None,
            **kwargs
    ) -> ProblemTree:
        """
        Create a Problem Tree directly from text without prior diagnosis.
        Useful for quick structuring without full Socratic flow.

        Args:
            problem_description: Text description of the problem
            session_id: Session ID for tracking
            task_id: Task ID for tracking

        Returns:
            ProblemTree with structured analysis
        """
        self.logger.info(f"Structuring problem from text: {problem_description[:50]}...")

        # Use direct messages to avoid template variable issues with JSON braces
        messages = [
            SystemMessage(content=self.system_prompt),
            SystemMessage(content=self._get_json_format_prompt()),
            HumanMessage(content=f"Create a Problem Tree for this business problem:\n\n{problem_description}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            # Parse JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            # Build ProblemTree from parsed data
            root_causes = []
            for cause_data in data.get("root_causes", []):
                root_causes.append(ProblemCause(
                    cause=cause_data.get("cause", "Unknown cause"),
                    sub_causes=cause_data.get("sub_causes", [])
                ))
            
            return ProblemTree(
                problem_type=data.get("problem_type", "Operational"),
                main_problem=data.get("main_problem", problem_description[:200]),
                root_causes=root_causes
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            return ProblemTree(
                problem_type="Operational",
                main_problem=problem_description[:200],
                root_causes=[
                    ProblemCause(
                        cause="Analysis requires manual review",
                        sub_causes=["JSON parsing error", "Please retry"]
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Text structuring failed: {e}")
            return ProblemTree(
                problem_type="Operational",
                main_problem=problem_description[:200],
                root_causes=[
                    ProblemCause(
                        cause="Unable to structure",
                        sub_causes=[str(e)]
                    )
                ]
            )
