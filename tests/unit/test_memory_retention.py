# Memory Retention Tests
"""Tests to verify chat history is properly passed to and used by agents."""

import pytest
from unittest.mock import Mock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage


class TestMemoryRetention:
    """Test that agents receive and use chat history for context."""
    
    @pytest.fixture
    def code_agent(self, mock_settings):
        from src.agents.code_agent import CodeAgent
        return CodeAgent()
    
    @pytest.fixture
    def content_agent(self, mock_settings):
        from src.agents.content_agent import ContentAgent
        return ContentAgent()
    
    @pytest.mark.asyncio
    async def test_code_agent_receives_chat_history(self, code_agent, mock_settings):
        """Test that CodeAgent receives chat history and includes it in LLM call."""
        mock_response = Mock()
        mock_response.content = """```python
def test():
    pass
```"""
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        code_agent._llm = mock_llm
        
        # Create chat history
        history = [
            HumanMessage(content="I'm working on a Java Spring Boot project"),
            AIMessage(content="Great! I can help with Java Spring Boot.")
        ]
        
        await code_agent.execute("Write a test function", chat_history=history)
        
        # Verify LLM was called with messages that include history
        call_args = mock_llm.ainvoke.call_args[0][0]
        
        # Should have: System prompt + 2 history messages + Human prompt = 4+ messages
        assert len(call_args) >= 4, f"Expected at least 4 messages, got {len(call_args)}"
        
        # Verify history messages are present
        message_contents = [m.content for m in call_args]
        assert any("Java Spring Boot" in content for content in message_contents), \
            "Chat history should be included in messages"
    
    @pytest.mark.asyncio
    async def test_code_agent_detects_language_from_history(self, code_agent, mock_settings):
        """Test that CodeAgent can detect language from conversation history."""
        mock_response = Mock()
        mock_response.content = """```java
public class Test {}
```"""
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        code_agent._llm = mock_llm
        
        # History mentions Java
        history = [
            HumanMessage(content="I'm building a Java application"),
            AIMessage(content="I can help with Java!")
        ]
        
        result = await code_agent.execute("Write a class", chat_history=history)
        
        # Should detect Java from history since task doesn't specify language
        assert result.language == "java", f"Expected 'java', got '{result.language}'"
    
    @pytest.mark.asyncio
    async def test_content_agent_receives_chat_history(self, content_agent, mock_settings):
        """Test that ContentAgent receives chat history."""
        mock_search = Mock()
        mock_search.invoke = Mock(return_value="Search results from https://example.com")
        
        mock_response = Mock()
        mock_response.content = "Here is information about your topic..."
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        
        content_agent.search_tool = mock_search
        content_agent._llm = mock_llm
        
        # Create chat history
        history = [
            HumanMessage(content="I want to learn about machine learning"),
            AIMessage(content="Machine learning is a fascinating field!")
        ]
        
        await content_agent.execute("Tell me more", chat_history=history)
        
        # Verify LLM was called with messages that include history
        call_args = mock_llm.ainvoke.call_args[0][0]
        
        # Should have: System + Search context + 2 history + Human = 5+ messages
        assert len(call_args) >= 5, f"Expected at least 5 messages, got {len(call_args)}"


class TestMemoryStore:
    """Test the MemoryStore functionality."""
    
    def test_memory_store_stores_interactions(self):
        """Test that MemoryStore stores and retrieves messages."""
        from src.utils.memory import get_memory_store
        
        memory = get_memory_store()
        session_id = "test-session-123"
        
        # Clear any existing session
        memory.clear_session(session_id)
        
        # Add interaction
        memory.add_interaction(session_id, "Hello", "Hi there!")
        
        # Retrieve messages
        messages = memory.get_messages(session_id)
        
        assert len(messages) == 2  # Human + AI
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there!"
    
    def test_memory_store_limits_messages(self):
        """Test that get_messages respects max_messages limit."""
        from src.utils.memory import get_memory_store
        
        memory = get_memory_store()
        session_id = "test-session-limit"
        
        # Clear any existing session
        memory.clear_session(session_id)
        
        # Add multiple interactions
        for i in range(10):
            memory.add_interaction(session_id, f"Question {i}", f"Answer {i}")
        
        # Retrieve limited messages
        messages = memory.get_messages(session_id, max_messages=4)
        
        assert len(messages) == 4


class TestLLMProviderFallback:
    """Test LLM provider fallback functionality."""
    
    def test_base_agent_has_fallback_order(self, mock_settings):
        """Test that BaseAgent defines fallback order."""
        from src.agents.base import BaseAgent
        
        assert hasattr(BaseAgent, 'FALLBACK_ORDER')
        assert "openai" in BaseAgent.FALLBACK_ORDER
        assert "google" in BaseAgent.FALLBACK_ORDER
        assert "anthropic" in BaseAgent.FALLBACK_ORDER
    
    def test_code_agent_has_active_provider_property(self, mock_settings):
        """Test that agents have active_provider property."""
        from src.agents.code_agent import CodeAgent
        
        agent = CodeAgent()
        # Property should exist (may be None before LLM initialization)
        assert hasattr(agent, 'active_provider')
    
    def test_code_agent_has_switch_provider_method(self, mock_settings):
        """Test that agents have switch_provider method."""
        from src.agents.code_agent import CodeAgent
        
        agent = CodeAgent()
        assert hasattr(agent, 'switch_provider')
        assert callable(agent.switch_provider)
    
    def test_default_models_defined(self, mock_settings):
        """Test that default models are defined for each provider."""
        from src.agents.base import DEFAULT_MODELS
        
        assert "openai" in DEFAULT_MODELS
        assert "google" in DEFAULT_MODELS
        assert "anthropic" in DEFAULT_MODELS
        assert DEFAULT_MODELS["google"] == "gemini-1.5-flash"
