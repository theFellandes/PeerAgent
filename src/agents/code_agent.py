# CodeAgent - Generates code based on user requests
from typing import Optional
import re
import json
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import BaseAgent
from src.models.agents import CodeOutput
from src.utils.logger import get_logger


class CodeAgent(BaseAgent):
    """Agent specialized in generating code solutions."""
    
    def __init__(self, session_id: Optional[str] = None):
        super().__init__(session_id)
        self.logger = get_logger("CodeAgent")
    
    @property
    def agent_type(self) -> str:
        return "code_agent"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert software engineer. Write clean, efficient code.
        
Generate code for the user's request. Include a brief explanation."""
    
    async def execute(
        self,
        task: str,
        language: str = "python",
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> CodeOutput:
        """Generate code based on the user's task description."""
        self.logger.info(f"CodeAgent executing: {task[:50]}...")
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", f"Write {language} code for: {task}")
            ])
            
            messages = prompt.format_messages()
            response = await self.llm.ainvoke(messages)
            raw = response.content.strip()
            
            self.logger.info(f"Got response: {len(raw)} chars")
            
            # Extract code from markdown blocks
            code_match = re.search(r'```(?:python|javascript|java|typescript|go|rust|cpp|c\+\+|csharp|ruby|php|swift|kotlin)?\s*\n(.*?)```', raw, re.DOTALL | re.IGNORECASE)
            
            if code_match:
                code = code_match.group(1).strip()
                explanation = re.sub(r'```[\s\S]*?```', '', raw).strip()
                explanation = ' '.join(explanation.split())[:500] or "Code generated."
            else:
                # No code block, use entire response
                code = raw
                explanation = "Code generated from response."
            
            self.logger.info("CodeAgent completed successfully")
            return CodeOutput(
                code=code,
                language=language,
                explanation=explanation
            )
            
        except Exception as e:
            self.logger.error(f"CodeAgent error: {e}")
            return CodeOutput(
                code=f"# Error: {e}",
                language=language,
                explanation=f"Error: {e}"
            )
