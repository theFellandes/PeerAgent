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

```mermaid
flowchart TB
    subgraph Clients["Client Layer"]
        UI[("🎨 Streamlit UI<br/>Port 8501")]
        API_Client["📱 API Clients<br/>REST/HTTP"]
        HTTP_Test["🧪 HTTP Tests<br/>test_main.http"]
    end
    
    subgraph API["API Layer"]
        FastAPI["⚡ FastAPI<br/>Port 8000"]
        Routes["📍 Routes<br/>/v1/agent/*"]
        Middleware["🛡️ CORS<br/>Middleware"]
    end
    
    subgraph Queue["Queue Layer"]
        Redis[("🔴 Redis<br/>Port 6379")]
        Celery["🥬 Celery<br/>Workers"]
    end
    
    subgraph Agents["Agent Layer (LangGraph)"]
        Peer["🤖 PeerAgent<br/>Router"]
        Code["💻 CodeAgent"]
        Content["📚 ContentAgent"]
        Business["📈 BusinessSenseAgent"]
        Problem["🌳 ProblemStructuringAgent"]
    end
    
    subgraph Storage["Storage Layer"]
        Mongo[("🍃 MongoDB<br/>Port 27017")]
    end
    
    subgraph External["External Services"]
        OpenAI["🧠 OpenAI API"]
        DuckDuckGo["🔍 DuckDuckGo"]
    end
    
    UI --> FastAPI
    API_Client --> FastAPI
    HTTP_Test --> FastAPI
    FastAPI --> Routes
    Routes --> Middleware
    
    Routes --> Redis
    Celery <--> Redis
    Celery --> Peer
    
    Peer --> Code
    Peer --> Content
    Peer --> Business
    Business --> Problem
    
    Code --> OpenAI
    Content --> OpenAI
    Content --> DuckDuckGo
    Business --> OpenAI
    
    Code --> Mongo
    Content --> Mongo
    Business --> Mongo
```

---

## Component Architecture

### Agent Hierarchy

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        +session_id: str
        +llm: ChatModel
        +logger: Logger
        +agent_type: str
        +system_prompt: str
        +execute(task) Any
        +invoke_llm(messages) Message
    }
    
    class PeerAgent {
        +code_agent: CodeAgent
        +content_agent: ContentAgent
        +business_agent: BusinessSenseAgent
        +graph: StateGraph
        +classify_task(task) str
        +execute(task) Dict
        +execute_with_agent_type(task, type) Dict
    }
    
    class CodeAgent {
        +execute(task, language) CodeOutput
        -_extract_code_from_markdown(text) CodeOutput
    }
    
    class ContentAgent {
        +search_tool: DuckDuckGoSearch
        +execute(task) ContentOutput
        -_perform_search(query) tuple
    }
    
    class BusinessSenseAgent {
        +graph: StateGraph
        +execute(task, answers) Dict
        -_build_workflow() StateGraph
    }
    
    class ProblemStructuringAgent {
        +execute(diagnosis) ProblemTree
    }
    
    BaseAgent <|-- PeerAgent
    BaseAgent <|-- CodeAgent
    BaseAgent <|-- ContentAgent
    BaseAgent <|-- BusinessSenseAgent
    BaseAgent <|-- ProblemStructuringAgent
    
    PeerAgent o-- CodeAgent
    PeerAgent o-- ContentAgent
    PeerAgent o-- BusinessSenseAgent
    BusinessSenseAgent --> ProblemStructuringAgent
```

### Pydantic Models

```mermaid
classDiagram
    class CodeOutput {
        +code: str
        +language: str
        +explanation: str
    }
    
    class ContentOutput {
        +content: str
        +sources: List~str~
    }
    
    class BusinessDiagnosis {
        +customer_stated_problem: str
        +identified_business_problem: str
        +hidden_root_risk: str
        +urgency_level: Literal
    }
    
    class ProblemTree {
        +problem_type: Literal
        +main_problem: str
        +root_causes: List~ProblemCause~
    }
    
    class ProblemCause {
        +cause: str
        +sub_causes: List~str~
    }
    
    ProblemTree *-- ProblemCause
```

---

## Agent Flow Diagrams

### PeerAgent Routing Flow

```mermaid
stateDiagram-v2
    [*] --> ReceiveTask: User submits task
    
    ReceiveTask --> KeywordClassify: Check keywords
    
    KeywordClassify --> CodeAgent: "code/python/function/debug"
    KeywordClassify --> ContentAgent: "search/explain/what is"
    KeywordClassify --> BusinessAgent: "sales/revenue/problem"
    KeywordClassify --> LLMClassify: No clear match
    
    LLMClassify --> CodeAgent: LLM says CODE
    LLMClassify --> ContentAgent: LLM says CONTENT
    LLMClassify --> BusinessAgent: LLM says BUSINESS
    
    CodeAgent --> ReturnResult: CodeOutput
    ContentAgent --> ReturnResult: ContentOutput
    BusinessAgent --> ReturnResult: Questions/Diagnosis
    
    ReturnResult --> [*]
```

### BusinessSenseAgent Socratic Flow

```mermaid
stateDiagram-v2
    [*] --> Identify: Start Analysis
    
    state Identify {
        [*] --> AskIdentify
        AskIdentify: Ask identification questions
        note right of AskIdentify
            - When did problem start?
            - What's the business impact?
            - Is it in TOP 3 priorities?
        end note
    }
    
    Identify --> Clarify: Answers received
    
    state Clarify {
        [*] --> AskClarify
        AskClarify: Ask clarification questions
        note right of AskClarify
            - Who is affected?
            - What happens if nothing changes?
            - Have you tried solutions?
        end note
    }
    
    Clarify --> Diagnose: Sufficient info
    
    state Diagnose {
        [*] --> Analyze
        Analyze: Analyze all answers
        Analyze --> CreateDiagnosis
        CreateDiagnosis: Generate BusinessDiagnosis
    }
    
    Diagnose --> ProblemTree: Create structure
    
    state ProblemTree {
        [*] --> Classify
        Classify: Classify problem type
        Classify --> BuildTree
        BuildTree: Build MECE tree
    }
    
    ProblemTree --> [*]: Return diagnosis + tree
```

### Task Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    participant U as User/UI
    participant A as FastAPI
    participant R as Redis
    participant P as PeerAgent
    participant C as CodeAgent
    participant L as OpenAI LLM
    participant M as MongoDB

    U->>A: POST /v1/agent/execute
    A->>A: Validate request
    A->>R: Queue task (optional)
    A->>P: execute(task)
    
    P->>P: Keyword classification
    alt Clear keyword match
        P->>P: Route by keywords
    else Ambiguous
        P->>L: Classify task
        L-->>P: CODE/CONTENT/BUSINESS
    end
    
    P->>C: execute(task)
    C->>L: Generate code
    L-->>C: Code response
    C->>C: Parse response
    C->>M: Log execution
    C-->>P: CodeOutput
    
    P-->>A: {agent_type, data}
    A-->>U: TaskResponse
    U->>A: GET /status/{id}
    A-->>U: Full result
```

---

## Data Flow

### Request/Response Flow

```mermaid
flowchart LR
    subgraph Request
        R1[TaskExecuteRequest] --> R2{Validate}
        R2 -->|Valid| R3[Generate task_id]
        R2 -->|Invalid| R4[400 Error]
    end
    
    subgraph Processing
        R3 --> P1[Store in task_store]
        P1 --> P2[PeerAgent.execute]
        P2 --> P3{Agent Type}
        P3 -->|code| P4[CodeAgent]
        P3 -->|content| P5[ContentAgent]
        P3 -->|business| P6[BusinessAgent]
    end
    
    subgraph Response
        P4 --> S1[CodeOutput]
        P5 --> S2[ContentOutput]
        P6 --> S3[Diagnosis/Questions]
        S1 --> F1[TaskResponse]
        S2 --> F1
        S3 --> F1
    end
```

### MongoDB Logging Schema

```mermaid
erDiagram
    AGENT_LOGS {
        ObjectId _id PK
        datetime timestamp
        string agent_type
        string session_id
        string task_id
        object input_data
        object output_data
        string error
        float duration_ms
        string llm_model
        object token_usage
    }
```

---

## API Navigation

### Endpoints Overview

```mermaid
flowchart TB
    subgraph Root["Root"]
        GET_Root["GET /"]
        GET_Health["GET /health"]
        GET_Docs["GET /docs"]
    end
    
    subgraph Agent["Agent API /v1/agent"]
        POST_Execute["POST /execute<br/>Submit any task"]
        GET_Status["GET /status/{id}<br/>Check result"]
        POST_Direct["POST /execute/direct/{type}<br/>Skip routing"]
        POST_Business["POST /business/continue<br/>Continue Q&A"]
        GET_Classify["GET /classify?task=<br/>Debug routing"]
    end
    
    GET_Root --> GET_Docs
    POST_Execute --> GET_Status
    POST_Direct --> GET_Status
    POST_Business --> GET_Status
```

### Usage Flow

```mermaid
journey
    title User Journey: Code Generation
    section Submit Task
      Open UI: 5: User
      Type request: 4: User
      Click send: 5: User
    section Processing
      Route to CodeAgent: 3: System
      Call OpenAI: 3: System
      Parse response: 4: System
    section Result
      Display code: 5: User
      Copy code: 5: User
```

---

## Deployment Architecture

### Docker Compose Setup

```mermaid
flowchart TB
    subgraph Docker["Docker Compose Network"]
        subgraph Services["Services"]
            API["api:8000<br/>FastAPI"]
            Worker["worker<br/>Celery"]
            UI["ui:8501<br/>Streamlit"]
        end
        
        subgraph Data["Data Stores"]
            Mongo["mongo:27017<br/>MongoDB 7.0"]
            Redis["redis:6379<br/>Redis 7"]
        end
    end
    
    subgraph Volumes["Persistent Volumes"]
        V1[("mongo-data")]
        V2[("redis-data")]
    end
    
    API --> Mongo
    API --> Redis
    Worker --> Mongo
    Worker --> Redis
    UI --> API
    
    Mongo --- V1
    Redis --- V2
```

### Production Deployment

```mermaid
flowchart TB
    subgraph Cloud["Cloud Provider"]
        subgraph LB["Load Balancer"]
            ALB["Application LB"]
        end
        
        subgraph Compute["Compute"]
            API1["API Instance 1"]
            API2["API Instance 2"]
            W1["Worker 1"]
            W2["Worker 2"]
        end
        
        subgraph DB["Managed Services"]
            Atlas["MongoDB Atlas"]
            ElastiCache["Redis ElastiCache"]
        end
    end
    
    ALB --> API1
    ALB --> API2
    API1 --> Atlas
    API2 --> Atlas
    API1 --> ElastiCache
    API2 --> ElastiCache
    W1 --> ElastiCache
    W2 --> ElastiCache
    W1 --> Atlas
    W2 --> Atlas
```

---

## Quick Reference

| Component | Port | Technology | Purpose |
|-----------|------|------------|---------|
| API | 8000 | FastAPI | REST endpoints |
| UI | 8501 | Streamlit | Chat interface |
| MongoDB | 27017 | MongoDB 7 | Logging, results |
| Redis | 6379 | Redis 7 | Task queue, cache |
| Worker | - | Celery | Async processing |
