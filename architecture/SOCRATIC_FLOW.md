# 🔍 Socratic Questioning Flow - Business Sense Agent

This document provides an extensive explanation of how the BusinessSenseAgent uses Socratic questioning to diagnose business problems. It covers all prompts, LLM interactions, and the validation logic that ensures quality conversations.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Phase System](#phase-system)
4. [Prompts & LLM Interactions](#prompts--llm-interactions)
5. [Answer Validation](#answer-validation)
6. [API Flow](#api-flow)
7. [Example Conversations](#example-conversations)
8. [Technical Implementation](#technical-implementation)

---

## Overview

The Business Sense Agent implements a **Socratic questioning methodology** to diagnose business problems. Rather than asking for all information upfront, it guides users through a structured conversation that:

1. **Uncovers hidden problems** beyond stated symptoms
2. **Distinguishes between stated and actual problems**
3. **Identifies root causes** that might not be obvious
4. **Assesses urgency** based on business impact

### Key Principles

- **Ask 2-3 focused questions at a time** - never overwhelm the user
- **Adapt questions based on answers** - each phase builds on previous responses
- **Look for hidden problems** - the stated problem is often not the real issue
- **Never provide solutions** until questioning is complete

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│  (Streamlit Chat)                                                │
├─────────────────────────────────────────────────────────────────┤
│                              │                                   │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │   API Endpoint  │                          │
│                    │  /business/     │                          │
│                    │   continue      │                          │
│                    └────────┬────────┘                          │
│                              │                                   │
│                              ▼                                   │
│              ┌───────────────────────────────┐                  │
│              │    BusinessSenseAgent         │                  │
│              │                               │                  │
│              │  ┌─────────────────────────┐  │                  │
│              │  │  _validate_answers()    │  │ ─── LLM Call 1   │
│              │  │  (Answer Quality Check) │  │                  │
│              │  └──────────┬──────────────┘  │                  │
│              │             │                 │                  │
│              │     ┌───────▼───────┐         │                  │
│              │     │ Valid?        │         │                  │
│              │     └───┬───────┬───┘         │                  │
│              │   No    │       │  Yes        │                  │
│              │   ┌─────▼─┐   ┌─▼───────────┐ │                  │
│              │   │Return │   │ Proceed to  │ │                  │
│              │   │Same Qs│   │ Next Phase  │ │                  │
│              │   │+Feedbk│   └──────┬──────┘ │                  │
│              │   └───────┘          │        │                  │
│              │                      ▼        │                  │
│              │  ┌─────────────────────────┐  │                  │
│              │  │ _generate_questions()   │  │ ─── LLM Call 2   │
│              │  │ or _generate_diagnosis()│  │                  │
│              │  └─────────────────────────┘  │                  │
│              └───────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase System

The Socratic dialogue consists of **3 questioning phases** followed by diagnosis:

| Phase | Emoji | Round | Goal |
|-------|-------|-------|------|
| **Identify** | 🔍 | 1 | Understand WHEN, WHAT, and WHY |
| **Clarify** | 🎯 | 2 | Understand WHO, CONSEQUENCES, and ATTEMPTS |
| **Diagnose** | 🔬 | 3 | Understand NEEDS, DATA, and SUCCESS CRITERIA |
| **Complete** | 📊 | - | Generate final diagnosis |

### Phase Progression Logic

```python
def _determine_next_phase(answer_rounds: int, max_rounds: int = 3):
    """
    Each user response = 1 round, regardless of how many questions answered.
    
    - 0 rounds: identify phase (first questions)
    - 1 round:  clarify phase  
    - 2 rounds: diagnose phase
    - 3+ rounds: complete (generate diagnosis)
    """
    if answer_rounds >= max_rounds:
        return "complete"
    
    phases = ["identify", "clarify", "diagnose", "complete"]
    return phases[min(answer_rounds, len(phases) - 1)]
```

---

## Prompts & LLM Interactions

### 1. System Prompt (Core Identity)

This prompt establishes the agent's role and methodology:

```
You are a Business Sense Agent that uses Socratic questioning methodology.

## YOUR ROLE
You help business professionals identify root causes of problems through 
careful, probing questions. Like Socrates, you lead customers to discover 
insights themselves rather than telling them what's wrong.

## QUESTIONING METHODOLOGY
1. Start with WHEN questions - understand timing and triggers
2. Progress to WHAT questions - understand scope and measurement  
3. Ask WHY questions - understand underlying causes
4. Include WHO questions - understand stakeholders affected
5. End with HOW questions - understand previous attempts and constraints

## CRITICAL RULES
1. Ask 2-3 focused questions at a time - never more
2. Adapt your next questions based on the answers received
3. Look for hidden problems beyond the stated symptoms
4. Always distinguish between STATED problem and ACTUAL business problem
5. Be empathetic but professionally probing
6. Never provide solutions until you've completed the questioning phases
```

### 2. Phase-Specific Instructions

Each phase has its own instruction set that's added to the prompt:

#### Identify Phase (Round 1)
```
You are in the PROBLEM IDENTIFICATION phase.
Ask 2-3 questions to understand:
- WHEN this problem started and what triggered it
- The MEASURABLE IMPACT (specific numbers, percentages, dollar amounts)
- Whether this is a TOP PRIORITY for the company
```

#### Clarify Phase (Round 2)
```
You are in the SCOPE & URGENCY phase.
Ask 2-3 questions to understand:
- WHO is most affected by this problem
- The CONSEQUENCES if nothing changes in 6 months
- Any PREVIOUS SOLUTION ATTEMPTS and why they failed
```

#### Diagnose Phase (Round 3)
```
You are in the ROOT CAUSE DISCOVERY phase.
Ask 2-3 final questions to understand:
- Whether they need a SOLUTION or first need VISIBILITY into the cause
- What DATA or METRICS they currently track
- What SUCCESS looks like and how they'll measure it
```

### 3. Question Generation Message

```python
human_content = f"""
Customer's problem statement: {task}

## Previous Answers from Customer:
{collected_answers_formatted}

Generate 2-3 targeted Socratic questions for this phase. 
Respond with a JSON object containing:
- "questions": an array of 2-3 question strings
- "category": a string describing what you're trying to understand
- "reasoning": a brief explanation of why these questions matter
"""
```

### 4. Diagnosis Generation Prompt

```
Based on the Socratic questioning dialogue, provide a comprehensive business diagnosis.

## Analysis Framework

### 1. Customer Stated Problem
What the customer initially described as their problem. Quote or closely paraphrase their words.

### 2. Identified Business Problem  
The actual underlying business issue you've uncovered through questioning. This is often 
different from or deeper than what the customer initially stated.

### 3. Hidden Root Risk
The deeper systemic risk or vulnerability that could cause bigger problems if not addressed. 
Think about:
- What patterns might this problem be a symptom of?
- What could go wrong if this continues unchecked?
- What related issues might exist but weren't mentioned?

### 4. Urgency Assessment
Rate as Low, Medium, or Critical based on:
- **Low**: Problem causes inconvenience but no immediate business threat
- **Medium**: Problem affecting operations or revenue but manageable short-term
- **Critical**: Problem threatening business viability, safety, or requiring immediate action

Be specific and actionable in your diagnosis. Reference concrete details from the conversation.
```

---

## Answer Validation

### Purpose

Before proceeding to the next phase, the agent validates that the user's answer is:
1. **Relevant** to the business questions
2. **Substantive** enough to provide useful information
3. **Actionable** for diagnosis purposes

### Validation Prompt

```python
validation_prompt = f"""
You are evaluating whether a user's answer is relevant and useful for a business diagnosis session.

## Original Business Problem
{task}

## Current Phase: {phase.upper()}

## Questions Asked
{questions_formatted}

## User's Answer
"{user_answer}"

## Your Task
Evaluate the answer and respond with a JSON object:

{{
    "valid": true/false (is this a genuine attempt to answer?),
    "quality": "irrelevant" | "vague" | "partial" | "good",
    "addressed_questions": [list of question numbers addressed],
    "missing_info": ["list of specific information still needed"],
    "feedback": "A helpful message for the user",
    "can_proceed": true/false (do we have enough to continue?)
}}

## Quality Guidelines
- "irrelevant": Answer has nothing to do with the business problem (e.g., "weather is rainy")
- "vague": Answer mentions the topic but lacks specifics (e.g., "things are bad")
- "partial": Some questions answered but key info missing
- "good": Most questions addressed with useful details

Be strict but helpful. If the answer is irrelevant, can_proceed should be false.
```

### Validation Flow

```
User Answer → Validate → Quality Assessment
                          │
                          ├── "irrelevant" → Stay in phase, show feedback
                          ├── "vague" → Stay in phase, ask for specifics
                          ├── "partial" → Proceed but note gaps
                          └── "good" → Proceed to next phase
```

---

## API Flow

### Endpoint: POST /v1/agent/business/continue

**Request Body:**
```json
{
    "session_id": "session-abc123",
    "answers": {"Q1": "answer1", "Q2": "answer2"},
    "answer_round": 1,
    "original_task": "Our sales are declining",
    "latest_answer": "The user's most recent response",
    "previous_questions": ["Q1?", "Q2?", "Q3?"]
}
```

**Response (Questions):**
```json
{
    "task_id": "task-xyz",
    "status": "completed",
    "agent_type": "business_sense_agent",
    "result": {
        "type": "questions",
        "data": {
            "session_id": "session-abc123",
            "questions": ["Question 1?", "Question 2?", "Question 3?"],
            "category": "problem_identification",
            "phase": "clarify",
            "phase_emoji": "🎯",
            "round_number": 2,
            "feedback": null
        }
    }
}
```

**Response (Validation Failed):**
```json
{
    "result": {
        "type": "questions",
        "data": {
            "questions": ["Same questions..."],
            "phase": "identify",
            "phase_emoji": "⚠️",
            "round_number": 1,
            "feedback": "Your answer doesn't address the business questions. Please provide details about when the problem started..."
        }
    }
}
```

---

## Example Conversations

### Example 1: Good Flow

```
👤 User: "Our product launch failed to meet targets by 30%"

🔍 Phase 1 - Identify
━━━━━━━━━━━━━━━━━━━━
🤖 Agent:
1. When did you first realize the launch was not meeting targets?
2. What specific metrics were set? How do actual results compare?
3. Is this currently one of your company's top 3 priorities?

👤 User: "We noticed day 1. Target was 10K units, hit 7K. Revenue 
gap of $450K. It's our CEO's #1 priority right now."

🎯 Phase 2 - Clarify
━━━━━━━━━━━━━━━━━━━━
🤖 Agent: 
1. Who is most affected by this shortfall?
2. What happens if this isn't fixed for the next launch?
3. What did you try during this launch that didn't work?

👤 User: "Sales team is demoralized. Marketing got blamed. If pattern 
repeats, we lose board confidence. We tried influencer marketing - 
spent $100K but couldn't track conversions."

🔬 Phase 3 - Diagnose
━━━━━━━━━━━━━━━━━━━━━
🤖 Agent:
1. Do you need a solution or first visibility into the root cause?
2. What data/metrics do you currently track pre-launch?
3. What would success look like for your next launch?

👤 User: "Visibility first - we don't know WHY it failed. We track spend 
and impressions but not conversion paths. Success = 15K units and 
being able to explain what drove sales."

📊 Diagnosis Generated
━━━━━━━━━━━━━━━━━━━━━
Customer Stated Problem: Product launch missed targets by 30%
Identified Problem: Complete lack of attribution tracking making 
                    it impossible to optimize marketing spend
Hidden Root Risk: Each failed launch erodes board/investor confidence; 
                  without attribution, this will repeat
Urgency: CRITICAL
```

### Example 2: Irrelevant Answer Handling

```
👤 User: "Our supply chain costs are rising"

🔍 Phase 1 - Identify
━━━━━━━━━━━━━━━━━━━━
🤖 Agent:
1. When did the cost increases begin?
2. What percentage increase have you seen?
3. Is this a top priority for your company?

👤 User: "The weather has been really rainy lately"

⚠️ Validation Failed
━━━━━━━━━━━━━━━━━━━━
🤖 Agent:
"Your answer doesn't seem to address the business questions about 
supply chain costs. Could you please share when you first noticed 
the cost increases and how significant they have been?"

[Re-shows same Phase 1 questions]
```

---

## Technical Implementation

### Files Involved

| File | Purpose |
|------|---------|
| `src/agents/business_agent.py` | Core agent with Socratic logic |
| `src/models/agents.py` | Data models (BusinessAgentQuestions, BusinessDiagnosis) |
| `src/models/requests.py` | API request models |
| `src/api/routes/agent.py` | API endpoints |
| `ui/streamlit_app.py` | User interface |

### Key Methods

```python
class BusinessSenseAgent:
    async def execute(task, collected_answers, answer_rounds, ...) -> Dict
        """Main entry point - routes to questions or diagnosis"""
    
    async def _validate_answers(task, questions, user_answer, phase) -> Dict
        """LLM call to validate answer quality"""
    
    async def _generate_questions(task, phase, collected_answers) -> Dict
        """LLM call to generate phase-appropriate questions"""
    
    async def _generate_diagnosis(task, collected_answers) -> BusinessDiagnosis
        """LLM call to generate final diagnosis"""
    
    def _determine_next_phase(answer_rounds, max_rounds) -> str
        """Determine which phase based on completed rounds"""
```

### Session State (UI)

```python
st.session_state.business_questions      # Current pending questions
st.session_state.business_original_task  # Initial problem statement
st.session_state.business_collected_answers  # All Q&A pairs
st.session_state.business_answer_round   # Current round number
```

---

## Configuration

### PHASE_CONFIG

```python
PHASE_CONFIG = {
    "identify": {
        "emoji": "🔍",
        "title": "Problem Identification",
        "description": "Understanding when, what, and why"
    },
    "clarify": {
        "emoji": "🎯", 
        "title": "Scope & Urgency",
        "description": "Understanding who, consequences, and attempts"
    },
    "diagnose": {
        "emoji": "🔬",
        "title": "Root Cause Discovery", 
        "description": "Understanding needs, data, and success criteria"
    },
    "complete": {
        "emoji": "📊",
        "title": "Diagnosis Complete",
        "description": "Generating final analysis"
    }
}
```

---

## Automated Demo Flow

The Business Agent supports an **automated demo mode** where the LLM generates both questions AND realistic answers, simulating a complete diagnostic conversation without user input.

### Purpose

- **Demonstrations**: Show stakeholders how the Socratic flow works
- **Testing**: Validate the diagnostic pipeline end-to-end
- **Training**: Generate example conversations for documentation

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEMO EXECUTION FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  POST /v1/agent/business/demo                                   │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              execute_demo(task)                       │       │
│  │                                                       │       │
│  │   FOR each phase [identify, clarify, diagnose]:      │       │
│  │     │                                                 │       │
│  │     ├─► _generate_questions() ──► LLM Call 1        │       │
│  │     │        (Returns 2-3 questions)                 │       │
│  │     │                                                 │       │
│  │     └─► _generate_demo_answer() ──► LLM Call 2      │       │
│  │              (Returns realistic user answer)         │       │
│  │                                                       │       │
│  │   THEN:                                               │       │
│  │     └─► _generate_diagnosis() ──► LLM Call 3        │       │
│  │              (Returns final diagnosis)               │       │
│  └──────────────────────────────────────────────────────┘       │
│         │                                                        │
│         ▼                                                        │
│  Return complete conversation with all phases + diagnosis       │
└─────────────────────────────────────────────────────────────────┘
```

### Demo Answer Generation Prompt

The `_generate_demo_answer` method uses this prompt to simulate realistic user responses:

```python
prompt = f"""You are simulating a business professional answering diagnostic questions about their problem.

## The Original Business Problem
{task}

## Current Phase: {phase.upper()}

## Questions Being Asked
{questions_formatted}

{previous_context}  # Previous Q&A for context

## Your Task
Generate a realistic, detailed answer that a business professional would give to these questions.
The answer should:
1. Be specific with numbers, percentages, timeframes where appropriate
2. Sound authentic and natural (not generic)
3. Reveal information useful for diagnosis
4. Be 2-4 sentences long, addressing all questions together
5. Include specific business context and realistic details

Respond with ONLY the answer text, no quotes or prefixes."""
```

### API Endpoint

#### POST /v1/agent/business/demo

**Request Body:**
```json
{
    "task": "Sales team is underperforming despite increased marketing budget",
    "session_id": "demo-session-123"
}
```

**Response:**
```json
{
    "task_id": "demo-abc123",
    "status": "completed",
    "agent_type": "business_sense_agent",
    "demo_mode": true,
    "result": {
        "type": "demo",
        "task": "Sales team is underperforming despite increased marketing budget",
        "rounds": [
            {
                "phase": "identify",
                "phase_emoji": "🔍",
                "questions": [
                    "When did you first notice the sales team underperformance?",
                    "What is the measurable gap between expected and actual performance?",
                    "Is this currently a top priority for leadership?"
                ],
                "answer": "We noticed the gap about 6 weeks ago. Despite increasing marketing spend by 40% to $2M/quarter, sales only grew 5% instead of the expected 25%. The CEO made this the top agenda item at our last board meeting."
            },
            {
                "phase": "clarify",
                "phase_emoji": "🎯",
                "questions": ["..."],
                "answer": "..."
            },
            {
                "phase": "diagnose",
                "phase_emoji": "🔬",
                "questions": ["..."],
                "answer": "..."
            }
        ],
        "diagnosis": {
            "customer_stated_problem": "Sales team is underperforming despite increased marketing budget",
            "identified_business_problem": "Disconnect between marketing-generated leads and sales team capacity/skills. Marketing is generating volume but not quality leads that match the sales team's expertise.",
            "hidden_root_risk": "Burning marketing budget on leads that don't convert erodes confidence in marketing effectiveness and creates tension between departments.",
            "urgency_level": "Critical"
        }
    }
}
```

### Key Implementation Methods

```python
class BusinessSenseAgent:
    
    async def execute_demo(self, task: str) -> Dict[str, Any]:
        """
        Execute a complete demo of the Socratic questioning flow.
        
        The LLM generates both questions AND realistic answers, 
        simulating an entire conversation through all 3 phases to diagnosis.
        """
        phases = ["identify", "clarify", "diagnose"]
        rounds = []
        collected_answers = {}
        
        for phase in phases:
            # Generate questions
            questions = await self._generate_questions(task, phase, collected_answers)
            
            # Generate simulated answer
            answer = await self._generate_demo_answer(task, questions, phase, collected_answers)
            
            rounds.append({
                "phase": phase,
                "questions": questions,
                "answer": answer
            })
            
            # Store for context
            for q in questions:
                collected_answers[q] = answer
        
        # Generate final diagnosis
        diagnosis = await self._generate_diagnosis(task, collected_answers)
        
        return {"type": "demo", "rounds": rounds, "diagnosis": diagnosis}
    
    async def _generate_demo_answer(self, task, questions, phase, previous) -> str:
        """Generate a realistic user answer for demo purposes."""
        # Uses LLM to simulate business professional response
        pass
```

### UI Integration

The UI calls the demo API when the user clicks the **📈 Demo** button:

```python
def render_business_demo(task: str) -> Optional[dict]:
    """Call API to run full automated demo."""
    
    with st.spinner("🎬 Generating demo... (LLM is creating questions and answers)"):
        response = requests.post(
            f"{API_URL}/v1/agent/business/demo",
            json={"task": task},
            timeout=180  # Demo takes longer - 6 LLM calls
        )
    
    # Render each phase with questions and simulated answers
    for round_data in result["rounds"]:
        st.markdown(f"### {round_data['phase_emoji']} {phase_title}")
        st.markdown("**Agent asks:**")
        for q in round_data["questions"]:
            st.markdown(f"  - *{q}*")
        st.success(f"💬 \"{round_data['answer']}\"")
    
    # Render diagnosis
    st.markdown("### 📊 Business Diagnosis Complete")
```

---

## Technical Implementation

### Files Involved

| File | Purpose |
|------|---------|
| `src/agents/business_agent.py` | Core agent with Socratic logic + demo methods |
| `src/models/agents.py` | Data models (BusinessAgentQuestions, BusinessDiagnosis) |
| `src/models/requests.py` | API request models |
| `src/api/routes/agent.py` | API endpoints including `/business/demo` |
| `ui/streamlit_app.py` | User interface with demo rendering |

### Key Methods

```python
class BusinessSenseAgent:
    # Interactive Flow
    async def execute(task, collected_answers, answer_rounds, ...) -> Dict
        """Main entry point - routes to questions or diagnosis"""
    
    async def _validate_answers(task, questions, user_answer, phase) -> Dict
        """LLM call to validate answer quality"""
    
    async def _generate_questions(task, phase, collected_answers) -> Dict
        """LLM call to generate phase-appropriate questions"""
    
    async def _generate_diagnosis(task, collected_answers) -> BusinessDiagnosis
        """LLM call to generate final diagnosis"""
    
    def _determine_next_phase(answer_rounds, max_rounds) -> str
        """Determine which phase based on completed rounds"""
    
    # Demo Flow (NEW)
    async def execute_demo(task) -> Dict
        """Run complete automated demo with LLM-generated Q&A"""
    
    async def _generate_demo_answer(task, questions, phase, previous) -> str
        """Generate realistic simulated user answers"""
```

### Session State (UI)

```python
st.session_state.business_questions      # Current pending questions
st.session_state.business_original_task  # Initial problem statement
st.session_state.business_collected_answers  # All Q&A pairs
st.session_state.business_answer_round   # Current round number
```

---

## Configuration

### PHASE_CONFIG

```python
PHASE_CONFIG = {
    "identify": {
        "emoji": "🔍",
        "title": "Problem Identification",
        "description": "Understanding when, what, and why"
    },
    "clarify": {
        "emoji": "🎯", 
        "title": "Scope & Urgency",
        "description": "Understanding who, consequences, and attempts"
    },
    "diagnose": {
        "emoji": "🔬",
        "title": "Root Cause Discovery", 
        "description": "Understanding needs, data, and success criteria"
    },
    "complete": {
        "emoji": "📊",
        "title": "Diagnosis Complete",
        "description": "Generating final analysis"
    }
}
```

---

## LLM Call Summary

| Method | Purpose | Input | Output |
|--------|---------|-------|--------|
| `_generate_questions` | Create phase-specific questions | task, phase, context | 2-3 questions |
| `_validate_answers` | Check answer relevance | questions, answer | valid/feedback |
| `_generate_diagnosis` | Final analysis | all Q&A pairs | diagnosis object |
| `_generate_demo_answer` | Simulate user response | questions, context | realistic answer |

---

## Future Enhancements

1. **Smart Skip to Diagnosis** - If user provides enough info early, skip remaining phases
2. **Follow-up Questions** - Allow "why are you asking this?" explanations
3. **Confidence Scoring** - Track confidence in diagnosis based on answer quality
4. **History Context** - Use previous session context for returning users
5. **Cost Tracking** - Add estimated_cost_usd for each conversation

---

*Document updated: December 2024*
*Version: 2.0 - Added Automated Demo Flow*
