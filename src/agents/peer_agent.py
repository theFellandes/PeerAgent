# PeerAgent - The master router/orchestrator
from typing import Any, Dict, Literal, Optional, List, Annotated
import operator
import re
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from src.agents.base import BaseAgent
from src.agents.code_agent import CodeAgent
from src.agents.content_agent import ContentAgent
from src.agents.business_agent import BusinessSenseAgent
from src.agents.problem_agent import ProblemStructuringAgent
from src.agents.summary_agent import SummaryAgent
from src.agents.translation_agent import TranslationAgent
from src.agents.email_agent import EmailAgent
from src.agents.data_agent import DataAnalysisAgent
from src.agents.competitor_agent import CompetitorAgent
from src.models.responses import AgentType
from src.utils.logger import log_agent_call, get_logger
from src.utils.memory import get_memory_store


class PeerAgentState(TypedDict):
    """State for the PeerAgent orchestrator."""
    messages: Annotated[List[BaseMessage], operator.add]
    task: str
    session_id: Optional[str]
    task_id: Optional[str]
    classified_type: Optional[str]
    agent_result: Optional[Dict[str, Any]]
    error: Optional[str]


# Keywords for quick classification (fallback if LLM fails)
AGENT_KEYWORDS = {
    "code": [
        "code", "script", "function", "program", "python", "javascript", "java",
        "write", "implement", "create a", "debug", "fix code", "algorithm",
        "class", "method", "api", "database query", "sql", "html", "css",
        "typescript", "react", "vue", "angular", "backend", "frontend"
    ],
    "content": [
        "search", "find", "research", "what is", "explain", "how does",
        "information about", "tell me about", "describe",
        "news about", "latest", "current", "article", "content about"
    ],
    "business": [
        "sales", "revenue", "profit", "cost", "customer", "market",
        "business problem", "company", "organization", "strategy",
        "growth", "decline", "dropping", "increasing", "operational",
        "efficiency", "process", "workflow", "team", "management",
        "budget", "investment", "roi", "kpi", "metric", "performance",
        "diagnosis", "analyze my", "understand why", "root cause"
    ],
    "summary": [
        "summarize", "summary", "tldr", "condense", "brief", "shorten",
        "key points", "main points", "overview of"
    ],
    "translate": [
        "translate", "translation", "in english", "in spanish", "in french",
        "in german", "in turkish", "to english", "to turkish"
    ],
    "email": [
        "email", "draft email", "write email", "compose email",
        "professional email", "business email", "reply email"
    ],
    "data": [
        "data analysis", "analyze data", "csv", "excel", "spreadsheet",
        "statistics", "dataset", "data insights", "trends in data"
    ],
    "competitor": [
        "competitor", "competition", "market analysis", "swot",
        "competitive analysis", "rival", "industry analysis"
    ]
}


class PeerAgent(BaseAgent):
    """
    Master orchestrator agent that routes tasks to appropriate sub-agents.
    
    Uses a combination of:
    1. Keyword matching (fast, reliable for clear cases)
    2. LLM classification (for ambiguous cases)
    
    Routes to:
    - CodeAgent: Programming and development tasks
    - ContentAgent: Research and information gathering
    - BusinessSenseAgent: Business problem analysis
    """
    
    def __init__(self, session_id: Optional[str] = None):
        super().__init__(session_id)
        # Initialize sub-agents
        self._code_agent = None
        self._content_agent = None
        self._business_agent = None
        self._problem_agent = None
        self._summary_agent = None
        self._translation_agent = None
        self._email_agent = None
        self._data_agent = None
        self._competitor_agent = None
        self._graph = None
    
    @property
    def agent_type(self) -> str:
        return "peer_agent"
    
    @property
    def system_prompt(self) -> str:
        return """You are an intelligent task router. Your job is to classify incoming tasks into one of these categories:

1. CODE: Tasks that require writing, debugging, or explaining code
   Examples: "Write a Python function", "Debug this script", "Create an API endpoint"

2. CONTENT: Tasks that require research, information gathering, or content creation
   Examples: "What is machine learning?", "Find information about X"

3. BUSINESS: Tasks that involve business problem diagnosis, analysis, or consulting
   Examples: "Our sales are dropping", "Help me understand this operational issue"

4. SUMMARY: Tasks that require summarizing text or documents
   Examples: "Summarize this article", "Give me the key points"

5. TRANSLATE: Tasks that require translating text between languages
   Examples: "Translate this to Spanish", "Convert to English"

6. EMAIL: Tasks that require drafting professional emails
   Examples: "Write an email to my client", "Draft a follow-up email"

7. DATA: Tasks that require analyzing data or statistics
   Examples: "Analyze this CSV data", "What trends do you see in this data"

8. COMPETITOR: Tasks that require analyzing competitors or markets
   Examples: "Analyze our competitors", "Market analysis for X"

Respond with ONLY one word: CODE, CONTENT, BUSINESS, SUMMARY, TRANSLATE, EMAIL, DATA, or COMPETITOR"""
    
    # Lazy-load sub-agents
    @property
    def code_agent(self) -> CodeAgent:
        if self._code_agent is None:
            self._code_agent = CodeAgent(self.session_id)
        return self._code_agent
    
    @property
    def content_agent(self) -> ContentAgent:
        if self._content_agent is None:
            self._content_agent = ContentAgent(self.session_id)
        return self._content_agent
    
    @property
    def business_agent(self) -> BusinessSenseAgent:
        if self._business_agent is None:
            self._business_agent = BusinessSenseAgent(self.session_id)
        return self._business_agent
    
    @property
    def problem_agent(self) -> ProblemStructuringAgent:
        if self._problem_agent is None:
            self._problem_agent = ProblemStructuringAgent(self.session_id)
        return self._problem_agent
    
    @property
    def summary_agent(self) -> SummaryAgent:
        if self._summary_agent is None:
            self._summary_agent = SummaryAgent(self.session_id)
        return self._summary_agent
    
    @property
    def translation_agent(self) -> TranslationAgent:
        if self._translation_agent is None:
            self._translation_agent = TranslationAgent(self.session_id)
        return self._translation_agent
    
    @property
    def email_agent(self) -> EmailAgent:
        if self._email_agent is None:
            self._email_agent = EmailAgent(self.session_id)
        return self._email_agent
    
    @property
    def data_agent(self) -> DataAnalysisAgent:
        if self._data_agent is None:
            self._data_agent = DataAnalysisAgent(self.session_id)
        return self._data_agent
    
    @property
    def competitor_agent(self) -> CompetitorAgent:
        if self._competitor_agent is None:
            self._competitor_agent = CompetitorAgent(self.session_id)
        return self._competitor_agent
    
    def _keyword_classify(self, task: str) -> Optional[str]:
        """
        Quick keyword-based classification.
        Returns None if no clear match (should fall back to LLM).
        """
        task_lower = task.lower()
        
        scores = {
            "code": 0, "content": 0, "business": 0,
            "summary": 0, "translate": 0, "email": 0,
            "data": 0, "competitor": 0
        }
        
        for agent_type, keywords in AGENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    scores[agent_type] += 1
        
        # Only return if there's a clear winner
        max_score = max(scores.values())
        if max_score >= 2:  # Require at least 2 keyword matches
            winners = [k for k, v in scores.items() if v == max_score]
            if len(winners) == 1:
                return winners[0]
        
        # For single-keyword matches, check specific cases
        if max_score == 1:
            for agent_type in ["summary", "translate", "email", "data", "competitor"]:
                if scores[agent_type] == 1:
                    return agent_type
        
        return None  # Ambiguous, use LLM
    
    async def _llm_classify(self, task: str) -> str:
        """Use LLM to classify the task."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", f"Classify this task: {task}")
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages(task=task))
            content = response.content.strip().upper()
            
            # Extract classification from response (check specific types first)
            if "SUMMARY" in content:
                return "summary"
            elif "TRANSLATE" in content:
                return "translate"
            elif "EMAIL" in content:
                return "email"
            elif "DATA" in content:
                return "data"
            elif "COMPETITOR" in content:
                return "competitor"
            elif "CODE" in content:
                return "code"
            elif "BUSINESS" in content:
                return "business"
            elif "CONTENT" in content:
                return "content"
            else:
                # Default to content for general queries
                return "content"
        except Exception as e:
            self.logger.error(f"LLM classification failed: {e}")
            return "content"  # Safe default
    
    async def classify_task(self, task: str) -> str:
        """
        Classify a task to determine which agent should handle it.
        Uses keyword matching first, falls back to LLM for ambiguous cases.
        
        Returns:
            "code", "content", or "business"
        """
        # Try keyword classification first (fast)
        keyword_result = self._keyword_classify(task)
        if keyword_result:
            self.logger.info(f"Task classified by keywords: {keyword_result}")
            return keyword_result
        
        # Fall back to LLM classification
        llm_result = await self._llm_classify(task)
        self.logger.info(f"Task classified by LLM: {llm_result}")
        return llm_result
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for task routing."""
        
        async def classify(state: PeerAgentState) -> Dict[str, Any]:
            """Classify the incoming task."""
            task = state["task"]
            classification = await self.classify_task(task)
            return {
                "classified_type": classification,
                "messages": [AIMessage(content=f"Task classified as: {classification}")]
            }
        
        async def route_to_code(state: PeerAgentState) -> Dict[str, Any]:
            """Route to CodeAgent with conversation history."""
            # Extract chat history (all messages except current task)
            chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
            
            result = await self.code_agent.execute(
                task=state["task"],
                session_id=state.get("session_id"),
                task_id=state.get("task_id"),
                chat_history=chat_history
            )
            return {
                "agent_result": {
                    "agent_type": "code_agent",
                    "data": result.model_dump() if hasattr(result, 'model_dump') else result
                },
                "messages": [AIMessage(content=f"Code generated successfully")]
            }
        
        async def route_to_content(state: PeerAgentState) -> Dict[str, Any]:
            """Route to ContentAgent with conversation history."""
            # Extract chat history (all messages except current task)
            chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
            
            result = await self.content_agent.execute(
                task=state["task"],
                session_id=state.get("session_id"),
                task_id=state.get("task_id"),
                chat_history=chat_history
            )
            return {
                "agent_result": {
                    "agent_type": "content_agent",
                    "data": result.model_dump() if hasattr(result, 'model_dump') else result
                },
                "messages": [AIMessage(content=f"Content generated with {len(result.sources)} sources")]
            }
        
        async def route_to_business(state: PeerAgentState) -> Dict[str, Any]:
            """Route to BusinessSenseAgent with conversation history."""
            # Extract chat history (all messages except current task)
            chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
            
            result = await self.business_agent.execute(
                task=state["task"],
                session_id=state.get("session_id"),
                task_id=state.get("task_id"),
                chat_history=chat_history
            )
            # Business agent returns {"type": "questions"/"diagnosis", "data": ...}
            data = result.get("data")
            data_dict = data.model_dump() if hasattr(data, 'model_dump') else data
            return {
                "agent_result": {
                    "agent_type": "business_sense_agent",
                    "type": result.get("type"),
                    "data": data_dict
                },
                "messages": [AIMessage(content=f"Business analysis: {result.get('type')}")]
            }
        
        def route_decision(state: PeerAgentState) -> str:
            """Decide which agent to route to based on classification."""
            classification = state.get("classified_type", "content")
            routing_map = {
                "code": "code_agent",
                "content": "content_agent",
                "business": "business_agent"
            }
            return routing_map.get(classification, "content_agent")
        
        # Build the graph
        builder = StateGraph(PeerAgentState)
        
        # Add nodes
        builder.add_node("classify", classify)
        builder.add_node("code_agent", route_to_code)
        builder.add_node("content_agent", route_to_content)
        builder.add_node("business_agent", route_to_business)
        
        # Add edges
        builder.add_edge(START, "classify")
        builder.add_conditional_edges(
            "classify",
            route_decision,
            {
                "code_agent": "code_agent",
                "content_agent": "content_agent",
                "business_agent": "business_agent"
            }
        )
        builder.add_edge("code_agent", END)
        builder.add_edge("content_agent", END)
        builder.add_edge("business_agent", END)
        
        return builder.compile()
    
    @property
    def graph(self):
        """Lazily build and cache the graph."""
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph
    
    @log_agent_call("peer_agent")
    async def execute(
        self,
        task: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the task by routing to the appropriate sub-agent.
        Uses session memory to maintain conversation context.
        
        Args:
            task: The task description
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            
        Returns:
            Dict containing agent_type and the agent's response data
        """
        self.logger.info(f"PeerAgent processing: {task[:100]}...")
        
        # Get conversation history from memory
        memory = get_memory_store()
        history_messages = []
        if session_id:
            history_messages = memory.get_messages(session_id, max_messages=10)
            self.logger.info(f"Loaded {len(history_messages)} messages from session {session_id}")
        
        # Build messages with history for context
        all_messages = list(history_messages) + [HumanMessage(content=task)]
        
        # Initialize state
        initial_state: PeerAgentState = {
            "messages": all_messages,
            "task": task,
            "session_id": session_id,
            "task_id": task_id,
            "classified_type": None,
            "agent_result": None,
            "error": None
        }
        
        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            
            if final_state.get("agent_result"):
                result = final_state["agent_result"]
                
                # Store interaction in memory
                if session_id:
                    ai_response = str(result.get("data", result))[:500]  # Truncate for memory
                    memory.add_interaction(session_id, task, ai_response)
                
                return result
            else:
                return {
                    "agent_type": "peer_agent",
                    "error": "No result from sub-agent"
                }
        except Exception as e:
            self.logger.error(f"PeerAgent execution failed: {e}")
            return {
                "agent_type": "peer_agent",
                "error": str(e)
            }
    
    async def execute_with_agent_type(
        self,
        task: str,
        agent_type: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute directly with a specific agent type (bypass classification).
        
        Args:
            task: The task description
            agent_type: One of "code", "content", "business"
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            
        Returns:
            Dict containing agent_type and the agent's response data
        """
        self.logger.info(f"Direct execution with {agent_type}: {task[:100]}...")
        
        # Get conversation history from memory for context
        memory = get_memory_store()
        chat_history = []
        if session_id:
            chat_history = memory.get_messages(session_id, max_messages=10)
        
        try:
            if agent_type == "code":
                result = await self.code_agent.execute(
                    task, session_id=session_id, task_id=task_id, chat_history=chat_history
                )
                # Store interaction in memory
                if session_id:
                    memory.add_interaction(session_id, task, str(result.model_dump())[:500])
                return {"agent_type": "code_agent", "data": result.model_dump()}
            elif agent_type == "content":
                result = await self.content_agent.execute(
                    task, session_id=session_id, task_id=task_id, chat_history=chat_history
                )
                if session_id:
                    memory.add_interaction(session_id, task, str(result.model_dump())[:500])
                return {"agent_type": "content_agent", "data": result.model_dump()}
            elif agent_type == "business":
                result = await self.business_agent.execute(
                    task, session_id=session_id, task_id=task_id, chat_history=chat_history
                )
                # Business agent returns {"type": "questions"/"diagnosis", "data": ...}
                data = result.get("data")
                data_dict = data.model_dump() if hasattr(data, 'model_dump') else data
                if session_id:
                    memory.add_interaction(session_id, task, str(result)[:500])
                return {
                    "agent_type": "business_sense_agent",
                    "type": result.get("type"),
                    "data": data_dict
                }
            elif agent_type == "summary":
                result = await self.summary_agent.execute(
                    task, session_id=session_id, task_id=task_id
                )
                if session_id:
                    memory.add_interaction(session_id, task, str(result)[:500])
                return {"agent_type": "summary_agent", "data": result}
            elif agent_type == "translate":
                result = await self.translation_agent.execute(
                    task, session_id=session_id, task_id=task_id
                )
                if session_id:
                    memory.add_interaction(session_id, task, str(result)[:500])
                return {"agent_type": "translation_agent", "data": result}
            elif agent_type == "email":
                result = await self.email_agent.execute(
                    task, session_id=session_id, task_id=task_id
                )
                if session_id:
                    memory.add_interaction(session_id, task, str(result)[:500])
                return {"agent_type": "email_agent", "data": result}
            elif agent_type == "data":
                result = await self.data_agent.execute(
                    task, session_id=session_id, task_id=task_id
                )
                if session_id:
                    memory.add_interaction(session_id, task, str(result)[:500])
                return {"agent_type": "data_analysis_agent", "data": result}
            elif agent_type == "competitor":
                result = await self.competitor_agent.execute(
                    task, session_id=session_id, task_id=task_id
                )
                if session_id:
                    memory.add_interaction(session_id, task, str(result)[:500])
                return {"agent_type": "competitor_agent", "data": result}
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
        except Exception as e:
            self.logger.error(f"Direct execution failed: {e}")
            return {"agent_type": agent_type, "error": str(e)}
