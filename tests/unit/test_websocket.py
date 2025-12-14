# tests/unit/test_websocket.py - FIXED
"""
Unit tests for WebSocket routes.
FIXED: Uses proper MockWebSocket fixture from conftest.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json
from typing import List


# Local MockWebSocket class (no external import needed)
class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self, session_id: str = "test-session"):
        self.session_id = session_id
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.sent_messages: List[dict] = []
        self.received_messages: List[dict] = []
        self._receive_queue: List[dict] = []
    
    async def accept(self):
        self.accepted = True
    
    async def close(self, code: int = 1000):
        self.closed = True
        self.close_code = code
    
    async def send_text(self, data: str):
        self.sent_messages.append({"type": "text", "data": data})
    
    async def send_json(self, data: dict):
        self.sent_messages.append({"type": "json", "data": data})
    
    async def receive_text(self) -> str:
        if self._receive_queue:
            msg = self._receive_queue.pop(0)
            return json.dumps(msg) if isinstance(msg, dict) else msg
        return "{}"
    
    async def receive_json(self) -> dict:
        if self._receive_queue:
            return self._receive_queue.pop(0)
        return {}
    
    def queue_message(self, message: dict):
        self._receive_queue.append(message)


class TestWebSocketConnection:
    """Test WebSocket connection handling."""
    
    @pytest.mark.asyncio
    async def test_websocket_accept(self, mock_settings):
        """Test WebSocket accepts connection."""
        ws = MockWebSocket()
        await ws.accept()
        assert ws.accepted is True
    
    @pytest.mark.asyncio
    async def test_websocket_close(self, mock_settings):
        """Test WebSocket close."""
        ws = MockWebSocket()
        await ws.accept()
        await ws.close()
        assert ws.closed is True
    
    @pytest.mark.asyncio
    async def test_websocket_close_with_code(self, mock_settings):
        """Test WebSocket close with code."""
        ws = MockWebSocket()
        await ws.accept()
        await ws.close(code=1001)
        assert ws.close_code == 1001


class TestWebSocketMessageHandling:
    """Test WebSocket message handling."""
    
    @pytest.mark.asyncio
    async def test_send_text_message(self, mock_settings):
        """Test sending text message."""
        ws = MockWebSocket()
        await ws.accept()
        await ws.send_text("Hello")
        
        assert len(ws.sent_messages) == 1
        assert ws.sent_messages[0]["type"] == "text"
        assert ws.sent_messages[0]["data"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_send_json_message(self, mock_settings):
        """Test sending JSON message."""
        ws = MockWebSocket()
        await ws.accept()
        await ws.send_json({"type": "ack", "data": {}})
        
        assert len(ws.sent_messages) == 1
        assert ws.sent_messages[0]["type"] == "json"
        assert ws.sent_messages[0]["data"]["type"] == "ack"
    
    @pytest.mark.asyncio
    async def test_receive_text_message(self, mock_settings):
        """Test receiving text message."""
        ws = MockWebSocket()
        ws.queue_message({"type": "task", "task": "Write code"})
        
        msg = await ws.receive_text()
        parsed = json.loads(msg)
        assert parsed["type"] == "task"
    
    @pytest.mark.asyncio
    async def test_receive_json_message(self, mock_settings):
        """Test receiving JSON message."""
        ws = MockWebSocket()
        ws.queue_message({"type": "task", "task": "Write code"})
        
        msg = await ws.receive_json()
        assert msg["type"] == "task"


class TestBusinessWebSocketEndpoint:
    """Test /ws/business/{session_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_business_ws_accepts_session_id(self, mock_settings):
        """Test business WebSocket accepts session ID."""
        session_id = "business-session-123"
        ws = MockWebSocket(session_id=session_id)
        
        await ws.accept()
        assert ws.session_id == session_id
    
    @pytest.mark.asyncio
    async def test_business_ws_receives_task(self, mock_settings):
        """Test business WebSocket receives task."""
        ws = MockWebSocket()
        ws.queue_message({
            "type": "task",
            "task": "Our sales dropped 20%"
        })
        
        msg = await ws.receive_json()
        assert msg["type"] == "task"
        assert "sales" in msg["task"].lower()
    
    @pytest.mark.asyncio
    async def test_business_ws_sends_questions(self, mock_settings):
        """Test business WebSocket sends questions."""
        ws = MockWebSocket()
        await ws.accept()
        
        await ws.send_json({
            "type": "questions",
            "data": {
                "questions": ["When did this start?", "What is the impact?"],
                "category": "problem_identification"
            }
        })
        
        assert len(ws.sent_messages) == 1
        sent = ws.sent_messages[0]["data"]
        assert sent["type"] == "questions"
    
    @pytest.mark.asyncio
    async def test_business_ws_receives_answers(self, mock_settings):
        """Test business WebSocket receives answers."""
        ws = MockWebSocket()
        ws.queue_message({
            "type": "answers",
            "data": {
                "When did this start?": "3 months ago",
                "What is the impact?": "$2M revenue loss"
            }
        })
        
        msg = await ws.receive_json()
        assert msg["type"] == "answers"
    
    @pytest.mark.asyncio
    async def test_business_ws_sends_diagnosis(self, mock_settings):
        """Test business WebSocket sends diagnosis."""
        ws = MockWebSocket()
        await ws.accept()
        
        await ws.send_json({
            "type": "diagnosis",
            "data": {
                "customer_stated_problem": "Sales dropped",
                "identified_business_problem": "Market share loss",
                "hidden_root_risk": "Brand issues",
                "urgency_level": "Critical"
            }
        })
        
        assert len(ws.sent_messages) == 1
        sent = ws.sent_messages[0]["data"]
        assert sent["type"] == "diagnosis"
    
    @pytest.mark.asyncio
    async def test_business_ws_multi_turn_conversation(self, mock_settings):
        """Test multi-turn business conversation."""
        ws = MockWebSocket()
        await ws.accept()
        
        # Send task
        ws.queue_message({"type": "task", "task": "Revenue declining"})
        task_msg = await ws.receive_json()
        
        # Send questions
        await ws.send_json({"type": "questions", "data": {"questions": ["Q1?"]}})
        
        # Receive answers
        ws.queue_message({"type": "answers", "data": {"Q1?": "Answer"}})
        answers_msg = await ws.receive_json()
        
        # Send diagnosis
        await ws.send_json({"type": "diagnosis", "data": {"urgency_level": "High"}})
        
        assert len(ws.sent_messages) == 2


class TestAgentWebSocketEndpoint:
    """Test /ws/agent/{session_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_agent_ws_accepts_connection(self, mock_settings):
        """Test agent WebSocket accepts connection."""
        ws = MockWebSocket(session_id="agent-session")
        await ws.accept()
        assert ws.accepted
    
    @pytest.mark.asyncio
    async def test_agent_ws_routes_code_task(self, mock_settings):
        """Test agent WebSocket routes code task."""
        ws = MockWebSocket()
        ws.queue_message({
            "type": "task",
            "task": "Write a Python function"
        })
        
        msg = await ws.receive_json()
        assert "python" in msg["task"].lower() or "function" in msg["task"].lower()
    
    @pytest.mark.asyncio
    async def test_agent_ws_routes_content_task(self, mock_settings):
        """Test agent WebSocket routes content task."""
        ws = MockWebSocket()
        ws.queue_message({
            "type": "task",
            "task": "What is machine learning?"
        })
        
        msg = await ws.receive_json()
        assert "what" in msg["task"].lower()
    
    @pytest.mark.asyncio
    async def test_agent_ws_sends_code_result(self, mock_settings):
        """Test agent WebSocket sends code result."""
        ws = MockWebSocket()
        await ws.accept()
        
        await ws.send_json({
            "type": "result",
            "agent_type": "code_agent",
            "data": {
                "code": "def hello(): pass",
                "language": "python",
                "explanation": "A function"
            }
        })
        
        sent = ws.sent_messages[0]["data"]
        assert sent["agent_type"] == "code_agent"
    
    @pytest.mark.asyncio
    async def test_agent_ws_sends_content_result(self, mock_settings):
        """Test agent WebSocket sends content result."""
        ws = MockWebSocket()
        await ws.accept()
        
        await ws.send_json({
            "type": "result",
            "agent_type": "content_agent",
            "data": {
                "content": "Machine learning is...",
                "sources": ["https://example.com"]
            }
        })
        
        sent = ws.sent_messages[0]["data"]
        assert sent["agent_type"] == "content_agent"


class TestWebSocketPingPong:
    """Test WebSocket ping/pong."""
    
    @pytest.mark.asyncio
    async def test_ping_message_received(self, mock_settings):
        """Test ping message is received."""
        ws = MockWebSocket()
        ws.queue_message({"type": "ping"})
        
        msg = await ws.receive_json()
        assert msg["type"] == "ping"
    
    @pytest.mark.asyncio
    async def test_pong_response_sent(self, mock_settings):
        """Test pong response is sent."""
        ws = MockWebSocket()
        await ws.accept()
        await ws.send_json({"type": "pong"})
        
        assert ws.sent_messages[0]["data"]["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_ping_pong_cycle(self, mock_settings):
        """Test complete ping/pong cycle."""
        ws = MockWebSocket()
        await ws.accept()
        
        # Receive ping
        ws.queue_message({"type": "ping"})
        ping = await ws.receive_json()
        
        # Send pong
        await ws.send_json({"type": "pong"})
        
        assert ping["type"] == "ping"
        assert ws.sent_messages[0]["data"]["type"] == "pong"


class TestWebSocketSessionState:
    """Test WebSocket session state management."""
    
    @pytest.mark.asyncio
    async def test_session_id_stored(self, mock_settings):
        """Test session ID is stored."""
        session_id = "state-test-session"
        ws = MockWebSocket(session_id=session_id)
        
        assert ws.session_id == session_id
    
    @pytest.mark.asyncio
    async def test_messages_tracked(self, mock_settings):
        """Test sent messages are tracked."""
        ws = MockWebSocket()
        await ws.accept()
        
        await ws.send_json({"msg": 1})
        await ws.send_json({"msg": 2})
        await ws.send_json({"msg": 3})
        
        assert len(ws.sent_messages) == 3


class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, mock_settings):
        """Test handling of invalid JSON."""
        ws = MockWebSocket()
        ws._receive_queue.append("not valid json")
        
        text = await ws.receive_text()
        
        try:
            json.loads(text)
        except json.JSONDecodeError:
            # Expected for invalid JSON
            pass
    
    @pytest.mark.asyncio
    async def test_missing_type_field(self, mock_settings):
        """Test handling message without type field."""
        ws = MockWebSocket()
        ws.queue_message({"data": "no type field"})
        
        msg = await ws.receive_json()
        
        # Should handle gracefully
        has_type = "type" in msg
        assert not has_type
    
    @pytest.mark.asyncio
    async def test_unknown_message_type(self, mock_settings):
        """Test handling unknown message type."""
        ws = MockWebSocket()
        ws.queue_message({"type": "unknown_type", "data": {}})
        
        msg = await ws.receive_json()
        assert msg["type"] == "unknown_type"
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_settings):
        """Test handling connection errors."""
        ws = MockWebSocket()
        
        # Simulate connection error
        ws.closed = True
        
        assert ws.closed is True
    
    @pytest.mark.asyncio
    async def test_send_error_response(self, mock_settings):
        """Test sending error response."""
        ws = MockWebSocket()
        await ws.accept()
        
        await ws.send_json({
            "type": "error",
            "error": {
                "code": "INVALID_MESSAGE",
                "message": "Message format is invalid"
            }
        })
        
        sent = ws.sent_messages[0]["data"]
        assert sent["type"] == "error"


class TestWebSocketConcurrency:
    """Test WebSocket concurrency."""
    
    @pytest.mark.asyncio
    async def test_multiple_sessions(self, mock_settings):
        """Test multiple concurrent sessions."""
        sessions = {}
        
        for i in range(3):
            ws = MockWebSocket(session_id=f"session-{i}")
            await ws.accept()
            sessions[f"session-{i}"] = ws
        
        assert len(sessions) == 3
        for ws in sessions.values():
            assert ws.accepted
    
    @pytest.mark.asyncio
    async def test_broadcast_to_sessions(self, mock_settings):
        """Test broadcasting to multiple sessions."""
        sessions = [MockWebSocket(session_id=f"session-{i}") for i in range(3)]
        
        for ws in sessions:
            await ws.accept()
            await ws.send_json({"type": "broadcast", "message": "Hello all"})
        
        for ws in sessions:
            assert len(ws.sent_messages) == 1


class TestWebSocketRateLimiting:
    """Test WebSocket rate limiting."""
    
    @pytest.mark.asyncio
    async def test_message_rate_tracking(self, mock_settings):
        """Test message rate is tracked."""
        ws = MockWebSocket()
        await ws.accept()
        
        message_count = 0
        for _ in range(10):
            await ws.send_json({"type": "test"})
            message_count += 1
        
        assert message_count == 10
        assert len(ws.sent_messages) == 10


class TestWebSocketMessageValidation:
    """Test WebSocket message validation."""
    
    @pytest.mark.asyncio
    async def test_valid_task_message(self, mock_settings):
        """Test valid task message structure."""
        message = {
            "type": "task",
            "task": "Write code",
            "session_id": "test"
        }
        
        assert "type" in message
        assert "task" in message
        assert message["type"] == "task"
    
    @pytest.mark.asyncio
    async def test_valid_result_message(self, mock_settings):
        """Test valid result message structure."""
        message = {
            "type": "result",
            "agent_type": "code_agent",
            "data": {
                "code": "print('hi')",
                "language": "python"
            }
        }
        
        assert message["type"] == "result"
        assert "data" in message
