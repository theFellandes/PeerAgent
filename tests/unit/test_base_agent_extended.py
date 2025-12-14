# tests/unit/test_base_agent_extended.py
"""
Fixed tests for BaseAgent - uses actual API from the codebase.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock


class TestBaseAgentStructure:
    """Test BaseAgent structure."""
    
    def test_base_agent_exists(self, mock_settings):
        """Test BaseAgent class exists."""
        from src.agents.base import BaseAgent
        
        assert BaseAgent is not None
    
    def test_base_agent_is_abstract(self, mock_settings):
        """Test BaseAgent is abstract."""
        from src.agents.base import BaseAgent
        from abc import ABC
        
        assert issubclass(BaseAgent, ABC)
    
    def test_default_models_exists(self, mock_settings):
        """Test DEFAULT_MODELS is defined."""
        from src.agents.base import DEFAULT_MODELS
        
        assert DEFAULT_MODELS is not None
        assert isinstance(DEFAULT_MODELS, dict)


class TestDefaultModels:
    """Test DEFAULT_MODELS constant."""
    
    def test_default_models_has_openai(self, mock_settings):
        """Test DEFAULT_MODELS has openai."""
        from src.agents.base import DEFAULT_MODELS
        
        assert "openai" in DEFAULT_MODELS
    
    def test_default_models_has_google(self, mock_settings):
        """Test DEFAULT_MODELS has google."""
        from src.agents.base import DEFAULT_MODELS
        
        assert "google" in DEFAULT_MODELS
    
    def test_default_models_has_anthropic(self, mock_settings):
        """Test DEFAULT_MODELS has anthropic."""
        from src.agents.base import DEFAULT_MODELS
        
        assert "anthropic" in DEFAULT_MODELS
    
    def test_google_model_value(self, mock_settings):
        """Test google model value."""
        from src.agents.base import DEFAULT_MODELS
        
        assert DEFAULT_MODELS["google"] == "gemini-1.5-flash"


class TestCodeAgentInitialization:
    """Test CodeAgent initialization (concrete implementation)."""
    
    def test_code_agent_creation(self, mock_settings):
        """Test CodeAgent can be created."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            with patch("langchain_community.tools.DuckDuckGoSearchResults"):
                from src.agents.code_agent import CodeAgent
                
                agent = CodeAgent()
                assert agent is not None
    
    def test_code_agent_has_agent_type(self, mock_settings):
        """Test CodeAgent has agent_type."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            with patch("langchain_community.tools.DuckDuckGoSearchResults"):
                from src.agents.code_agent import CodeAgent
                
                agent = CodeAgent()
                assert agent.agent_type == "code_agent"
    
    def test_code_agent_has_system_prompt(self, mock_settings):
        """Test CodeAgent has system_prompt."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            with patch("langchain_community.tools.DuckDuckGoSearchResults"):
                from src.agents.code_agent import CodeAgent
                
                agent = CodeAgent()
                assert agent.system_prompt is not None
                assert len(agent.system_prompt) > 0


class TestContentAgentInitialization:
    """Test ContentAgent initialization."""
    
    def test_content_agent_creation(self, mock_settings):
        """Test ContentAgent can be created."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            with patch("langchain_community.tools.DuckDuckGoSearchResults"):
                from src.agents.content_agent import ContentAgent
                
                agent = ContentAgent()
                assert agent is not None
    
    def test_content_agent_has_agent_type(self, mock_settings):
        """Test ContentAgent has agent_type."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            with patch("langchain_community.tools.DuckDuckGoSearchResults"):
                from src.agents.content_agent import ContentAgent
                
                agent = ContentAgent()
                assert agent.agent_type == "content_agent"


class TestAgentLLMProperty:
    """Test agent LLM property."""
    
    def test_code_agent_has_llm_property(self, mock_settings):
        """Test CodeAgent has llm property."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            with patch("langchain_community.tools.DuckDuckGoSearchResults"):
                from src.agents.code_agent import CodeAgent
                
                agent = CodeAgent()
                assert hasattr(agent, 'llm') or hasattr(agent, '_llm')


class TestAgentExecution:
    """Test agent execution."""
    
    @pytest.mark.asyncio
    async def test_code_agent_execute_exists(self, mock_settings):
        """Test CodeAgent has execute method."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            with patch("langchain_community.tools.DuckDuckGoSearchResults"):
                from src.agents.code_agent import CodeAgent
                
                agent = CodeAgent()
                assert hasattr(agent, 'execute')
                assert callable(agent.execute)
    
    @pytest.mark.asyncio
    async def test_content_agent_execute_exists(self, mock_settings):
        """Test ContentAgent has execute method."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            with patch("langchain_community.tools.DuckDuckGoSearchResults"):
                from src.agents.content_agent import ContentAgent
                
                agent = ContentAgent()
                assert hasattr(agent, 'execute')
                assert callable(agent.execute)


class TestBaseAgentFallbackOrder:
    """Test FALLBACK_ORDER constant."""
    
    def test_fallback_order_exists(self, mock_settings):
        """Test FALLBACK_ORDER is defined."""
        from src.agents.base import BaseAgent
        
        assert hasattr(BaseAgent, 'FALLBACK_ORDER')
    
    def test_fallback_order_is_list(self, mock_settings):
        """Test FALLBACK_ORDER is a list or tuple."""
        from src.agents.base import BaseAgent
        
        assert isinstance(BaseAgent.FALLBACK_ORDER, (list, tuple))
    
    def test_fallback_order_has_providers(self, mock_settings):
        """Test FALLBACK_ORDER has providers."""
        from src.agents.base import BaseAgent
        
        order = BaseAgent.FALLBACK_ORDER
        assert "openai" in order
        assert "google" in order
        assert "anthropic" in order
