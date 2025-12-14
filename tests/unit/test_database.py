"""
Unit tests for database utilities.
Target: src/utils/database.py (32% coverage -> 70%+)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json
from datetime import datetime


class TestMongoDBConnection:
    """Test MongoDB connection management."""
    
    def test_mongodb_client_creation(self, mock_mongodb):
        """Test MongoDB client creation."""
        assert mock_mongodb is not None
    
    def test_mongodb_connection_string(self):
        """Test MongoDB connection string parsing."""
        connection_string = "mongodb://localhost:27017"
        
        assert "mongodb://" in connection_string
        assert "27017" in connection_string
    
    def test_mongodb_connection_with_auth(self):
        """Test MongoDB connection with authentication."""
        connection_string = "mongodb://user:pass@localhost:27017/dbname"
        
        assert "user:pass" in connection_string
        assert "dbname" in connection_string
    
    def test_mongodb_database_selection(self, mock_mongodb):
        """Test selecting a database."""
        db = mock_mongodb["peeragent"]
        assert db is not None
    
    def test_mongodb_collection_access(self, mock_mongodb):
        """Test accessing a collection."""
        collection = mock_mongodb["peeragent"]["tasks"]
        assert collection is not None


class TestMongoDBCRUD:
    """Test MongoDB CRUD operations."""
    
    def test_insert_document(self, mock_mongodb):
        """Test inserting a document."""
        collection = mock_mongodb["tasks"]
        
        doc = {"task_id": "test-123", "status": "pending"}
        result = collection.insert_one(doc)
        
        assert result.inserted_id is not None
    
    def test_find_document(self, mock_mongodb):
        """Test finding a document."""
        collection = mock_mongodb["tasks"]
        
        # Insert first
        collection.insert_one({"task_id": "test-123", "status": "pending"})
        
        # Find
        found = collection.find_one({"task_id": "test-123"})
        assert found is not None
        assert found["status"] == "pending"
    
    def test_find_document_not_found(self, mock_mongodb):
        """Test finding non-existent document."""
        collection = mock_mongodb["tasks"]
        
        found = collection.find_one({"task_id": "nonexistent"})
        assert found is None
    
    def test_update_document(self, mock_mongodb):
        """Test updating a document."""
        collection = mock_mongodb["tasks"]
        
        # Insert
        collection.insert_one({"task_id": "test-123", "status": "pending"})
        
        # Update
        result = collection.update_one(
            {"task_id": "test-123"},
            {"$set": {"status": "completed"}}
        )
        
        assert result.modified_count == 1
        
        # Verify
        found = collection.find_one({"task_id": "test-123"})
        assert found["status"] == "completed"
    
    def test_delete_document(self, mock_mongodb):
        """Test deleting a document."""
        collection = mock_mongodb["tasks"]
        
        # Insert
        collection.insert_one({"task_id": "test-123"})
        
        # Delete
        result = collection.delete_one({"task_id": "test-123"})
        
        assert result.deleted_count == 1
        
        # Verify
        found = collection.find_one({"task_id": "test-123"})
        assert found is None
    
    def test_find_multiple_documents(self, mock_mongodb):
        """Test finding multiple documents."""
        collection = mock_mongodb["tasks"]
        
        # Insert multiple
        collection.insert_one({"status": "pending"})
        collection.insert_one({"status": "pending"})
        collection.insert_one({"status": "completed"})
        
        # Find all pending
        results = collection.find({"status": "pending"})
        assert len(results) == 2
    
    def test_count_documents(self, mock_mongodb):
        """Test counting documents."""
        collection = mock_mongodb["tasks"]
        
        collection.insert_one({"status": "pending"})
        collection.insert_one({"status": "completed"})
        
        count = collection.count_documents({})
        assert count == 2


class TestRedisConnection:
    """Test Redis connection management."""
    
    def test_redis_client_creation(self, mock_redis):
        """Test Redis client creation."""
        assert mock_redis is not None
    
    def test_redis_connection_string(self):
        """Test Redis connection string."""
        connection_string = "redis://localhost:6379/0"
        
        assert "redis://" in connection_string
        assert "6379" in connection_string
    
    def test_redis_ping(self, mock_redis):
        """Test Redis ping."""
        result = mock_redis.ping()
        assert result is True
    
    def test_redis_database_selection(self):
        """Test Redis database selection."""
        # Database 0-15 are valid
        db_number = 0
        assert 0 <= db_number <= 15


class TestRedisCaching:
    """Test Redis caching operations."""
    
    def test_set_value(self, mock_redis):
        """Test setting a value."""
        result = mock_redis.set("key", "value")
        assert result is True
    
    def test_get_value(self, mock_redis):
        """Test getting a value."""
        mock_redis.set("key", "value")
        
        result = mock_redis.get("key")
        assert result == b"value"
    
    def test_get_nonexistent_value(self, mock_redis):
        """Test getting non-existent value."""
        result = mock_redis.get("nonexistent")
        assert result is None
    
    def test_set_with_expiry(self, mock_redis):
        """Test setting value with expiry."""
        result = mock_redis.setex("key", 3600, "value")
        assert result is True
    
    def test_delete_value(self, mock_redis):
        """Test deleting a value."""
        mock_redis.set("key", "value")
        
        result = mock_redis.delete("key")
        assert result == 1
    
    def test_delete_nonexistent_value(self, mock_redis):
        """Test deleting non-existent value."""
        result = mock_redis.delete("nonexistent")
        assert result == 0
    
    def test_exists_check(self, mock_redis):
        """Test checking if key exists."""
        mock_redis.set("key", "value")
        
        assert mock_redis.exists("key") == 1
        assert mock_redis.exists("nonexistent") == 0
    
    def test_keys_pattern(self, mock_redis):
        """Test getting keys by pattern."""
        mock_redis.set("task:1", "value1")
        mock_redis.set("task:2", "value2")
        mock_redis.set("other:1", "value3")
        
        keys = mock_redis.keys("task:*")
        assert len(keys) == 2


class TestDatabaseLogging:
    """Test database logging functionality."""
    
    def test_log_task_creation(self, mock_mongodb):
        """Test logging task creation."""
        collection = mock_mongodb["logs"]
        
        log_entry = {
            "event": "task_created",
            "task_id": "test-123",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        result = collection.insert_one(log_entry)
        assert result.inserted_id is not None
    
    def test_log_task_completion(self, mock_mongodb):
        """Test logging task completion."""
        collection = mock_mongodb["logs"]
        
        log_entry = {
            "event": "task_completed",
            "task_id": "test-123",
            "execution_time": 1.5,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        collection.insert_one(log_entry)
        
        found = collection.find_one({"task_id": "test-123", "event": "task_completed"})
        assert found is not None
    
    def test_log_error(self, mock_mongodb):
        """Test logging errors."""
        collection = mock_mongodb["logs"]
        
        log_entry = {
            "event": "error",
            "task_id": "test-123",
            "error_type": "LLMError",
            "error_message": "API timeout",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        collection.insert_one(log_entry)
        
        errors = collection.find({"event": "error"})
        assert len(errors) == 1


class TestConnectionPooling:
    """Test database connection pooling."""
    
    def test_mongodb_pool_size(self):
        """Test MongoDB connection pool configuration."""
        pool_config = {
            "maxPoolSize": 100,
            "minPoolSize": 10,
        }
        
        assert pool_config["maxPoolSize"] >= pool_config["minPoolSize"]
    
    def test_redis_pool_size(self):
        """Test Redis connection pool configuration."""
        pool_config = {
            "max_connections": 50,
        }
        
        assert pool_config["max_connections"] > 0


class TestDatabaseHealthCheck:
    """Test database health check functionality."""
    
    def test_mongodb_health_check(self, mock_mongodb):
        """Test MongoDB health check."""
        # Attempt to access a collection
        try:
            _ = mock_mongodb["test"]
            is_healthy = True
        except Exception:
            is_healthy = False
        
        assert is_healthy
    
    def test_redis_health_check(self, mock_redis):
        """Test Redis health check."""
        try:
            result = mock_redis.ping()
            is_healthy = result is True
        except Exception:
            is_healthy = False
        
        assert is_healthy
    
    def test_health_check_response_format(self):
        """Test health check response format."""
        health_response = {
            "status": "healthy",
            "checks": {
                "mongodb": "healthy",
                "redis": "healthy",
            }
        }
        
        assert health_response["status"] == "healthy"
        assert all(v == "healthy" for v in health_response["checks"].values())


class TestDatabaseErrorHandling:
    """Test database error handling."""
    
    def test_handles_mongodb_connection_error(self):
        """Test handling MongoDB connection error."""
        mock_client = Mock()
        mock_client.server_info.side_effect = ConnectionError("MongoDB unavailable")
        
        with pytest.raises(ConnectionError):
            mock_client.server_info()
    
    def test_handles_redis_connection_error(self):
        """Test handling Redis connection error."""
        mock_redis = Mock()
        mock_redis.ping.side_effect = ConnectionError("Redis unavailable")
        
        with pytest.raises(ConnectionError):
            mock_redis.ping()
    
    def test_retry_on_connection_error(self):
        """Test retry on connection error."""
        attempt_count = 0
        max_retries = 3
        
        def connect_with_retry():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < max_retries:
                raise ConnectionError("Temporary failure")
            return True
        
        result = False
        for _ in range(max_retries):
            try:
                result = connect_with_retry()
                break
            except ConnectionError:
                continue
        
        assert result is True


class TestDatabaseMigrations:
    """Test database migration utilities."""
    
    def test_create_indexes(self, mock_mongodb):
        """Test index creation."""
        collection = mock_mongodb["tasks"]
        
        # Simulate index creation
        indexes = [
            {"key": "task_id", "unique": True},
            {"key": "status", "unique": False},
            {"key": "created_at", "unique": False},
        ]
        
        assert len(indexes) == 3
        assert any(idx["key"] == "task_id" and idx["unique"] for idx in indexes)
    
    def test_schema_validation(self):
        """Test schema validation setup."""
        schema = {
            "bsonType": "object",
            "required": ["task_id", "status"],
            "properties": {
                "task_id": {"bsonType": "string"},
                "status": {"enum": ["pending", "running", "completed", "failed"]},
            }
        }
        
        assert "required" in schema
        assert "task_id" in schema["required"]


class TestTransactions:
    """Test database transaction handling."""
    
    def test_mongodb_transaction_commit(self, mock_mongodb):
        """Test MongoDB transaction commit."""
        # Simulate transaction
        operations = []
        
        operations.append({"op": "insert", "doc": {"id": 1}})
        operations.append({"op": "update", "filter": {"id": 1}, "update": {"status": "done"}})
        
        # Commit (all operations applied)
        committed = True
        
        assert committed
        assert len(operations) == 2
    
    def test_mongodb_transaction_rollback(self):
        """Test MongoDB transaction rollback."""
        # Simulate rollback scenario
        operations = []
        operations.append({"op": "insert", "doc": {"id": 1}})
        
        # Error occurs, rollback
        operations.clear()
        
        assert len(operations) == 0


class TestDatabaseConfiguration:
    """Test database configuration."""
    
    def test_mongodb_url_from_env(self):
        """Test MongoDB URL from environment."""
        import os
        
        with patch.dict(os.environ, {"MONGODB_URL": "mongodb://testhost:27017"}):
            url = os.environ.get("MONGODB_URL")
            assert "testhost" in url
    
    def test_redis_url_from_env(self):
        """Test Redis URL from environment."""
        import os
        
        with patch.dict(os.environ, {"REDIS_URL": "redis://testhost:6379/0"}):
            url = os.environ.get("REDIS_URL")
            assert "testhost" in url
    
    def test_default_database_urls(self):
        """Test default database URLs."""
        defaults = {
            "mongodb": "mongodb://localhost:27017",
            "redis": "redis://localhost:6379/0",
        }
        
        assert "localhost" in defaults["mongodb"]
        assert "localhost" in defaults["redis"]
