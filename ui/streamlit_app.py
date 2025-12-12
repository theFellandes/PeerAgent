# Streamlit Chat UI for PeerAgent
import streamlit as st
import requests
import random
import os
from typing import Optional, List

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Expanded example pool
EXAMPLE_POOL = {
    "code": [
        "Write a Python function to read a CSV file and calculate the average of a column",
        "Create a Python class for a binary search tree with insert and search methods",
        "Write a function to validate email addresses using regex",
        "Create a REST API endpoint using FastAPI for user registration",
        "Write a Python script to scrape headlines from a news website",
        "Implement a rate limiter class using the token bucket algorithm",
        "Create a decorator that caches function results with TTL",
        "Write a function to merge two sorted arrays efficiently",
        "Create a context manager for database transactions",
        "Write a Python generator for Fibonacci sequence",
    ],
    "content": [
        "What are the latest trends in artificial intelligence?",
        "Explain the differences between SQL and NoSQL databases",
        "What is quantum computing and how does it work?",
        "Summarize the key principles of clean code architecture",
        "What are the best practices for API security?",
        "Explain microservices architecture vs monolithic",
        "What are the latest developments in renewable energy?",
        "How does blockchain technology work?",
        "What is DevOps and its key practices?",
        "Explain the concept of edge computing",
    ],
    "business": [
        "Our customer acquisition cost has increased by 40% this year, help me understand why",
        "Our employee turnover rate doubled in the last quarter, diagnose the problem",
        "Sales team is underperforming despite increased marketing spend",
        "Our product launch failed to meet targets, analyze what went wrong",
        "Customer satisfaction scores are declining, help identify root causes",
        "Our supply chain costs are increasing faster than revenue",
        "We're losing market share to competitors, analyze the situation",
        "Our conversion rate dropped after website redesign",
        "Help me understand why our subscription renewal rate is falling",
        "Our operational efficiency has decreased, diagnose the issues",
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
    .example-btn {
        margin: 0.25rem;
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


def get_random_example(category: str) -> Optional[str]:
    """Get a random unused example from the pool."""
    available = [ex for ex in EXAMPLE_POOL[category] 
                 if ex not in st.session_state.used_examples[category]]
    
    if available:
        example = random.choice(available)
        st.session_state.used_examples[category].append(example)
        st.session_state.example_count += 1
        return example
    return None


async def generate_llm_example(category: str) -> str:
    """Generate a new example using LLM when pool is exhausted."""
    prompts = {
        "code": "Generate a unique programming task for a developer. Just the task, no code.",
        "content": "Generate a unique research question about technology or science. Just the question.",
        "business": "Generate a unique business problem scenario for analysis. Just the scenario."
    }
    
    try:
        response = requests.post(
            f"{API_URL}/v1/agent/execute/direct/content",
            json={"task": prompts[category]},
            timeout=30
        )
        if response.ok:
            result = response.json()
            task_id = result.get("task_id")
            if task_id:
                status = requests.get(f"{API_URL}/v1/agent/status/{task_id}", timeout=10)
                if status.ok:
                    data = status.json()
                    content = data.get("result", {}).get("data", {}).get("content", "")
                    if content:
                        return content[:200]  # Limit length
    except Exception:
        pass
    
    # Fallback generic examples
    fallbacks = {
        "code": "Write a function to process and analyze log files",
        "content": "What are emerging technology trends?",
        "business": "Analyze a startup's growth challenges"
    }
    return fallbacks[category]


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
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        task_id = result.get("task_id")
        if task_id:
            status_response = requests.get(f"{API_URL}/v1/agent/status/{task_id}", timeout=30)
            status_response.raise_for_status()
            return status_response.json()
        
        return result
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to API. Make sure the server is running."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out."}
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
        
        if st.button("🔄 New Session"):
            import uuid
            st.session_state.session_id = f"session-{uuid.uuid4().hex[:8]}"
            st.session_state.messages = []
            st.session_state.used_examples = {"code": [], "content": [], "business": []}
            st.session_state.example_count = 0
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Try Random Examples")
        st.caption("Click to get a random example from each category")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💻", key="ex_code", help="Random code example"):
                example = get_random_example("code")
                if example:
                    st.session_state.example_task = example
                    st.session_state.example_type = "code"
                else:
                    st.warning("Pool exhausted! Generating new...")
                    st.session_state.generate_example = "code"
        
        with col2:
            if st.button("📚", key="ex_content", help="Random content example"):
                example = get_random_example("content")
                if example:
                    st.session_state.example_task = example
                    st.session_state.example_type = "content"
                else:
                    st.warning("Pool exhausted!")
                    st.session_state.generate_example = "content"
        
        with col3:
            if st.button("📈", key="ex_business", help="Random business example"):
                example = get_random_example("business")
                if example:
                    st.session_state.example_task = example
                    st.session_state.example_type = "business"
                else:
                    st.warning("Pool exhausted!")
                    st.session_state.generate_example = "business"
        
        # Show remaining examples
        remaining = {k: len(EXAMPLE_POOL[k]) - len(st.session_state.used_examples[k]) 
                    for k in EXAMPLE_POOL}
        st.caption(f"Remaining: 💻{remaining['code']} 📚{remaining['content']} 📈{remaining['business']}")
    
    # Main content
    st.title("💬 PeerAgent Chat")
    st.markdown("*Your intelligent multi-agent assistant*")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                render_response(message["content"])
    
    # Handle example task
    if "example_task" in st.session_state:
        task = st.session_state.example_task
        del st.session_state.example_task
        example_type = st.session_state.pop("example_type", None)
        
        st.session_state.messages.append({"role": "user", "content": task})
        
        with st.spinner("🔄 Processing..."):
            agent_type = example_type if agent_mode == "Automatic" else agent_mode.lower()
            result = send_task(task, agent_type)
        
        st.session_state.messages.append({"role": "assistant", "content": result})
        st.rerun()
    
    # Chat input
    if task := st.chat_input("Ask me anything..."):
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
