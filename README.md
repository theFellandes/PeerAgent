# 🤖 PeerAgent - Multi-Agent AI System

> **Intelligent task routing with specialized AI agents powered by LangGraph**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Agents](#-agents)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Development](#-development)

---

## 🎯 Overview

PeerAgent is a sophisticated multi-agent AI system that intelligently routes user requests to specialized agents:

| Agent | Purpose | Example Tasks |
|-------|---------|---------------|
| 💻 **CodeAgent** | Code generation & debugging | "Write a Python function", "Debug this script" |
| 📚 **ContentAgent** | Research & information | "What is machine learning?", "Latest AI trends" |
| 📈 **BusinessSenseAgent** | Business problem diagnosis | "Sales are dropping 20%", "Diagnose customer churn" |
| 🌳 **ProblemAgent** | Problem tree structuring | Converts diagnosis to MECE problem tree |

---

## 🏗 Architecture

### High-Level System View

![FastAPI Agent Routing-2025-12-12-170717.png](architecture/graphs/FastAPI%20Agent%20Routing-2025-12-12-170717.png)

### Agent Routing Flow

![FastAPI Agent Routing-2025-12-12-170837.png](architecture/graphs/FastAPI%20Agent%20Routing-2025-12-12-170837.png)

### LangGraph Workflow (PeerAgent)

![FastAPI Agent Routing-2025-12-12-170924.png](architecture/graphs/FastAPI%20Agent%20Routing-2025-12-12-170924.png)

### Business Analysis Flow (Socratic Method)

![FastAPI Agent Routing-2025-12-12-170954.png](architecture/graphs/FastAPI%20Agent%20Routing-2025-12-12-170954.png)

### Data Flow

![FastAPI Agent Routing-2025-12-12-171025.png](architecture/graphs/FastAPI%20Agent%20Routing-2025-12-12-171025.png)

### Deployment

![FastAPI Agent Routing-2025-12-12-171050.png](architecture/graphs/FastAPI%20Agent%20Routing-2025-12-12-171050.png)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key

### 1. Clone & Configure

```bash
git clone https://github.com/theFellandes/PeerAgent.git
cd peeragent

# Create environment file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Run with Docker (Recommended)

```bash
docker-compose up --build
```

**Services:**
- 🌐 API: http://localhost:8000
- 📖 Docs: http://localhost:8000/docs
- 🎨 UI: http://localhost:8501

### 3. Run Locally (Development)

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev,ui]"

# Start services
python main.py  # API
celery -A src.worker.celery_app worker  # Worker
streamlit run ui/streamlit_app.py  # UI
```

---

## 🤖 Agents

### CodeAgent

Generates production-ready code with explanations.

```python
# Request
{"task": "Write a function to validate email addresses"}

# Response
{
    "code": "import re\n\ndef validate_email(email: str) -> bool:\n    ...",
    "language": "python",
    "explanation": "Uses regex pattern matching..."
}
```

### ContentAgent

Researches topics with source citations.

```python
# Request
{"task": "What is quantum computing?"}

# Response
{
    "content": "Quantum computing leverages quantum mechanical phenomena...",
    "sources": ["https://...", "https://..."]
}
```

### BusinessSenseAgent

Diagnoses business problems using Socratic questioning.

```python
# Request
{"task": "Our sales dropped 20% this quarter"}

# Response (Questions)
{
    "type": "questions",
    "questions": [
        "When did you first notice this drop?",
        "Which customer segments are affected?"
    ]
}

# Response (Diagnosis)
{
    "type": "diagnosis",
    "customer_stated_problem": "Sales dropped 20%",
    "identified_business_problem": "Market share erosion",
    "hidden_root_risk": "Brand perception degradation",
    "urgency_level": "Critical"
}
```

---

## 📡 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/v1/agent/execute` | Submit task (auto-route) |
| `GET` | `/v1/agent/status/{id}` | Get task result |
| `POST` | `/v1/agent/execute/direct/{type}` | Direct agent call |
| `GET` | `/v1/agent/classify` | Debug classification |

### Example Requests

```bash
# Auto-routed task
curl -X POST http://localhost:8000/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a hello world function"}'

# Direct to CodeAgent
curl -X POST http://localhost:8000/v1/agent/execute/direct/code \
  -H "Content-Type: application/json" \
  -d '{"task": "Create a REST API client class"}'

# Check status
curl http://localhost:8000/v1/agent/status/task-abc123
```

---

## 📁 Project Structure

```
PeerAgent/
├── 📂 src/
│   ├── 📂 agents/          # AI Agents
│   │   ├── base.py         # BaseAgent (abstract)
│   │   ├── peer_agent.py   # Router (LangGraph)
│   │   ├── code_agent.py   # Code generation
│   │   ├── content_agent.py # Research
│   │   ├── business_agent.py # Diagnosis
│   │   └── problem_agent.py  # Problem tree
│   ├── 📂 api/             # FastAPI
│   │   ├── main.py         # App factory
│   │   └── routes/         # Endpoints
│   ├── 📂 models/          # Pydantic schemas
│   ├── 📂 worker/          # Celery tasks
│   └── 📂 utils/           # Helpers
├── 📂 ui/                  # Streamlit
├── 📂 tests/               # Pytest
├── 📂 architecture/        # Diagrams & docs
├── 📄 docker-compose.yml
├── 📄 pyproject.toml
└── 📄 README.md
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider |
| `LLM_MODEL` | `gpt-4o-mini` | Model name (cheapest with good performance) |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `GOOGLE_API_KEY` | - | Google Gemini API key (fallback) |
| `ANTHROPIC_API_KEY` | - | Anthropic Claude API key (fallback) |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `DEBUG` | `false` | Debug mode |

### 🔄 LLM Provider Fallback

The system automatically falls back to alternative LLM providers if the primary one fails:

```
OpenAI (primary) → Gemini → Anthropic
```

**Features:**
- **Automatic fallback**: If API key is invalid or quota exceeded, tries next provider
- **Runtime retry**: Auth errors trigger automatic provider switch and retry
- **Cost-optimized defaults**: Uses cheapest models per provider

| Provider | Default Model | Cost |
|----------|--------------|------|
| OpenAI | `gpt-4o-mini` | $0.15/1M tokens |
| Google | `gemini-1.5-flash` | Free tier available |
| Anthropic | `claude-3-sonnet` | $3/1M tokens |

**Configure fallback** by setting multiple API keys in `.env`:

```bash
OPENAI_API_KEY=sk-...       # Primary
GOOGLE_API_KEY=AIza...      # Fallback 1
ANTHROPIC_API_KEY=sk-ant-...  # Fallback 2
```

---

## 🛠 Development

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Lint
ruff check src/

# Format
black src/

# Type check
mypy src/
```

### Export LangGraph Diagrams

```bash
python scripts/export_graphs.py
```

---

## 📊 Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Orchestration** | LangGraph | Native state management, conditional routing |
| **Queue** | Redis + Celery | Optimal for task queues, low latency |
| **Database** | MongoDB | Flexible schema for logs |
| **LLM** | Multi-provider | OpenAI, Anthropic, Google support |
| **UI** | Streamlit | Rapid prototyping, Python native |

### Why Redis + Celery Over Kafka?

We evaluated Kafka but chose Redis + Celery for the following reasons:

| Factor | Redis + Celery | Kafka |
|--------|:-------------:|:-----:|
| **Setup Complexity** | ✅ Low | ❌ High (needs Zookeeper) |
| **Throughput Needed** | ~100 req/s | 100K+ req/s |
| **Message Persistence** | Limited | Excellent |
| **Memory Usage** | ✅ Low | Medium-High |
| **Latency** | ✅ ~1ms | ~10ms |
| **Use Case Fit** | ✅ Task queues | Event streaming |
| **Containers** | 1 (Redis) | 2+ (Kafka + Zookeeper) |

**Bottom Line**: Kafka is overkill for our scale. For AI agent requests (~100/sec), Redis + Celery provides:
- Lower latency for request-response patterns
- Simpler infrastructure
- Already configured and working

> 📖 See [architecture/QUEUE_ANALYSIS.md](architecture/QUEUE_ANALYSIS.md) for detailed analysis

### Performance Optimizations

Instead of Kafka, we added:
- **Connection Pooling**: 20 Redis connections, 50 MongoDB connections
- **Celery Tuning**: `worker_prefetch_multiplier=1` for long LLM tasks
- **Increased Timeouts**: 120s for LLM calls

---

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

The project uses GitHub Actions for continuous integration and deployment. The pipeline runs on every push to `main` and `develop` branches, and on pull requests to `main`.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐  │
│  │  Lint   │ ──▶│  Test   │ ──▶│  Build  │ ──▶│   Deploy    │  │
│  │(flake8) │    │(pytest) │    │(Docker) │    │(Production) │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────────┘  │
│                                                                 │
│  Triggers: push to main/develop, PRs to main                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Pipeline Stages

| Stage | Tools | Description |
|-------|-------|-------------|
| **Lint** | flake8, mypy | Code quality and type checking |
| **Test** | pytest | Unit and integration tests with Redis/MongoDB |
| **Build** | Docker | Build and push images to GitHub Container Registry |
| **Deploy** | Custom | Deploy to production (configurable) |

#### Required Secrets

Configure these secrets in your GitHub repository:

| Secret | Description |
|--------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for production |
| `GITHUB_TOKEN` | Auto-provided for container registry |

#### Manual Deployment

```bash
# Trigger deployment manually
git push origin main

# Or use GitHub Actions UI:
# Actions → PeerAgent CI/CD → Run workflow
```

---

## 🌿 Branch Management

### Git Flow Strategy

We follow a modified Git Flow model:

```
main (production)
 │
 ├── develop (integration)
 │    │
 │    ├── feature/add-new-agent
 │    ├── feature/improve-prompts
 │    └── feature/api-versioning
 │
 └── hotfix/critical-bug-fix
```

### Branch Types

| Branch | Purpose | Merges Into |
|--------|---------|-------------|
| `main` | Production-ready code | - |
| `develop` | Integration branch | `main` |
| `feature/*` | New features | `develop` |
| `hotfix/*` | Critical fixes | `main` + `develop` |
| `release/*` | Release preparation | `main` + `develop` |

### Workflow

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-feature
   ```

2. **Develop & Commit**
   ```bash
   git add .
   git commit -m "feat: add new functionality"
   ```

3. **Create Pull Request**
   - Target: `develop` branch
   - Request reviews from team members
   - Ensure CI passes

4. **Merge to Main (Release)**
   ```bash
   git checkout main
   git merge develop
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin main --tags
   ```

### Commit Convention

Use conventional commits for clear history:

```
feat: add new feature
fix: resolve bug
docs: update documentation
refactor: improve code structure
test: add tests
chore: maintenance tasks
```

---

## 📈 Production Recommendations

### Rate Limiting

Add rate limiting with FastAPI middleware:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/v1/agent/execute")
@limiter.limit("10/minute")
async def execute_task(...):
    ...
```

### API Versioning

- Current: `/v1/agent/*`
- Future versions: `/v2/agent/*` with backward compatibility
- Deprecation notices in response headers

### Scaling Considerations

- **Horizontal**: Add more Celery workers
- **Vertical**: Increase container resources
- **Caching**: Redis for frequently accessed data

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
  <b>Built with ❤️ using LangGraph, FastAPI, and OpenAI</b>
</div>
