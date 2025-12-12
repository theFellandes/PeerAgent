# Base Agent class for all PeerAgent agents
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from src.config import get_settings
from src.utils.logger import get_logger, MongoDBLogger


# Default models for each provider
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",  # Cheapest OpenAI model with good performance
    "google": "gemini-1.5-flash",
    "anthropic": "claude-3-sonnet-20240229"
}


class BaseAgent(ABC):
    """Abstract base class for all agents in the PeerAgent system."""
    
    # Fallback order: primary provider, then alternatives
    FALLBACK_ORDER = ["openai", "google", "anthropic"]
    
    def __init__(self, session_id: Optional[str] = None):
        self.settings = get_settings()
        self.session_id = session_id
        self.logger = get_logger(self.__class__.__name__)
        self.mongo_logger = MongoDBLogger()
        self._llm = None
        self._active_provider = None
        self.model_name = self.settings.llm_model
    
    @property
    def llm(self):
        """Lazily initialize the LLM based on configuration with fallback support."""
        if self._llm is None:
            self._llm = self._create_llm_with_fallback()
        return self._llm
    
    @property
    def active_provider(self) -> Optional[str]:
        """Return the currently active LLM provider."""
        return self._active_provider
    
    def _get_provider_config(self, provider: str) -> Tuple[Optional[str], str]:
        """Get API key and default model for a provider.
        
        Returns:
            Tuple of (api_key, default_model)
        """
        if provider == "openai":
            return self.settings.openai_api_key, DEFAULT_MODELS["openai"]
        elif provider == "google":
            return self.settings.google_api_key, DEFAULT_MODELS["google"]
        elif provider == "anthropic":
            return self.settings.anthropic_api_key, DEFAULT_MODELS["anthropic"]
        return None, ""
    
    def _create_llm_for_provider(self, provider: str, api_key: str, model: str):
        """Create LLM instance for a specific provider."""
        if provider == "openai":
            return ChatOpenAI(
                model=model,
                temperature=self.settings.llm_temperature,
                api_key=api_key
            )
        elif provider == "google":
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=self.settings.llm_temperature,
                google_api_key=api_key
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=model,
                temperature=self.settings.llm_temperature,
                api_key=api_key
            )
        raise ValueError(f"Unknown provider: {provider}")
    
    def _create_llm_with_fallback(self):
        """Create LLM with automatic fallback to alternative providers.
        
        Tries providers in order: configured provider first, then fallbacks.
        If a provider's API key is invalid or missing, tries the next one.
        """
        primary_provider = self.settings.llm_provider.lower()
        
        # Build provider order: primary first, then fallbacks
        providers_to_try = [primary_provider]
        for fallback in self.FALLBACK_ORDER:
            if fallback not in providers_to_try:
                providers_to_try.append(fallback)
        
        errors = []
        
        for provider in providers_to_try:
            api_key, default_model = self._get_provider_config(provider)
            
            if not api_key:
                self.logger.debug(f"Skipping {provider}: no API key configured")
                errors.append(f"{provider}: no API key")
                continue
            
            # Use configured model for primary provider, default for fallbacks
            model = self.settings.llm_model if provider == primary_provider else default_model
            
            try:
                llm = self._create_llm_for_provider(provider, api_key, model)
                
                # Test the connection with a simple call
                # Note: We only validate on first actual use, not here
                # This keeps initialization fast
                
                self._active_provider = provider
                if provider != primary_provider:
                    self.logger.warning(
                        f"Using fallback provider '{provider}' (model: {model}) "
                        f"instead of '{primary_provider}'"
                    )
                else:
                    self.logger.info(f"Initialized LLM with {provider} (model: {model})")
                
                return llm
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize {provider}: {e}")
                errors.append(f"{provider}: {str(e)}")
                continue
        
        # All providers failed
        error_details = "; ".join(errors)
        raise ValueError(
            f"Failed to initialize any LLM provider. Tried: {providers_to_try}. "
            f"Errors: {error_details}"
        )
    
    def _create_llm(self):
        """Create the appropriate LLM based on provider setting.
        
        Deprecated: Use _create_llm_with_fallback() instead.
        Kept for backward compatibility.
        """
        return self._create_llm_with_fallback()
    
    def switch_provider(self, provider: str) -> bool:
        """Manually switch to a different LLM provider.
        
        Args:
            provider: The provider to switch to ('openai', 'google', 'anthropic')
            
        Returns:
            True if switch was successful, False otherwise
        """
        api_key, default_model = self._get_provider_config(provider)
        
        if not api_key:
            self.logger.error(f"Cannot switch to {provider}: no API key configured")
            return False
        
        try:
            self._llm = self._create_llm_for_provider(provider, api_key, default_model)
            self._active_provider = provider
            self.logger.info(f"Switched to {provider} (model: {default_model})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to switch to {provider}: {e}")
            return False
    
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
        Handles common error handling, logging, and automatic provider fallback on failure.
        """
        try:
            response = await self.llm.ainvoke(messages, **kwargs)
            self.logger.debug(f"LLM response: {response.content[:100]}...")
            return response
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if this is an API key or authentication error
            is_auth_error = any(term in error_str for term in [
                "invalid api key", "unauthorized", "authentication", 
                "api key", "invalid_api_key", "401", "403"
            ])
            
            if is_auth_error:
                self.logger.warning(f"Auth error with {self._active_provider}, attempting fallback...")
                
                # Try fallback providers
                for provider in self.FALLBACK_ORDER:
                    if provider == self._active_provider:
                        continue
                    
                    if self.switch_provider(provider):
                        self.logger.info(f"Retrying with fallback provider: {provider}")
                        try:
                            response = await self.llm.ainvoke(messages, **kwargs)
                            self.logger.debug(f"LLM response (fallback): {response.content[:100]}...")
                            return response
                        except Exception as fallback_e:
                            self.logger.warning(f"Fallback {provider} also failed: {fallback_e}")
                            continue
            
            self.logger.error(f"LLM invocation failed: {e}")
            raise
    
    def create_messages(
        self,
        user_message: str,
        additional_context: Optional[str] = None,
        chat_history: Optional[list[BaseMessage]] = None
    ) -> list[BaseMessage]:
        """Create a standard message list with system prompt, history, and user message.
        
        Args:
            user_message: The current user request
            additional_context: Optional additional system context
            chat_history: Optional list of previous messages for conversation context
        """
        messages = [SystemMessage(content=self.system_prompt)]
        
        if additional_context:
            messages.append(SystemMessage(content=additional_context))
        
        # Include chat history for conversation context
        if chat_history:
            messages.extend(chat_history)
        
        messages.append(HumanMessage(content=user_message))
        return messages
