# EmailAgent - Professional email drafting
"""
Agent specialized in drafting professional emails.
"""
from typing import Any, Dict, Optional
import json
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base import BaseAgent
from src.utils.logger import log_agent_call


class EmailAgent(BaseAgent):
    """
    Agent specialized in drafting professional emails.
    
    Handles:
    - Business correspondence
    - Follow-up emails
    - Meeting requests
    - Formal announcements
    - Customer communication
    """

    @property
    def agent_type(self) -> str:
        return "email_agent"

    @property
    def system_prompt(self) -> str:
        return """You are an expert business communication specialist.

## Email Writing Guidelines:

1. **Clear Subject Lines**: Concise and informative
2. **Professional Tone**: Appropriate formality level
3. **Structured Content**: 
   - Opening (greeting + context)
   - Body (main message)
   - Closing (action items + sign-off)
4. **Concise Language**: Get to the point quickly
5. **Call to Action**: Clear next steps when needed

## Email Types:
- **Formal**: Board communications, legal matters
- **Professional**: Client communications, partnerships
- **Friendly-Professional**: Team updates, internal memos
- **Concise**: Quick updates, confirmations

Always consider the recipient and context."""

    @log_agent_call("email_agent")
    async def execute(
            self,
            task: str,
            email_type: str = "professional",
            session_id: Optional[str] = None,
            task_id: Optional[str] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Draft a professional email.
        
        Args:
            task: Description of the email to write
            email_type: Type of email (formal/professional/friendly)
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            
        Returns:
            Dictionary with email components
        """
        self.logger.info(f"EmailAgent drafting: {task[:50]}...")

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""Draft a professional email based on this request:

---
{task}
---

Provide a JSON response with:
- "subject": email subject line
- "greeting": opening greeting
- "body": main email content (can include paragraphs)
- "closing": closing statement
- "signature": suggested sign-off
- "tone": the tone used (formal/professional/friendly)
- "tips": any suggestions for improvement (optional)""")
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
                
                # Build full email text
                full_email = f"""Subject: {data.get('subject', '')}

{data.get('greeting', '')}

{data.get('body', '')}

{data.get('closing', '')}

{data.get('signature', '')}"""
                
                return {
                    "type": "email",
                    "subject": data.get("subject", ""),
                    "greeting": data.get("greeting", ""),
                    "body": data.get("body", ""),
                    "closing": data.get("closing", ""),
                    "signature": data.get("signature", ""),
                    "full_email": full_email,
                    "tone": data.get("tone", email_type),
                    "tips": data.get("tips", "")
                }
            except json.JSONDecodeError:
                # Return raw content as email body
                return {
                    "type": "email",
                    "subject": "Draft Email",
                    "body": content,
                    "full_email": content,
                    "tone": email_type
                }
                
        except Exception as e:
            self.logger.error(f"EmailAgent failed: {e}")
            return {
                "type": "error",
                "error": str(e)
            }
