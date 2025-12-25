# TranslationAgent - Multi-language translation
"""
Agent specialized in translating text between languages.
"""
from typing import Any, Dict, Optional
import json
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base import BaseAgent
from src.utils.logger import log_agent_call


class TranslationAgent(BaseAgent):
    """
    Agent specialized in language translation.
    
    Handles:
    - Text translation between any languages
    - Language detection
    - Preserving tone and context
    - Technical/business terminology
    """

    @property
    def agent_type(self) -> str:
        return "translation_agent"

    @property
    def system_prompt(self) -> str:
        return """You are an expert multilingual translator.

## Translation Guidelines:

1. **Accuracy**: Translate meaning, not just words
2. **Context Preservation**: Maintain the original tone and intent
3. **Natural Flow**: Use natural expressions in target language
4. **Technical Terms**: Handle specialized vocabulary appropriately
5. **Cultural Adaptation**: Adapt idioms and expressions appropriately

## Supported Tasks:
- Direct translation to specified language
- Automatic language detection
- Formal/informal register adaptation
- Technical document translation

Always preserve formatting (paragraphs, bullet points, etc.)."""

    @log_agent_call("translation_agent")
    async def execute(
            self,
            task: str,
            target_language: str = "English",
            session_id: Optional[str] = None,
            task_id: Optional[str] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Translate text to the target language.
        
        Args:
            task: The text to translate
            target_language: Target language (default: English)
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            
        Returns:
            Dictionary with translation and metadata
        """
        self.logger.info(f"TranslationAgent translating to {target_language}: {task[:50]}...")

        # Parse target language from task if specified
        if "to " in task.lower() and "translate" in task.lower():
            # Extract target language from "translate X to Y" pattern
            parts = task.lower().split("to ")
            if len(parts) > 1:
                potential_lang = parts[-1].split()[0].strip('.:,')
                if potential_lang in ["english", "turkish", "german", "french", "spanish", 
                                       "italian", "portuguese", "dutch", "russian", "chinese",
                                       "japanese", "korean", "arabic"]:
                    target_language = potential_lang.capitalize()

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""Translate the following text to {target_language}:

---
{task}
---

Provide a JSON response with:
- "source_language": detected source language
- "target_language": target language
- "original_text": the original text
- "translated_text": the translated text
- "notes": any translation notes or caveats (optional)""")
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
                    "type": "translation",
                    "source_language": data.get("source_language", "Unknown"),
                    "target_language": data.get("target_language", target_language),
                    "original_text": data.get("original_text", task),
                    "translated_text": data.get("translated_text", ""),
                    "notes": data.get("notes", "")
                }
            except json.JSONDecodeError:
                # Return raw translation
                return {
                    "type": "translation",
                    "source_language": "Unknown",
                    "target_language": target_language,
                    "original_text": task,
                    "translated_text": content,
                    "notes": ""
                }
                
        except Exception as e:
            self.logger.error(f"TranslationAgent failed: {e}")
            return {
                "type": "error",
                "error": str(e)
            }
