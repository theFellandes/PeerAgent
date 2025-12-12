# Streamlit Chat UI for PeerAgent
import streamlit as st
import requests
import random
import os
from typing import Optional

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Welcome message (not sent to LLM, just displayed in UI)
WELCOME_MESSAGE = """
## 👋 Welcome to PeerAgent!

I'm your intelligent multi-agent assistant. I can help you with:

| Agent | What I Can Do |
|-------|--------------|
| 💻 **Code** | Write code in Python, Java, SQL, JavaScript, and more |
| 📚 **Research** | Find and summarize information on any topic |
| 📈 **Business** | Diagnose business problems using Socratic questioning |

### How to use:
1. **Type your question** in the chat box below
2. I'll automatically route to the best agent
3. Or use the sidebar buttons for specific examples

### Tips:
- Be specific about what you need
- For code, mention the programming language
- For business problems, describe the situation in detail

---
*Start by typing a question or click an example button!*
"""

# Example pool aligned with PDF guidelines - focused on technical test scenarios
EXAMPLE_POOL = {
    "code": [
        # Multi-language support examples
        "Write a SQL query that returns all customers who made purchases last month",
        "Create a Java class to implement a REST API client with error handling",
        "Write a JavaScript function to validate form inputs",
        "Generate a Python script that reads a CSV and calculates averages",
        "Create a TypeScript interface for a User object with validation",
        # Algorithm/Design examples
        "Implement a rate limiter using the token bucket algorithm in Python",
        "Write a function to find the shortest path in a graph using BFS",
        "Create a decorator pattern implementation in Python",
        "Write SQL to find the top 10 products by sales with joins",
        "Implement a simple state machine in JavaScript",
    ],
    "content": [
        # Technology research examples
        "What are the key differences between REST and GraphQL APIs?",
        "Explain the SOLID principles in software development",
        "What are the best practices for securing a REST API?",
        "Compare SQL and NoSQL databases - when to use each?",
        "What is the CAP theorem and its implications?",
        # Industry trends
        "What are the latest trends in AI and machine learning?",
        "Explain microservices architecture and its benefits",
        "What is event-driven architecture?",
        "How does containerization with Docker work?",
        "What are the principles of clean code?",
    ],
    "business": [
        # Business diagnosis scenarios (Socratic method)
        "Our customer acquisition cost increased 40% this year, help diagnose why",
        "Sales team is underperforming despite increased marketing budget",
        "Customer churn doubled in Q4, what could be the root causes?",
        "Our product launch failed to meet targets by 30%",
        "Employee turnover increased significantly after the merger",
        # Operational problems
        "Warehouse operations slowed 25% after new system implementation",
        "Our SaaS conversion rate dropped after website redesign",
        "Supply chain costs are growing faster than revenue",
        "Customer satisfaction scores are declining despite new features",
        "Our startup is struggling to achieve product-market fit",
    ]
}

# Fallback examples
FALLBACK_EXAMPLES = {
    "code": [
        "Write a function to parse JSON data and handle errors",
        "Create a simple HTTP server with routing",
        "Implement a binary search tree in any language",
    ],
    "content": [
        "Explain the concept of technical debt",
        "What are design patterns in software engineering?",
        "How do message queues work?",
    ],
    "business": [
        "Analyze factors that lead to startup failure",
        "What causes low employee engagement?",
        "How to identify market opportunities?",
    ]
}

# Page configuration
st.set_page_config(
    page_title="PeerAgent - AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        transition: transform 0.2s;
    }
    .stButton button:hover {
        transform: scale(1.05);
    }
    .welcome-box {
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"
    if "used_examples" not in st.session_state:
        st.session_state.used_examples = {"code": [], "content": [], "business": []}
    if "example_count" not in st.session_state:
        st.session_state.example_count = 0
    if "using_fallback" not in st.session_state:
        st.session_state.using_fallback = {"code": False, "content": False, "business": False}
    if "show_welcome" not in st.session_state:
        st.session_state.show_welcome = True


def get_random_example(category: str) -> Optional[str]:
    """Get a random unused example from the pool or fallback."""
    if not st.session_state.using_fallback[category]:
        available = [ex for ex in EXAMPLE_POOL[category] 
                     if ex not in st.session_state.used_examples[category]]
        
        if available:
            example = random.choice(available)
            st.session_state.used_examples[category].append(example)
            st.session_state.example_count += 1
            return example
        else:
            st.session_state.using_fallback[category] = True
    
    fallback_available = [ex for ex in FALLBACK_EXAMPLES[category] 
                          if ex not in st.session_state.used_examples[category]]
    
    if fallback_available:
        example = random.choice(fallback_available)
        st.session_state.used_examples[category].append(example)
        st.session_state.example_count += 1
        return example
    
    # All exhausted - reset and start over
    st.session_state.used_examples[category] = []
    st.session_state.using_fallback[category] = False
    return random.choice(EXAMPLE_POOL[category])


def send_task(task: str, agent_type: Optional[str] = None) -> dict:
    """Send a task to the API and wait for result."""
    try:
        if agent_type:
            endpoint = f"{API_URL}/v1/agent/execute/direct/{agent_type}"
        else:
            endpoint = f"{API_URL}/v1/agent/execute"
        
        response = requests.post(
            endpoint,
            json={"task": task, "session_id": st.session_state.session_id},
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        task_id = result.get("task_id")
        if task_id:
            status_response = requests.get(
                f"{API_URL}/v1/agent/status/{task_id}", 
                timeout=30
            )
            status_response.raise_for_status()
            return status_response.json()
        
        return result
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to API. Make sure the server is running."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Try a simpler query."}
    except Exception as e:
        return {"error": str(e)}


def render_code_output(data: dict):
    """Render code agent output."""
    st.markdown("**Generated Code:**")
    language = data.get("language", "python")
    code = data.get("code", "")
    st.code(code, language=language)
    
    if data.get("explanation"):
        st.markdown("**Explanation:**")
        st.markdown(data["explanation"])


def render_content_output(data: dict):
    """Render content agent output."""
    st.markdown(data.get("content", ""))
    
    sources = data.get("sources", [])
    if sources:
        st.markdown("---")
        st.markdown("**Sources:**")
        for i, source in enumerate(sources, 1):
            st.markdown(f"{i}. [{source}]({source})")


def render_business_output(data: dict):
    """Render business agent output."""
    output_type = data.get("type", "")
    output_data = data.get("data", data)
    
    if output_type == "questions" or "questions" in output_data:
        questions = output_data.get("questions", [])
        st.markdown("**Please answer these questions:**")
        for i, q in enumerate(questions, 1):
            st.markdown(f"{i}. {q}")
    elif output_type == "diagnosis" or "customer_stated_problem" in output_data:
        st.markdown("### 📊 Business Diagnosis")
        st.markdown(f"**Customer Stated Problem:** {output_data.get('customer_stated_problem', 'N/A')}")
        st.markdown(f"**Identified Business Problem:** {output_data.get('identified_business_problem', 'N/A')}")
        st.markdown(f"**Hidden Root Risk:** {output_data.get('hidden_root_risk', 'N/A')}")
        urgency = output_data.get("urgency_level", "Medium")
        urgency_color = {"Low": "🟢", "Medium": "🟡", "Critical": "🔴"}.get(urgency, "🟡")
        st.markdown(f"**Urgency Level:** {urgency_color} {urgency}")
    else:
        st.json(output_data)


def render_response(result: dict):
    """Render the API response based on agent type."""
    if "error" in result and result["error"]:
        st.error(f"❌ Error: {result['error']}")
        return
    
    agent_type = result.get("agent_type")
    data = result.get("result", result)
    
    if isinstance(data, dict):
        if not agent_type:
            agent_type = data.get("agent_type", "unknown")
        if "data" in data:
            data = data["data"]
    
    agent_names = {
        "code_agent": "💻 Code Agent",
        "content_agent": "📚 Content Agent",
        "business_sense_agent": "📈 Business Agent",
        "peer_agent": "🤖 Peer Agent"
    }
    st.markdown(f"*{agent_names.get(agent_type, str(agent_type))}*")
    
    if not isinstance(data, dict):
        st.markdown(str(data))
        return
    
    if agent_type == "code_agent":
        render_code_output(data)
    elif agent_type == "content_agent":
        render_content_output(data)
    elif agent_type == "business_sense_agent":
        render_business_output(data)
    else:
        if "code" in data:
            render_code_output(data)
        elif "content" in data:
            render_content_output(data)
        elif "customer_stated_problem" in data or "questions" in data:
            render_business_output(data)
        else:
            st.json(data)


def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 PeerAgent")
        st.markdown("---")
        
        st.markdown("### Agent Selection")
        agent_mode = st.radio(
            "Routing Mode",
            ["Automatic", "Code", "Content", "Business"],
            help="Automatic lets the system decide which agent to use"
        )
        
        st.markdown("---")
        st.markdown("### Session Info")
        st.text(f"Session: {st.session_state.session_id[:20]}...")
        st.text(f"Examples used: {st.session_state.example_count}")
        st.caption("💾 Session memory is enabled")
        
        if st.button("🔄 New Session"):
            import uuid
            st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"
            st.session_state.messages = []
            st.session_state.used_examples = {"code": [], "content": [], "business": []}
            st.session_state.using_fallback = {"code": False, "content": False, "business": False}
            st.session_state.example_count = 0
            st.session_state.show_welcome = True
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Try Random Examples")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            code_remaining = len(EXAMPLE_POOL["code"]) + len(FALLBACK_EXAMPLES["code"]) - len(st.session_state.used_examples["code"])
            if st.button(f"💻 ({code_remaining})", key="ex_code", help="Random code example"):
                example = get_random_example("code")
                if example:
                    st.session_state.pending_example = {"task": example, "type": "code"}
                    st.session_state.show_welcome = False
        
        with col2:
            content_remaining = len(EXAMPLE_POOL["content"]) + len(FALLBACK_EXAMPLES["content"]) - len(st.session_state.used_examples["content"])
            if st.button(f"📚 ({content_remaining})", key="ex_content", help="Random content example"):
                example = get_random_example("content")
                if example:
                    st.session_state.pending_example = {"task": example, "type": "content"}
                    st.session_state.show_welcome = False
        
        with col3:
            business_remaining = len(EXAMPLE_POOL["business"]) + len(FALLBACK_EXAMPLES["business"]) - len(st.session_state.used_examples["business"])
            if st.button(f"📈 ({business_remaining})", key="ex_business", help="Random business example"):
                example = get_random_example("business")
                if example:
                    st.session_state.pending_example = {"task": example, "type": "business"}
                    st.session_state.show_welcome = False
        
        if any(st.session_state.using_fallback.values()):
            st.caption("🔄 Using extended pool")
    
    # Main content
    st.title("💬 PeerAgent Chat")
    st.markdown("*Your intelligent multi-agent assistant*")
    
    # Show welcome message if no messages yet
    if st.session_state.show_welcome and not st.session_state.messages:
        st.markdown(WELCOME_MESSAGE)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                render_response(message["content"])
    
    # Handle pending example
    if "pending_example" in st.session_state:
        pending = st.session_state.pending_example
        del st.session_state.pending_example
        
        task = pending["task"]
        example_type = pending["type"]
        
        st.session_state.messages.append({"role": "user", "content": task})
        
        with st.spinner(f"🔄 Processing with {example_type} agent..."):
            agent_type_to_use = example_type if agent_mode == "Automatic" else agent_mode.lower()
            result = send_task(task, agent_type_to_use)
        
        st.session_state.messages.append({"role": "assistant", "content": result})
        st.rerun()
    
    # Chat input
    if task := st.chat_input("Ask me anything..."):
        st.session_state.show_welcome = False
        st.session_state.messages.append({"role": "user", "content": task})
        
        with st.chat_message("user"):
            st.markdown(task)
        
        with st.chat_message("assistant"):
            with st.spinner("🔄 Processing..."):
                agent_type = None if agent_mode == "Automatic" else agent_mode.lower()
                result = send_task(task, agent_type)
            
            render_response(result)
        
        st.session_state.messages.append({"role": "assistant", "content": result})


if __name__ == "__main__":
    main()
