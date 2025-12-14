# 🤖 PeerAgent v2.0 - Multi-Agent AI System

> **Intelligent task routing with specialized AI agents powered by LangGraph**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [What's New in v2.0](#-whats-new-in-v20)
- [Overview](#-overview)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Agents](#-agents)
- [API Documentation](#-api-documentation)
- [WebSocket Support](#-websocket-support)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🆕 What's New in v2.0

### Major Improvements

| Feature | v1.0 | v2.0 |
|---------|------|------|
| **Task Storage** | In-memory dict | ✅ Redis-backed persistent store |
| **Real-time Communication** | HTTP polling | ✅ WebSocket support |
| **CI/CD Pipeline** | Basic | ✅ Comprehensive GitHub Actions |
| **Health Checks** | Simple | ✅ Comprehensive with dependency checks |
| **Integration Tests** | Limited | ✅ Full coverage |
| **Configuration** | Basic | ✅ Enhanced with validation |

### New Features

1. **Redis Task Store** (`src/utils/task_store.py`)
   - Persistent task storage across restarts
   - TTL-based automatic cleanup
   - Task listing and filtering
   - Atomic updates

2. **WebSocket Endpoints** (`src/api/routes/websocket.py`)
   - Real-time business Q&A: `ws://host/ws/business/{session_id}`
   - General agent communication: `ws://host/ws/agent/{session_id}`
   - Ping/pong keep-alive
   - Session state management

3. **Enhanced CI/CD** (`.github/workflows/ci.yml`)
   - Lint → Test → Security → Build → Deploy stages
   - Docker multi-platform builds
   - Coverage reporting
   - Staging and production environments

4. **Comprehensive Tests** (`tests/integration/`)
   - Full API workflow tests
   - Redis task store tests
   - WebSocket communication tests
   - Rate limiting tests

---

## 🎯 Overview

PeerAgent is a production-ready multi-agent AI system that intelligently routes user requests to specialized agents:

| Agent | Purpose | Example Tasks |
|-------|---------|---------------|
| 💻 **CodeAgent** | Code generation in any language | "Write a Python function", "Create SQL query" |
| 📚 **ContentAgent** | Research with citations | "What is machine learning?", "Latest AI trends" |
| 📈 **BusinessSenseAgent** | Socratic problem diagnosis | "Sales are dropping 20%", "Diagnose churn" |
| 🌳 **ProblemAgent** | MECE problem tree | Converts diagnosis to structured analysis |

---

## 🏗 Architecture

### High-Level System View

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  Streamlit UI (8501)  │  WebSocket  │  REST API Clients                 │
└───────────────────────┴─────────────┴───────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API LAYER (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  HTTP Endpoints       │  WebSocket Handlers  │  Rate Limiting (slowapi)  │
│  POST /v1/agent/*     │  ws://*/ws/business  │  10 req/min per IP        │
│  GET /v1/agent/*      │  ws://*/ws/agent     │                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │   Redis   │   │  Celery   │   │  MongoDB  │
            │  (Tasks)  │   │ (Workers) │   │  (Logs)   │
            └───────────┘   └───────────┘   └───────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER (LangGraph)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                         ┌──────────────┐                                │
│                         │  PeerAgent   │                                │
│                         │  (Router)    │                                │
│                         └──────┬───────┘                                │
│              ┌─────────────────┼─────────────────┐                      │
│              ▼                 ▼                 ▼                      │
│       ┌──────────┐      ┌──────────┐      ┌───────────────┐            │
│       │CodeAgent │      │Content   │      │BusinessSense  │            │
│       │          │      │Agent     │      │Agent          │            │
│       └──────────┘      └──────────┘      └───────┬───────┘            │
│                                                   ▼                     │
│                                           ┌───────────────┐            │
│                                           │Problem        │            │
│                                           │Structuring    │            │
│                                           │Agent          │            │
│                                           └───────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

### LangGraph State Machine

```python
class PeerAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    task: str
    session_id: Optional[str]
    classified_type: Optional[str]  # code/content/business
    agent_result: Optional[Dict[str, Any]]

# Flow: START → classify → [code_agent | content_agent | business_agent] → END
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Runtime |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Service orchestration |
| OpenAI API Key | - | LLM provider |

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/theFellandes/PeerAgent.git
cd PeerAgent

# 2. Create environment file
cp .env.example .env

# 3. Add your API key
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# 4. Start all services
docker-compose up -d

# 5. Access the services:
#    API:     http://localhost:8000
#    Docs:    http://localhost:8000/docs
#    UI:      http://localhost:8501
#    Flower:  http://localhost:5555 (monitoring, use --profile monitoring)
```

### Option 2: Local Development

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 2. Install dependencies
pip install -e ".[dev,ui]"

# 3. Start MongoDB and Redis
docker run -d -p 27017:27017 --name mongo mongo:7.0
docker run -d -p 6379:6379 --name redis redis:7-alpine

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Start the API
python main.py

# 6. (Optional) Start Celery worker
celery -A src.worker.celery_app worker --loglevel=info

# 7. (Optional) Start UI
streamlit run ui/streamlit_app.py
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
    "status": "healthy",
    "app": "PeerAgent",
    "version": "2.0.0",
    "checks": {
        "redis": "healthy",
        "mongodb": "healthy"
    }
}
```

---

## 🤖 Agents

### CodeAgent

Generates production-ready code in **any programming language**.

```bash
curl -X POST http://localhost:8000/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a SQL query to find top 10 customers by revenue"}'
```

```json
{
    "agent_type": "code_agent",
    "data": {
        "code": "SELECT customer_id, SUM(amount) as revenue\nFROM orders\nGROUP BY customer_id\nORDER BY revenue DESC\nLIMIT 10;",
        "language": "sql",
        "explanation": "Aggregates orders by customer and returns top 10 by total revenue."
    }
}
```

### ContentAgent

Researches topics with **source citations**.

```bash
curl -X POST http://localhost:8000/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "What are the latest trends in AI?"}'
```

### BusinessSenseAgent

**Socratic questioning** to diagnose business problems.

```bash
# Step 1: Submit problem
curl -X POST http://localhost:8000/v1/agent/execute/direct/business \
  -H "Content-Type: application/json" \
  -d '{"task": "Our sales dropped 20% this quarter", "session_id": "biz-123"}'

# Response: Questions
{
    "type": "questions",
    "data": {
        "questions": [
            "When did you first notice this drop?",
            "Which customer segments are affected?",
            "What is the measurable impact in revenue?"
        ]
    }
}

# Step 2: Continue with answers
curl -X POST http://localhost:8000/v1/agent/business/continue \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "biz-123",
    "answers": {"When did it start?": "3 months ago", "Impact?": "$2M loss"}
  }'

# Response: Diagnosis
{
    "type": "diagnosis",
    "data": {
        "customer_stated_problem": "Sales dropped 20%",
        "identified_business_problem": "Market share erosion",
        "hidden_root_risk": "Brand perception degradation",
        "urgency_level": "Critical"
    }
}
```

---

## 📡 API Documentation

### Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `GET` | `/health` | Comprehensive health check | None |
| `GET` | `/ping` | Simple ping (for load balancers) | None |
| `POST` | `/v1/agent/execute` | Submit task (auto-route) | 10/min |
| `POST` | `/v1/agent/execute/async` | Submit task to queue | 10/min |
| `GET` | `/v1/agent/status/{id}` | Get task result | 30/min |
| `POST` | `/v1/agent/execute/direct/{type}` | Direct agent call | 10/min |
| `GET` | `/v1/agent/tasks` | List tasks | 20/min |
| `GET` | `/v1/agent/classify` | Debug classification | None |
| `GET` | `/v1/agent/stats` | Task statistics | None |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔌 WebSocket Support

### Business Q&A WebSocket

Real-time interaction with BusinessSenseAgent:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/business/my-session');

ws.onopen = () => {
    // Start analysis
    ws.send(JSON.stringify({
        type: 'task',
        data: { task: 'Our sales dropped 20%' }
    }));
};

ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    
    if (response.type === 'questions') {
        console.log('Questions:', response.data.questions);
        
        // Send answers
        ws.send(JSON.stringify({
            type: 'answer',
            data: { answers: { 'When did it start?': '3 months ago' } }
        }));
    } else if (response.type === 'diagnosis') {
        console.log('Diagnosis:', response.data);
    }
};
```

### General Agent WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agent/my-session');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'task',
        data: { task: 'Write a Python hello world function' }
    }));
};
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider: openai, anthropic, google |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key (fallback) |
| `GOOGLE_API_KEY` | - | Google API key (fallback) |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `TASK_TTL_HOURS` | `24` | Task expiration time |
| `DEBUG` | `false` | Debug mode |

### LLM Provider Fallback

```
OpenAI (primary) → Google Gemini → Anthropic Claude
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Test Coverage

| Module | Coverage |
|--------|----------|
| `src/agents/` | 90%+ |
| `src/api/` | 85%+ |
| `src/utils/` | 80%+ |

---

## 🚀 Deployment

### CI/CD Pipeline

```
┌─────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐
│  Lint   │ →  │  Test   │ →  │ Security │ →  │  Build  │
│ (ruff)  │    │(pytest) │    │ (bandit) │    │(Docker) │
└─────────┘    └─────────┘    └──────────┘    └─────────┘
                                                    │
                              ┌─────────────────────┴───────────────────────┐
                              ▼                                             ▼
                       ┌─────────────┐                              ┌─────────────┐
                       │   Staging   │                              │ Production  │
                       │  (develop)  │                              │   (main)    │
                       └─────────────┘                              └─────────────┘
```

### Production Deployment

```bash
# Using docker-compose with production settings
docker-compose -f docker-compose.yml up -d

# Scale workers
docker-compose up -d --scale worker=4

# With monitoring (Flower + Prometheus)
docker-compose --profile monitoring up -d
```

---

## 📊 Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Task Storage** | Redis | Persistent, fast, supports TTL |
| **Orchestration** | LangGraph | Native state management |
| **Queue** | Celery + Redis | Low latency, simple |
| **WebSocket** | FastAPI native | Integrated with routing |
| **LLM** | Multi-provider | Resilience through fallback |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Run tests: `pytest tests/ -v`
4. Commit: `git commit -m "feat: add amazing feature"`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
  <b>Built with ❤️ using LangGraph, FastAPI, and OpenAI</b>
</div>
