# Base Agent class for all PeerAgent agents
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.config import get_settings
from src.utils.logger import get_logger, MongoDBLogger


class BaseAgent(ABC):
    """Abstract base class for all agents in the PeerAgent system."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.settings = get_settings()
        self.session_id = session_id
        self.logger = get_logger(self.__class__.__name__)
        self.mongo_logger = MongoDBLogger()
        self._llm = None
        self.model_name = self.settings.llm_model
    
    @property
    def llm(self):
        """Lazily initialize the LLM based on configuration."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm
    
    def _create_llm(self):
        """Create the appropriate LLM based on provider setting."""
        provider = self.settings.llm_provider.lower()
        
        if provider == "openai":
            if not self.settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            return ChatOpenAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.openai_api_key
            )
        elif provider == "anthropic":
            if not self.settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            return ChatAnthropic(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                api_key=self.settings.anthropic_api_key
            )
        elif provider == "google":
            if not self.settings.google_api_key:
                raise ValueError("Google API key not configured")
            return ChatGoogleGenerativeAI(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                google_api_key=self.settings.google_api_key
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Return the agent type identifier."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Any:
        """Execute the agent's main task."""
        pass
    
    async def invoke_llm(
        self,
        messages: list[BaseMessage],
        **kwargs
    ) -> BaseMessage:
        """
        Invoke the LLM with the given messages.
        Handles common error handling and logging.
        """
        try:
            response = await self.llm.ainvoke(messages, **kwargs)
            self.logger.debug(f"LLM response: {response.content[:100]}...")
            return response
        except Exception as e:
            self.logger.error(f"LLM invocation failed: {e}")
            raise
    
    def create_messages(
        self,
        user_message: str,
        additional_context: Optional[str] = None
    ) -> list[BaseMessage]:
        """Create a standard message list with system prompt and user message."""
        messages = [SystemMessage(content=self.system_prompt)]
        
        if additional_context:
            messages.append(SystemMessage(content=additional_context))
        
        messages.append(HumanMessage(content=user_message))
        return messages
