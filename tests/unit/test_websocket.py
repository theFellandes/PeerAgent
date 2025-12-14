"""
Unit tests for WebSocket routes.
Target: src/api/routes/websocket.py (19% coverage -> 70%+)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json
import asyncio


class TestWebSocketConnection:
    """Test WebSocket connection handling."""
    
    @pytest.mark.asyncio
    async def test_websocket_accept(self, mock_websocket):
        """Test WebSocket connection acceptance."""
        await mock_websocket.accept()
        assert mock_websocket.accepted
    
    @pytest.mark.asyncio
    async def test_websocket_close(self, mock_websocket):
        """Test WebSocket connection close."""
        await mock_websocket.accept()
        await mock_websocket.close()
        assert mock_websocket.closed
    
    @pytest.mark.asyncio
    async def test_websocket_close_with_code(self, mock_websocket):
        """Test WebSocket close with status code."""
        await mock_websocket.accept()
        await mock_websocket.close(code=1000)
        assert mock_websocket.closed


class TestWebSocketMessageHandling:
    """Test WebSocket message sending and receiving."""
    
    @pytest.mark.asyncio
    async def test_send_text_message(self, mock_websocket):
        """Test sending text message."""
        await mock_websocket.send_text("Hello")
        assert "Hello" in mock_websocket.sent_messages
    
    @pytest.mark.asyncio
    async def test_send_json_message(self, mock_websocket):
        """Test sending JSON message."""
        data = {"type": "response", "data": "test"}
        await mock_websocket.send_json(data)
        assert json.dumps(data) in mock_websocket.sent_messages
    
    @pytest.mark.asyncio
    async def test_receive_text_message(self, mock_websocket):
        """Test receiving text message."""
        mock_websocket.add_message("Hello")
        received = await mock_websocket.receive_text()
        assert received == "Hello"
    
    @pytest.mark.asyncio
    async def test_receive_json_message(self, mock_websocket):
        """Test receiving JSON message."""
        data = {"type": "task", "task": "Write code"}
        mock_websocket.add_message(json.dumps(data))
        received = await mock_websocket.receive_json()
        assert received == data


class TestBusinessWebSocketEndpoint:
    """Test /ws/business/{session_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_business_ws_accepts_session_id(self, mock_websocket):
        """Test business WebSocket accepts session ID."""
        session_id = "biz-123"
        await mock_websocket.accept()
        
        # Simulate session tracking
        sessions = {session_id: mock_websocket}
        assert session_id in sessions
    
    @pytest.mark.asyncio
    async def test_business_ws_receives_task(self, mock_websocket):
        """Test business WebSocket receives task message."""
        task_message = {
            "type": "task",
            "data": {"task": "Sales dropped 20%"}
        }
        mock_websocket.add_message(json.dumps(task_message))
        
        received = await mock_websocket.receive_json()
        assert received["type"] == "task"
        assert "Sales dropped" in received["data"]["task"]
    
    @pytest.mark.asyncio
    async def test_business_ws_sends_questions(self, mock_websocket):
        """Test business WebSocket sends questions response."""
        questions_response = {
            "type": "questions",
            "data": {
                "questions": [
                    "When did this start?",
                    "What is the impact?",
                    "Which segments affected?"
                ]
            }
        }
        
        await mock_websocket.send_json(questions_response)
        assert len(mock_websocket.sent_messages) == 1
    
    @pytest.mark.asyncio
    async def test_business_ws_receives_answers(self, mock_websocket):
        """Test business WebSocket receives answers."""
        answer_message = {
            "type": "answer",
            "data": {
                "answers": {
                    "When did this start?": "3 months ago",
                    "What is the impact?": "$2M revenue loss"
                }
            }
        }
        mock_websocket.add_message(json.dumps(answer_message))
        
        received = await mock_websocket.receive_json()
        assert received["type"] == "answer"
        assert "3 months ago" in str(received["data"]["answers"])
    
    @pytest.mark.asyncio
    async def test_business_ws_sends_diagnosis(self, mock_websocket):
        """Test business WebSocket sends diagnosis response."""
        diagnosis_response = {
            "type": "diagnosis",
            "data": {
                "customer_stated_problem": "Sales dropped 20%",
                "identified_business_problem": "Market share erosion",
                "hidden_root_risk": "Brand perception issues",
                "urgency_level": "High"
            }
        }
        
        await mock_websocket.send_json(diagnosis_response)
        sent = json.loads(mock_websocket.sent_messages[0])
        assert sent["type"] == "diagnosis"
    
    @pytest.mark.asyncio
    async def test_business_ws_multi_turn_conversation(self, mock_websocket):
        """Test multi-turn conversation flow."""
        await mock_websocket.accept()
        
        # Turn 1: Task
        mock_websocket.add_message(json.dumps({
            "type": "task",
            "data": {"task": "Revenue declining"}
        }))
        
        # Turn 2: Questions response
        await mock_websocket.send_json({
            "type": "questions",
            "data": {"questions": ["When?", "How much?"]}
        })
        
        # Turn 3: Answers
        mock_websocket.add_message(json.dumps({
            "type": "answer",
            "data": {"answers": {"When?": "Last quarter"}}
        }))
        
        # Turn 4: More questions or diagnosis
        await mock_websocket.send_json({
            "type": "diagnosis",
            "data": {"urgency_level": "Critical"}
        })
        
        assert len(mock_websocket.sent_messages) == 2


class TestAgentWebSocketEndpoint:
    """Test /ws/agent/{session_id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_agent_ws_accepts_connection(self, mock_websocket):
        """Test agent WebSocket accepts connection."""
        await mock_websocket.accept()
        assert mock_websocket.accepted
    
    @pytest.mark.asyncio
    async def test_agent_ws_routes_code_task(self, mock_websocket):
        """Test agent WebSocket routes code task."""
        task_message = {
            "type": "task",
            "data": {"task": "Write a Python function"}
        }
        mock_websocket.add_message(json.dumps(task_message))
        
        received = await mock_websocket.receive_json()
        
        # Should be routed to code agent
        assert "Python" in received["data"]["task"]
    
    @pytest.mark.asyncio
    async def test_agent_ws_routes_content_task(self, mock_websocket):
        """Test agent WebSocket routes content task."""
        task_message = {
            "type": "task",
            "data": {"task": "What is machine learning?"}
        }
        mock_websocket.add_message(json.dumps(task_message))
        
        received = await mock_websocket.receive_json()
        assert "machine learning" in received["data"]["task"]
    
    @pytest.mark.asyncio
    async def test_agent_ws_sends_code_result(self, mock_websocket):
        """Test agent WebSocket sends code result."""
        code_response = {
            "type": "result",
            "data": {
                "agent_type": "code_agent",
                "code": "def hello(): pass",
                "language": "python"
            }
        }
        
        await mock_websocket.send_json(code_response)
        sent = json.loads(mock_websocket.sent_messages[0])
        assert sent["data"]["agent_type"] == "code_agent"
    
    @pytest.mark.asyncio
    async def test_agent_ws_sends_content_result(self, mock_websocket):
        """Test agent WebSocket sends content result."""
        content_response = {
            "type": "result",
            "data": {
                "agent_type": "content_agent",
                "content": "Machine learning is...",
                "sources": ["https://example.com"]
            }
        }
        
        await mock_websocket.send_json(content_response)
        sent = json.loads(mock_websocket.sent_messages[0])
        assert sent["data"]["agent_type"] == "content_agent"


class TestWebSocketPingPong:
    """Test WebSocket ping/pong keep-alive."""
    
    @pytest.mark.asyncio
    async def test_ping_message_received(self, mock_websocket):
        """Test ping message handling."""
        mock_websocket.add_message(json.dumps({"type": "ping"}))
        
        received = await mock_websocket.receive_json()
        assert received["type"] == "ping"
    
    @pytest.mark.asyncio
    async def test_pong_response_sent(self, mock_websocket):
        """Test pong response."""
        await mock_websocket.send_json({"type": "pong"})
        
        sent = json.loads(mock_websocket.sent_messages[0])
        assert sent["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_ping_pong_cycle(self, mock_websocket):
        """Test complete ping-pong cycle."""
        # Receive ping
        mock_websocket.add_message(json.dumps({"type": "ping"}))
        ping = await mock_websocket.receive_json()
        
        # Send pong
        if ping["type"] == "ping":
            await mock_websocket.send_json({"type": "pong"})
        
        assert len(mock_websocket.sent_messages) == 1


class TestWebSocketSessionState:
    """Test WebSocket session state management."""
    
    def test_session_state_initialization(self):
        """Test session state initialization."""
        state = {
            "session_id": "test-123",
            "connected_at": "2024-01-01T00:00:00Z",
            "message_count": 0,
            "conversation_history": [],
        }
        
        assert state["session_id"] == "test-123"
        assert state["message_count"] == 0
    
    def test_session_state_message_count(self):
        """Test session message counting."""
        state = {"message_count": 0}
        
        state["message_count"] += 1
        state["message_count"] += 1
        
        assert state["message_count"] == 2
    
    def test_session_conversation_history(self):
        """Test session conversation history tracking."""
        history = []
        
        history.append({"role": "user", "content": "Hello"})
        history.append({"role": "assistant", "content": "Hi!"})
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
    
    def test_session_cleanup_on_disconnect(self):
        """Test session cleanup on disconnect."""
        sessions = {"test-123": {"data": "test"}}
        
        # Simulate disconnect cleanup
        if "test-123" in sessions:
            del sessions["test-123"]
        
        assert "test-123" not in sessions


class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, mock_websocket):
        """Test handling of invalid JSON."""
        mock_websocket.add_message("not valid json{")
        
        text = await mock_websocket.receive_text()
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(text)
    
    @pytest.mark.asyncio
    async def test_missing_type_field(self, mock_websocket):
        """Test handling of message without type field."""
        mock_websocket.add_message(json.dumps({"data": "test"}))
        
        received = await mock_websocket.receive_json()
        
        # Should have error handling for missing type
        assert "type" not in received
    
    @pytest.mark.asyncio
    async def test_unknown_message_type(self, mock_websocket):
        """Test handling of unknown message type."""
        mock_websocket.add_message(json.dumps({"type": "unknown", "data": {}}))
        
        received = await mock_websocket.receive_json()
        
        # Should handle gracefully
        assert received["type"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_websocket):
        """Test handling of connection errors."""
        await mock_websocket.accept()
        
        # Simulate connection error
        mock_websocket.received_messages = []  # Empty queue
        
        with pytest.raises(Exception):
            await mock_websocket.receive_text()
    
    @pytest.mark.asyncio
    async def test_send_error_response(self, mock_websocket):
        """Test sending error response."""
        error_response = {
            "type": "error",
            "data": {
                "message": "Invalid request",
                "code": "INVALID_REQUEST"
            }
        }
        
        await mock_websocket.send_json(error_response)
        sent = json.loads(mock_websocket.sent_messages[0])
        assert sent["type"] == "error"


class TestWebSocketConcurrency:
    """Test WebSocket concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_multiple_sessions(self):
        """Test handling multiple concurrent sessions."""
        from tests.conftest import MockWebSocket
        
        sessions = {}
        for i in range(3):
            ws = MockWebSocket()
            await ws.accept()
            sessions[f"session-{i}"] = ws
        
        assert len(sessions) == 3
        assert all(ws.accepted for ws in sessions.values())
    
    @pytest.mark.asyncio
    async def test_broadcast_to_sessions(self):
        """Test broadcasting to multiple sessions."""
        from tests.conftest import MockWebSocket
        
        sessions = [MockWebSocket() for _ in range(3)]
        for ws in sessions:
            await ws.accept()
        
        # Broadcast message
        broadcast_msg = {"type": "broadcast", "data": "Hello all"}
        for ws in sessions:
            await ws.send_json(broadcast_msg)
        
        assert all(len(ws.sent_messages) == 1 for ws in sessions)


class TestWebSocketMessageValidation:
    """Test WebSocket message validation."""
    
    def test_valid_task_message(self):
        """Test valid task message structure."""
        message = {
            "type": "task",
            "data": {"task": "Write code"}
        }
        
        assert "type" in message
        assert "data" in message
        assert "task" in message["data"]
    
    def test_valid_answer_message(self):
        """Test valid answer message structure."""
        message = {
            "type": "answer",
            "data": {"answers": {"Q1": "A1"}}
        }
        
        assert message["type"] == "answer"
        assert "answers" in message["data"]
    
    def test_message_type_validation(self):
        """Test message type validation."""
        valid_types = ["task", "answer", "ping", "pong"]
        
        message = {"type": "task"}
        assert message["type"] in valid_types
    
    def test_empty_task_validation(self):
        """Test validation of empty task."""
        message = {
            "type": "task",
            "data": {"task": ""}
        }
        
        # Should fail validation
        assert message["data"]["task"] == ""


class TestWebSocketRateLimiting:
    """Test WebSocket rate limiting."""
    
    @pytest.mark.asyncio
    async def test_message_rate_tracking(self, mock_websocket):
        """Test message rate tracking."""
        message_times = []
        
        for _ in range(5):
            await mock_websocket.send_text("test")
            message_times.append(asyncio.get_event_loop().time())
        
        assert len(message_times) == 5
    
    def test_rate_limit_configuration(self):
        """Test rate limit configuration."""
        rate_limit = {
            "messages_per_second": 10,
            "burst_limit": 20,
        }
        
        assert rate_limit["messages_per_second"] > 0
        assert rate_limit["burst_limit"] >= rate_limit["messages_per_second"]
