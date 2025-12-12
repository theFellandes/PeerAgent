# Pytest configuration and fixtures
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, patch, AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    mock_response = Mock()
    mock_response.content = '{"code": "def test(): pass", "language": "python", "explanation": "Test function"}'
    return mock_response


@pytest.fixture
def mock_settings():
    """Mock settings for testing without real API keys."""
    with patch("src.config.get_settings") as mock:
        settings = Mock()
        settings.llm_provider = "openai"
        settings.openai_api_key = "test-key"
        settings.llm_model = "gpt-4"
        settings.llm_temperature = 0.7
        settings.mongodb_url = "mongodb://localhost:27017"
        settings.mongodb_db_name = "peeragent_test"
        settings.redis_url = "redis://localhost:6379/0"
        settings.app_name = "PeerAgent"
        settings.app_version = "1.0.0"
        settings.api_prefix = "/v1"
        settings.debug = True
        mock.return_value = settings
        yield settings


@pytest.fixture
def sample_tasks():
    """Sample tasks for testing classification."""
    return {
        "code": [
            "Write a Python function to read a file",
            "Create a JavaScript class for user authentication",
            "Debug this Python script that has an error"
        ],
        "content": [
            "What is machine learning?",
            "Find information about climate change",
            "Explain quantum computing"
        ],
        "business": [
            "Our sales are dropping by 20% yearly",
            "Help me understand our customer churn problem",
            "We have operational inefficiencies in our warehouse"
        ]
    }


@pytest.fixture
def mock_mongo_db():
    """Mock MongoDB database."""
    with patch("src.utils.database.get_mongo_db") as mock:
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock(return_value=Mock(inserted_id="test-id"))
        mock_collection.find = Mock(return_value=Mock(
            sort=Mock(return_value=Mock(
                limit=Mock(return_value=Mock(
                    to_list=AsyncMock(return_value=[])
                ))
            ))
        ))
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock.return_value = mock_db
        yield mock_db
