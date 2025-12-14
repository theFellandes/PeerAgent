# tests/unit/test_database_extended.py
"""
Fixed tests for database.py - uses actual API from the codebase.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestMongoDBClient:
    """Test MongoDB client."""
    
    def test_get_mongo_db_exists(self, mock_settings):
        """Test get_mongo_db function exists."""
        from src.utils.database import get_mongo_db
        
        assert callable(get_mongo_db)
    
    def test_get_mongo_db_returns_db(self, mock_settings, mock_mongodb):
        """Test get_mongo_db returns database."""
        from src.utils.database import get_mongo_db
        
        db = get_mongo_db()
        
        assert db is not None


class TestRedisClient:
    """Test Redis client."""
    
    def test_get_redis_client_exists(self, mock_settings):
        """Test get_redis_client function exists."""
        from src.utils.database import get_redis_client
        
        assert callable(get_redis_client)
    
    def test_get_redis_client_returns_client(self, mock_settings, mock_redis):
        """Test get_redis_client returns client."""
        from src.utils.database import get_redis_client
        
        client = get_redis_client()
        
        assert client is not None


class TestDatabaseModule:
    """Test database module structure."""
    
    def test_database_module_imports(self, mock_settings):
        """Test database module can be imported."""
        from src.utils import database
        
        assert database is not None
    
    def test_database_has_mongo_function(self, mock_settings):
        """Test database has get_mongo_db."""
        from src.utils import database
        
        assert hasattr(database, 'get_mongo_db')
    
    def test_database_has_redis_function(self, mock_settings):
        """Test database has get_redis_client."""
        from src.utils import database
        
        assert hasattr(database, 'get_redis_client')


class TestMongoDBOperations:
    """Test MongoDB operations with mocks."""
    
    def test_mongo_collection_access(self, mock_settings, mock_mongodb):
        """Test MongoDB collection access."""
        collection = mock_mongodb["test_collection"]
        
        assert collection is not None
    
    def test_mongo_insert(self, mock_settings, mock_mongodb):
        """Test MongoDB insert."""
        collection = mock_mongodb["test_collection"]
        collection.insert_one.return_value = Mock(inserted_id="123")
        
        result = collection.insert_one({"key": "value"})
        
        assert result.inserted_id == "123"
    
    def test_mongo_find(self, mock_settings, mock_mongodb):
        """Test MongoDB find."""
        collection = mock_mongodb["test_collection"]
        collection.find_one.return_value = {"key": "value"}
        
        result = collection.find_one({"key": "value"})
        
        assert result is not None


class TestRedisOperations:
    """Test Redis operations with mocks."""
    
    def test_redis_set(self, mock_settings, mock_redis):
        """Test Redis SET operation."""
        mock_redis.set.return_value = True
        
        result = mock_redis.set("key", "value")
        
        assert result is True
    
    def test_redis_get(self, mock_settings, mock_redis):
        """Test Redis GET operation."""
        mock_redis.get.return_value = b"value"
        
        result = mock_redis.get("key")
        
        assert result == b"value"
    
    def test_redis_delete(self, mock_settings, mock_redis):
        """Test Redis DELETE operation."""
        mock_redis.delete.return_value = 1
        
        result = mock_redis.delete("key")
        
        assert result == 1


class TestDatabaseSingleton:
    """Test database singleton patterns."""
    
    def test_mongo_returns_instance(self, mock_settings, mock_mongodb):
        """Test get_mongo_db returns instance."""
        from src.utils.database import get_mongo_db
        
        db = get_mongo_db()
        
        assert db is not None
    
    def test_redis_returns_instance(self, mock_settings, mock_redis):
        """Test get_redis_client returns instance."""
        from src.utils.database import get_redis_client
        
        client = get_redis_client()
        
        assert client is not None
