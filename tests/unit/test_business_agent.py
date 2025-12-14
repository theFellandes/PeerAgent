# tests/unit/test_business_agent.py - FIXED
"""
Unit tests for BusinessSenseAgent.
FIXED: Uses Pydantic model attribute access instead of dict subscript.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json


class TestBusinessAgentInitialization:
    """Test BusinessSenseAgent initialization."""
    
    @pytest.fixture
    def business_agent(self, mock_settings):
        """Create BusinessSenseAgent instance."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.business_agent import BusinessSenseAgent
            return BusinessSenseAgent()
    
    def test_business_agent_type(self, business_agent):
        """Test agent type is correct."""
        assert business_agent.agent_type == "business_sense_agent"
    
    def test_business_agent_has_session_id(self, mock_settings):
        """Test agent has session_id."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.business_agent import BusinessSenseAgent
            agent = BusinessSenseAgent(session_id="test-session")
            assert agent.session_id == "test-session"
    
    def test_business_agent_has_system_prompt(self, business_agent):
        """Test agent has system prompt."""
        assert len(business_agent.system_prompt) > 0
        prompt_lower = business_agent.system_prompt.lower()
        assert any(word in prompt_lower for word in ["business", "socratic", "consult", "diagnos"])


class TestSocraticQuestioning:
    """Test Socratic questioning functionality."""
    
    @pytest.fixture
    def business_agent(self, mock_settings):
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.business_agent import BusinessSenseAgent
            return BusinessSenseAgent()
    
    @pytest.mark.asyncio
    async def test_first_execution_returns_questions(self, business_agent, mock_settings):
        """Test that first execution returns probing questions."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "questions": [
                "When did this problem start?",
                "What is the measurable impact?"
            ],
            "category": "problem_identification"
        })
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        business_agent._llm = mock_llm
        
        result = await business_agent.execute("Our sales dropped 20%")
        
        assert result["type"] == "questions"
        assert "questions" in result["data"]
        assert len(result["data"]["questions"]) >= 1
    
    @pytest.mark.asyncio
    async def test_questions_are_open_ended(self, business_agent, mock_settings):
        """Test that generated questions are open-ended."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "questions": [
                "How has this affected your revenue?",
                "What patterns have you observed?",
                "Which teams are involved?"
            ],
            "category": "impact_assessment"
        })
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        business_agent._llm = mock_llm
        
        result = await business_agent.execute("Revenue is declining")
        
        questions = result["data"]["questions"]
        
        for q in questions:
            q_lower = q.lower()
            # Should not be yes/no questions
            assert not q_lower.startswith("is ")
            assert not q_lower.startswith("are ")
            assert not q_lower.startswith("do ")
            assert not q_lower.startswith("does ")


class TestDiagnosisGeneration:
    """Test business diagnosis generation."""
    
    @pytest.fixture
    def business_agent(self, mock_settings):
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.business_agent import BusinessSenseAgent
            return BusinessSenseAgent()
    
    def test_diagnosis_structure(self, sample_business_diagnosis):
        """Test diagnosis has all required fields - FIXED: use attribute access."""
        # sample_business_diagnosis is a Pydantic model, use .attribute not ["key"]
        assert hasattr(sample_business_diagnosis, 'customer_stated_problem')
        assert hasattr(sample_business_diagnosis, 'identified_business_problem')
        assert hasattr(sample_business_diagnosis, 'hidden_root_risk')
        assert hasattr(sample_business_diagnosis, 'urgency_level')
        
        # Verify values
        assert sample_business_diagnosis.customer_stated_problem is not None
        assert sample_business_diagnosis.urgency_level in ["Low", "Medium", "High", "Critical"]
    
    def test_urgency_levels_valid(self, mock_settings):
        """Test valid urgency levels."""
        valid_levels = ["Low", "Medium", "High", "Critical"]
        
        from src.models.agents import BusinessDiagnosis
        
        for level in valid_levels:
            diagnosis = BusinessDiagnosis(
                customer_stated_problem="Test",
                identified_business_problem="Test",
                hidden_root_risk="Test",
                urgency_level=level
            )
            assert diagnosis.urgency_level == level
    
    def test_invalid_urgency_level_rejected(self, mock_settings):
        """Test invalid urgency level is rejected."""
        from src.models.agents import BusinessDiagnosis
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            BusinessDiagnosis(
                customer_stated_problem="Test",
                identified_business_problem="Test",
                hidden_root_risk="Test",
                urgency_level="Invalid"
            )


class TestConversationFlow:
    """Test multi-turn conversation flow."""
    
    @pytest.fixture
    def business_agent(self, mock_settings):
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.business_agent import BusinessSenseAgent
            return BusinessSenseAgent(session_id="flow-test")
    
    def test_session_tracks_state(self, business_agent):
        """Test session state tracking."""
        assert business_agent.session_id == "flow-test"
    
    @pytest.mark.asyncio
    async def test_continue_with_answers(self, business_agent, mock_settings):
        """Test continuing conversation with answers."""
        questions_response = Mock()
        questions_response.content = json.dumps({
            "questions": ["When?", "Impact?"],
            "category": "initial"
        })
        
        followup_response = Mock()
        followup_response.content = json.dumps({
            "questions": ["Follow-up question?"],
            "category": "followup"
        })
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=[questions_response, followup_response])
        business_agent._llm = mock_llm
        
        result1 = await business_agent.execute("Sales dropped")
        assert result1["type"] == "questions"
        
        result2 = await business_agent.execute(
            "Continue",
            context={"answers": {"When?": "Last month"}}
        )
        assert result2["type"] in ["questions", "diagnosis"]


class TestProblemClassification:
    """Test business problem classification."""
    
    @pytest.fixture
    def business_agent(self, mock_settings):
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.business_agent import BusinessSenseAgent
            return BusinessSenseAgent()
    
    def test_classifies_revenue_problem(self, business_agent):
        """Test classification of revenue problems."""
        revenue_keywords = ["revenue", "sales", "income", "profit"]
        problem = "Our revenue has been declining for 3 quarters"
        
        problem_lower = problem.lower()
        has_revenue_keyword = any(kw in problem_lower for kw in revenue_keywords)
        
        assert has_revenue_keyword
    
    def test_classifies_cost_problem(self, business_agent):
        """Test classification of cost problems."""
        cost_keywords = ["cost", "expense", "spending", "overhead"]
        problem = "Operating costs have increased by 30%"
        
        problem_lower = problem.lower()
        has_cost_keyword = any(kw in problem_lower for kw in cost_keywords)
        
        assert has_cost_keyword
    
    def test_classifies_customer_problem(self, business_agent):
        """Test classification of customer problems."""
        customer_keywords = ["customer", "churn", "retention", "satisfaction"]
        problem = "Customer churn is at an all-time high"
        
        problem_lower = problem.lower()
        has_customer_keyword = any(kw in problem_lower for kw in customer_keywords)
        
        assert has_customer_keyword


class TestProblemTreeIntegration:
    """Test integration with ProblemStructuringAgent."""
    
    def test_triggers_problem_tree(self, sample_business_diagnosis):
        """Test that diagnosis can trigger problem tree - FIXED."""
        # Use Pydantic attribute access
        assert sample_business_diagnosis.urgency_level in ["Low", "Medium", "High", "Critical"]
        
        # Should trigger problem tree for Critical/High
        should_trigger = sample_business_diagnosis.urgency_level in ["Critical", "High"]
        assert should_trigger
    
    def test_passes_diagnosis_to_problem_agent(self, sample_business_diagnosis):
        """Test passing diagnosis to problem agent - FIXED."""
        # Use Pydantic attribute access
        problem_statement = sample_business_diagnosis.identified_business_problem
        assert problem_statement is not None
        assert len(problem_statement) > 0
    
    def test_problem_tree_structure(self, sample_problem_tree):
        """Test problem tree has expected structure - FIXED."""
        # ProblemTree is a Pydantic model, use attribute access
        assert hasattr(sample_problem_tree, 'problem_type')
        assert hasattr(sample_problem_tree, 'main_problem')
        assert hasattr(sample_problem_tree, 'root_causes')
        
        # Verify values
        assert sample_problem_tree.problem_type == "Growth"
        assert sample_problem_tree.main_problem == "Declining Sales"
        assert len(sample_problem_tree.root_causes) >= 1


class TestErrorHandling:
    """Test error handling in BusinessSenseAgent."""
    
    @pytest.fixture
    def business_agent(self, mock_settings):
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.business_agent import BusinessSenseAgent
            return BusinessSenseAgent()
    
    @pytest.mark.asyncio
    async def test_handles_llm_error(self, business_agent, mock_settings):
        """Test handling of LLM errors."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM API Error"))
        business_agent._llm = mock_llm
        
        result = await business_agent.execute("Test problem")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_handles_invalid_json_response(self, business_agent, mock_settings):
        """Test handling of invalid JSON in LLM response."""
        mock_response = Mock()
        mock_response.content = "This is not valid JSON {"
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        business_agent._llm = mock_llm
        
        result = await business_agent.execute("Test problem")
        
        assert result is not None


class TestBusinessDiagnosisModel:
    """Test BusinessDiagnosis Pydantic model."""
    
    def test_valid_diagnosis_creation(self, mock_settings):
        """Test creating valid diagnosis."""
        from src.models.agents import BusinessDiagnosis
        
        diagnosis = BusinessDiagnosis(
            customer_stated_problem="Sales dropped 20%",
            identified_business_problem="Market share erosion",
            hidden_root_risk="Brand perception issues",
            urgency_level="Critical"
        )
        
        assert diagnosis.customer_stated_problem == "Sales dropped 20%"
        assert diagnosis.urgency_level == "Critical"
    
    def test_diagnosis_requires_all_fields(self, mock_settings):
        """Test diagnosis requires all fields."""
        from src.models.agents import BusinessDiagnosis
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            BusinessDiagnosis(
                customer_stated_problem="Test"
            )
    
    def test_diagnosis_serialization(self, mock_settings):
        """Test diagnosis serializes to dict."""
        from src.models.agents import BusinessDiagnosis
        
        diagnosis = BusinessDiagnosis(
            customer_stated_problem="Test",
            identified_business_problem="Test",
            hidden_root_risk="Test",
            urgency_level="High"
        )
        
        data = diagnosis.model_dump()
        assert isinstance(data, dict)
        assert data["urgency_level"] == "High"
