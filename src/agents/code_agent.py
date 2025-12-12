# CodeAgent - Generates code in any programming language
from typing import Optional, List
import re
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import BaseAgent
from src.models.agents import CodeOutput
from src.utils.logger import get_logger


class CodeAgent(BaseAgent):
    """Agent specialized in generating code in ANY programming language."""
    
    def __init__(self, session_id: Optional[str] = None):
        super().__init__(session_id)
        self.logger = get_logger("CodeAgent")
    
    @property
    def agent_type(self) -> str:
        return "code_agent"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert software engineer proficient in ALL programming languages.

IMPORTANT: Generate code in the EXACT language the user requests. 
- If they ask for Java, write Java code
- If they ask for JavaScript, write JavaScript code
- If they ask for SQL, write SQL code
- If they ask for Python, write Python code
- If they ask for C++, write C++ code
- And so on for any language

Do NOT wrap code from other languages in Python. Write native code in the requested language.

For each response:
1. Identify the programming language requested
2. Write clean, idiomatic code in THAT language
3. Include proper syntax and conventions for that language
4. Provide a brief explanation

IMPORTANT: Pay attention to the conversation history. If the user mentioned they are working 
with a specific language or framework earlier, use that context for your response."""
    
    def _detect_language(self, task: str) -> str:
        """Detect the programming language from the task."""
        task_lower = task.lower()
        
        # Language detection patterns - order matters! More specific patterns first
        # Note: javascript must come before java since 'javascript' contains 'java'
        language_patterns = {
            "sql": ["sql", "query", "select", "insert", "database query", "mysql", "postgresql", "sqlite"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular", "typescript", "ts"],
            "java": [" java ", "java ", " java", "jvm", "spring boot", "maven", "gradle"],
            "cpp": ["c++", "cpp", "c plus plus"],
            "c": ["in c ", " c code", "c language", "c programming"],
            "csharp": ["c#", "csharp", ".net", "dotnet"],
            "go": ["golang", " go ", "go language"],
            "rust": ["rust", "cargo"],
            "ruby": ["ruby", "rails"],
            "php": ["php", "laravel"],
            "swift": ["swift", "ios", "xcode"],
            "kotlin": ["kotlin", "android"],
            "scala": ["scala", "akka"],
            "r": [" r ", "r language", "rstudio", "r programming"],
            "bash": ["bash", "shell", "sh script"],
            "powershell": ["powershell", "ps1"],
            "html": ["html", "webpage"],
            "css": ["css", "stylesheet"],
            "python": ["python", "py", "django", "flask", "pandas", "numpy"],
        }
        
        for lang, patterns in language_patterns.items():
            for pattern in patterns:
                if pattern in task_lower:
                    return lang
        
        # Default to python if no language detected
        return "python"
    
    async def execute(
        self,
        task: str,
        language: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        chat_history: Optional[List[BaseMessage]] = None,
        **kwargs
    ) -> CodeOutput:
        """Generate code in the requested programming language.
        
        Args:
            task: The code generation request
            language: Optional explicit language override
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            chat_history: Previous conversation messages for context
        """
        self.logger.info(f"CodeAgent executing: {task[:50]}...")
        
        # Auto-detect language if not specified
        detected_language = language or self._detect_language(task)
        
        # Check chat history for language context clues
        if chat_history and detected_language == "python":
            history_text = " ".join([m.content for m in chat_history if hasattr(m, 'content')])
            history_language = self._detect_language(history_text)
            if history_language != "python":
                detected_language = history_language
                self.logger.info(f"Detected language from history: {detected_language}")
        
        self.logger.info(f"Detected language: {detected_language}")
        
        try:
            # Build messages with chat history for context
            user_prompt = f"""Generate {detected_language.upper()} code for: {task}

IMPORTANT: Write the code in {detected_language.upper()}, NOT in Python (unless Python was requested).
Write native {detected_language} code with proper syntax."""

            messages = [SystemMessage(content=self.system_prompt)]
            
            # Include chat history for conversation context
            if chat_history:
                messages.extend(chat_history)
            
            messages.append(HumanMessage(content=user_prompt))
            
            response = await self.llm.ainvoke(messages)
            raw = response.content.strip()
            
            self.logger.info(f"Got response: {len(raw)} chars")
            
            # Extract code from markdown blocks - handle various language markers
            code_pattern = rf'```(?:{detected_language}|sql|java|javascript|typescript|cpp|c\+\+|csharp|go|rust|ruby|php|swift|kotlin|scala|r|bash|sh|html|css|python)?\s*\n(.*?)```'
            code_match = re.search(code_pattern, raw, re.DOTALL | re.IGNORECASE)
            
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
                language=detected_language,
                explanation=explanation
            )
            
        except Exception as e:
            self.logger.error(f"CodeAgent error: {e}")
            return CodeOutput(
                code=f"-- Error: {e}",
                language=detected_language,
                explanation=f"Error: {e}"
            )
