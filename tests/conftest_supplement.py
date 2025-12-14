# Supplemental conftest.py - Add to existing conftest.py
# CRITICAL: This patches ddgs to fix ContentAgent import errors
"""
Supplemental fixtures to fix ddgs import issue and add missing fixtures.
Merge these into your existing conftest.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import sys


# =============================================================================
# CRITICAL FIX: Patch ddgs before any imports
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def patch_ddgs_globally():
    """
    CRITICAL: Patches ddgs module to prevent ImportError in ContentAgent.
    This must run before any test imports ContentAgent.
    """
    # Create mock ddgs module
    mock_ddgs_module = MagicMock()
    mock_ddgs_class = MagicMock()
    mock_ddgs_class.return_value.text = MagicMock(return_value=[
        {"title": "Result 1", "href": "https://example.com/1", "body": "Body 1"},
        {"title": "Result 2", "href": "https://example.com/2", "body": "Body 2"},
    ])
    mock_ddgs_module.DDGS = mock_ddgs_class
    
    # Patch before any imports
    sys.modules["ddgs"] = mock_ddgs_module
    
    yield
    
    # Cleanup (optional)
    if "ddgs" in sys.modules:
        del sys.modules["ddgs"]


@pytest.fixture
def mock_duckduckgo_wrapper():
    """Mock DuckDuckGoSearchAPIWrapper for ContentAgent tests."""
    with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper") as mock:
        mock_instance = MagicMock()
        mock_instance.run.return_value = "Results from https://example.com"
        mock_instance.results.return_value = [
            {"title": "Result", "link": "https://example.com", "snippet": "Test"}
        ]
        mock.return_value = mock_instance
        yield mock_instance


# =============================================================================
# Worker/Celery Fixtures
# =============================================================================

@pytest.fixture
def mock_celery_app():
    """Mock Celery application for worker tests."""
    with patch("celery.Celery") as mock:
        mock_app = MagicMock()
        mock_app.task = MagicMock(side_effect=lambda *args, **kwargs: lambda f: f)
        mock.return_value = mock_app
        yield mock_app


@pytest.fixture
def mock_celery_task():
    """Mock a Celery task for testing."""
    task = MagicMock()
    task.delay = MagicMock(return_value=MagicMock(id="mock-task-id"))
    task.apply_async = MagicMock(return_value=MagicMock(id="mock-task-id"))
    return task


# =============================================================================
# Database Fixtures (Extended)
# =============================================================================

@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client with more operations."""
    with patch("pymongo.MongoClient") as mock:
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        # Collection operations
        mock_collection.insert_one.return_value = MagicMock(inserted_id="test-id")
        mock_collection.find_one.return_value = None
        mock_collection.find.return_value = MagicMock(
            sort=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=[])
            ))
        )
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
        mock_collection.count_documents.return_value = 0
        
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_client.__getitem__ = MagicMock(return_value=mock_db)
        mock_client.server_info.return_value = {"version": "6.0.0"}
        
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture  
def mock_redis_client():
    """Mock Redis client with full operations."""
    with patch("redis.Redis") as mock:
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = 0
        mock_redis.keys.return_value = []
        mock_redis.scan_iter.return_value = iter([])
        mock_redis.ping.return_value = True
        mock_redis.flushdb.return_value = True
        
        mock.return_value = mock_redis
        yield mock_redis


# =============================================================================
# Business Agent Fixtures
# =============================================================================

@pytest.fixture
def mock_business_agent_llm():
    """Mock LLM specifically for BusinessSenseAgent testing."""
    mock_llm = AsyncMock()
    
    # Questions response
    questions_response = Mock()
    questions_response.content = '''{
        "questions": [
            "When did you first notice this problem?",
            "What is the measurable business impact?",
            "Is this in your company TOP 3 priorities?"
        ],
        "category": "problem_identification"
    }'''
    
    # Diagnosis response  
    diagnosis_response = Mock()
    diagnosis_response.content = '''{
        "customer_stated_problem": "Sales dropped 20%",
        "identified_business_problem": "Market share erosion",
        "hidden_root_risk": "Brand perception degradation",
        "urgency_level": "Critical"
    }'''
    
    mock_llm.ainvoke = AsyncMock(side_effect=[questions_response, diagnosis_response])
    return mock_llm


@pytest.fixture
def sample_business_questions():
    """Sample business diagnostic questions."""
    return {
        "questions": [
            "When did you first notice this problem?",
            "What is the measurable business impact?",
            "Which customer segments are affected?",
            "Is this in your company's TOP 3 priorities?",
            "What solutions have you already tried?"
        ],
        "category": "problem_identification"
    }


@pytest.fixture
def sample_business_answers():
    """Sample answers to business questions."""
    return {
        "When did you first notice this problem?": "About 3 months ago",
        "What is the measurable business impact?": "$2M monthly revenue loss",
        "Which customer segments are affected?": "Enterprise customers primarily",
        "Is this in your company's TOP 3 priorities?": "Yes, it's our #1 priority",
        "What solutions have you already tried?": "We tried discounting but it didn't help"
    }


# =============================================================================
# Problem Agent Fixtures
# =============================================================================

@pytest.fixture
def mock_problem_agent_llm():
    """Mock LLM for ProblemStructuringAgent testing."""
    mock_llm = AsyncMock()
    
    response = Mock()
    response.content = '''{
        "problem_type": "Growth",
        "main_problem": "Declining Revenue",
        "root_causes": [
            {
                "cause": "Sales Performance",
                "sub_causes": ["Low conversion rate", "Insufficient leads", "Long sales cycle"]
            },
            {
                "cause": "Market Factors",
                "sub_causes": ["Increased competition", "Market saturation"]
            },
            {
                "cause": "Product Issues",
                "sub_causes": ["Feature gaps", "Quality concerns"]
            }
        ]
    }'''
    
    mock_llm.ainvoke = AsyncMock(return_value=response)
    return mock_llm


# =============================================================================
# Logger Fixtures
# =============================================================================

@pytest.fixture
def mock_logger():
    """Mock logger for testing logging functionality."""
    with patch("logging.getLogger") as mock:
        mock_log = MagicMock()
        mock_log.debug = MagicMock()
        mock_log.info = MagicMock()
        mock_log.warning = MagicMock()
        mock_log.error = MagicMock()
        mock_log.critical = MagicMock()
        mock.return_value = mock_log
        yield mock_log


# =============================================================================
# Config Fixtures
# =============================================================================

@pytest.fixture
def env_override():
    """Context manager for overriding environment variables."""
    import os
    original = os.environ.copy()
    
    def override(**kwargs):
        for key, value in kwargs.items():
            os.environ[key] = value
    
    yield override
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original)
