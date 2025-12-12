# BusinessSenseAgent - Socratic questioning with LangGraph StateGraph
from typing import Any, Dict, List, Literal, Optional, Annotated
import operator
import json
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from src.agents.base import BaseAgent
from src.models.agents import BusinessDiagnosis, BusinessAgentQuestions
from src.utils.logger import log_agent_call, get_logger


class BusinessAgentState(TypedDict):
    """State for the BusinessSenseAgent workflow."""
    messages: Annotated[List[BaseMessage], operator.add]
    task: str
    session_id: Optional[str]
    questions_asked: int
    max_questions: int
    current_phase: Literal["identify", "clarify", "diagnose"]
    collected_answers: Dict[str, str]
    diagnosis: Optional[Dict[str, Any]]
    needs_more_info: bool


class BusinessSenseAgent(BaseAgent):
    """
    Agent specialized in business problem diagnosis through Socratic questioning.
    
    Uses LangGraph StateGraph to manage the multi-turn conversation flow:
    1. AskQuestion - Ask clarifying questions
    2. EvaluateAnswers - Analyze user responses
    3. FinalizeDiagnosis - Generate final BusinessDiagnosis
    """
    
    def __init__(self, session_id: Optional[str] = None):
        super().__init__(session_id)
        self._graph = None
    
    @property
    def agent_type(self) -> str:
        return "business_sense_agent"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert business consultant with deep expertise in problem diagnosis.
Your approach is Socratic - you ask questions to understand before proposing solutions.

Your diagnostic process follows these phases:

1. PROBLEM IDENTIFICATION (First Phase):
   - When did this problem first start?
   - What measurable impact has it had? (%, $, etc.)
   - Is this in the company's TOP 3 priorities?

2. SCOPE & URGENCY CLARIFICATION (Second Phase):
   - Who is most affected by this problem?
   - What happens if nothing changes in 6 months?
   - Have you tried any solutions before? Why did they fail?

3. ROOT CAUSE DISCOVERY (Third Phase):
   - Do you need a solution or first need visibility into the cause?
   - What data/metrics do you currently track related to this?
   - What does success look like for you?

IMPORTANT RULES:
- Ask 2-3 questions at a time, maximum
- Adapt questions based on previous answers
- Look for hidden problems beyond what the customer states
- Assess urgency level (Low, Medium, Critical)
- Always distinguish between stated problem and actual business problem"""
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for business analysis."""
        
        async def ask_questions(state: BusinessAgentState) -> Dict[str, Any]:
            """Generate clarifying questions based on current state."""
            phase = state["current_phase"]
            task = state["task"]
            collected = state.get("collected_answers", {})
            
            # Build context from previous answers
            context = ""
            if collected:
                context = "\n\nPrevious answers from the customer:\n"
                for q, a in collected.items():
                    context += f"Q: {q}\nA: {a}\n"
            
            phase_prompts = {
                "identify": "Ask 2-3 questions to understand WHEN this problem started, its MEASURABLE IMPACT, and its PRIORITY level.",
                "clarify": "Ask 2-3 questions to understand WHO is affected, the CONSEQUENCES of inaction, and PREVIOUS SOLUTION ATTEMPTS.",
                "diagnose": "Ask 2-3 questions to understand whether they need a SOLUTION or VISIBILITY, what DATA they track, and what SUCCESS looks like."
            }
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("system", f"Current phase: {phase}\n{phase_prompts[phase]}{context}"),
                ("human", f"Customer's initial problem statement: {task}\n\nGenerate 2-3 targeted questions for this phase. Respond with a JSON object containing 'questions' (list of strings) and 'category' (string describing what you're trying to understand).")
            ])
            
            response = await self.llm.ainvoke(prompt.format_messages(task=task))
            
            # Parse the response
            try:
                content = response.content
                # Try to extract JSON from the response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                data = json.loads(content)
                questions = data.get("questions", [])
                category = data.get("category", phase)
            except (json.JSONDecodeError, IndexError):
                # Fallback: extract questions from text
                questions = [line.strip() for line in response.content.split("\n") if "?" in line][:3]
                category = phase
            
            return {
                "messages": [AIMessage(content=json.dumps({"questions": questions, "category": category}))],
                "questions_asked": state["questions_asked"] + 1,
                "needs_more_info": True
            }
        
        async def evaluate_answers(state: BusinessAgentState) -> Dict[str, Any]:
            """Evaluate if we have enough information to proceed."""
            questions_asked = state["questions_asked"]
            max_questions = state["max_questions"]
            current_phase = state["current_phase"]
            
            # Determine next phase or if we can proceed to diagnosis
            if questions_asked >= max_questions:
                return {"current_phase": "diagnose", "needs_more_info": False}
            
            phase_progression = {
                "identify": "clarify",
                "clarify": "diagnose",
                "diagnose": "diagnose"
            }
            
            # Move to next phase if we have answers
            if state.get("collected_answers"):
                next_phase = phase_progression[current_phase]
                return {"current_phase": next_phase, "needs_more_info": next_phase != "diagnose"}
            
            return {"needs_more_info": True}
        
        async def finalize_diagnosis(state: BusinessAgentState) -> Dict[str, Any]:
            """Generate the final BusinessDiagnosis."""
            task = state["task"]
            collected = state.get("collected_answers", {})
            
            # Build comprehensive context
            context = f"Original problem: {task}\n\nCollected information:\n"
            for q, a in collected.items():
                context += f"Q: {q}\nA: {a}\n"
            
            parser = PydanticOutputParser(pydantic_object=BusinessDiagnosis)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("system", "Based on your analysis, provide a final diagnosis."),
                ("system", f"You must respond in this JSON format:\n{parser.get_format_instructions()}"),
                ("human", context)
            ])
            
            try:
                chain = prompt | self.llm | parser
                diagnosis = await chain.ainvoke({})
                return {
                    "diagnosis": diagnosis.model_dump(),
                    "needs_more_info": False,
                    "messages": [AIMessage(content=f"Diagnosis complete: {diagnosis.model_dump_json()}")]
                }
            except Exception as e:
                self.logger.error(f"Diagnosis generation failed: {e}")
                return {
                    "diagnosis": {
                        "customer_stated_problem": task,
                        "identified_business_problem": "Unable to complete analysis",
                        "hidden_root_risk": "Insufficient information",
                        "urgency_level": "Medium"
                    },
                    "needs_more_info": False
                }
        
        def should_continue(state: BusinessAgentState) -> Literal["ask_questions", "finalize"]:
            """Determine if we need more questions or can finalize."""
            if state.get("needs_more_info", True) and state["questions_asked"] < state["max_questions"]:
                return "ask_questions"
            return "finalize"
        
        # Build the graph
        builder = StateGraph(BusinessAgentState)
        
        # Add nodes
        builder.add_node("ask_questions", ask_questions)
        builder.add_node("evaluate", evaluate_answers)
        builder.add_node("finalize", finalize_diagnosis)
        
        # Add edges
        builder.add_edge(START, "ask_questions")
        builder.add_edge("ask_questions", "evaluate")
        builder.add_conditional_edges(
            "evaluate",
            should_continue,
            {"ask_questions": "ask_questions", "finalize": "finalize"}
        )
        builder.add_edge("finalize", END)
        
        return builder.compile()
    
    @property
    def graph(self):
        """Lazily build and cache the graph."""
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph
    
    @log_agent_call("business_sense_agent")
    async def execute(
        self,
        task: str,
        collected_answers: Optional[Dict[str, str]] = None,
        max_questions: int = 3,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute business analysis with Socratic questioning.
        
        For synchronous mode (no existing answers):
            Returns questions to ask the user
            
        For follow-up mode (with collected_answers):
            Continues analysis and may return more questions or final diagnosis
            
        Args:
            task: The business problem description
            collected_answers: Previous Q&A pairs from the conversation
            max_questions: Maximum question rounds before forcing diagnosis
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            
        Returns:
            Dict with either 'questions' (List[str]) or 'diagnosis' (BusinessDiagnosis)
        """
        self.logger.info(f"BusinessSenseAgent executing: {task[:100]}...")
        
        # Initialize state
        initial_state: BusinessAgentState = {
            "messages": [HumanMessage(content=task)],
            "task": task,
            "session_id": session_id,
            "questions_asked": 0 if not collected_answers else len(collected_answers),
            "max_questions": max_questions,
            "current_phase": "identify",
            "collected_answers": collected_answers or {},
            "diagnosis": None,
            "needs_more_info": True
        }
        
        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        # Check if we have a diagnosis
        if final_state.get("diagnosis"):
            return {
                "type": "diagnosis",
                "data": BusinessDiagnosis(**final_state["diagnosis"])
            }
        
        # Otherwise, return questions for the user
        last_message = final_state["messages"][-1] if final_state["messages"] else None
        if last_message:
            try:
                data = json.loads(last_message.content)
                return {
                    "type": "questions",
                    "data": BusinessAgentQuestions(
                        session_id=session_id or "default",
                        questions=data.get("questions", []),
                        category=data.get("category", "clarification")
                    )
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback
        return {
            "type": "error",
            "data": "Unable to process business analysis"
        }
    
    async def get_initial_questions(self, task: str, session_id: Optional[str] = None) -> BusinessAgentQuestions:
        """
        Get initial clarifying questions without starting full workflow.
        Useful for sync API to quickly return questions.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("system", "Generate 2-3 initial clarifying questions to understand this business problem better. Focus on: when it started, measurable impact, and priority level."),
            ("human", f"Customer's problem: {task}")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages(task=task))
        
        # Parse questions from response
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            data = json.loads(content)
            questions = data.get("questions", [])
        except (json.JSONDecodeError, IndexError):
            questions = [line.strip() for line in response.content.split("\n") if "?" in line][:3]
        
        return BusinessAgentQuestions(
            session_id=session_id or "default",
            questions=questions,
            category="problem_identification"
        )
