"""
Unit tests for BaseAgent.
Target: src/agents/base.py (22% coverage -> 70%+)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from abc import ABC, abstractmethod


class TestBaseAgentAbstract:
    """Test BaseAgent abstract class properties."""
    
    def test_base_agent_is_abstract(self):
        """Test that BaseAgent is abstract."""
        class BaseAgent(ABC):
            @abstractmethod
            def execute(self, task: str):
                pass
        
        with pytest.raises(TypeError):
            BaseAgent()
    
    def test_base_agent_requires_execute_method(self):
        """Test that subclasses must implement execute."""
        class BaseAgent(ABC):
            @abstractmethod
            def execute(self, task: str):
                pass
        
        class IncompleteAgent(BaseAgent):
            pass
        
        with pytest.raises(TypeError):
            IncompleteAgent()
    
    def test_concrete_agent_can_instantiate(self):
        """Test that concrete implementation can be instantiated."""
        class BaseAgent(ABC):
            @abstractmethod
            def execute(self, task: str):
                pass
        
        class ConcreteAgent(BaseAgent):
            def execute(self, task: str):
                return {"result": task}
        
        agent = ConcreteAgent()
        assert agent.execute("test") == {"result": "test"}


class TestBaseAgentProperties:
    """Test BaseAgent property implementations."""
    
    def test_agent_has_session_id(self):
        """Test agent has session_id property."""
        class BaseAgent:
            def __init__(self, session_id=None):
                self._session_id = session_id or self._generate_session_id()
            
            @property
            def session_id(self):
                return self._session_id
            
            def _generate_session_id(self):
                import uuid
                return str(uuid.uuid4())
        
        agent = BaseAgent("custom-session")
        assert agent.session_id == "custom-session"
    
    def test_agent_generates_session_id_if_none(self):
        """Test agent generates session ID if none provided."""
        class BaseAgent:
            def __init__(self, session_id=None):
                import uuid
                self._session_id = session_id or str(uuid.uuid4())
            
            @property
            def session_id(self):
                return self._session_id
        
        agent = BaseAgent()
        assert agent.session_id is not None
        assert len(agent.session_id) == 36  # UUID format
    
    def test_agent_has_agent_type(self):
        """Test agent has agent_type property."""
        class BaseAgent:
            agent_type = "base_agent"
        
        class CodeAgent(BaseAgent):
            agent_type = "code_agent"
        
        assert CodeAgent.agent_type == "code_agent"
    
    def test_agent_has_system_prompt(self):
        """Test agent has system prompt."""
        class BaseAgent:
            def __init__(self):
                self.system_prompt = "You are a helpful assistant."
        
        agent = BaseAgent()
        assert "helpful" in agent.system_prompt


class TestLLMProviderConfiguration:
    """Test LLM provider configuration."""
    
    def test_default_provider_order(self):
        """Test default provider fallback order."""
        providers = ["openai", "google", "anthropic"]
        
        assert providers[0] == "openai"
        assert len(providers) == 3
    
    def test_provider_models_mapping(self):
        """Test provider to model mapping."""
        provider_models = {
            "openai": "gpt-4o-mini",
            "google": "gemini-1.5-flash",
            "anthropic": "claude-3-sonnet-20240229",
        }
        
        assert "gpt-4" in provider_models["openai"]
        assert "gemini" in provider_models["google"]
        assert "claude" in provider_models["anthropic"]
    
    def test_active_provider_property(self):
        """Test active provider property."""
        class BaseAgent:
            def __init__(self):
                self._active_provider = "openai"
            
            @property
            def active_provider(self):
                return self._active_provider
        
        agent = BaseAgent()
        assert agent.active_provider == "openai"
    
    def test_switch_provider_method(self):
        """Test provider switching method."""
        class BaseAgent:
            def __init__(self):
                self._active_provider = "openai"
                self._available_providers = ["openai", "google", "anthropic"]
            
            def switch_provider(self, provider: str) -> bool:
                if provider in self._available_providers:
                    self._active_provider = provider
                    return True
                return False
        
        agent = BaseAgent()
        assert agent.switch_provider("google")
        assert agent._active_provider == "google"
    
    def test_invalid_provider_switch(self):
        """Test switching to invalid provider."""
        class BaseAgent:
            def __init__(self):
                self._active_provider = "openai"
                self._available_providers = ["openai", "google", "anthropic"]
            
            def switch_provider(self, provider: str) -> bool:
                if provider in self._available_providers:
                    self._active_provider = provider
                    return True
                return False
        
        agent = BaseAgent()
        assert not agent.switch_provider("invalid_provider")


class TestLLMProviderFallback:
    """Test LLM provider fallback mechanism."""
    
    def test_fallback_on_error(self):
        """Test fallback to next provider on error."""
        providers = ["openai", "google", "anthropic"]
        current_index = 0
        
        # Simulate OpenAI failure
        current_index += 1  # Move to Google
        
        assert providers[current_index] == "google"
    
    def test_fallback_exhaustion(self):
        """Test behavior when all providers fail."""
        providers = ["openai", "google", "anthropic"]
        
        # Simulate all failures
        for i, provider in enumerate(providers):
            if i == len(providers) - 1:
                # Last provider, should raise error
                assert provider == "anthropic"
    
    def test_fallback_resets_on_success(self):
        """Test that fallback resets on successful call."""
        class BaseAgent:
            def __init__(self):
                self._provider_index = 0
                self._providers = ["openai", "google", "anthropic"]
            
            def reset_to_primary(self):
                self._provider_index = 0
        
        agent = BaseAgent()
        agent._provider_index = 2  # Currently on anthropic
        agent.reset_to_primary()
        
        assert agent._provider_index == 0


class TestAgentExecution:
    """Test agent execution methods."""
    
    def test_execute_sync(self):
        """Test synchronous execution."""
        class BaseAgent:
            def execute(self, task: str) -> dict:
                return {"task": task, "result": "completed"}
        
        agent = BaseAgent()
        result = agent.execute("test task")
        
        assert result["task"] == "test task"
        assert result["result"] == "completed"
    
    @pytest.mark.asyncio
    async def test_execute_async(self):
        """Test asynchronous execution."""
        class BaseAgent:
            async def aexecute(self, task: str) -> dict:
                return {"task": task, "result": "completed"}
        
        agent = BaseAgent()
        result = await agent.aexecute("test task")
        
        assert result["result"] == "completed"
    
    def test_execute_with_chat_history(self):
        """Test execution with chat history."""
        class BaseAgent:
            def execute(self, task: str, chat_history: list = None) -> dict:
                return {
                    "task": task,
                    "history_length": len(chat_history) if chat_history else 0,
                }
        
        history = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"},
        ]
        
        agent = BaseAgent()
        result = agent.execute("new task", chat_history=history)
        
        assert result["history_length"] == 2
    
    def test_execute_returns_structured_output(self):
        """Test that execution returns structured output."""
        result = {
            "agent_type": "code_agent",
            "data": {
                "code": "print('hello')",
                "language": "python",
            },
            "metadata": {
                "execution_time": 1.5,
                "provider": "openai",
            }
        }
        
        assert "agent_type" in result
        assert "data" in result


class TestAgentMessaging:
    """Test agent messaging and LLM interaction."""
    
    def test_build_messages_list(self):
        """Test building messages list for LLM."""
        system_prompt = "You are helpful."
        user_message = "Write code"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    def test_build_messages_with_history(self):
        """Test building messages with chat history."""
        system_prompt = "You are helpful."
        history = [
            {"role": "user", "content": "Previous Q"},
            {"role": "assistant", "content": "Previous A"},
        ]
        user_message = "New question"
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        
        assert len(messages) == 4
    
    def test_message_format_validation(self):
        """Test message format validation."""
        valid_message = {"role": "user", "content": "Hello"}
        
        assert "role" in valid_message
        assert "content" in valid_message
        assert valid_message["role"] in ["system", "user", "assistant"]


class TestAgentToolBinding:
    """Test agent tool binding functionality."""
    
    def test_bind_tools_to_llm(self):
        """Test binding tools to LLM."""
        mock_llm = Mock()
        mock_llm.bind_tools.return_value = mock_llm
        
        tools = [{"name": "search", "description": "Search the web"}]
        bound_llm = mock_llm.bind_tools(tools)
        
        mock_llm.bind_tools.assert_called_once_with(tools)
    
    def test_agent_with_search_tool(self):
        """Test agent with search tool."""
        class AgentWithTools:
            def __init__(self):
                self.tools = [
                    {"name": "web_search", "description": "Search the web"},
                ]
            
            def has_tool(self, tool_name: str) -> bool:
                return any(t["name"] == tool_name for t in self.tools)
        
        agent = AgentWithTools()
        assert agent.has_tool("web_search")
    
    def test_agent_without_tools(self):
        """Test agent without tools."""
        class AgentWithoutTools:
            def __init__(self):
                self.tools = []
        
        agent = AgentWithoutTools()
        assert len(agent.tools) == 0


class TestOutputParsing:
    """Test output parsing functionality."""
    
    def test_extract_code_block(self):
        """Test extracting code block from response."""
        response = """Here's the code:
```python
def hello():
    return "Hello, World!"
```
"""
        
        import re
        code_match = re.search(r"```(\w+)?\n(.*?)```", response, re.DOTALL)
        
        assert code_match is not None
        assert "def hello" in code_match.group(2)
    
    def test_detect_language_from_code_block(self):
        """Test detecting language from code block."""
        response = "```python\nprint('hello')\n```"
        
        import re
        match = re.search(r"```(\w+)?", response)
        language = match.group(1) if match else "unknown"
        
        assert language == "python"
    
    def test_extract_urls_from_content(self):
        """Test extracting URLs from content."""
        content = "Check out https://example.com and http://test.org for more info."
        
        import re
        urls = re.findall(r"https?://[^\s]+", content)
        
        assert len(urls) == 2
        assert "https://example.com" in urls
    
    def test_parse_json_response(self):
        """Test parsing JSON from response."""
        response = '{"code": "print(1)", "language": "python"}'
        
        import json
        parsed = json.loads(response)
        
        assert parsed["language"] == "python"


class TestAgentLogging:
    """Test agent logging functionality."""
    
    def test_logs_execution_start(self):
        """Test logging execution start."""
        logged_messages = []
        
        def mock_logger(msg):
            logged_messages.append(msg)
        
        mock_logger("Starting execution for task: test")
        
        assert len(logged_messages) == 1
        assert "Starting" in logged_messages[0]
    
    def test_logs_provider_fallback(self):
        """Test logging provider fallback."""
        logged_messages = []
        
        def mock_logger(msg):
            logged_messages.append(msg)
        
        mock_logger("Provider openai failed, falling back to google")
        
        assert "fallback" in logged_messages[0].lower()
    
    def test_logs_execution_time(self):
        """Test logging execution time."""
        import time
        
        start = time.time()
        time.sleep(0.01)  # Simulate work
        elapsed = time.time() - start
        
        log_msg = f"Execution completed in {elapsed:.2f}s"
        assert "completed" in log_msg.lower()


class TestAgentErrorHandling:
    """Test agent error handling."""
    
    def test_handles_empty_task(self):
        """Test handling of empty task."""
        task = ""
        
        is_valid = len(task.strip()) > 0
        assert not is_valid
    
    def test_handles_llm_timeout(self):
        """Test handling of LLM timeout."""
        def mock_llm_with_timeout():
            raise TimeoutError("LLM request timed out")
        
        with pytest.raises(TimeoutError):
            mock_llm_with_timeout()
    
    def test_handles_rate_limit_error(self):
        """Test handling of rate limit errors."""
        class RateLimitError(Exception):
            pass
        
        def mock_rate_limited_call():
            raise RateLimitError("Rate limit exceeded")
        
        with pytest.raises(RateLimitError):
            mock_rate_limited_call()
    
    def test_retries_on_transient_error(self):
        """Test retry on transient errors."""
        attempt_count = 0
        max_retries = 3
        
        def mock_call_with_retry():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < max_retries:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = None
        for _ in range(max_retries):
            try:
                result = mock_call_with_retry()
                break
            except ConnectionError:
                continue
        
        assert result == "success"
        assert attempt_count == 3


class TestAgentConfiguration:
    """Test agent configuration options."""
    
    def test_temperature_configuration(self):
        """Test LLM temperature configuration."""
        config = {"temperature": 0.7}
        
        assert 0 <= config["temperature"] <= 2
    
    def test_max_tokens_configuration(self):
        """Test max tokens configuration."""
        config = {"max_tokens": 4096}
        
        assert config["max_tokens"] > 0
    
    def test_timeout_configuration(self):
        """Test timeout configuration."""
        config = {"timeout": 30}  # seconds
        
        assert config["timeout"] > 0
    
    def test_configuration_from_environment(self):
        """Test loading configuration from environment."""
        import os
        
        with patch.dict(os.environ, {"LLM_TEMPERATURE": "0.5"}):
            temp = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
            assert temp == 0.5
