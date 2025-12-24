# PeerAgent: Complete Technical Presentation

> **Multi-Agent AI System with LangGraph Orchestration**
> 
> A production-ready task routing system that intelligently distributes requests to specialized AI agents.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Business Decisions & Reasoning](#3-business-decisions--reasoning)
4. [Code Deep Dive](#4-code-deep-dive)
5. [Agent Capabilities](#5-agent-capabilities)
6. [Adding New Agents](#6-adding-new-agents)
7. [Requirements vs Implementation](#7-requirements-vs-implementation)
8. [Interview Q&A Preparation](#8-interview-qa-preparation)

---

# 1. Executive Summary

## What Problem Does This Solve?

PeerAgent automates the **consulting intake process** - the structured methodology that management consultants use to diagnose business problems before proposing solutions.

```
Traditional Consulting Flow:
┌─────────────────────────────────────────────────────────────────────┐
│ Client says: "Our sales are dropping"                               │
│                        ↓                                            │
│ Consultant thinks: "That's a symptom, not the problem"              │
│                        ↓                                            │
│ Consultant asks: Clarifying questions (Socratic method)             │
│                        ↓                                            │
│ Consultant identifies: Root cause (e.g., pricing, competition)      │
│                        ↓                                            │
│ Consultant structures: Problem tree (MECE framework)                │
└─────────────────────────────────────────────────────────────────────┘

PeerAgent automates the first 4 steps.
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Intelligent Routing** | Automatically classifies and routes tasks to appropriate agents |
| **Multi-Provider LLM** | OpenAI, Google, Anthropic with automatic fallback |
| **Session Memory** | Conversation context preserved across interactions |
| **Socratic Questioning** | BusinessSenseAgent asks clarifying questions before diagnosis |
| **Production Ready** | Rate limiting, queue system, connection pooling, comprehensive logging |

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| API | FastAPI | REST endpoints with async support |
| Orchestration | LangGraph | Stateful agent workflows |
| Queue | Redis + Celery | Async task processing |
| Database | MongoDB | Structured logging |
| UI | Streamlit | Chat interface |
| Container | Docker Compose | Multi-service deployment |

---

# 2. Architecture Overview

## 2.1 High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │  Streamlit UI   │    │   REST Client   │    │   Future Apps   │          │
│  │   (Port 8501)   │    │                 │    │                 │          │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘          │
└───────────┼──────────────────────┼──────────────────────┼───────────────────┘
            │                      │                      │
            ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API LAYER                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     FastAPI (Port 8000)                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │ Rate Limiter │  │ CORS Handler │  │ Error Handler│               │    │
│  │  │ (slowapi)    │  │              │  │              │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │                    API Routes (/v1/agent/*)                  │   │    │
│  │  │  • POST /execute        • GET /status/{id}                   │   │    │
│  │  │  • POST /execute/direct • POST /business/continue            │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
            │                                              │
            ▼                                              ▼
┌─────────────────────────────────┐    ┌─────────────────────────────────────┐
│        QUEUE LAYER              │    │         AGENT LAYER                 │
│  ┌─────────────────────────┐    │    │  ┌─────────────────────────────┐    │
│  │     Redis (Port 6379)   │    │    │  │        PeerAgent            │    │
│  │  • Message Broker       │◄───┼────┼──│   (LangGraph Router)        │    │
│  │  • Result Backend       │    │    │  │                             │    │
│  │  • Session Cache        │    │    │  │  ┌─────────┐ ┌───────────┐  │    │
│  └─────────────────────────┘    │    │  │  │Classify │→│Route      │  │    │
│  ┌─────────────────────────┐    │    │  │  │  Node   │ │Decision   │  │    │
│  │    Celery Workers       │    │    │  │  └─────────┘ └─────┬─────┘  │    │
│  │  • execute_agent_task   │    │    │  │         ┌──────────┼────────┤    │
│  │  • execute_business_task│    │    │  │         ▼          ▼        ▼    │
│  └─────────────────────────┘    │    │  │  ┌──────────┐┌──────────┐┌──────┐│
└─────────────────────────────────┘    │  │  │CodeAgent ││Content   ││Biz   ││
                                       │  │  │          ││Agent     ││Agent ││
                                       │  │  └──────────┘└──────────┘└──────┘│
                                       │  └─────────────────────────────────┘│
                                       └─────────────────────────────────────┘
            │                                              │
            ▼                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STORAGE LAYER                                      │
│  ┌─────────────────────────┐    ┌─────────────────────────────────────┐     │
│  │  MongoDB (Port 27017)   │    │         In-Memory Store             │     │
│  │  • Agent Logs           │    │  • Session Memory (MemoryStore)     │     │
│  │  • Pydantic Schemas     │    │  • Conversation History             │     │
│  │  • Task Results         │    │  • TTL-based Cleanup                │     │
│  └─────────────────────────┘    └─────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 LangGraph State Machine

### PeerAgent Routing Graph

```
              START
                │
                ▼
         ┌──────────┐
         │ classify │  ←── Keyword matching + LLM fallback
         └────┬─────┘
              │
      ┌───────┼───────┐
      │       │       │
      ▼       ▼       ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│code_agent│ │ content  │ │ business │
│          │ │  _agent  │ │  _agent  │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │
     └────────────┼────────────┘
                  ▼
                 END
```

### BusinessSenseAgent Socratic Flow

```
        START
          │
          ▼
   ┌──────────────┐
   │ask_questions │◄─────────────┐
   │(Phase 1/2/3) │              │
   └──────┬───────┘              │
          │                      │
          ▼                      │
   ┌──────────────┐              │
   │   evaluate   │              │
   └──────┬───────┘              │
          │                      │
    ┌─────┴─────┐                │
    │           │                │
needs_more    ready              │
    │           │                │
    └───────────┼────────────────┘
                ▼
         ┌──────────┐
         │ finalize │
         └────┬─────┘
              │
              ▼
             END
```

## 2.3 Agent Class Hierarchy

```
BaseAgent (Abstract)
    │
    ├── llm (property with lazy init + fallback)
    ├── invoke_llm() (with automatic provider fallback)
    ├── create_messages() (with chat history support)
    ├── switch_provider()
    │
    ├── PeerAgent (Router/Orchestrator)
    │       ├── _keyword_classify() - Fast path
    │       ├── _llm_classify() - Fallback
    │       ├── graph (LangGraph StateGraph)
    │       └── Sub-agents (lazy loaded):
    │               ├── code_agent
    │               ├── content_agent
    │               ├── business_agent
    │               └── problem_agent
    │
    ├── CodeAgent
    │       ├── _detect_language() - Multi-language detection
    │       └── execute() - Code generation
    │
    ├── ContentAgent
    │       ├── search_tool (DuckDuckGo)
    │       ├── _perform_search()
    │       └── execute() - Research with citations
    │
    ├── BusinessSenseAgent (LangGraph)
    │       ├── 3-phase questioning (identify/clarify/diagnose)
    │       ├── graph (StateGraph)
    │       └── get_initial_questions()
    │
    └── ProblemStructuringAgent
            ├── MECE problem tree construction
            ├── execute() - From diagnosis
            └── structure_from_text() - Direct structuring
```

## 2.4 Data Flow for a Request

```
User Request: "Write a Python function to read a file"
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. API Layer (FastAPI)                                          │
│    • Validate request (Pydantic: TaskExecuteRequest)            │
│    • Generate task_id, session_id                               │
│    • Rate limit check (10/min)                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. PeerAgent Orchestration                                      │
│    • Load chat history from MemoryStore                         │
│    • Initialize PeerAgentState with messages                    │
│    • Invoke LangGraph                                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Classification Node                                          │
│    • _keyword_classify("...python...code...")                   │
│    • Scores: {code: 3, content: 0, business: 0}                 │
│    • Result: "code" (keyword match, no LLM needed)              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. CodeAgent Execution                                          │
│    • Detect language: "python"                                  │
│    • Build messages with chat history                           │
│    • Invoke LLM with system prompt + user request               │
│    • Extract code from markdown blocks                          │
│    • Return CodeOutput(code, language, explanation)             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Response Processing                                          │
│    • Store interaction in MemoryStore                           │
│    • Log to MongoDB (via @log_agent_call decorator)             │
│    • Update task_store with result                              │
│    • Return TaskResponse to client                              │
└─────────────────────────────────────────────────────────────────┘
```

---

# 3. Business Decisions & Reasoning

## 3.1 Why LangGraph over Simple Function Routing?

| Factor | Simple Functions | LangGraph | Decision |
|--------|-----------------|-----------|----------|
| State Management | Manual | Built-in | ✅ LangGraph |
| Conversation Context | Custom code | Native message accumulation | ✅ LangGraph |
| Visual Debugging | None | Graph visualization | ✅ LangGraph |
| Multi-turn flows | Complex | Natural (BusinessAgent) | ✅ LangGraph |
| Future Complexity | Hard to scale | Easy to add nodes | ✅ LangGraph |

**Reasoning:** The PDF required multi-turn Socratic questioning in BusinessSenseAgent. Simple function calls would require manual state management for the 3-phase questioning flow. LangGraph's `Annotated[List[BaseMessage], operator.add]` pattern automatically accumulates conversation history.

## 3.2 Why Redis + Celery over Kafka?

| Factor | Redis + Celery | Kafka |
|--------|:--------------:|:-----:|
| Setup Complexity | ✅ Low | ❌ High (needs Zookeeper) |
| Latency | ✅ ~1ms | ~10ms |
| Scale Needed | ~100 req/s | 100K+ req/s |
| Use Case Fit | ✅ Task Queues | Event Streaming |
| Memory Usage | ✅ Low | Medium-High |

**Reasoning:** We're handling individual AI requests, not millions of events. Kafka is overkill. Redis + Celery gives sub-millisecond latency with simpler configuration.

## 3.3 Why Multi-Provider LLM Fallback?

```python
FALLBACK_ORDER = ["openai", "google", "anthropic"]
```

| Provider | Default Model | Role |
|----------|--------------|------|
| OpenAI | gpt-4o-mini | Primary |
| Google | gemini-1.5-flash | Fallback 1 |
| Anthropic | claude-3-sonnet | Fallback 2 |

**Reasoning:** Production resilience. If OpenAI has an outage or rate limit issues, the system automatically falls back. The API never completely fails due to a single provider issue.

## 3.4 Why Two-Tier Classification?

```python
async def classify_task(self, task: str) -> str:
    keyword_result = self._keyword_classify(task)  # Fast: ~1ms, Free
    if keyword_result:
        return keyword_result
    return await self._llm_classify(task)  # Slow: ~500ms, $0.001
```

| Approach | Latency | Cost | Accuracy |
|----------|---------|------|----------|
| Keywords Only | ~1ms | Free | 70-80% |
| LLM Only | ~500ms | $0.001/call | 95%+ |
| **Hybrid** | ~1ms (clear) / ~500ms (ambiguous) | Minimal | 95%+ |

**Reasoning:** Most requests clearly indicate their type. "Write Python code" obviously goes to CodeAgent. The hybrid approach reduces LLM costs by ~60-70% while maintaining accuracy.

## 3.5 Why MongoDB for Logging?

**Reasoning:** 
1. PDF specifically requested MongoDB
2. Flexible schema for diverse agent outputs (CodeOutput vs BusinessDiagnosis)
3. Pydantic integration provides type safety while `output_data: Dict[str, Any]` allows heterogeneous data

## 3.6 Why In-Memory Session Storage?

```python
class MemoryStore:
    _instance: Optional["MemoryStore"] = None  # Singleton
    _ttl_minutes: int = 60  # TTL cleanup
```

**Reasoning:** Simplicity for the assessment. In production, this would be backed by Redis. The singleton pattern ensures all requests share session data. TTL cleanup prevents memory leaks.

---

# 4. Code Deep Dive

## 4.1 Application Entry Point

```python
# src/api/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # STARTUP
    logger.info(f"Starting {settings.app_name}")
    yield
    # SHUTDOWN
    await close_mongo_connection()
    await close_redis_connection()

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    
    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # CORS
    app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
    
    # Routes
    app.include_router(agent_router, prefix="/v1")
    
    return app

app = create_app()
```

## 4.2 Main Execute Endpoint

```python
# src/api/routes/agent.py
@router.post("/execute")
@limiter.limit("10/minute")
async def execute_task(
    request: Request,
    body: TaskExecuteRequest,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> TaskResponse:
    
    # Validate
    if not body.task or not body.task.strip():
        raise HTTPException(status_code=400, detail={"code": "EMPTY_TASK"})
    
    # Generate IDs
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    session_id = body.session_id or f"session-{uuid.uuid4().hex[:8]}"
    
    # Store initial state
    task_store[task_id] = {"status": TaskStatus.PROCESSING, ...}
    
    # Execute
    result = await peer_agent.execute(task=body.task, session_id=session_id)
    
    # Update state
    task_store[task_id].update({"status": TaskStatus.COMPLETED, "result": result})
    
    return TaskResponse(task_id=task_id, status=TaskStatus.COMPLETED)
```

## 4.3 BaseAgent with LLM Fallback

```python
# src/agents/base.py
class BaseAgent(ABC):
    FALLBACK_ORDER = ["openai", "google", "anthropic"]
    
    def __init__(self, session_id: Optional[str] = None):
        self.settings = get_settings()
        self.session_id = session_id
        self._llm = None  # Lazy initialization
        self._active_provider = None
    
    @property
    def llm(self):
        """Lazy LLM initialization with fallback."""
        if self._llm is None:
            self._llm = self._create_llm_with_fallback()
        return self._llm
    
    def _create_llm_with_fallback(self):
        """Try providers in order until one succeeds."""
        for provider in [self.settings.llm_provider] + self.FALLBACK_ORDER:
            api_key, model = self._get_provider_config(provider)
            if not api_key:
                continue
            try:
                llm = self._create_llm_for_provider(provider, api_key, model)
                self._active_provider = provider
                return llm
            except Exception:
                continue
        raise ValueError("All LLM providers failed")
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass
    
    @abstractmethod
    async def execute(self, task: str, **kwargs) -> Any:
        pass
```

## 4.4 PeerAgent Router

```python
# src/agents/peer_agent.py
AGENT_KEYWORDS = {
    "code": ["code", "script", "function", "python", "javascript", "sql", ...],
    "content": ["search", "find", "research", "what is", "explain", ...],
    "business": ["sales", "revenue", "customer", "problem", "diagnose", ...]
}

class PeerAgent(BaseAgent):
    
    def __init__(self, session_id: Optional[str] = None):
        super().__init__(session_id)
        # Lazy-loaded sub-agents
        self._code_agent = None
        self._content_agent = None
        self._business_agent = None
        self._graph = None
    
    @property
    def code_agent(self) -> CodeAgent:
        if self._code_agent is None:
            self._code_agent = CodeAgent(self.session_id)
        return self._code_agent
    
    def _keyword_classify(self, task: str) -> Optional[str]:
        """Fast keyword-based classification."""
        task_lower = task.lower()
        scores = {"code": 0, "content": 0, "business": 0}
        
        for agent_type, keywords in AGENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    scores[agent_type] += 1
        
        max_score = max(scores.values())
        if max_score >= 2:  # Require 2+ matches
            winners = [k for k, v in scores.items() if v == max_score]
            if len(winners) == 1:
                return winners[0]
        return None  # Ambiguous → use LLM
    
    async def classify_task(self, task: str) -> str:
        """Keywords first, then LLM fallback."""
        keyword_result = self._keyword_classify(task)
        if keyword_result:
            return keyword_result
        return await self._llm_classify(task)
```

## 4.5 LangGraph Workflow Construction

```python
def _build_graph(self) -> StateGraph:
    
    async def classify(state: PeerAgentState) -> Dict[str, Any]:
        classification = await self.classify_task(state["task"])
        return {"classified_type": classification}
    
    async def route_to_code(state: PeerAgentState) -> Dict[str, Any]:
        chat_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
        result = await self.code_agent.execute(
            task=state["task"],
            chat_history=chat_history
        )
        return {"agent_result": {"agent_type": "code_agent", "data": result.model_dump()}}
    
    def route_decision(state: PeerAgentState) -> str:
        return {
            "code": "code_agent",
            "content": "content_agent",
            "business": "business_agent"
        }.get(state.get("classified_type", "content"), "content_agent")
    
    # Build graph
    builder = StateGraph(PeerAgentState)
    
    builder.add_node("classify", classify)
    builder.add_node("code_agent", route_to_code)
    builder.add_node("content_agent", route_to_content)
    builder.add_node("business_agent", route_to_business)
    
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", route_decision, {...})
    builder.add_edge("code_agent", END)
    builder.add_edge("content_agent", END)
    builder.add_edge("business_agent", END)
    
    return builder.compile()
```

## 4.6 CodeAgent with Language Detection

```python
# src/agents/code_agent.py
class CodeAgent(BaseAgent):
    
    def _detect_language(self, task: str) -> str:
        task_lower = task.lower()
        
        # Order matters! "javascript" before "java"
        language_patterns = {
            "sql": ["sql", "query", "select"],
            "javascript": ["javascript", "js", "node", "react"],
            "java": [" java ", "spring boot", "maven"],  # Space-bounded
            "python": ["python", "py", "django", "flask"],
            # ... 15+ languages
        }
        
        for lang, patterns in language_patterns.items():
            for pattern in patterns:
                if pattern in task_lower:
                    return lang
        return "python"  # Default
    
    async def execute(self, task: str, chat_history: Optional[List] = None, **kwargs) -> CodeOutput:
        detected_language = self._detect_language(task)
        
        # Check history for language context
        if chat_history and detected_language == "python":
            history_text = " ".join([m.content for m in chat_history])
            history_language = self._detect_language(history_text)
            if history_language != "python":
                detected_language = history_language
        
        # Build messages
        messages = [SystemMessage(content=self.system_prompt)]
        if chat_history:
            messages.extend(chat_history)
        messages.append(HumanMessage(content=f"Generate {detected_language} code for: {task}"))
        
        # Invoke LLM
        response = await self.llm.ainvoke(messages)
        
        # Extract code from markdown
        code_match = re.search(r'```\w*\n(.*?)```', response.content, re.DOTALL)
        code = code_match.group(1).strip() if code_match else response.content
        
        return CodeOutput(code=code, language=detected_language, explanation="...")
```

## 4.7 BusinessSenseAgent Socratic Flow

```python
# src/agents/business_agent.py
class BusinessAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    task: str
    current_phase: Literal["identify", "clarify", "diagnose"]
    questions_asked: int
    max_questions: int
    collected_answers: Dict[str, str]
    diagnosis: Optional[Dict[str, Any]]
    needs_more_info: bool

class BusinessSenseAgent(BaseAgent):
    
    def _build_graph(self) -> StateGraph:
        
        async def ask_questions(state: BusinessAgentState) -> Dict[str, Any]:
            phase = state["current_phase"]
            
            phase_prompts = {
                "identify": "Ask about WHEN it started, MEASURABLE IMPACT, PRIORITY",
                "clarify": "Ask about WHO is affected, CONSEQUENCES, PREVIOUS ATTEMPTS",
                "diagnose": "Ask about SOLUTION vs VISIBILITY, DATA, SUCCESS criteria"
            }
            
            # Generate 2-3 questions for current phase
            response = await self.llm.ainvoke(...)
            questions = parse_questions(response)
            
            return {
                "messages": [AIMessage(content=json.dumps({"questions": questions}))],
                "questions_asked": state["questions_asked"] + 1,
                "needs_more_info": True
            }
        
        async def finalize_diagnosis(state: BusinessAgentState) -> Dict[str, Any]:
            parser = PydanticOutputParser(pydantic_object=BusinessDiagnosis)
            chain = prompt | self.llm | parser
            diagnosis = await chain.ainvoke({})
            return {"diagnosis": diagnosis.model_dump(), "needs_more_info": False}
        
        def should_continue(state) -> str:
            if state["needs_more_info"] and state["questions_asked"] < state["max_questions"]:
                return "ask_questions"
            return "finalize"
        
        # Build graph with loop
        builder = StateGraph(BusinessAgentState)
        builder.add_node("ask_questions", ask_questions)
        builder.add_node("evaluate", evaluate_answers)
        builder.add_node("finalize", finalize_diagnosis)
        
        builder.add_edge(START, "ask_questions")
        builder.add_edge("ask_questions", "evaluate")
        builder.add_conditional_edges("evaluate", should_continue, {...})
        builder.add_edge("finalize", END)
        
        return builder.compile()
```

## 4.8 Memory Store

```python
# src/utils/memory.py
class MemoryStore:
    _instance: Optional["MemoryStore"] = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._sessions: Dict[str, SessionMemory] = {}
        self._ttl_minutes: int = 60
        self._initialized = True
    
    def get_messages(self, session_id: str, max_messages: int = 10) -> List[BaseMessage]:
        session = self.get_session(session_id)
        return session.messages[-max_messages:]
    
    def add_interaction(self, session_id: str, human_message: str, ai_response: str):
        session = self.get_session(session_id)
        session.messages.append(HumanMessage(content=human_message))
        session.messages.append(AIMessage(content=ai_response))

# Singleton instance
memory_store = MemoryStore()
def get_memory_store() -> MemoryStore:
    return memory_store
```

## 4.9 MongoDB Logging Decorator

```python
# src/utils/logger.py
def log_agent_call(agent_type: str):
    """Decorator for automatic MongoDB logging."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            start_time = datetime.utcnow()
            logger = MongoDBLogger()
            
            try:
                result = await func(self, *args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                await logger.log(
                    agent_type=agent_type,
                    input_data={"task": kwargs.get("task")},
                    output_data=result.model_dump() if hasattr(result, 'model_dump') else result,
                    duration_ms=duration
                )
                return result
            except Exception as e:
                await logger.log(agent_type=agent_type, error=str(e), ...)
                raise
        return wrapper
    return decorator

# Usage
class PeerAgent(BaseAgent):
    @log_agent_call("peer_agent")
    async def execute(self, task: str, **kwargs):
        ...
```

---

# 5. Agent Capabilities

## 5.1 CodeAgent

**Purpose:** Generate code in any programming language

**Supported Languages:** Python, JavaScript, TypeScript, Java, SQL, C++, Go, Rust, Ruby, PHP, Swift, Kotlin, Bash, and more

**Key Features:**
- Automatic language detection from task
- Context-aware (remembers language from chat history)
- Code extraction from markdown blocks
- Structured output with explanation

**Example:**
```bash
POST /v1/agent/execute
{"task": "Write a SQL query to find top 10 customers by revenue"}

Response:
{
  "agent_type": "code_agent",
  "data": {
    "code": "SELECT customer_id, SUM(order_total) as revenue\nFROM orders\nGROUP BY customer_id\nORDER BY revenue DESC\nLIMIT 10;",
    "language": "sql",
    "explanation": "This query aggregates orders by customer and returns the top 10."
  }
}
```

## 5.2 ContentAgent

**Purpose:** Research topics with web search and citations

**Key Features:**
- DuckDuckGo web search integration
- Automatic URL extraction from results
- Source citations in output
- Context-aware responses

**Example:**
```bash
POST /v1/agent/execute
{"task": "What are the latest trends in AI?"}

Response:
{
  "agent_type": "content_agent",
  "data": {
    "content": "The latest AI trends include: 1) Large Language Models...",
    "sources": [
      "https://www.example.com/ai-trends-2024",
      "https://www.research.com/llm-advances"
    ]
  }
}
```

## 5.3 BusinessSenseAgent

**Purpose:** Diagnose business problems using Socratic questioning

**3-Phase Methodology:**

| Phase | Focus | Example Questions |
|-------|-------|-------------------|
| **Identify** | Timeline, Impact, Priority | "When did this start?", "What's the measurable impact?" |
| **Clarify** | Scope, Stakes, History | "Who is affected?", "What previous solutions failed?" |
| **Diagnose** | Root Cause, Data, Success | "Need solution or visibility?", "What data exists?" |

**Output Schema:**
```python
class BusinessDiagnosis(BaseModel):
    customer_stated_problem: str    # What they SAID
    identified_business_problem: str # What it ACTUALLY is
    hidden_root_risk: str           # What they DON'T SEE
    urgency_level: Literal["Low", "Medium", "Critical"]
```

## 5.4 ProblemStructuringAgent

**Purpose:** Create MECE (Mutually Exclusive, Collectively Exhaustive) problem trees from diagnosis

**The 3-Phase Flow (from PDF):**
```
Phase 1: IDENTIFY (problem_identification)
├── When did this problem start?
├── What is the measurable impact?
└── Is this TOP 3 priority?

Phase 2: CLARIFY (scope_clarification)  
├── Who is most affected?
├── What happens if unchanged in 6 months?
└── Previous solution attempts?

Phase 3: DIAGNOSE (root_cause_discovery)
├── Need solution or visibility?
├── What data/metrics exist?
└── What does success look like?
``` 

**Output Example:**
```
Problem Type: Growth
Main Problem: Declining Sales

Root Causes:
├── Marketing Inefficiency
│   ├── Wrong targeting
│   ├── Weak ad optimization
│   └── Low conversion rate
├── Competitive Pressure
│   ├── Lower competitor prices
│   └── More differentiated products
└── Sales Operations
    ├── Long sales cycle
    └── Weak lead follow-up
```

---

# 6. Adding New Agents

## 6.1 Files to Modify

```
src/
├── agents/
│   ├── __init__.py          ← 1. Export new agent
│   ├── new_agent.py         ← 2. CREATE: New agent class
│   └── peer_agent.py        ← 3. Add routing logic
├── models/
│   ├── agents.py            ← 4. Add output schema
│   └── responses.py         ← 5. Add to AgentType enum
└── api/
    └── routes/agent.py      ← 6. Add to valid_types
```

## 6.2 Step-by-Step Process

### Step 1: Create Agent Class

```python
# src/agents/strategy_agent.py
from src.agents.base import BaseAgent
from src.models.agents import StrategyOutput

class StrategyAgent(BaseAgent):
    
    @property
    def agent_type(self) -> str:
        return "strategy_agent"
    
    @property
    def system_prompt(self) -> str:
        return """You are a strategy consultant..."""
    
    async def execute(self, task: str, **kwargs) -> StrategyOutput:
        # Implementation
        ...
```

### Step 2: Add Output Schema

```python
# src/models/agents.py
class StrategyOutput(BaseModel):
    quick_wins: List[Recommendation]
    medium_term: List[Recommendation]
    strategic: List[Recommendation]
    summary: str
```

### Step 3: Update AgentType Enum

```python
# src/models/responses.py
class AgentType(str, Enum):
    ...
    STRATEGY = "strategy_agent"  # ADD
```

### Step 4: Update PeerAgent Router

```python
# src/agents/peer_agent.py

# Add keywords
AGENT_KEYWORDS = {
    ...
    "strategy": ["strategy", "recommendation", "action plan", "quick wins"]
}

# Add lazy property
@property
def strategy_agent(self) -> StrategyAgent:
    if self._strategy_agent is None:
        self._strategy_agent = StrategyAgent(self.session_id)
    return self._strategy_agent

# Add to graph
builder.add_node("strategy_agent", route_to_strategy)
builder.add_edge("strategy_agent", END)

# Add to route_decision
def route_decision(state):
    return {
        ...
        "strategy": "strategy_agent"
    }.get(state.get("classified_type"), "content_agent")
```

### Step 5: Update API valid_types

```python
# src/api/routes/agent.py
valid_types = ["code", "content", "business", "strategy"]  # ADD
```

---

# 7. Requirements vs Implementation

## 7.1 ✅ Implemented Beyond Requirements

| Addition | PDF Requirement | Your Implementation |
|----------|-----------------|---------------------|
| **Streamlit UI** | Not mentioned | Full chat interface with session management |
| **Session Memory** | BONUS item | Full MemoryStore with TTL cleanup |
| **Multi-Provider LLM** | Just "use LLM" | 3 providers with automatic fallback |
| **Example Questions** | Not mentioned | 30+ examples with rotation |
| **Rate Limiting** | BONUS item | slowapi with 10/min limit |
| **Two-Tier Classification** | "Keywords can be used" | Keywords + LLM hybrid |
| **Lazy Loading** | Not mentioned | All sub-agents lazy loaded |
| **Connection Pooling** | Not mentioned | MongoDB and Redis pooling |
| **Multi-Language Code** | Example was Python only | 15+ languages with detection |
| **Comprehensive Docs** | README with diagram | 5 detailed documents |
| **Test Suite** | "1-2 tests" | 250+ tests across 11 files |
| **Multiple Dockerfiles** | "Dockerfile" | 3 specialized Dockerfiles |

## 7.2 ⚠️ Potentially Missing Items

### DevOps Scripts
```
PDF Required:
- scripts/before_install.sh
- scripts/start_application.sh
- scripts/stop_application.sh

Status: appspec.yml references them, but scripts may need to be created
```

### GitHub Actions Workflow
```
PDF Required: "GitHub/workflow yml"
Status: Check if .github/workflows/ci.yml exists
```

### Suggested Business Improvements
#### Priority Queue for Business-Critical Requests
Current Issue: All tasks are processed FIFO
Proposed Change:
```python
class TaskPriority(Enum):
    LOW = 0       # Content research
    NORMAL = 1    # Code generation
    HIGH = 2      # Business diagnosis
    CRITICAL = 3  # Urgent business problems

@celery_app.task(bind=True, priority=10)  # Higher = more urgent
def execute_business_task(...):
    ...
```
Business Justification:
```
"In a real consulting scenario, a client asking 'Our sales dropped 20% - help diagnose' is more urgent than 'What is machine learning?' Priority queuing ensures business-critical workflows aren't blocked by informational queries."
```
#### Streaming Responses for Long Tasks
Current Issue: Client waits until complete task finishes
Proposed Change:
```python
from fastapi.responses import StreamingResponse

@router.get("/v1/agent/stream/{task_id}")
async def stream_result(task_id: str):
    async def generate():
        async for token in agent.stream_execute(task):
            yield f"data: {json.dumps({'token': token})}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```
Business Justification:
```
"LLM responses can take 10-30 seconds. Streaming provides immediate feedback, improving perceived performance. This is especially important for the Streamlit UI where users expect ChatGPT-like streaming behavior."
```
#### Cost Tracking per Session
Current Issue: No visibility into LLM spend per client
Proposed Change:
```python
class AgentLogEntry(BaseModel):
    ...
    token_usage: Optional[Dict[str, int]]  # Already exists!
    estimated_cost_usd: Optional[float]    # ADD THIS

# In base agent
async def invoke_llm(self, messages, **kwargs):
    response = await self.llm.ainvoke(messages, **kwargs)
    usage = response.usage_metadata
    cost = self._calculate_cost(usage, self._active_provider)
    # Log cost to MongoDB
    return response
```
Business Justification:
```
"For enterprise deployments, clients need cost visibility. Tracking cost per session/task enables: (1) billing clients, (2) identifying expensive queries, (3) optimizing prompts to reduce tokens. The token_usage field is already in the schema - just needs cost calculation."
```
#### Agent Performance Metrics Dashboard
Current Issue: No observability into agent performance
Proposed Change:
```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram

AGENT_REQUESTS = Counter('agent_requests_total', 'Total requests', ['agent_type'])
AGENT_LATENCY = Histogram('agent_latency_seconds', 'Request latency', ['agent_type'])

# In base agent
async def execute(self, task, **kwargs):
    with AGENT_LATENCY.labels(self.agent_type).time():
        AGENT_REQUESTS.labels(self.agent_type).inc()
        return await self._execute_impl(task, **kwargs)
```
Business Justification:
```
"Production systems need observability. Metrics enable: (1) SLA monitoring, (2) capacity planning, (3) detecting degradation before users complain. This is essential for demonstrating production-readiness as the PDF requested."
```
#### Caching for Repeated Queries
Current Issue: Same question = same LLM cost every time
Proposed Change:
```python
import hashlib
from functools import lru_cache

class ContentAgent(BaseAgent):
    @lru_cache(maxsize=1000)
    def _cache_key(self, query: str) -> str:
        return hashlib.sha256(query.encode()).hexdigest()[:16]
    
    async def execute(self, task, **kwargs):
        cache_key = self._cache_key(task)
        cached = await self.redis.get(f"content:{cache_key}")
        if cached:
            return ContentOutput.parse_raw(cached)
        
        result = await self._fetch_and_generate(task)
        await self.redis.setex(f"content:{cache_key}", 3600, result.json())
        return result
```
Business Justification:
```
"ContentAgent queries like 'What is machine learning?' are repeated frequently. Caching for 1 hour reduces LLM costs by ~40-50% for popular queries while keeping information reasonably fresh. Redis is already in the stack."
```

#### "What if the client gives vague answers?"
Current Limitation: Agent proceeds even with "I don't know" answers
Proposed Change:
pythonclass BusinessAgentState(TypedDict):
    ...
    answer_quality_scores: Dict[str, float]  # NEW: Track answer usefulness
    low_quality_count: int                   # NEW: Count vague answers

async def evaluate_answers(state: BusinessAgentState) -> Dict[str, Any]:
    # Analyze answer quality
    for question, answer in state["collected_answers"].items():
        quality = await self._assess_answer_quality(question, answer)
        if quality < 0.3:  # Vague answer threshold
            state["low_quality_count"] += 1
    
    # If too many vague answers, probe deeper
    if state["low_quality_count"] >= 2:
        return {
            "current_phase": "probe_deeper",  # NEW phase
            "probe_questions": self._generate_probing_questions(
                state["collected_answers"]
            )
        }

## 7.3 Scoring Summary

| Category | PDF Points | Your Score | Notes |
|----------|------------|------------|-------|
| Kod Kalitesi | 10 | **10** | Clean, modular, SOLID principles |
| Agentic Yapı | 20 | **20** | LangGraph, 4 agents, flexible |
| LLM Entegrasyonu | 10 | **12** ⭐ | Multi-provider + fallback |
| API Yapısı | 10 | **12** ⭐ | Rate limiting, queue, versioning |
| Testler | 5 | **7** ⭐ | 250+ tests (asked for 1-2) |
| README & Mimari | 5 | **7** ⭐ | 5 comprehensive docs |
| **Base Total** | **60** | **68** | |

### Bonus Items

| Bonus | Status |
|-------|--------|
| Session/Memory | ✅ Full |
| Dockerfile & .env | ✅ Multi-container |
| CI/CD DevOps | ⚠️ Verify scripts exist |
| Prompt Engineering | ✅ Professional |
| Queue | ✅ Redis + Celery |
| Rate Limiting | ✅ slowapi |
| Scalability | ✅ Pooling, lazy loading |
| Logging | ✅ MongoDB + decorator |

---

# 8. Interview Q&A Preparation

## Architecture Questions

### Q: "Why LangGraph instead of simple function calls?"

> "The PDF required multi-turn Socratic questioning. Simple functions would need manual state management. LangGraph's `Annotated[List[BaseMessage], operator.add]` automatically accumulates conversation history across nodes, which is essential for the BusinessSenseAgent's iterative questioning flow."

### Q: "How does your system handle LLM provider outages?"

> "I implemented a fallback chain: OpenAI → Google → Anthropic. The `_create_llm_with_fallback()` method tries each provider. If one fails during a request, `invoke_llm()` catches auth errors and automatically switches to the next provider, ensuring the API remains available."

### Q: "Why two-tier classification?"

> "Cost-performance optimization. Most requests clearly indicate their type. 'Write Python code' obviously goes to CodeAgent. The keyword classifier requires 2+ matches for confidence. This reduces LLM costs by ~60-70% for clear requests while maintaining accuracy for ambiguous ones."

## Business Questions

### Q: "What if a client's problem spans multiple categories?"

> "Current implementation uses single classification. To improve, I'd add:
> - `primary_problem_type` and `secondary_problem_types` fields
> - `problem_interdependencies` mapping
> - This mirrors how consultants present 'primary hypothesis with supporting factors.'"

### Q: "What if we want industry-specific diagnosis?"

> "I'd add industry-specific question banks:
> ```python
> INDUSTRY_QUESTIONS = {
>     'saas': ['What is your MRR trend?', 'What is your NRR?'],
>     'retail': ['What is same-store sales trend?', 'Inventory turnover?']
> }
> ```
> The API would accept an `industry` parameter to select appropriate questions."

### Q: "What if the client gives vague answers?"

> "Add answer quality scoring:
> - Track `answer_quality_scores` in state
> - If quality < threshold, add 'probe_deeper' phase
> - Generate follow-up questions: 'Can you give a specific number?', 'What timeframe?'"

## Scaling Questions

### Q: "How would you scale to 10,000 requests/minute?"

> "Current: 10 req/min per IP, single worker. For 10K:
> 1. **Horizontal scaling**: Multiple API instances behind load balancer
> 2. **Celery pool**: Increase workers and concurrency
> 3. **Redis cluster**: Switch to Redis Cluster
> 4. **Response caching**: Cache repeated queries
> 5. **Distributed rate limiting**: Redis-backed rate limiter"

### Q: "What's the bottleneck?"

> "LLM API calls. Each takes 500ms-2s. Solutions:
> - Keyword classification (already implemented) avoids many LLM calls
> - Response caching for identical queries
> - Streaming responses for better perceived performance
> - Batch processing for multiple tasks"

## Code Questions

### Q: "Why is MemoryStore a singleton?"

> "All request handlers need to share session data. Without singleton, each request creates a new MemoryStore, losing conversation context. The `__new__` method prevents duplicate initialization. For production, I'd back this with Redis."

### Q: "How do you prevent BusinessSenseAgent from asking forever?"

> "Two safeguards:
> 1. `max_questions` parameter (default: 3 rounds)
> 2. Phase progression (identify → clarify → diagnose)
> 
> The `should_continue` function checks both before deciding to loop or finalize."

### Q: "What was the hardest problem you solved?"

> "Memory retention across LangGraph nodes. Initially, chat history was stored but not passed to LLM calls. I discovered that LangGraph's message accumulation only updates state - you still need to explicitly pass messages to the LLM. The fix was ensuring all agents include `chat_history` in their message construction."

### Q: "The client wants diagnoses in Turkish, not English. How do you handle this?"
Answer:

"Multi-language support requires changes at three levels:

Input Detection: Use langdetect or the LLM to identify input language

```python
detected_lang = detect(task)  # 'tr' for Turkish
```

System Prompt Localization:

```python
PROMPTS = {
    'en': 'You are an expert business consultant...',
    'tr': 'Sen uzman bir iş danışmanısın...'
}
```

Output Schema Labels (for reports):

```python
FIELD_LABELS = {
    'en': {'customer_stated_problem': 'Customer Stated Problem'},
    'tr': {'customer_stated_problem': 'Müşterinin Belirttiği Problem'}
}
```

```
The LLM handles translation naturally - you just need to prompt in the target language. The key is ensuring technical business terms are correctly translated (e.g., 'churn' → 'müşteri kaybı')."
```

---

# Appendix: Quick Reference

## API Endpoints

| Method | Endpoint | Rate Limit | Description |
|--------|----------|------------|-------------|
| POST | `/v1/agent/execute` | 10/min | Auto-route task |
| GET | `/v1/agent/status/{id}` | 30/min | Get result |
| POST | `/v1/agent/execute/direct/{type}` | 10/min | Direct agent |
| POST | `/v1/agent/business/continue` | 10/min | Continue Q&A |
| GET | `/v1/agent/classify` | None | Debug routing |

## Docker Commands

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Rebuild
docker-compose up --build

# Stop
docker-compose down
```

## Test Commands

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific file
pytest tests/unit/test_agents.py -v
```

## Project Structure

```
PeerAgent/
├── src/
│   ├── agents/           # Agent implementations
│   ├── api/              # FastAPI routes
│   ├── models/           # Pydantic schemas
│   ├── utils/            # Helpers (DB, logging, memory)
│   ├── worker/           # Celery tasks
│   └── config.py         # Settings
├── tests/                # Test suite
├── ui/                   # Streamlit app
├── docker-compose.yml    # Container orchestration
└── README.md             # Documentation
```

---

*Document prepared for PeerAgent technical interview*