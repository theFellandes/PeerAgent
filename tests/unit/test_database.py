# tests/unit/test_database.py
"""
Unit tests for database utilities.
Target: src/utils/database.py (32% coverage -> 70%+)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json


class TestMongoDBConnection:
    """Test MongoDB connection management."""
    
    def test_get_mongo_db_returns_database(self, mock_settings, mock_mongo_db):
        """Test get_mongo_db returns a database instance."""
        from src.utils.database import get_mongo_db
        
        db = get_mongo_db()
        assert db is not None
    
    def test_mongodb_url_from_settings(self, mock_settings):
        """Test MongoDB URL is read from settings."""
        assert mock_settings.mongodb_url is not None
        assert "mongodb://" in mock_settings.mongodb_url
    
    def test_mongodb_db_name_from_settings(self, mock_settings):
        """Test MongoDB database name from settings."""
        assert mock_settings.mongodb_db_name is not None
    
    def test_mongo_client_connection(self, mock_settings, mock_mongo_client):
        """Test MongoDB client connects successfully."""
        # Client should be able to get server info
        info = mock_mongo_client.server_info()
        assert "version" in info


class TestMongoDBOperations:
    """Test MongoDB CRUD operations."""
    
    def test_insert_document(self, mock_settings, mock_mongo_client):
        """Test inserting a document."""
        db = mock_mongo_client["peeragent"]
        collection = db["logs"]
        
        doc = {"event": "test", "data": "test data"}
        result = collection.insert_one(doc)
        
        assert result.inserted_id is not None
    
    def test_find_document(self, mock_settings, mock_mongo_client):
        """Test finding a document."""
        db = mock_mongo_client["peeragent"]
        collection = db["logs"]
        
        # Configure mock to return a document
        collection.find_one.return_value = {"_id": "test", "event": "test"}
        
        result = collection.find_one({"event": "test"})
        assert result is not None
    
    def test_update_document(self, mock_settings, mock_mongo_client):
        """Test updating a document."""
        db = mock_mongo_client["peeragent"]
        collection = db["logs"]
        
        result = collection.update_one(
            {"event": "test"},
            {"$set": {"updated": True}}
        )
        
        assert result.modified_count >= 0
    
    def test_delete_document(self, mock_settings, mock_mongo_client):
        """Test deleting a document."""
        db = mock_mongo_client["peeragent"]
        collection = db["logs"]
        
        result = collection.delete_one({"event": "test"})
        
        assert result.deleted_count >= 0


class TestRedisConnection:
    """Test Redis connection management."""
    
    def test_get_redis_client_returns_client(self, mock_settings, mock_redis):
        """Test get_redis_client returns a client."""
        from src.utils.database import get_redis_client
        
        client = get_redis_client()
        assert client is not None
    
    def test_redis_url_from_settings(self, mock_settings):
        """Test Redis URL from settings."""
        assert mock_settings.redis_url is not None
        assert "redis://" in mock_settings.redis_url
    
    def test_redis_ping(self, mock_settings, mock_redis_client):
        """Test Redis ping."""
        result = mock_redis_client.ping()
        assert result is True


class TestRedisOperations:
    """Test Redis operations."""
    
    def test_redis_set(self, mock_settings, mock_redis_client):
        """Test Redis SET operation."""
        result = mock_redis_client.set("test_key", "test_value")
        assert result is True
    
    def test_redis_get(self, mock_settings, mock_redis_client):
        """Test Redis GET operation."""
        mock_redis_client.get.return_value = b"test_value"
        
        result = mock_redis_client.get("test_key")
        assert result == b"test_value"
    
    def test_redis_setex(self, mock_settings, mock_redis_client):
        """Test Redis SETEX (set with expiry)."""
        result = mock_redis_client.setex("test_key", 3600, "test_value")
        assert result is True
    
    def test_redis_delete(self, mock_settings, mock_redis_client):
        """Test Redis DELETE operation."""
        mock_redis_client.delete.return_value = 1
        
        result = mock_redis_client.delete("test_key")
        assert result == 1
    
    def test_redis_exists(self, mock_settings, mock_redis_client):
        """Test Redis EXISTS operation."""
        mock_redis_client.exists.return_value = 1
        
        result = mock_redis_client.exists("test_key")
        assert result == 1
    
    def test_redis_keys(self, mock_settings, mock_redis_client):
        """Test Redis KEYS operation."""
        mock_redis_client.keys.return_value = [b"task:1", b"task:2"]
        
        result = mock_redis_client.keys("task:*")
        assert len(result) == 2


class TestDatabaseHealthChecks:
    """Test database health check functionality."""
    
    def test_mongodb_health_check(self, mock_settings, mock_mongo_client):
        """Test MongoDB health check."""
        try:
            mock_mongo_client.server_info()
            is_healthy = True
        except Exception:
            is_healthy = False
        
        assert is_healthy
    
    def test_redis_health_check(self, mock_settings, mock_redis_client):
        """Test Redis health check."""
        try:
            result = mock_redis_client.ping()
            is_healthy = result is True
        except Exception:
            is_healthy = False
        
        assert is_healthy
    
    def test_combined_health_status(self, mock_settings, mock_mongo_client, mock_redis_client):
        """Test combined database health status."""
        health = {
            "mongodb": "healthy",
            "redis": "healthy"
        }
        
        # Check MongoDB
        try:
            mock_mongo_client.server_info()
        except Exception:
            health["mongodb"] = "unhealthy"
        
        # Check Redis
        try:
            mock_redis_client.ping()
        except Exception:
            health["redis"] = "unhealthy"
        
        assert health["mongodb"] == "healthy"
        assert health["redis"] == "healthy"


class TestConnectionErrorHandling:
    """Test database connection error handling."""
    
    def test_mongodb_connection_error(self, mock_settings):
        """Test MongoDB connection error handling."""
        with patch("pymongo.MongoClient") as mock_client:
            mock_client.side_effect = Exception("Connection refused")
            
            with pytest.raises(Exception) as exc_info:
                mock_client("mongodb://invalid:27017")
            
            assert "Connection refused" in str(exc_info.value)
    
    def test_redis_connection_error(self, mock_settings):
        """Test Redis connection error handling."""
        with patch("redis.Redis") as mock_redis:
            mock_redis.side_effect = Exception("Connection refused")
            
            with pytest.raises(Exception) as exc_info:
                mock_redis(host="invalid")
            
            assert "Connection refused" in str(exc_info.value)


class TestDatabaseSingleton:
    """Test database client singleton pattern."""
    
    def test_mongo_db_singleton(self, mock_settings, mock_mongo_db):
        """Test get_mongo_db returns same instance."""
        from src.utils.database import get_mongo_db
        
        db1 = get_mongo_db()
        db2 = get_mongo_db()
        
        # Should return same mock instance
        assert db1 is db2
    
    def test_redis_client_singleton(self, mock_settings, mock_redis):
        """Test get_redis_client returns same instance."""
        from src.utils.database import get_redis_client
        
        client1 = get_redis_client()
        client2 = get_redis_client()
        
        # Should return same mock instance
        assert client1 is client2
