# PeerAgent Architecture Overview

This document provides a comprehensive overview of the PeerAgent multi-agent system architecture, including detailed diagrams and component explanations.

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Agent Flow Diagrams](#agent-flow-diagrams)
4. [Data Flow](#data-flow)
5. [API Navigation](#api-navigation)
6. [Deployment Architecture](#deployment-architecture)

---

## System Overview

PeerAgent is a multi-agent AI system that intelligently routes tasks to specialized agents using LangGraph for orchestration.

![FastAPI Agent Routing-2025-12-13-094311.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094311.png)

---

## Component Architecture

### Agent Hierarchy

![FastAPI Agent Routing-2025-12-13-094348.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094348.png)

### Pydantic Models

![FastAPI Agent Routing-2025-12-13-094413.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094413.png)

---

## Agent Flow Diagrams

### PeerAgent Routing Flow

![FastAPI Agent Routing-2025-12-13-094436.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094436.png)

### BusinessSenseAgent Socratic Flow

![FastAPI Agent Routing-2025-12-13-094459.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094459.png)

### Task Execution Sequence

![FastAPI Agent Routing-2025-12-13-094535.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094535.png)

---

## Data Flow

### Request/Response Flow

![FastAPI Agent Routing-2025-12-13-094557.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094557.png)

### MongoDB Logging Schema

![FastAPI Agent Routing-2025-12-13-094624.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094624.png)
 
---

## API Navigation

### Endpoints Overview

![FastAPI Agent Routing-2025-12-13-094649.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094649.png)

### Usage Flow

![FastAPI Agent Routing-2025-12-13-094710.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094710.png)

---

## Deployment Architecture

### Docker Compose Setup

![FastAPI Agent Routing-2025-12-13-094727.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094727.png)

### Production Deployment

![FastAPI Agent Routing-2025-12-13-094750.png](graphs/FastAPI%20Agent%20Routing-2025-12-13-094750.png)

---

## Quick Reference

| Component | Port | Technology | Purpose |
|-----------|------|------------|---------|
| API | 8000 | FastAPI | REST endpoints |
| UI | 8501 | Streamlit | Chat interface |
| MongoDB | 27017 | MongoDB 7 | Logging, results |
| Redis | 6379 | Redis 7 | Task queue, cache |
| Worker | - | Celery | Async processing |
