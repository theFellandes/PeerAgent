# Unit Tests for Agent Outputs
import pytest
from unittest.mock import Mock, patch, AsyncMock, PropertyMock


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
        
        # Patch the private _llm attribute instead of the property
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        code_agent._llm = mock_llm
        
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
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        code_agent._llm = mock_llm
        
        result = await code_agent.execute("Write an add function")
        
        assert "def add" in result.code
        assert "```" not in result.code  # Markdown should be stripped
    
    @pytest.mark.asyncio
    async def test_execute_handles_error(self, code_agent, mock_settings):
        """Test that errors are handled gracefully."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
        code_agent._llm = mock_llm
        
        result = await code_agent.execute("Write code")
        
        assert "Error" in result.code or "Error" in result.explanation
    
    @pytest.mark.asyncio
    async def test_execute_detects_sql_language(self, code_agent, mock_settings):
        """Test SQL language detection."""
        mock_response = Mock()
        mock_response.content = """
```sql
SELECT * FROM customers WHERE active = 1;
```
"""
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        code_agent._llm = mock_llm
        
        result = await code_agent.execute("Write a SQL query for customers")
        
        assert result.language == "sql"
    
    @pytest.mark.asyncio
    async def test_execute_detects_java_language(self, code_agent, mock_settings):
        """Test Java language detection."""
        mock_response = Mock()
        mock_response.content = """
```java
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
```
"""
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        code_agent._llm = mock_llm
        
        result = await code_agent.execute("Write a Java hello world")
        
        assert result.language == "java"


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
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        
        content_agent.search_tool = mock_search
        content_agent._llm = mock_llm
        
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
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        
        content_agent.search_tool = mock_search
        content_agent._llm = mock_llm
        
        result = await content_agent.execute("Search query")
        
        assert len(result.sources) >= 1


class TestBaseAgent:
    """Test BaseAgent functionality."""
    
    def test_base_agent_is_abstract(self):
        """Test that BaseAgent cannot be instantiated directly."""
        from src.agents.base import BaseAgent
        from abc import ABC
        
        assert issubclass(BaseAgent, ABC)
    
    def test_code_agent_has_session_id(self, mock_settings):
        """Test that agents have session_id."""
        from src.agents.code_agent import CodeAgent
        
        agent = CodeAgent(session_id="test-session")
        assert agent.session_id == "test-session"
    
    def test_code_agent_type(self, mock_settings):
        """Test agent_type property."""
        from src.agents.code_agent import CodeAgent
        
        agent = CodeAgent()
        assert agent.agent_type == "code_agent"
    
    def test_content_agent_has_search_tool(self, mock_settings):
        """Test ContentAgent has search tool."""
        from src.agents.content_agent import ContentAgent
        
        agent = ContentAgent()
        assert agent.search_tool is not None


class TestLanguageDetection:
    """Test CodeAgent language detection."""
    
    @pytest.fixture
    def code_agent(self, mock_settings):
        from src.agents.code_agent import CodeAgent
        return CodeAgent()
    
    def test_detect_python(self, code_agent):
        assert code_agent._detect_language("Write Python code") == "python"
    
    def test_detect_sql(self, code_agent):
        assert code_agent._detect_language("SQL query") == "sql"
    
    def test_detect_java(self, code_agent):
        assert code_agent._detect_language("Java class") == "java"
    
    def test_detect_javascript(self, code_agent):
        assert code_agent._detect_language("JavaScript function") == "javascript"
    
    def test_detect_default(self, code_agent):
        # Ambiguous should default to python
        assert code_agent._detect_language("Write some code") == "python"
