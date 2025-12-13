# 🤖 PeerAgent - Multi-Agent AI System

> **Intelligent task routing with specialized AI agents powered by LangGraph**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Agents](#-agents)
- [API Documentation](#-api-documentation)
- [Session & Memory](#-session--memory)
- [Testing](#-testing)
- [Configuration](#-configuration)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Design Decisions](#-design-decisions)
- [Prompt Engineering](#-prompt-engineering)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🎯 Overview

PeerAgent is a production-ready multi-agent AI system that intelligently routes user requests to specialized agents. Built with **LangGraph** for orchestration, **FastAPI** for the API layer, and **Redis + Celery** for async task processing.

### What It Does

```
User Request → PeerAgent (Router) → Specialized Agent → Structured Response
```

| Agent | Purpose | Example Tasks |
|-------|---------|---------------|
| 💻 **CodeAgent** | Code generation in any language | "Write a Python function", "Create a SQL query" |
| 📚 **ContentAgent** | Research with source citations | "What is machine learning?", "Latest AI trends" |
| 📈 **BusinessSenseAgent** | Socratic problem diagnosis | "Sales are dropping 20%", "Diagnose customer churn" |
| 🌳 **ProblemStructuringAgent** | MECE problem tree construction | Converts diagnosis to structured analysis |

---

## ✨ Key Features

### Core Capabilities
- 🔀 **Intelligent Routing** - Automatic task classification using keywords + LLM fallback
- 🧠 **Multi-Provider LLM** - OpenAI, Google Gemini, Anthropic with automatic fallback
- 💬 **Session Memory** - Conversation context preserved across interactions
- 🔍 **Web Search** - ContentAgent searches the web with source citations
- 📊 **Socratic Questioning** - BusinessSenseAgent asks clarifying questions before diagnosis

### Production Ready
- ⚡ **Async Processing** - Celery workers for non-blocking task execution
- 🚦 **Rate Limiting** - 10 requests/minute per IP (configurable)
- 📝 **Structured Logging** - MongoDB logging with Pydantic schemas
- 🐳 **Docker Ready** - Full docker-compose setup with all services
- 🔄 **CI/CD** - GitHub Actions pipeline with tests, linting, and deployment

### Developer Experience
- 📖 **Auto-Generated Docs** - Swagger UI and ReDoc at `/docs` and `/redoc`
- 🧪 **Comprehensive Tests** - Unit and integration tests with pytest
- 🎨 **Chat UI** - Streamlit-based chat interface for testing

---

## 🏗 Architecture

### High-Level System View

![System Overview](architecture/graphs/FastAPI%20Agent%20Routing-2025-12-13-094311.png)

The system consists of 5 layers:

| Layer | Components | Purpose |
|-------|------------|---------|
| **Client** | Streamlit UI, REST clients | User interaction |
| **API** | FastAPI + Rate Limiting | Request handling |
| **Queue** | Redis + Celery | Async task processing |
| **Agents** | PeerAgent + Sub-agents | AI task execution |
| **Storage** | MongoDB + Redis | Logging & caching |

### Agent Routing Flow

![Routing Flow](architecture/graphs/FastAPI%20Agent%20Routing-2025-12-13-094436.png)

### LangGraph State Machine

PeerAgent uses LangGraph for stateful workflow orchestration:

```python
# State flows through: START → classify → [agent] → END
PeerAgentState:
  - messages: List[BaseMessage]  # Conversation history
  - task: str                    # Original request
  - classified_type: str         # code/content/business
  - agent_result: Dict           # Final response
```

> 📖 See [architecture/LANGGRAPH.md](architecture/LANGGRAPH.md) for detailed LangGraph documentation

### Business Analysis Flow (Socratic Method)

![Business Flow](architecture/graphs/FastAPI%20Agent%20Routing-2025-12-13-094459.png)

The BusinessSenseAgent follows a 3-phase questioning approach:

1. **Identify** - When did it start? What's the impact? Is it a priority?
2. **Clarify** - Who is affected? What happens if unchanged? Previous attempts?
3. **Diagnose** - Need solution or visibility? What data exists? What is success?

> 📖 See [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) for all diagrams

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Service orchestration |
| OpenAI API Key | - | LLM provider (or Google/Anthropic) |

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/theFellandes/PeerAgent.git
cd PeerAgent

# 2. Create environment file
cp .env.example .env

# 3. Add your API key to .env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# 4. Start all services
docker-compose up --build

# 5. Access the services
#    API:  http://localhost:8000
#    Docs: http://localhost:8000/docs
#    UI:   http://localhost:8501
```

### Option 2: Local Development

```bash
# 1. Clone and enter directory
git clone https://github.com/theFellandes/PeerAgent.git
cd PeerAgent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -e ".[dev,ui]"

# 4. Start MongoDB and Redis (required)
docker run -d -p 27017:27017 --name mongo mongo:7.0
docker run -d -p 6379:6379 --name redis redis:7-alpine

# 5. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 6. Start the API
uvicorn src.api.main:app --reload --port 8000

# 7. (Optional) Start Celery worker
celery -A src.worker.celery_app worker --loglevel=info

# 8. (Optional) Start Streamlit UI
streamlit run ui/streamlit_app.py
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "app": "PeerAgent", "version": "1.0.0"}
```

---

## 🤖 Agents

### CodeAgent

Generates production-ready code in **any programming language** with explanations.

**Supported Languages:** Python, JavaScript, TypeScript, Java, SQL, C++, Go, Rust, Ruby, PHP, Swift, Kotlin, Bash, and more.

```bash
# Request
curl -X POST http://localhost:8000/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a SQL query to find top 10 customers by revenue"}'
```

```json
// Response
{
  "task_id": "task-abc123",
  "status": "completed",
  "result": {
    "agent_type": "code_agent",
    "data": {
      "code": "SELECT customer_id, customer_name, SUM(order_total) as total_revenue\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nGROUP BY customer_id, customer_name\nORDER BY total_revenue DESC\nLIMIT 10;",
      "language": "sql",
      "explanation": "This query joins customers with orders, calculates total revenue per customer, and returns the top 10."
    }
  }
}
```

### ContentAgent

Researches topics using **web search** and provides **source citations**.

```bash
# Request
curl -X POST http://localhost:8000/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "What are the latest trends in AI?"}'
```

```json
// Response
{
  "task_id": "task-def456",
  "status": "completed",
  "result": {
    "agent_type": "content_agent",
    "data": {
      "content": "The latest AI trends include: 1) Large Language Models (LLMs) becoming more efficient...",
      "sources": [
        "https://www.example.com/ai-trends-2024",
        "https://www.research.com/llm-advances"
      ]
    }
  }
}
```

### BusinessSenseAgent

Uses **Socratic questioning** to diagnose business problems before proposing solutions.

**Phase 1: Questions**
```bash
curl -X POST http://localhost:8000/v1/agent/execute/direct/business \
  -H "Content-Type: application/json" \
  -d '{"task": "Our sales dropped 20% this quarter", "session_id": "business-123"}'
```

```json
{
  "type": "questions",
  "data": {
    "questions": [
      "When did you first notice this drop?",
      "What is the measurable impact in revenue?",
      "Is this in your company's TOP 3 priorities?"
    ],
    "category": "problem_identification"
  }
}
```

**Phase 2: Continue with Answers**
```bash
curl -X POST http://localhost:8000/v1/agent/business/continue \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "business-123",
    "answers": {
      "When did it start?": "3 months ago",
      "What is the impact?": "$2M revenue loss",
      "Is it TOP 3?": "Yes, number 1 priority"
    }
  }'
```

**Final Diagnosis Output:**
```json
{
  "type": "diagnosis",
  "data": {
    "customer_stated_problem": "Sales dropped 20% this quarter",
    "identified_business_problem": "Market share erosion due to competitive pressure",
    "hidden_root_risk": "Brand perception degradation among key segments",
    "urgency_level": "Critical"
  }
}
```

### ProblemStructuringAgent

Converts diagnosis into a **MECE Problem Tree** (Mutually Exclusive, Collectively Exhaustive).

```json
{
  "problem_type": "Growth",
  "main_problem": "Declining Sales",
  "root_causes": [
    {
      "cause": "Marketing Inefficiency",
      "sub_causes": ["Wrong targeting", "Weak ad optimization", "Low conversion rate"]
    },
    {
      "cause": "Competitive Pressure",
      "sub_causes": ["Competitors have lower prices", "Competitor products more differentiated"]
    },
    {
      "cause": "Sales Operations",
      "sub_causes": ["Long sales cycle", "Weak lead follow-up", "CRM data issues"]
    }
  ]
}
```

---

## 📡 API Documentation

### Endpoints Overview

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `GET` | `/health` | Health check | None |
| `GET` | `/docs` | Swagger UI | None |
| `POST` | `/v1/agent/execute` | Submit task (auto-route) | 10/min |
| `GET` | `/v1/agent/status/{task_id}` | Get task result | 30/min |
| `POST` | `/v1/agent/execute/direct/{type}` | Direct agent call | 10/min |
| `POST` | `/v1/agent/business/continue` | Continue business Q&A | 10/min |
| `GET` | `/v1/agent/classify?task=...` | Debug classification | None |

### Request/Response Schemas

**TaskExecuteRequest:**
```json
{
  "task": "string (required, min 1 char)",
  "session_id": "string (optional)",
  "context": { "key": "value" }
}
```

**TaskResponse:**
```json
{
  "task_id": "task-abc123",
  "status": "pending | processing | completed | failed",
  "message": "Task submitted successfully"
}
```

**TaskStatusResponse:**
```json
{
  "task_id": "task-abc123",
  "status": "completed",
  "result": { "agent_type": "...", "data": {...} },
  "error": null,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:05Z"
}
```

### Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 400 | `EMPTY_TASK` | Task field is empty or whitespace |
| 400 | `INVALID_AGENT_TYPE` | Unknown agent type in direct call |
| 404 | `TASK_NOT_FOUND` | Task ID doesn't exist |
| 422 | Validation Error | Pydantic validation failed |
| 429 | Rate Limit | Too many requests |
| 500 | `EXECUTION_ERROR` | Agent execution failed |

> 📖 See [architecture/API_NAVIGATION.md](architecture/API_NAVIGATION.md) for complete API guide

---

## 💾 Session & Memory

PeerAgent includes a **session-based memory system** for conversation continuity.

### How It Works

```python
# Each session maintains:
SessionMemory:
  - session_id: str              # Unique identifier
  - messages: List[BaseMessage]  # Conversation history
  - context: Dict[str, Any]      # Custom context data
  - last_accessed: datetime      # For TTL cleanup
```

### Using Sessions

```bash
# First request - create session
curl -X POST http://localhost:8000/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "I am working on a Java project", "session_id": "my-session-123"}'

# Follow-up request - context is preserved
curl -X POST http://localhost:8000/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a class for user authentication", "session_id": "my-session-123"}'
# CodeAgent will generate Java code because it remembers the context!
```

### Memory Features

| Feature | Description |
|---------|-------------|
| **Auto Language Detection** | Remembers programming language from previous messages |
| **Context Window** | Last 10 messages by default (configurable) |
| **TTL Cleanup** | Sessions expire after 60 minutes of inactivity |
| **Thread-Safe** | Singleton pattern with proper isolation |

---

## 🧪 Testing

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_router.py       # Classification tests
│   ├── test_agents.py       # Agent execution tests
│   └── test_memory.py       # Memory system tests
└── integration/             # Integration tests
    └── test_api.py          # API endpoint tests
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_router.py -v

# Run specific test class
pytest tests/unit/test_router.py::TestKeywordClassification -v
```

### Test Categories

| Category | Purpose | Example |
|----------|---------|---------|
| **Classification** | Test keyword + LLM routing | `test_keyword_classify_python_function` |
| **Agent Execution** | Test agent output schemas | `test_execute_returns_code_output` |
| **Language Detection** | Test multi-language support | `test_detect_sql`, `test_detect_java` |
| **Memory** | Test session persistence | `test_memory_store_stores_interactions` |
| **API** | Test HTTP endpoints | `test_execute_valid_task_returns_task_id` |

### Writing New Tests

```python
# tests/unit/test_example.py
import pytest
from unittest.mock import Mock, AsyncMock

class TestMyFeature:
    @pytest.fixture
    def my_agent(self, mock_settings):
        from src.agents.my_agent import MyAgent
        return MyAgent()
    
    @pytest.mark.asyncio
    async def test_my_feature(self, my_agent, mock_settings):
        # Arrange
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=Mock(content="test"))
        my_agent._llm = mock_llm
        
        # Act
        result = await my_agent.execute("test task")
        
        # Assert
        assert result is not None
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | Primary LLM provider |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `LLM_TEMPERATURE` | `0.7` | Response creativity |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `GOOGLE_API_KEY` | - | Google Gemini API key (fallback) |
| `ANTHROPIC_API_KEY` | - | Anthropic Claude API key (fallback) |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection |
| `MONGODB_DB_NAME` | `peeragent` | Database name |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `DEBUG` | `false` | Enable debug logging |

### LLM Provider Fallback

The system automatically falls back to alternative providers:

```
OpenAI (primary) → Google Gemini → Anthropic Claude
```

| Provider | Default Model | Cost (approx) |
|----------|--------------|---------------|
| OpenAI | `gpt-4o-mini` | $0.15/1M tokens |
| Google | `gemini-1.5-flash` | Free tier available |
| Anthropic | `claude-3-sonnet` | $3/1M tokens |

**Configure fallback:**
```bash
# .env file
OPENAI_API_KEY=sk-...       # Primary
GOOGLE_API_KEY=AIza...      # Fallback 1
ANTHROPIC_API_KEY=sk-ant-...  # Fallback 2
```

---

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐  │
│  │  Lint   │ ──▶│  Test   │ ──▶│  Build  │ ──▶│   Deploy    │  │
│  │(ruff)   │    │(pytest) │    │(Docker) │    │(optional)   │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────────┘  │
│                                                                 │
│  Triggers: push to main/develop, PRs to main                   │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

| Stage | Tools | Actions |
|-------|-------|---------|
| **Lint** | ruff, flake8 | Code quality checks |
| **Test** | pytest | Unit + integration tests with Redis/MongoDB services |
| **Build** | Docker | Build & push to GitHub Container Registry |
| **Deploy** | Custom | Deploy to production (configurable) |

### Required Secrets

| Secret | Description |
|--------|-------------|
| `GITHUB_TOKEN` | Auto-provided for container registry |

---

## 📊 Design Decisions

### Why These Technologies?

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Orchestration** | LangGraph | Native state management, conditional routing, visual debugging |
| **Queue** | Redis + Celery | Low latency (~1ms), simple setup, perfect for task queues |
| **Database** | MongoDB | Flexible schema for diverse log structures |
| **LLM** | Multi-provider | Resilience through automatic fallback |
| **UI** | Streamlit | Rapid prototyping, Python-native |

### Why Not Kafka?

| Factor | Redis + Celery | Kafka |
|--------|:-------------:|:-----:|
| **Setup** | ✅ Simple | ❌ Complex (needs Zookeeper) |
| **Latency** | ✅ ~1ms | ~10ms |
| **Our Scale** | ✅ ~100 req/s | Overkill (100K+ req/s) |
| **Memory** | ✅ Low | Medium-High |

> 📖 See [architecture/QUEUE_ANALYSIS.md](architecture/QUEUE_ANALYSIS.md) for detailed analysis

---

## 🎨 Prompt Engineering

### Design Principles

Our prompts follow these best practices:

1. **Clear Role Definition** - Each agent has a specific persona
2. **Structured Output** - JSON schemas with Pydantic validation
3. **Few-Shot Examples** - Include examples in system prompts
4. **Task Decomposition** - Break complex tasks into steps
5. **Error Handling** - Graceful fallbacks for parsing failures

### Example: CodeAgent System Prompt

```python
"""You are an expert software engineer proficient in ALL programming languages.

IMPORTANT: Generate code in the EXACT language the user requests.
- If they ask for Java, write Java code
- If they ask for SQL, write SQL code
- And so on for any language

For each response:
1. Identify the programming language requested
2. Write clean, idiomatic code in THAT language
3. Include proper syntax and conventions
4. Provide a brief explanation

IMPORTANT: Pay attention to the conversation history. If the user mentioned 
they are working with a specific language or framework earlier, use that context."""
```

### Example: BusinessSenseAgent Phases

```python
# Phase 1: Problem Identification
questions = [
    "When did this problem first start?",
    "What measurable impact has it had?",
    "Is this in the company's TOP 3 priorities?"
]

# Phase 2: Scope Clarification
questions = [
    "Who is most affected by this problem?",
    "What happens if nothing changes in 6 months?",
    "Have you tried any solutions before?"
]

# Phase 3: Root Cause Discovery
questions = [
    "Do you need a solution or first need visibility into the cause?",
    "What data/metrics do you currently track?",
    "What does success look like for you?"
]
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Cannot connect to MongoDB/Redis"
```bash
# Ensure services are running
docker ps | grep -E "mongo|redis"

# Start if needed
docker run -d -p 27017:27017 --name mongo mongo:7.0
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

#### 2. "Invalid API Key" errors
```bash
# Check your .env file
cat .env | grep API_KEY

# Verify key format
# OpenAI: sk-...
# Google: AIza...
# Anthropic: sk-ant-...
```

#### 3. Tests failing with "module not found"
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=$PWD

# Or run with pytest properly
python -m pytest tests/ -v
```

#### 4. Rate limit exceeded (429)
```bash
# Default: 10 requests/minute per IP
# Wait 60 seconds or adjust in src/api/routes/agent.py:
# @limiter.limit("10/minute")  # Change this value
```

#### 5. Docker build fails
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Debug Mode

Enable verbose logging:
```bash
# In .env
DEBUG=true

# Or at runtime
DEBUG=true python -m uvicorn src.api.main:app --reload
```

---

## 🤝 Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Commit: `git commit -m "feat: add amazing feature"`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Commit Convention

```
feat: add new feature
fix: resolve bug
docs: update documentation
refactor: improve code structure
test: add tests
chore: maintenance tasks
```

### Adding a New Agent

1. Create `src/agents/my_agent.py`:
```python
from src.agents.base import BaseAgent

class MyAgent(BaseAgent):
    @property
    def agent_type(self) -> str:
        return "my_agent"
    
    @property
    def system_prompt(self) -> str:
        return "You are a specialized agent..."
    
    async def execute(self, task: str, **kwargs):
        # Implementation
        pass
```

2. Register in `peer_agent.py` keywords and routing
3. Add tests in `tests/unit/test_my_agent.py`
4. Update documentation

---

## 📁 Project Structure

```
PeerAgent/
├── 📂 src/
│   ├── 📂 agents/              # AI Agents
│   │   ├── base.py             # BaseAgent (abstract)
│   │   ├── peer_agent.py       # Router (LangGraph)
│   │   ├── code_agent.py       # Code generation
│   │   ├── content_agent.py    # Research
│   │   ├── business_agent.py   # Diagnosis
│   │   └── problem_agent.py    # Problem tree
│   ├── 📂 api/                 # FastAPI
│   │   ├── main.py             # App factory
│   │   └── routes/             # Endpoints
│   ├── 📂 models/              # Pydantic schemas
│   │   ├── requests.py         # Input models
│   │   ├── responses.py        # Output models
│   │   └── agents.py           # Agent output schemas
│   ├── 📂 worker/              # Celery tasks
│   │   ├── celery_app.py       # Celery config
│   │   └── tasks.py            # Task definitions
│   ├── 📂 utils/               # Helpers
│   │   ├── database.py         # DB connections
│   │   ├── logger.py           # Logging
│   │   └── memory.py           # Session memory
│   └── config.py               # Settings
├── 📂 tests/                   # Pytest
│   ├── conftest.py             # Fixtures
│   ├── unit/                   # Unit tests
│   └── integration/            # API tests
├── 📂 ui/                      # Streamlit
│   └── streamlit_app.py        # Chat UI
├── 📂 architecture/            # Documentation
│   ├── ARCHITECTURE.md         # System design
│   ├── API_NAVIGATION.md       # API guide
│   ├── LANGGRAPH.md            # LangGraph docs
│   ├── QUEUE_ANALYSIS.md       # Queue decision
│   └── graphs/                 # Diagrams
├── 📂 .github/workflows/       # CI/CD
│   └── ci.yml                  # Pipeline
├── 📄 docker-compose.yml       # Services
├── 📄 Dockerfile               # API image
├── 📄 Dockerfile.worker        # Worker image
├── 📄 Dockerfile.ui            # UI image
├── 📄 pyproject.toml           # Dependencies
├── 📄 requirements.txt         # Pip requirements
├── 📄 .env.example             # Env template
└── 📄 README.md                # This file
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Streamlit](https://streamlit.io/) - UI framework

---

<div align="center">
  <b>Built with ❤️ using LangGraph, FastAPI, and OpenAI</b>
  <br><br>
  <a href="https://github.com/theFellandes/PeerAgent/issues">Report Bug</a>
  ·
  <a href="https://github.com/theFellandes/PeerAgent/issues">Request Feature</a>
</div>