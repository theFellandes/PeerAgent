# -*- coding: utf-8 -*-
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
    
    Uses a multi-turn conversation flow:
    1. First call (no answers): Generate clarifying questions and RETURN them to user
    2. Subsequent calls (with answers): Continue questioning or generate diagnosis
    
    The key insight is that this agent should NOT run through all phases in one execution.
    It should stop and return questions, then wait for user input.
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
Your approach is Socratic - you ask probing questions to understand problems before proposing solutions.

## Your Questioning Approach

You help clients discover insights through guided questioning. Never jump to conclusions or solutions.

### Phase 1: PROBLEM IDENTIFICATION
Ask about:
- When exactly did this problem first start? What triggered it?
- What is the measurable impact? (specific %, $, numbers)
- Is this currently in the company's TOP 3 priorities? Why or why not?
- Who first noticed this issue and how?

### Phase 2: SCOPE & URGENCY CLARIFICATION  
Ask about:
- Who is most affected by this problem? (customers, employees, specific departments)
- What happens if nothing changes in the next 6 months?
- Have you tried any solutions before? What happened? Why did they fail?
- What resources (budget, time, people) are available to address this?

### Phase 3: ROOT CAUSE DISCOVERY
Ask about:
- Do you need a solution, or first need visibility into the actual cause?
- What data or metrics do you currently track related to this issue?
- What does success look like for you? How will you measure it?
- What constraints or blockers might prevent a solution?

## CRITICAL RULES
1. Ask 2-3 focused questions at a time - never more
2. Adapt your next questions based on the answers received
3. Look for hidden problems beyond the stated symptoms
4. Always distinguish between STATED problem and ACTUAL business problem
5. Be empathetic but professionally probing
6. Never provide solutions until you've completed the questioning phases"""
    
    @property
    def diagnosis_prompt(self) -> str:
        """Enhanced prompt for generating the final diagnosis."""
        return """Based on the Socratic questioning dialogue, provide a comprehensive business diagnosis.

## Analysis Framework

### 1. Customer Stated Problem
What the customer initially described as their problem. Quote or closely paraphrase their words.

### 2. Identified Business Problem  
The actual underlying business issue you've uncovered through questioning. This is often different from or deeper than what the customer initially stated.

### 3. Hidden Root Risk
The deeper systemic risk or vulnerability that could cause bigger problems if not addressed. Think about:
- What patterns might this problem be a symptom of?
- What could go wrong if this continues unchecked?
- What related issues might exist but weren't mentioned?

### 4. Urgency Assessment
Rate as Low, Medium, or Critical based on:
- **Low**: Problem causes inconvenience but no immediate business threat
- **Medium**: Problem affecting operations or revenue but manageable short-term
- **Critical**: Problem threatening business viability, safety, or requiring immediate action

Be specific and actionable in your diagnosis. Reference concrete details from the conversation."""

    async def _generate_questions(
        self,
        task: str,
        phase: str,
        collected_answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generate clarifying questions for the current phase."""
        
        # Build context from previous answers
        context = ""
        if collected_answers:
            context = "\n\n## Previous Answers from Customer:\n"
            for q, a in collected_answers.items():
                context += f"**Q:** {q}\n**A:** {a}\n\n"
        
        phase_instructions = {
            "identify": """You are in the PROBLEM IDENTIFICATION phase.
Ask 2-3 questions to understand:
- WHEN this problem started and what triggered it
- The MEASURABLE IMPACT (specific numbers, percentages, dollar amounts)
- Whether this is a TOP PRIORITY for the company""",
            
            "clarify": """You are in the SCOPE & URGENCY phase.
Ask 2-3 questions to understand:
- WHO is most affected by this problem
- The CONSEQUENCES if nothing changes in 6 months
- Any PREVIOUS SOLUTION ATTEMPTS and why they failed""",
            
            "diagnose": """You are in the ROOT CAUSE DISCOVERY phase.
Ask 2-3 final questions to understand:
- Whether they need a SOLUTION or first need VISIBILITY into the cause
- What DATA or METRICS they currently track
- What SUCCESS looks like and how they'll measure it"""
        }
        
        # Build the human message content (avoid f-string to prevent brace issues)
        human_content = f"""Customer's problem statement: {task}
{context}

Generate 2-3 targeted Socratic questions for this phase. 
Respond with a JSON object containing:
- "questions": an array of 2-3 question strings
- "category": a string describing what you're trying to understand
- "reasoning": a brief explanation of why these questions matter"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("system", phase_instructions.get(phase, phase_instructions["identify"])),
            ("human", human_content)
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        
        # Parse the response
        try:
            content = response.content
            # Try to extract JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            return {
                "questions": data.get("questions", [])[:3],  # Max 3 questions
                "category": data.get("category", phase),
                "reasoning": data.get("reasoning", "")
            }
        except (json.JSONDecodeError, IndexError) as e:
            self.logger.warning(f"Failed to parse questions JSON: {e}")
            # Fallback: extract questions from text
            questions = [line.strip() for line in response.content.split("\n") if "?" in line][:3]
            return {
                "questions": questions,
                "category": phase,
                "reasoning": ""
            }
    
    async def _generate_diagnosis(
        self,
        task: str,
        collected_answers: Dict[str, str]
    ) -> BusinessDiagnosis:
        """Generate the final business diagnosis after questioning is complete."""
        
        # Build comprehensive context
        context = f"## Original Problem Statement\n{task}\n\n"
        context += "## Collected Information from Socratic Dialogue\n\n"
        for q, a in collected_answers.items():
            context += f"**Q:** {q}\n**A:** {a}\n\n"
        
        parser = PydanticOutputParser(pydantic_object=BusinessDiagnosis)
        
        # Escape curly braces in format instructions
        format_instructions = parser.get_format_instructions()
        escaped_instructions = format_instructions.replace("{", "{{").replace("}", "}}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("system", self.diagnosis_prompt),
            ("system", f"You must respond in this exact JSON format:\n{escaped_instructions}"),
            ("human", context)
        ])
        
        try:
            chain = prompt | self.llm | parser
            diagnosis = await chain.ainvoke({})
            return diagnosis
        except Exception as e:
            self.logger.error(f"Diagnosis generation failed: {e}")
            # Return a structured fallback
            return BusinessDiagnosis(
                customer_stated_problem=task,
                identified_business_problem="Unable to complete full analysis - insufficient information gathered",
                hidden_root_risk="Unknown - recommend conducting complete diagnostic interview",
                urgency_level="Medium"
            )
    
    def _determine_next_phase(
        self,
        collected_answers: Dict[str, str],
        max_question_rounds: int = 3
    ) -> Literal["identify", "clarify", "diagnose", "complete"]:
        """Determine the next phase of questioning based on collected answers.
        
        Phase progression:
        - 0 answers: identify phase
        - 1-3 answers: clarify phase  
        - 4-6 answers: diagnose phase
        - 7+ answers OR max rounds reached: complete (generate diagnosis)
        """
        num_answers = len(collected_answers)
        
        # Calculate how many rounds of questions have been answered
        # (assuming ~3 questions per round)
        rounds_completed = (num_answers + 2) // 3  # ceiling division
        
        if rounds_completed >= max_question_rounds:
            return "complete"
        
        if num_answers == 0:
            return "identify"
        elif num_answers <= 3:
            return "clarify"
        elif num_answers <= 6:
            return "diagnose"
        else:
            return "complete"
    
    @log_agent_call("business_sense_agent")
    async def execute(
        self,
        task: str,
        collected_answers: Optional[Dict[str, str]] = None,
        max_questions: int = 3,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        chat_history: Optional[List[BaseMessage]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute business analysis with Socratic questioning.
        
        KEY BEHAVIOR:
        - First call (no collected_answers): Returns questions to ask the user
        - Subsequent calls (with collected_answers): Either returns more questions or final diagnosis
        
        This enables true multi-turn Socratic dialogue where the user must respond.
        
        Args:
            task: The business problem description
            collected_answers: Previous Q&A pairs from the conversation (Dict[question, answer])
            max_questions: Maximum question rounds before forcing diagnosis (default 3)
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            chat_history: Previous conversation messages for context
            
        Returns:
            Dict with either:
            - {"type": "questions", "data": BusinessAgentQuestions} - User should answer these
            - {"type": "diagnosis", "data": BusinessDiagnosis} - Final analysis
        """
        self.logger.info(f"BusinessSenseAgent executing: {task[:100]}...")
        collected_answers = collected_answers or {}
        
        # Determine current phase based on answer count
        current_phase = self._determine_next_phase(collected_answers, max_questions)
        
        self.logger.info(f"Current phase: {current_phase}, answers collected: {len(collected_answers)}")
        
        # If we have enough information, generate diagnosis
        if current_phase == "complete":
            self.logger.info("Generating final diagnosis...")
            diagnosis = await self._generate_diagnosis(task, collected_answers)
            return {
                "type": "diagnosis",
                "data": diagnosis
            }
        
        # Otherwise, generate more questions for the current phase
        self.logger.info(f"Generating questions for phase: {current_phase}")
        question_data = await self._generate_questions(task, current_phase, collected_answers)
        
        return {
            "type": "questions",
            "data": BusinessAgentQuestions(
                session_id=session_id or "default",
                questions=question_data["questions"],
                category=question_data["category"]
            )
        }
    
    async def get_initial_questions(self, task: str, session_id: Optional[str] = None) -> BusinessAgentQuestions:
        """
        Get initial clarifying questions without starting full workflow.
        Useful for sync API to quickly return questions.
        """
        result = await self.execute(task=task, session_id=session_id)
        
        if result["type"] == "questions":
            return result["data"]
        
        # Fallback if somehow got diagnosis (shouldn't happen on first call)
        return BusinessAgentQuestions(
            session_id=session_id or "default",
            questions=[
                "When did you first notice this problem?",
                "What is the measurable impact on your business?",
                "Is this currently in your top 3 priorities?"
            ],
            category="problem_identification"
        )
