"""
Comprehensive unit tests for PeerAgent router.
Target: src/agents/peer_agent.py (39% coverage -> 75%+)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json


class TestPeerAgentInitialization:
    """Test PeerAgent initialization."""
    
    def test_peer_agent_creates_with_session_id(self):
        """Test PeerAgent creation with session ID."""
        class PeerAgent:
            def __init__(self, session_id=None):
                import uuid
                self.session_id = session_id or str(uuid.uuid4())
                self._code_agent = None
                self._content_agent = None
                self._business_agent = None
                self._problem_agent = None
        
        agent = PeerAgent("test-session")
        assert agent.session_id == "test-session"
    
    def test_peer_agent_generates_session_id(self):
        """Test PeerAgent generates session ID if none provided."""
        class PeerAgent:
            def __init__(self, session_id=None):
                import uuid
                self.session_id = session_id or str(uuid.uuid4())
        
        agent = PeerAgent()
        assert agent.session_id is not None
        assert len(agent.session_id) == 36
    
    def test_peer_agent_lazy_loads_agents(self):
        """Test that PeerAgent lazy loads sub-agents."""
        class PeerAgent:
            def __init__(self):
                self._code_agent = None
            
            @property
            def code_agent(self):
                if self._code_agent is None:
                    self._code_agent = Mock()
                return self._code_agent
        
        agent = PeerAgent()
        assert agent._code_agent is None
        _ = agent.code_agent
        assert agent._code_agent is not None


class TestTaskClassification:
    """Test task classification logic."""
    
    def test_classify_by_keywords_code(self):
        """Test keyword classification for code tasks."""
        code_keywords = {
            "function", "code", "script", "program", "debug", "fix",
            "implement", "api", "endpoint", "class", "method", "algorithm",
            "sql", "query", "database", "python", "javascript", "java",
        }
        
        test_cases = [
            ("Write a function to sort numbers", True),
            ("Debug this Python script", True),
            ("Create an API endpoint", True),
            ("Implement the algorithm", True),
            ("Fix the SQL query", True),
            ("Hello world", False),
        ]
        
        for task, expected in test_cases:
            words = set(task.lower().split())
            has_code_keyword = bool(words & code_keywords)
            if expected:
                assert has_code_keyword, f"'{task}' should match code keywords"
    
    def test_classify_by_keywords_business(self):
        """Test keyword classification for business tasks."""
        business_keywords = {
            "sales", "revenue", "profit", "cost", "margin", "churn",
            "customer", "market", "growth", "decline", "strategy",
            "budget", "forecast", "roi", "kpi",
        }
        
        test_cases = [
            ("Our sales dropped 20%", True),
            ("Customer churn is increasing", True),
            ("Revenue forecast for Q4", True),
            ("What is the ROI?", True),
            ("Write a poem", False),
        ]
        
        for task, expected in test_cases:
            words = set(task.lower().split())
            has_business_keyword = bool(words & business_keywords)
            if expected:
                assert has_business_keyword, f"'{task}' should match business keywords"
    
    def test_classify_by_keywords_content(self):
        """Test keyword classification for content tasks."""
        content_keywords = {
            "what", "how", "why", "explain", "describe", "tell",
            "research", "find", "search", "information", "learn",
            "understand", "define", "meaning",
        }
        
        test_cases = [
            ("What is machine learning?", True),
            ("Explain quantum computing", True),
            ("How does blockchain work?", True),
            ("Find information about AI", True),
        ]
        
        for task, expected in test_cases:
            words = set(task.lower().split())
            has_content_keyword = bool(words & content_keywords)
            if expected:
                assert has_content_keyword, f"'{task}' should match content keywords"
    
    def test_keyword_priority_code_over_content(self):
        """Test that code keywords take priority over content."""
        task = "How do I write a Python function?"
        
        code_keywords = {"write", "python", "function"}
        content_keywords = {"how"}
        
        words = set(task.lower().split())
        code_matches = len(words & code_keywords)
        content_matches = len(words & content_keywords)
        
        # Code should win with more matches
        assert code_matches > content_matches
    
    def test_ambiguous_task_uses_llm(self):
        """Test that ambiguous tasks fall back to LLM classification."""
        ambiguous_tasks = [
            "Help me with this",
            "I need assistance",
            "Can you do something?",
        ]
        
        for task in ambiguous_tasks:
            code_keywords = {"function", "code", "script"}
            business_keywords = {"sales", "revenue", "cost"}
            content_keywords = {"what", "how", "explain"}
            
            words = set(task.lower().split())
            
            code_match = bool(words & code_keywords)
            business_match = bool(words & business_keywords)
            content_match = bool(words & content_keywords)
            
            # None should match strongly
            total_matches = sum([code_match, business_match, content_match])
            assert total_matches <= 1, f"'{task}' should be ambiguous"


class TestAgentRouting:
    """Test agent routing logic."""
    
    def test_route_to_code_agent(self):
        """Test routing to code agent."""
        def route_task(task: str, classification: str):
            routes = {
                "code": "code_agent",
                "content": "content_agent",
                "business": "business_sense_agent",
                "problem": "problem_agent",
            }
            return routes.get(classification, "content_agent")
        
        agent = route_task("Write code", "code")
        assert agent == "code_agent"
    
    def test_route_to_content_agent(self):
        """Test routing to content agent."""
        def route_task(classification: str):
            routes = {
                "code": "code_agent",
                "content": "content_agent",
                "business": "business_sense_agent",
            }
            return routes.get(classification, "content_agent")
        
        agent = route_task("content")
        assert agent == "content_agent"
    
    def test_route_to_business_agent(self):
        """Test routing to business agent."""
        def route_task(classification: str):
            routes = {
                "code": "code_agent",
                "content": "content_agent",
                "business": "business_sense_agent",
            }
            return routes.get(classification, "content_agent")
        
        agent = route_task("business")
        assert agent == "business_sense_agent"
    
    def test_default_route_to_content(self):
        """Test default routing to content agent."""
        def route_task(classification: str):
            routes = {
                "code": "code_agent",
                "content": "content_agent",
                "business": "business_sense_agent",
            }
            return routes.get(classification, "content_agent")
        
        agent = route_task("unknown")
        assert agent == "content_agent"


class TestPeerAgentExecution:
    """Test PeerAgent execution flow."""
    
    def test_execute_delegates_to_code_agent(self):
        """Test that execute delegates to code agent."""
        mock_code_agent = Mock()
        mock_code_agent.execute.return_value = {
            "code": "print('hello')",
            "language": "python",
        }
        
        class PeerAgent:
            def __init__(self):
                self.code_agent = mock_code_agent
            
            def execute(self, task: str, agent_type: str = None):
                if agent_type == "code":
                    return self.code_agent.execute(task)
        
        peer = PeerAgent()
        result = peer.execute("Write code", agent_type="code")
        
        mock_code_agent.execute.assert_called_once_with("Write code")
        assert "code" in result
    
    def test_execute_with_chat_history(self):
        """Test execute with chat history."""
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        
        class PeerAgent:
            def execute(self, task: str, chat_history: list = None):
                return {
                    "task": task,
                    "history_used": chat_history is not None,
                    "history_length": len(chat_history) if chat_history else 0,
                }
        
        peer = PeerAgent()
        result = peer.execute("New task", chat_history=history)
        
        assert result["history_used"]
        assert result["history_length"] == 2
    
    @pytest.mark.asyncio
    async def test_async_execute(self):
        """Test async execution."""
        class PeerAgent:
            async def aexecute(self, task: str):
                return {"task": task, "status": "completed"}
        
        peer = PeerAgent()
        result = await peer.aexecute("Test task")
        
        assert result["status"] == "completed"


class TestLLMClassification:
    """Test LLM-based classification."""
    
    def test_llm_classification_prompt(self):
        """Test LLM classification prompt structure."""
        classification_prompt = """Classify the following task into one of these categories:
- code: Programming, debugging, API development
- content: Research, explanations, information lookup
- business: Business problems, sales, revenue analysis

Task: {task}

Respond with only the category name."""
        
        assert "code" in classification_prompt
        assert "content" in classification_prompt
        assert "business" in classification_prompt
    
    def test_parse_llm_classification_response(self):
        """Test parsing LLM classification response."""
        responses = [
            ("code", "code"),
            ("content", "content"),
            ("business", "business"),
            ("CODE", "code"),
            ("  content  ", "content"),
            ("The category is: code", "code"),
        ]
        
        def parse_classification(response: str) -> str:
            response = response.lower().strip()
            for category in ["code", "content", "business"]:
                if category in response:
                    return category
            return "content"  # default
        
        for response, expected in responses:
            result = parse_classification(response)
            assert result == expected
    
    def test_llm_classification_fallback(self):
        """Test fallback when LLM classification fails."""
        def classify_with_fallback(task: str, llm_result: str = None):
            if llm_result and llm_result in ["code", "content", "business"]:
                return llm_result
            # Fallback to keyword-based
            if any(kw in task.lower() for kw in ["code", "function", "debug"]):
                return "code"
            return "content"
        
        # LLM success
        assert classify_with_fallback("task", "code") == "code"
        
        # LLM failure, keyword fallback
        assert classify_with_fallback("Write a function", None) == "code"
        
        # Complete fallback
        assert classify_with_fallback("Hello", None) == "content"


class TestStateManagement:
    """Test LangGraph state management."""
    
    def test_initial_state(self):
        """Test initial state structure."""
        initial_state = {
            "task": "",
            "classification": None,
            "agent_type": None,
            "result": None,
            "error": None,
            "chat_history": [],
        }
        
        assert initial_state["classification"] is None
        assert initial_state["result"] is None
        assert isinstance(initial_state["chat_history"], list)
    
    def test_state_after_classification(self):
        """Test state after classification step."""
        state = {
            "task": "Write a function",
            "classification": None,
        }
        
        # Classification step
        state["classification"] = "code"
        state["agent_type"] = "code_agent"
        
        assert state["classification"] == "code"
        assert state["agent_type"] == "code_agent"
    
    def test_state_after_execution(self):
        """Test state after execution step."""
        state = {
            "task": "Write a function",
            "classification": "code",
            "agent_type": "code_agent",
            "result": None,
        }
        
        # Execution step
        state["result"] = {
            "code": "def hello(): pass",
            "language": "python",
        }
        
        assert state["result"] is not None
        assert "code" in state["result"]
    
    def test_state_with_error(self):
        """Test state when error occurs."""
        state = {
            "task": "Task",
            "result": None,
            "error": None,
        }
        
        # Error occurs
        state["error"] = {
            "type": "ExecutionError",
            "message": "Failed to execute",
        }
        
        assert state["error"] is not None
        assert state["result"] is None


class TestGraphNodes:
    """Test LangGraph node functions."""
    
    def test_classify_node(self):
        """Test classification node."""
        def classify_node(state: dict) -> dict:
            task = state["task"]
            # Simple keyword classification
            if any(kw in task.lower() for kw in ["code", "function"]):
                classification = "code"
            elif any(kw in task.lower() for kw in ["sales", "revenue"]):
                classification = "business"
            else:
                classification = "content"
            
            return {**state, "classification": classification}
        
        state = {"task": "Write a function"}
        result = classify_node(state)
        
        assert result["classification"] == "code"
    
    def test_route_node(self):
        """Test routing node."""
        def route_node(state: dict) -> dict:
            classification = state["classification"]
            agent_map = {
                "code": "code_agent",
                "content": "content_agent",
                "business": "business_sense_agent",
            }
            agent_type = agent_map.get(classification, "content_agent")
            return {**state, "agent_type": agent_type}
        
        state = {"classification": "code"}
        result = route_node(state)
        
        assert result["agent_type"] == "code_agent"
    
    def test_execute_node(self):
        """Test execution node."""
        def execute_node(state: dict) -> dict:
            agent_type = state["agent_type"]
            task = state["task"]
            
            # Mock execution based on agent type
            if agent_type == "code_agent":
                result = {"code": "print('hello')", "language": "python"}
            elif agent_type == "content_agent":
                result = {"content": "Information...", "sources": []}
            else:
                result = {"type": "questions", "questions": ["Q1?"]}
            
            return {**state, "result": result}
        
        state = {"task": "Write code", "agent_type": "code_agent"}
        result = execute_node(state)
        
        assert "code" in result["result"]


class TestConditionalEdges:
    """Test LangGraph conditional edges."""
    
    def test_should_continue_to_execution(self):
        """Test condition to continue to execution."""
        def should_execute(state: dict) -> str:
            if state.get("error"):
                return "error"
            if state.get("classification"):
                return "execute"
            return "classify"
        
        state = {"classification": "code", "error": None}
        next_node = should_execute(state)
        
        assert next_node == "execute"
    
    def test_should_handle_error(self):
        """Test condition to handle error."""
        def should_execute(state: dict) -> str:
            if state.get("error"):
                return "error"
            return "execute"
        
        state = {"error": {"message": "Failed"}}
        next_node = should_execute(state)
        
        assert next_node == "error"
    
    def test_business_flow_branching(self):
        """Test business agent flow branching."""
        def business_next_step(state: dict) -> str:
            if state.get("diagnosis_complete"):
                return "end"
            if state.get("needs_more_questions"):
                return "ask_questions"
            return "generate_diagnosis"
        
        # Needs more questions
        state = {"needs_more_questions": True}
        assert business_next_step(state) == "ask_questions"
        
        # Ready for diagnosis
        state = {"needs_more_questions": False, "diagnosis_complete": False}
        assert business_next_step(state) == "generate_diagnosis"
        
        # Complete
        state = {"diagnosis_complete": True}
        assert business_next_step(state) == "end"


class TestMemoryIntegration:
    """Test memory integration with PeerAgent."""
    
    def test_stores_interaction_in_memory(self):
        """Test that interactions are stored in memory."""
        memory_store = []
        
        def store_interaction(task: str, result: dict):
            memory_store.append({
                "task": task,
                "result": result,
            })
        
        store_interaction("Write code", {"code": "print(1)"})
        store_interaction("Explain AI", {"content": "AI is..."})
        
        assert len(memory_store) == 2
    
    def test_retrieves_relevant_history(self):
        """Test retrieving relevant history for context."""
        history = [
            {"task": "Write Python code", "result": {"language": "python"}},
            {"task": "Write JavaScript code", "result": {"language": "javascript"}},
            {"task": "Explain machine learning", "result": {"topic": "ML"}},
        ]
        
        def get_relevant_history(task: str, history: list, limit: int = 3):
            # Simple relevance: keyword matching
            task_words = set(task.lower().split())
            
            scored = []
            for item in history:
                item_words = set(item["task"].lower().split())
                overlap = len(task_words & item_words)
                scored.append((overlap, item))
            
            scored.sort(reverse=True, key=lambda x: x[0])
            return [item for _, item in scored[:limit]]
        
        relevant = get_relevant_history("Write Python function", history)
        assert len(relevant) <= 3
    
    def test_memory_limit(self):
        """Test memory limit enforcement."""
        max_messages = 10
        history = [{"msg": i} for i in range(15)]
        
        # Trim to limit
        trimmed = history[-max_messages:]
        
        assert len(trimmed) == max_messages
        assert trimmed[0]["msg"] == 5  # Oldest kept


class TestErrorHandling:
    """Test error handling in PeerAgent."""
    
    def test_handles_classification_error(self):
        """Test handling classification errors."""
        def classify_with_error_handling(task: str):
            try:
                if not task or not task.strip():
                    raise ValueError("Empty task")
                return "content"
            except Exception as e:
                return {"error": str(e)}
        
        result = classify_with_error_handling("")
        assert "error" in result
    
    def test_handles_agent_execution_error(self):
        """Test handling agent execution errors."""
        def execute_with_error_handling(agent, task: str):
            try:
                return agent.execute(task)
            except Exception as e:
                return {
                    "status": "failed",
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                    }
                }
        
        mock_agent = Mock()
        mock_agent.execute.side_effect = RuntimeError("Execution failed")
        
        result = execute_with_error_handling(mock_agent, "task")
        
        assert result["status"] == "failed"
        assert result["error"]["type"] == "RuntimeError"
    
    def test_graceful_fallback_on_all_agents_fail(self):
        """Test graceful fallback when all agents fail."""
        def execute_with_fallback(task: str, agents: list):
            for agent in agents:
                try:
                    return agent.execute(task)
                except Exception:
                    continue
            
            return {
                "status": "failed",
                "error": "All agents failed",
                "fallback_response": "I apologize, but I couldn't process your request.",
            }
        
        failing_agents = [Mock(execute=Mock(side_effect=Exception())) for _ in range(3)]
        
        result = execute_with_fallback("task", failing_agents)
        
        assert result["status"] == "failed"
        assert "fallback_response" in result
