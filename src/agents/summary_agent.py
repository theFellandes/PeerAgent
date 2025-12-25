# SummaryAgent - Text summarization
"""
Agent specialized in summarizing long texts, documents, or conversations.
"""
from typing import Any, Dict, Optional
import json
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base import BaseAgent
from src.utils.logger import log_agent_call


class SummaryAgent(BaseAgent):
    """
    Agent specialized in summarizing content.
    
    Handles:
    - Long document summarization
    - Conversation summaries
    - Meeting notes condensation
    - Article/report abstracts
    """

    @property
    def agent_type(self) -> str:
        return "summary_agent"

    @property
    def system_prompt(self) -> str:
        return """You are an expert summarization specialist.

Your task is to create clear, concise summaries that capture the essential information.

## Summarization Guidelines:

1. **Identify Key Points**: Extract the most important information
2. **Maintain Context**: Preserve the meaning and intent
3. **Be Concise**: Use fewer words while keeping clarity
4. **Structure Well**: Use bullet points for complex topics
5. **Preserve Facts**: Never add information not in the original

## Output Format:
- Start with a one-line TL;DR
- Follow with 3-5 key points
- End with any important details or caveats

Respond in the same language as the input text."""

    @log_agent_call("summary_agent")
    async def execute(
            self,
            task: str,
            session_id: Optional[str] = None,
            task_id: Optional[str] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Summarize the provided text.
        
        Args:
            task: The text to summarize
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            
        Returns:
            Dictionary with summary and key points
        """
        self.logger.info(f"SummaryAgent processing: {task[:50]}...")

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""Please summarize the following text:

---
{task}
---

Provide:
1. A brief TL;DR (one sentence)
2. Key points (bullet list)
3. Any important details

Respond with a JSON object containing:
- "tldr": one-sentence summary
- "key_points": array of key points
- "details": any additional important information
- "word_count_reduction": percentage reduction from original""")
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
                    "type": "summary",
                    "tldr": data.get("tldr", ""),
                    "key_points": data.get("key_points", []),
                    "details": data.get("details", ""),
                    "word_count_reduction": data.get("word_count_reduction", "N/A")
                }
            except json.JSONDecodeError:
                # Return as plain text summary
                return {
                    "type": "summary",
                    "tldr": content[:200] + "..." if len(content) > 200 else content,
                    "key_points": [],
                    "details": content,
                    "word_count_reduction": "N/A"
                }
                
        except Exception as e:
            self.logger.error(f"SummaryAgent failed: {e}")
            return {
                "type": "error",
                "error": str(e)
            }
