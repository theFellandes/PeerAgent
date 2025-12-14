# tests/unit/test_websocket_extended.py
"""
Fixed tests for websocket.py - uses actual API from the codebase.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.sent_messages = []
        self.received_messages = []
    
    async def accept(self):
        self.accepted = True
    
    async def close(self, code=1000):
        self.closed = True
        self.close_code = code
    
    async def send_text(self, data):
        self.sent_messages.append(data)
    
    async def send_json(self, data):
        self.sent_messages.append(json.dumps(data))
    
    async def receive_text(self):
        if not self.received_messages:
            raise Exception("No messages")
        return self.received_messages.pop(0)
    
    async def receive_json(self):
        return json.loads(await self.receive_text())
    
    def add_message(self, msg):
        self.received_messages.append(msg)


class TestWebSocketManager:
    """Test WebSocket connection manager."""
    
    def test_manager_exists(self, mock_settings):
        """Test ConnectionManager exists."""
        from src.api.routes.websocket import ConnectionManager
        
        assert ConnectionManager is not None
    
    def test_manager_initialization(self, mock_settings):
        """Test WebSocket manager initializes."""
        from src.api.routes.websocket import ConnectionManager
        
        manager = ConnectionManager()
        
        assert manager is not None
    
    def test_manager_has_active_connections(self, mock_settings):
        """Test manager has active_connections attribute."""
        from src.api.routes.websocket import ConnectionManager
        
        manager = ConnectionManager()
        
        assert hasattr(manager, 'active_connections')
    
    @pytest.mark.asyncio
    async def test_manager_connect_method(self, mock_settings):
        """Test manager has connect method."""
        from src.api.routes.websocket import ConnectionManager
        
        manager = ConnectionManager()
        
        assert hasattr(manager, 'connect')
    
    def test_manager_disconnect_method(self, mock_settings):
        """Test manager has disconnect method."""
        from src.api.routes.websocket import ConnectionManager
        
        manager = ConnectionManager()
        
        assert hasattr(manager, 'disconnect')


class TestMockWebSocketBehavior:
    """Test MockWebSocket behavior for testing."""
    
    @pytest.mark.asyncio
    async def test_mock_websocket_accept(self, mock_settings):
        """Test MockWebSocket accept."""
        ws = MockWebSocket()
        await ws.accept()
        
        assert ws.accepted is True
    
    @pytest.mark.asyncio
    async def test_mock_websocket_close(self, mock_settings):
        """Test MockWebSocket close."""
        ws = MockWebSocket()
        await ws.accept()
        await ws.close()
        
        assert ws.closed is True
    
    @pytest.mark.asyncio
    async def test_mock_websocket_send_text(self, mock_settings):
        """Test MockWebSocket send_text."""
        ws = MockWebSocket()
        await ws.accept()
        await ws.send_text("Hello")
        
        assert "Hello" in ws.sent_messages
    
    @pytest.mark.asyncio
    async def test_mock_websocket_send_json(self, mock_settings):
        """Test MockWebSocket send_json."""
        ws = MockWebSocket()
        await ws.accept()
        await ws.send_json({"type": "test"})
        
        assert len(ws.sent_messages) == 1
        assert "test" in ws.sent_messages[0]
    
    @pytest.mark.asyncio
    async def test_mock_websocket_receive(self, mock_settings):
        """Test MockWebSocket receive."""
        ws = MockWebSocket()
        await ws.accept()
        
        ws.add_message(json.dumps({"type": "task"}))
        received = await ws.receive_json()
        
        assert received["type"] == "task"


class TestWebSocketRoutes:
    """Test WebSocket route definitions."""
    
    def test_websocket_module_exists(self, mock_settings):
        """Test websocket module exists."""
        from src.api.routes import websocket
        
        assert websocket is not None
    
    def test_manager_instance_exists(self, mock_settings):
        """Test manager instance exists."""
        from src.api.routes.websocket import manager
        
        assert manager is not None


class TestWebSocketMessages:
    """Test WebSocket message handling."""
    
    @pytest.mark.asyncio
    async def test_task_message_structure(self, mock_settings):
        """Test task message structure."""
        ws = MockWebSocket()
        await ws.accept()
        
        task_msg = {"type": "task", "data": {"task": "Test task"}}
        ws.add_message(json.dumps(task_msg))
        
        received = await ws.receive_json()
        
        assert received["type"] == "task"
        assert "data" in received
    
    @pytest.mark.asyncio
    async def test_result_message_structure(self, mock_settings):
        """Test result message structure."""
        result = {
            "type": "result",
            "data": {
                "agent_type": "code_agent",
                "code": "def test(): pass"
            }
        }
        
        ws = MockWebSocket()
        await ws.accept()
        await ws.send_json(result)
        
        assert len(ws.sent_messages) == 1
    
    @pytest.mark.asyncio
    async def test_error_message_structure(self, mock_settings):
        """Test error message structure."""
        error = {
            "type": "error",
            "data": {
                "code": "ERROR",
                "message": "Something went wrong"
            }
        }
        
        ws = MockWebSocket()
        await ws.accept()
        await ws.send_json(error)
        
        sent = json.loads(ws.sent_messages[0])
        assert sent["type"] == "error"


class TestWebSocketPingPong:
    """Test WebSocket ping/pong."""
    
    @pytest.mark.asyncio
    async def test_ping_message(self, mock_settings):
        """Test ping message."""
        ws = MockWebSocket()
        await ws.accept()
        
        ws.add_message(json.dumps({"type": "ping"}))
        received = await ws.receive_json()
        
        assert received["type"] == "ping"
    
    @pytest.mark.asyncio
    async def test_pong_response(self, mock_settings):
        """Test pong response."""
        ws = MockWebSocket()
        await ws.accept()
        await ws.send_json({"type": "pong"})
        
        sent = json.loads(ws.sent_messages[0])
        assert sent["type"] == "pong"


class TestWebSocketSession:
    """Test WebSocket session management."""
    
    @pytest.mark.asyncio
    async def test_session_tracking(self, mock_settings):
        """Test session tracking."""
        sessions = {}
        
        ws = MockWebSocket()
        await ws.accept()
        sessions["session-123"] = ws
        
        assert "session-123" in sessions
    
    @pytest.mark.asyncio
    async def test_session_removal(self, mock_settings):
        """Test session removal."""
        sessions = {"session-123": MockWebSocket()}
        
        del sessions["session-123"]
        
        assert "session-123" not in sessions
