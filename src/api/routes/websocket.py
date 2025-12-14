# WebSocket Support for Real-time Business Q&A
"""
Provides WebSocket endpoints for real-time interaction with the BusinessSenseAgent.
Enables streaming questions and answers without HTTP polling.
"""

import json
import asyncio
from typing import Any, Dict, Optional, Set
from datetime import datetime
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, Field

from src.agents.peer_agent import PeerAgent
from src.utils.logger import get_logger
from src.utils.memory import get_memory_store

logger = get_logger("WebSocketHandler")
router = APIRouter(prefix="/ws", tags=["WebSocket"])


class WSMessage(BaseModel):
    """WebSocket message schema."""
    type: str = Field(..., description="Message type: 'task', 'answer', 'ping'")
    data: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WSResponse(BaseModel):
    """WebSocket response schema."""
    type: str = Field(..., description="Response type: 'questions', 'diagnosis', 'error', 'ack', 'pong'")
    data: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.
    
    Features:
    - Connection tracking by session
    - Broadcast support
    - Automatic reconnection handling
    """
    
    def __init__(self):
        # session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # session_id -> conversation state
        self.session_states: Dict[str, Dict[str, Any]] = {}
        # All connections for broadcast
        self._all_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """
        Accept and register a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            session_id: Session identifier
            
        Returns:
            True if connection accepted
        """
        await websocket.accept()
        
        # Close existing connection for this session (if any)
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].close()
            except Exception:
                pass
        
        self.active_connections[session_id] = websocket
        self._all_connections.add(websocket)
        
        # Initialize session state
        if session_id not in self.session_states:
            self.session_states[session_id] = {
                "collected_answers": {},
                "current_questions": [],
                "phase": "identify",
                "task_count": 0
            }
        
        logger.info(f"WebSocket connected: session={session_id}")
        return True
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            ws = self.active_connections.pop(session_id)
            self._all_connections.discard(ws)
            logger.info(f"WebSocket disconnected: session={session_id}")
    
    async def send_message(self, session_id: str, message: WSResponse):
        """
        Send a message to a specific session.
        
        Args:
            session_id: Target session
            message: Message to send
        """
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(
                    message.model_dump()
                )
            except WebSocketDisconnect:
                self.disconnect(session_id)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                self.disconnect(session_id)
    
    async def broadcast(self, message: WSResponse):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast
        """
        disconnected = []
        for ws in self._all_connections:
            try:
                await ws.send_json(message.model_dump())
            except Exception:
                disconnected.append(ws)
        
        # Clean up disconnected
        for ws in disconnected:
            self._all_connections.discard(ws)
    
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get the current state for a session."""
        return self.session_states.get(session_id, {})
    
    def update_session_state(self, session_id: str, updates: Dict[str, Any]):
        """Update session state."""
        if session_id in self.session_states:
            self.session_states[session_id].update(updates)
    
    def is_connected(self, session_id: str) -> bool:
        """Check if a session is connected."""
        return session_id in self.active_connections
    
    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self._all_connections)


# Global connection manager
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Dependency to get the connection manager."""
    return manager


@router.websocket("/business/{session_id}")
async def business_websocket(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for real-time business analysis.
    
    Message Types (Client -> Server):
    - task: Start a new business analysis
    - answer: Provide answers to questions
    - ping: Keep-alive ping
    
    Response Types (Server -> Client):
    - questions: Follow-up questions from agent
    - diagnosis: Final business diagnosis
    - error: Error message
    - ack: Acknowledgment
    - pong: Ping response
    
    Example Usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/business/session-123');
    
    // Start analysis
    ws.send(JSON.stringify({
        type: 'task',
        data: { task: 'Our sales dropped 20%' }
    }));
    
    // Send answers
    ws.send(JSON.stringify({
        type: 'answer',
        data: { answers: { 'When did it start?': '3 months ago' } }
    }));
    ```
    """
    await manager.connect(websocket, session_id)
    peer_agent = PeerAgent(session_id=session_id)
    memory = get_memory_store()
    
    try:
        # Send connection acknowledgment
        await manager.send_message(
            session_id,
            WSResponse(
                type="ack",
                data={"message": "Connected to business analysis"},
                session_id=session_id
            )
        )
        
        while True:
            # Receive message
            raw_data = await websocket.receive_text()
            
            try:
                message = WSMessage.model_validate_json(raw_data)
            except Exception as e:
                await manager.send_message(
                    session_id,
                    WSResponse(
                        type="error",
                        data={"error": f"Invalid message format: {e}"},
                        session_id=session_id
                    )
                )
                continue
            
            # Handle different message types
            if message.type == "ping":
                await manager.send_message(
                    session_id,
                    WSResponse(type="pong", session_id=session_id)
                )
            
            elif message.type == "task":
                # Start new business analysis
                task = message.data.get("task", "")
                if not task.strip():
                    await manager.send_message(
                        session_id,
                        WSResponse(
                            type="error",
                            data={"error": "Task cannot be empty"},
                            session_id=session_id
                        )
                    )
                    continue
                
                task_id = f"ws-task-{uuid.uuid4().hex[:12]}"
                
                # Reset session state for new task
                manager.update_session_state(session_id, {
                    "collected_answers": {},
                    "current_task": task,
                    "task_id": task_id,
                    "task_count": manager.get_session_state(session_id).get("task_count", 0) + 1
                })
                
                # Execute business agent
                try:
                    result = await peer_agent.business_agent.execute(
                        task=task,
                        session_id=session_id,
                        task_id=task_id
                    )
                    
                    # Store in memory
                    memory.add_interaction(
                        session_id,
                        task,
                        json.dumps(result.get("data", result), default=str)[:500]
                    )
                    
                    # Send response
                    if result.get("type") == "questions":
                        questions_data = result.get("data", {})
                        if hasattr(questions_data, "model_dump"):
                            questions_data = questions_data.model_dump()
                        
                        manager.update_session_state(session_id, {
                            "current_questions": questions_data.get("questions", [])
                        })
                        
                        await manager.send_message(
                            session_id,
                            WSResponse(
                                type="questions",
                                data=questions_data,
                                session_id=session_id,
                                task_id=task_id
                            )
                        )
                    else:
                        diagnosis_data = result.get("data", {})
                        if hasattr(diagnosis_data, "model_dump"):
                            diagnosis_data = diagnosis_data.model_dump()
                        
                        await manager.send_message(
                            session_id,
                            WSResponse(
                                type="diagnosis",
                                data=diagnosis_data,
                                session_id=session_id,
                                task_id=task_id
                            )
                        )
                
                except Exception as e:
                    logger.error(f"Business analysis failed: {e}")
                    await manager.send_message(
                        session_id,
                        WSResponse(
                            type="error",
                            data={"error": str(e)},
                            session_id=session_id,
                            task_id=task_id
                        )
                    )
            
            elif message.type == "answer":
                # Process answers to questions
                answers = message.data.get("answers", {})
                state = manager.get_session_state(session_id)
                
                if not answers:
                    await manager.send_message(
                        session_id,
                        WSResponse(
                            type="error",
                            data={"error": "Answers cannot be empty"},
                            session_id=session_id
                        )
                    )
                    continue
                
                # Merge with existing answers
                collected = state.get("collected_answers", {})
                collected.update(answers)
                manager.update_session_state(session_id, {"collected_answers": collected})
                
                task_id = state.get("task_id", f"ws-task-{uuid.uuid4().hex[:12]}")
                original_task = state.get("current_task", "Continue analysis")
                
                # Continue analysis with answers
                try:
                    result = await peer_agent.business_agent.execute(
                        task=original_task,
                        collected_answers=collected,
                        session_id=session_id,
                        task_id=task_id
                    )
                    
                    # Store in memory
                    memory.add_interaction(
                        session_id,
                        json.dumps(answers),
                        json.dumps(result.get("data", result), default=str)[:500]
                    )
                    
                    # Send response
                    if result.get("type") == "questions":
                        questions_data = result.get("data", {})
                        if hasattr(questions_data, "model_dump"):
                            questions_data = questions_data.model_dump()
                        
                        manager.update_session_state(session_id, {
                            "current_questions": questions_data.get("questions", [])
                        })
                        
                        await manager.send_message(
                            session_id,
                            WSResponse(
                                type="questions",
                                data=questions_data,
                                session_id=session_id,
                                task_id=task_id
                            )
                        )
                    else:
                        diagnosis_data = result.get("data", {})
                        if hasattr(diagnosis_data, "model_dump"):
                            diagnosis_data = diagnosis_data.model_dump()
                        
                        await manager.send_message(
                            session_id,
                            WSResponse(
                                type="diagnosis",
                                data=diagnosis_data,
                                session_id=session_id,
                                task_id=task_id
                            )
                        )
                
                except Exception as e:
                    logger.error(f"Answer processing failed: {e}")
                    await manager.send_message(
                        session_id,
                        WSResponse(
                            type="error",
                            data={"error": str(e)},
                            session_id=session_id
                        )
                    )
            
            else:
                await manager.send_message(
                    session_id,
                    WSResponse(
                        type="error",
                        data={"error": f"Unknown message type: {message.type}"},
                        session_id=session_id
                    )
                )
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Client disconnected: session={session_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)


@router.websocket("/agent/{session_id}")
async def agent_websocket(
    websocket: WebSocket,
    session_id: str
):
    """
    General WebSocket endpoint for all agent types.
    
    Message Types (Client -> Server):
    - task: Execute a task (auto-routed or direct)
    - ping: Keep-alive ping
    
    The task data should include:
    - task: The task description
    - agent_type: Optional, one of 'code', 'content', 'business' (auto-routes if not specified)
    """
    await manager.connect(websocket, session_id)
    peer_agent = PeerAgent(session_id=session_id)
    
    try:
        await manager.send_message(
            session_id,
            WSResponse(
                type="ack",
                data={"message": "Connected to PeerAgent"},
                session_id=session_id
            )
        )
        
        while True:
            raw_data = await websocket.receive_text()
            
            try:
                message = WSMessage.model_validate_json(raw_data)
            except Exception as e:
                await manager.send_message(
                    session_id,
                    WSResponse(
                        type="error",
                        data={"error": f"Invalid message format: {e}"},
                        session_id=session_id
                    )
                )
                continue
            
            if message.type == "ping":
                await manager.send_message(
                    session_id,
                    WSResponse(type="pong", session_id=session_id)
                )
            
            elif message.type == "task":
                task = message.data.get("task", "")
                agent_type = message.data.get("agent_type")
                
                if not task.strip():
                    await manager.send_message(
                        session_id,
                        WSResponse(
                            type="error",
                            data={"error": "Task cannot be empty"},
                            session_id=session_id
                        )
                    )
                    continue
                
                task_id = f"ws-task-{uuid.uuid4().hex[:12]}"
                
                try:
                    if agent_type:
                        result = await peer_agent.execute_with_agent_type(
                            task=task,
                            agent_type=agent_type,
                            session_id=session_id,
                            task_id=task_id
                        )
                    else:
                        result = await peer_agent.execute(
                            task=task,
                            session_id=session_id,
                            task_id=task_id
                        )
                    
                    await manager.send_message(
                        session_id,
                        WSResponse(
                            type="result",
                            data=result,
                            session_id=session_id,
                            task_id=task_id
                        )
                    )
                
                except Exception as e:
                    logger.error(f"Task execution failed: {e}")
                    await manager.send_message(
                        session_id,
                        WSResponse(
                            type="error",
                            data={"error": str(e)},
                            session_id=session_id,
                            task_id=task_id
                        )
                    )
            
            else:
                await manager.send_message(
                    session_id,
                    WSResponse(
                        type="error",
                        data={"error": f"Unknown message type: {message.type}"},
                        session_id=session_id
                    )
                )
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)


@router.get("/connections")
async def get_connection_stats():
    """Get WebSocket connection statistics."""
    return {
        "active_connections": manager.connection_count,
        "sessions": list(manager.active_connections.keys())
    }
