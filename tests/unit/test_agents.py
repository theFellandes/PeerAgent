# Unit Tests for Agent Outputs
import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestCodeAgentExecution:
    """Test CodeAgent execution logic."""
    
    @pytest.fixture
    def code_agent(self, mock_settings):
        from src.agents.code_agent import CodeAgent
        return CodeAgent()
    
    @pytest.mark.asyncio
    async def test_execute_returns_code_output(self, code_agent, mock_settings):
        """Test that execute returns CodeOutput."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = """Here's the code:
```python
def hello():
    print("Hello World")
```
This is a simple hello world function."""
        
        with patch.object(code_agent, "llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await code_agent.execute("Write hello world")
            
            assert result.code is not None
            assert result.language == "python"
            assert result.explanation is not None
    
    @pytest.mark.asyncio
    async def test_execute_extracts_code_block(self, code_agent, mock_settings):
        """Test that code is extracted from markdown blocks."""
        mock_response = Mock()
        mock_response.content = """
```python
def add(a, b):
    return a + b
```
"""
        with patch.object(code_agent, "llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await code_agent.execute("Write an add function")
            
            assert "def add" in result.code
            assert "```" not in result.code  # Markdown should be stripped
    
    @pytest.mark.asyncio
    async def test_execute_handles_error(self, code_agent, mock_settings):
        """Test that errors are handled gracefully."""
        with patch.object(code_agent, "llm") as mock_llm:
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
            
            result = await code_agent.execute("Write code")
            
            assert "Error" in result.code or "Error" in result.explanation


class TestContentAgentExecution:
    """Test ContentAgent execution logic."""
    
    @pytest.fixture
    def content_agent(self, mock_settings):
        from src.agents.content_agent import ContentAgent
        return ContentAgent()
    
    @pytest.mark.asyncio
    async def test_execute_returns_content_output(self, content_agent, mock_settings):
        """Test that execute returns ContentOutput."""
        mock_search = Mock()
        mock_search.invoke = Mock(return_value="Results from https://example.com")
        
        mock_response = Mock()
        mock_response.content = "AI is a technology that..."
        
        with patch.object(content_agent, "search_tool", mock_search):
            with patch.object(content_agent, "llm") as mock_llm:
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                
                result = await content_agent.execute("What is AI?")
                
                assert result.content is not None
                assert isinstance(result.sources, list)
    
    @pytest.mark.asyncio
    async def test_execute_extracts_urls(self, content_agent, mock_settings):
        """Test that URLs are extracted from search results."""
        mock_search = Mock()
        mock_search.invoke = Mock(return_value="""
            Results: Article at https://example.com/article and 
            https://another.com/page
        """)
        
        mock_response = Mock()
        mock_response.content = "Content here"
        
        with patch.object(content_agent, "search_tool", mock_search):
            with patch.object(content_agent, "llm") as mock_llm:
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                
                result = await content_agent.execute("Search query")
                
                assert len(result.sources) >= 1


class TestBaseAgent:
    """Test BaseAgent functionality."""
    
    def test_base_agent_is_abstract(self):
        """Test that BaseAgent cannot be instantiated directly."""
        from src.agents.base import BaseAgent
        from abc import ABC
        
        assert issubclass(BaseAgent, ABC)
    
    def test_llm_property_is_lazy(self, mock_settings):
        """Test that LLM is lazily initialized."""
        from src.agents.code_agent import CodeAgent
        
        agent = CodeAgent()
        assert agent._llm is None  # Not initialized yet
    
    def test_create_messages(self, mock_settings):
        """Test message creation."""
        from src.agents.code_agent import CodeAgent
        
        agent = CodeAgent()
        messages = agent.create_messages("User input")
        
        assert len(messages) >= 2  # System + Human at minimum
