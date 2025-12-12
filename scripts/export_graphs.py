"""
LangGraph Visualization Utility

Generates visual representations of the agent workflow graphs.
Run this script to export graph diagrams as PNG and Mermaid.

Usage:
    python scripts/export_graphs.py
    
Outputs:
    - architecture/graphs/peer_agent_graph.png
    - architecture/graphs/business_agent_graph.png
    - architecture/graphs/peer_agent_graph.md (Mermaid)
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


def export_peer_agent_graph():
    """Export PeerAgent LangGraph workflow visualization."""
    from src.agents.peer_agent import PeerAgent
    
    print("Creating PeerAgent graph...")
    agent = PeerAgent()
    graph = agent.graph
    
    # Get the graph structure
    compiled_graph = graph
    
    # Export as Mermaid
    try:
        mermaid_code = compiled_graph.get_graph().draw_mermaid()
        
        output_dir = Path("architecture/graphs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save Mermaid
        mermaid_path = output_dir / "peer_agent_graph.md"
        with open(mermaid_path, "w") as f:
            f.write("# PeerAgent LangGraph Workflow\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n")
        print(f"  ✓ Saved Mermaid: {mermaid_path}")
        
        # Try to export as PNG (requires graphviz)
        try:
            png_data = compiled_graph.get_graph().draw_mermaid_png()
            png_path = output_dir / "peer_agent_graph.png"
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"  ✓ Saved PNG: {png_path}")
        except Exception as e:
            print(f"  ⚠ PNG export failed (install graphviz): {e}")
            
    except Exception as e:
        print(f"  ✗ Export failed: {e}")


def export_business_agent_graph():
    """Export BusinessSenseAgent LangGraph workflow visualization."""
    from src.agents.business_agent import BusinessSenseAgent
    
    print("Creating BusinessSenseAgent graph...")
    agent = BusinessSenseAgent()
    graph = agent.graph
    
    try:
        mermaid_code = graph.get_graph().draw_mermaid()
        
        output_dir = Path("architecture/graphs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save Mermaid
        mermaid_path = output_dir / "business_agent_graph.md"
        with open(mermaid_path, "w") as f:
            f.write("# BusinessSenseAgent LangGraph Workflow\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n")
        print(f"  ✓ Saved Mermaid: {mermaid_path}")
        
        # Try PNG
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            png_path = output_dir / "business_agent_graph.png"
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"  ✓ Saved PNG: {png_path}")
        except Exception as e:
            print(f"  ⚠ PNG export failed: {e}")
            
    except Exception as e:
        print(f"  ✗ Export failed: {e}")


def create_combined_architecture():
    """Create a combined architecture diagram."""
    output_dir = Path("architecture/graphs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    combined = """# PeerAgent Complete Architecture

## System Flow

```mermaid
flowchart TB
    subgraph Client["📱 Client Layer"]
        UI["🎨 Streamlit UI"]
        REST["🔌 REST Client"]
    end
    
    subgraph API["⚡ FastAPI Layer"]
        Routes["📍 /v1/agent/*"]
        Valid["✅ Validation"]
        Auth["🔐 Auth"]
    end
    
    subgraph Queue["📬 Queue Layer"]
        Redis[("🔴 Redis")]
        Celery["🥬 Celery"]
    end
    
    subgraph Agents["🤖 Agent Layer"]
        subgraph Router["PeerAgent Router"]
            KW["🔤 Keywords"]
            LLM_C["🧠 LLM Classify"]
        end
        
        Code["💻 CodeAgent"]
        Content["📚 ContentAgent"]  
        Business["📈 BusinessAgent"]
        Problem["🌳 ProblemAgent"]
    end
    
    subgraph External["🌐 External"]
        OpenAI["🧠 OpenAI"]
        DDG["🔍 DuckDuckGo"]
    end
    
    subgraph Storage["💾 Storage"]
        Mongo[("🍃 MongoDB")]
    end
    
    UI --> Routes
    REST --> Routes
    Routes --> Valid --> Auth
    Auth --> Redis
    Celery <--> Redis
    Celery --> Router
    
    Router --> KW
    KW --> LLM_C
    
    Router --> Code
    Router --> Content
    Router --> Business
    Business --> Problem
    
    Code --> OpenAI
    Content --> OpenAI
    Content --> DDG
    Business --> OpenAI
    
    Code --> Mongo
    Content --> Mongo
    Business --> Mongo
```

## Agent Routing Logic

```mermaid
flowchart LR
    subgraph Input
        Task["📝 Task"]
    end
    
    subgraph Classification
        KW{"🔤 Keyword<br/>Match?"}
        LLM{"🧠 LLM<br/>Classify"}
    end
    
    subgraph Agents
        C["💻 Code"]
        CT["📚 Content"]
        B["📈 Business"]
    end
    
    Task --> KW
    KW -->|"code/python/api"| C
    KW -->|"search/explain"| CT
    KW -->|"sales/revenue"| B
    KW -->|"unclear"| LLM
    
    LLM -->|CODE| C
    LLM -->|CONTENT| CT
    LLM -->|BUSINESS| B
```

## Data Models

```mermaid
classDiagram
    class TaskExecuteRequest {
        +task: str
        +session_id: Optional[str]
    }
    
    class TaskResponse {
        +task_id: str
        +status: TaskStatus
        +message: str
        +result: Optional[Dict]
    }
    
    class CodeOutput {
        +code: str
        +language: str
        +explanation: str
    }
    
    class ContentOutput {
        +content: str
        +sources: List[str]
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
        +root_causes: List[ProblemCause]
    }
    
    TaskExecuteRequest --> TaskResponse
    TaskResponse --> CodeOutput
    TaskResponse --> ContentOutput
    TaskResponse --> BusinessDiagnosis
    BusinessDiagnosis --> ProblemTree
```

## Deployment Architecture

```mermaid
flowchart TB
    subgraph Docker["🐳 Docker Compose"]
        subgraph Network["peeragent-network"]
            API["api:8000<br/>FastAPI"]
            Worker["worker<br/>Celery"]
            UI["ui:8501<br/>Streamlit"]
            
            Mongo[("mongo:27017<br/>MongoDB 7")]
            Redis[("redis:6379<br/>Redis 7")]
        end
    end
    
    subgraph Volumes["💾 Volumes"]
        V1[("mongo-data")]
        V2[("redis-data")]
    end
    
    API --> Mongo
    API --> Redis
    Worker --> Mongo
    Worker --> Redis
    UI --> API
    
    Mongo -.-> V1
    Redis -.-> V2
    
    style API fill:#4ecdc4
    style Worker fill:#45b7d1
    style UI fill:#96ceb4
    style Mongo fill:#88d8b0
    style Redis fill:#ff6b6b
```

## Request Lifecycle

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant S as 🎨 Streamlit
    participant A as ⚡ FastAPI
    participant R as 🔴 Redis
    participant C as 🥬 Celery
    participant P as 🤖 PeerAgent
    participant L as 🧠 LLM
    participant M as 🍃 MongoDB
    
    U->>S: Submit task
    S->>A: POST /v1/agent/execute
    A->>A: Validate & generate task_id
    A->>R: Queue task
    A-->>S: {task_id, status: pending}
    
    C->>R: Poll for tasks
    R-->>C: Task received
    C->>P: process(task)
    
    P->>P: Keyword classify
    alt Clear match
        P->>P: Route by keywords
    else Ambiguous
        P->>L: Classify task
        L-->>P: CODE/CONTENT/BUSINESS
    end
    
    P->>L: Execute agent
    L-->>P: Result
    P->>M: Log execution
    
    C->>R: Store result
    
    S->>A: GET /status/{task_id}
    A->>R: Get result
    R-->>A: Task result
    A-->>S: {status: completed, result: {...}}
    S-->>U: Display result
```
"""
    
    path = output_dir / "full_architecture.md"
    with open(path, "w") as f:
        f.write(combined)
    print(f"  ✓ Created combined architecture: {path}")


if __name__ == "__main__":
    print("=" * 50)
    print("LangGraph Visualization Export")
    print("=" * 50)
    
    try:
        export_peer_agent_graph()
    except Exception as e:
        print(f"PeerAgent export error: {e}")
    
    try:
        export_business_agent_graph()
    except Exception as e:
        print(f"BusinessAgent export error: {e}")
    
    create_combined_architecture()
    
    print("=" * 50)
    print("Done! Check architecture/graphs/ folder")
    print("=" * 50)
