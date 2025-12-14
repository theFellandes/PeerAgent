# Fixed conftest.py - REPLACE your existing tests/conftest.py with this
"""
Complete fixtures for PeerAgent tests.
Includes fixes for:
- MockWebSocket class
- mock_mongodb fixture  
- Proper Redis mock return values
- ddgs patching
"""

import pytest
import asyncio
import sys
import json
from typing import Generator, AsyncGenerator, Dict, Any, List
from unittest.mock import Mock, MagicMock, patch, AsyncMock


# =============================================================================
# CRITICAL: Patch ddgs before any imports
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def patch_ddgs_globally():
    """Patches ddgs module to prevent ImportError in ContentAgent."""
    mock_ddgs_module = MagicMock()
    mock_ddgs_class = MagicMock()
    mock_ddgs_class.return_value.text = MagicMock(return_value=[
        {"title": "Result 1", "href": "https://example.com/1", "body": "Body 1"},
        {"title": "Result 2", "href": "https://example.com/2", "body": "Body 2"},
    ])
    mock_ddgs_module.DDGS = mock_ddgs_class
    sys.modules["ddgs"] = mock_ddgs_module
    yield


# =============================================================================
# Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# MockWebSocket Class - EXPORTED FOR IMPORTS
# =============================================================================

class MockWebSocket:
    """Mock WebSocket for testing WebSocket endpoints."""
    
    def __init__(self, session_id: str = "test-session"):
        self.session_id = session_id
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.sent_messages: List[dict] = []
        self.received_messages: List[dict] = []
        self._receive_queue: List[dict] = []
    
    async def accept(self):
        """Accept the WebSocket connection."""
        self.accepted = True
    
    async def close(self, code: int = 1000):
        """Close the WebSocket connection."""
        self.closed = True
        self.close_code = code
    
    async def send_text(self, data: str):
        """Send text message."""
        self.sent_messages.append({"type": "text", "data": data})
    
    async def send_json(self, data: dict):
        """Send JSON message."""
        self.sent_messages.append({"type": "json", "data": data})
    
    async def receive_text(self) -> str:
        """Receive text message."""
        if self._receive_queue:
            msg = self._receive_queue.pop(0)
            return json.dumps(msg) if isinstance(msg, dict) else msg
        return "{}"
    
    async def receive_json(self) -> dict:
        """Receive JSON message."""
        if self._receive_queue:
            return self._receive_queue.pop(0)
        return {}
    
    def queue_message(self, message: dict):
        """Queue a message to be received."""
        self._receive_queue.append(message)


@pytest.fixture
def mock_websocket():
    """Create a MockWebSocket instance."""
    return MockWebSocket()


# =============================================================================
# Settings Fixtures
# =============================================================================

@pytest.fixture
def mock_settings():
    """Mock settings for testing without real API keys."""
    with patch("src.config.get_settings") as mock:
        settings = Mock()
        # Application
        settings.app_name = "PeerAgent"
        settings.app_version = "2.0.0"
        settings.debug = True
        settings.environment = "test"
        
        # API
        settings.api_prefix = "/v1"
        settings.api_host = "0.0.0.0"
        settings.api_port = 8000
        settings.cors_origins = ["*"]
        
        # LLM
        settings.llm_provider = "openai"
        settings.llm_model = "gpt-4o-mini"
        settings.llm_temperature = 0.7
        settings.openai_api_key = "test-openai-key"
        settings.anthropic_api_key = "test-anthropic-key"
        settings.google_api_key = "test-google-key"
        
        # Database
        settings.mongodb_url = "mongodb://localhost:27017"
        settings.mongodb_db_name = "peeragent_test"
        settings.redis_url = "redis://localhost:6379/0"
        
        # Celery
        settings.celery_broker_url = "redis://localhost:6379/0"
        settings.celery_result_backend = "redis://localhost:6379/0"
        
        # Task Store
        settings.task_ttl_hours = 24
        
        # Session
        settings.session_ttl_minutes = 60
        settings.max_messages_per_session = 50
        
        # Properties
        settings.is_production = False
        settings.is_development = True
        settings.has_valid_llm_key = True
        
        mock.return_value = settings
        yield settings


# =============================================================================
# LLM Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    mock_response = Mock()
    mock_response.content = '{"code": "def test(): pass", "language": "python", "explanation": "Test function"}'
    return mock_response


@pytest.fixture
def mock_code_response():
    """Mock response for CodeAgent."""
    mock_response = Mock()
    mock_response.content = """Here's the code:
```python
def hello_world():
    '''A simple hello world function.'''
    return "Hello, World!"
```
This function returns a greeting string."""
    return mock_response


@pytest.fixture
def mock_content_response():
    """Mock response for ContentAgent."""
    mock_response = Mock()
    mock_response.content = """Machine learning is a subset of artificial intelligence 
that enables systems to learn and improve from experience without being explicitly programmed.
It focuses on developing algorithms that can access data and use it to learn for themselves."""
    return mock_response


@pytest.fixture
def mock_business_questions_response():
    """Mock response for BusinessSenseAgent questions."""
    mock_response = Mock()
    mock_response.content = """{
        "questions": [
            "When did you first notice this problem?",
            "What is the measurable impact on your business?",
            "Is this problem in your company's TOP 3 priorities?"
        ],
        "category": "problem_identification"
    }"""
    return mock_response


@pytest.fixture
def mock_search_wrapper():
    """Mock DuckDuckGo search wrapper."""
    mock = MagicMock()
    mock.run.return_value = json.dumps([
        {"title": "Result 1", "link": "https://example.com/1", "snippet": "Test snippet 1"},
        {"title": "Result 2", "link": "https://example.com/2", "snippet": "Test snippet 2"},
    ])
    mock.results.return_value = [
        {"title": "Result 1", "link": "https://example.com/1", "snippet": "Test snippet 1"},
        {"title": "Result 2", "link": "https://example.com/2", "snippet": "Test snippet 2"},
    ]
    return mock


# =============================================================================
# Database Mock Fixtures - FIXED
# =============================================================================

@pytest.fixture
def mock_mongo_db():
    """Mock MongoDB database."""
    with patch("src.utils.database.get_mongo_db") as mock:
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock(
            return_value=Mock(inserted_id="test-id")
        )
        mock_collection.find = Mock(return_value=Mock(
            sort=Mock(return_value=Mock(
                limit=Mock(return_value=Mock(
                    to_list=AsyncMock(return_value=[])
                ))
            ))
        ))
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.update_one = AsyncMock(return_value=Mock(modified_count=1))
        mock_collection.delete_one = AsyncMock(return_value=Mock(deleted_count=1))
        mock_collection.count_documents = AsyncMock(return_value=0)
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB client - alias for compatibility."""
    with patch("src.utils.database.get_mongo_db") as mock:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        # Configure collection methods
        mock_collection.insert_one.return_value = Mock(inserted_id="test-id")
        mock_collection.find_one.return_value = {"_id": "test-id", "data": "test"}
        mock_collection.find.return_value = MagicMock(
            sort=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=[])
            ))
        )
        mock_collection.update_one.return_value = Mock(modified_count=1)
        mock_collection.delete_one.return_value = Mock(deleted_count=1)
        mock_collection.count_documents.return_value = 0
        
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_db.list_collection_names.return_value = ["tasks", "logs"]
        mock_db.command.return_value = {"ok": 1}
        
        mock.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_redis():
    """Mock Redis client with PROPER return values."""
    with patch("src.utils.database.get_redis_client") as mock:
        mock_redis = MagicMock()
        
        # Storage for simulating Redis
        _storage = {}
        
        def mock_get(key):
            return _storage.get(key)
        
        def mock_set(key, value, *args, **kwargs):
            _storage[key] = value.encode() if isinstance(value, str) else value
            return True
        
        def mock_setex(key, ttl, value):
            _storage[key] = value.encode() if isinstance(value, str) else value
            return True
        
        def mock_delete(key):
            if key in _storage:
                del _storage[key]
                return 1
            return 0
        
        def mock_exists(key):
            return 1 if key in _storage else 0
        
        def mock_keys(pattern):
            import fnmatch
            pattern = pattern.replace("*", ".*")
            return [k.encode() for k in _storage.keys()]
        
        mock_redis.get = MagicMock(side_effect=mock_get)
        mock_redis.set = MagicMock(side_effect=mock_set)
        mock_redis.setex = MagicMock(side_effect=mock_setex)
        mock_redis.delete = MagicMock(side_effect=mock_delete)
        mock_redis.exists = MagicMock(side_effect=mock_exists)
        mock_redis.keys = MagicMock(side_effect=mock_keys)
        mock_redis.ping = MagicMock(return_value=True)
        mock_redis.scan_iter = MagicMock(return_value=iter([]))
        mock_redis._storage = _storage  # Expose for test setup
        
        mock.return_value = mock_redis
        yield mock_redis


# =============================================================================
# Agent Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_peer_agent():
    """Mock PeerAgent for testing."""
    with patch("src.agents.peer_agent.PeerAgent") as MockAgent:
        mock_instance = Mock()
        mock_instance.session_id = "test-session"
        mock_instance.execute = AsyncMock(return_value={
            "agent_type": "code_agent",
            "data": {
                "code": "def test(): pass",
                "language": "python",
                "explanation": "Test function"
            }
        })
        mock_instance.execute_with_agent_type = AsyncMock(return_value={
            "agent_type": "code_agent",
            "data": {
                "code": "def test(): pass",
                "language": "python",
                "explanation": "Test function"
            }
        })
        mock_instance.classify_task = AsyncMock(return_value="code")
        mock_instance._keyword_classify = Mock(return_value="code")
        
        # Mock sub-agents
        mock_instance.code_agent = Mock()
        mock_instance.content_agent = Mock()
        mock_instance.business_agent = Mock()
        
        MockAgent.return_value = mock_instance
        yield mock_instance


# =============================================================================
# Sample Data Fixtures - FIXED FOR PYDANTIC MODELS
# =============================================================================

@pytest.fixture
def sample_tasks() -> Dict[str, list]:
    """Sample tasks for testing classification."""
    return {
        "code": [
            "Write a Python function to read a file",
            "Create a JavaScript class for user authentication",
            "Debug this Python script that has an error",
            "Implement a REST API endpoint in Java",
            "Write a SQL query to join two tables"
        ],
        "content": [
            "What is machine learning?",
            "Find information about climate change",
            "Explain quantum computing",
            "Research the latest AI news",
            "Tell me about blockchain technology"
        ],
        "business": [
            "Our sales are dropping by 20% yearly",
            "Help me understand our customer churn problem",
            "We have operational inefficiencies in our warehouse",
            "Revenue is declining and costs are increasing",
            "Diagnose our market share loss"
        ]
    }


@pytest.fixture
def sample_code_output():
    """Sample CodeAgent output."""
    from src.models.agents import CodeOutput
    return CodeOutput(
        code="def hello():\n    return 'Hello, World!'",
        language="python",
        explanation="A simple function that returns a greeting."
    )


@pytest.fixture
def sample_content_output():
    """Sample ContentAgent output."""
    from src.models.agents import ContentOutput
    return ContentOutput(
        content="Machine learning is a subset of AI...",
        sources=[
            "https://en.wikipedia.org/wiki/Machine_learning",
            "https://www.ibm.com/topics/machine-learning"
        ]
    )


@pytest.fixture
def sample_business_diagnosis():
    """Sample BusinessSenseAgent diagnosis - returns Pydantic model."""
    from src.models.agents import BusinessDiagnosis
    return BusinessDiagnosis(
        customer_stated_problem="Sales dropped 20% this quarter",
        identified_business_problem="Market share erosion due to competitive pressure",
        hidden_root_risk="Brand perception degradation among target segments",
        urgency_level="Critical"
    )


@pytest.fixture
def sample_problem_tree():
    """Sample ProblemStructuringAgent output - returns Pydantic model."""
    from src.models.agents import ProblemTree, ProblemCause
    return ProblemTree(
        problem_type="Growth",
        main_problem="Declining Sales",
        root_causes=[
            ProblemCause(
                cause="Marketing Inefficiency",
                sub_causes=["Wrong targeting", "Weak ad optimization", "Low conversion rate"]
            ),
            ProblemCause(
                cause="Competitive Pressure",
                sub_causes=["Lower competitor prices", "Better competitor products"]
            ),
            ProblemCause(
                cause="Sales Operations",
                sub_causes=["Long sales cycle", "Weak lead follow-up"]
            )
        ]
    )


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def cleanup_memory():
    """Fixture to clean up memory store after tests."""
    from src.utils.memory import get_memory_store
    memory = get_memory_store()
    
    yield memory
    
    # Cleanup
    memory.cleanup_expired()


@pytest.fixture
def cleanup_task_store():
    """Fixture to clean up task store after tests."""
    from src.utils.task_store import get_task_store
    store = get_task_store()
    
    yield store
    
    # Cleanup
    store.cleanup_expired()


# =============================================================================
# API Test Client Fixtures
# =============================================================================

@pytest.fixture
def test_client(mock_settings):
    """Create test client for FastAPI app."""
    from src.api.main import create_app
    from fastapi.testclient import TestClient
    
    app = create_app()
    return TestClient(app)


@pytest.fixture
def async_test_client(mock_settings):
    """Create async test client for FastAPI app."""
    from src.api.main import create_app
    from httpx import AsyncClient
    
    app = create_app()
    return AsyncClient(app=app, base_url="http://test")
