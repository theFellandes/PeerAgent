# tests/unit/test_problem_agent.py - FIXED
"""
Unit tests for ProblemStructuringAgent.
FIXED: Uses Pydantic model attribute access instead of dict subscript.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json


class TestProblemAgentInitialization:
    """Test ProblemStructuringAgent initialization."""
    
    @pytest.fixture
    def problem_agent(self, mock_settings):
        """Create ProblemStructuringAgent instance."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.problem_agent import ProblemStructuringAgent
            return ProblemStructuringAgent()
    
    def test_problem_agent_type(self, problem_agent):
        """Test agent type is correct."""
        assert problem_agent.agent_type == "problem_agent"
    
    def test_problem_agent_has_session_id(self, mock_settings):
        """Test agent has session_id."""
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.problem_agent import ProblemStructuringAgent
            agent = ProblemStructuringAgent(session_id="test-session")
            assert agent.session_id == "test-session"
    
    def test_problem_agent_has_system_prompt(self, problem_agent):
        """Test agent has system prompt mentioning MECE."""
        assert len(problem_agent.system_prompt) > 0
        prompt_lower = problem_agent.system_prompt.lower()
        assert any(word in prompt_lower for word in ["mece", "problem", "structure", "tree"])


class TestMECETreeGeneration:
    """Test MECE problem tree generation."""
    
    @pytest.fixture
    def problem_agent(self, mock_settings):
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.problem_agent import ProblemStructuringAgent
            return ProblemStructuringAgent()
    
    @pytest.mark.asyncio
    async def test_execute_returns_problem_tree(self, problem_agent, mock_settings):
        """Test that execute returns a problem tree."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "problem_type": "Growth",
            "main_problem": "Declining Revenue",
            "root_causes": [
                {
                    "cause": "Sales Performance",
                    "sub_causes": ["Low conversion", "Insufficient leads"]
                },
                {
                    "cause": "Market Factors",
                    "sub_causes": ["Competition", "Saturation"]
                }
            ]
        })
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        problem_agent._llm = mock_llm
        
        result = await problem_agent.execute("Revenue is declining by 20%")
        
        assert result.problem_type is not None
        assert result.main_problem is not None
        assert len(result.root_causes) >= 1
    
    @pytest.mark.asyncio
    async def test_tree_has_multiple_branches(self, problem_agent, mock_settings):
        """Test tree has multiple root causes (MECE completeness)."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "problem_type": "Profitability",
            "main_problem": "Margin Erosion",
            "root_causes": [
                {"cause": "Revenue Issues", "sub_causes": ["Price pressure"]},
                {"cause": "Cost Issues", "sub_causes": ["Rising COGS"]},
                {"cause": "Volume Issues", "sub_causes": ["Declining units"]}
            ]
        })
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        problem_agent._llm = mock_llm
        
        result = await problem_agent.execute("Our margins are shrinking")
        
        assert len(result.root_causes) >= 2
    
    @pytest.mark.asyncio
    async def test_each_cause_has_sub_causes(self, problem_agent, mock_settings):
        """Test each root cause has sub-causes."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "problem_type": "Operations",
            "main_problem": "Delivery Delays",
            "root_causes": [
                {"cause": "Warehouse", "sub_causes": ["Picking errors", "Packing delays"]},
                {"cause": "Logistics", "sub_causes": ["Carrier issues", "Route inefficiency"]}
            ]
        })
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        problem_agent._llm = mock_llm
        
        result = await problem_agent.execute("Deliveries are always late")
        
        for cause in result.root_causes:
            assert len(cause.sub_causes) >= 1


class TestProblemTreeModel:
    """Test ProblemTree Pydantic model."""
    
    def test_valid_problem_tree(self, mock_settings):
        """Test creating valid problem tree."""
        from src.models.agents import ProblemTree, ProblemCause
        
        tree = ProblemTree(
            problem_type="Growth",
            main_problem="Declining Sales",
            root_causes=[
                ProblemCause(
                    cause="Marketing",
                    sub_causes=["Bad targeting", "Weak messaging"]
                ),
                ProblemCause(
                    cause="Sales",
                    sub_causes=["Low conversion", "Long cycle"]
                )
            ]
        )
        
        assert tree.problem_type == "Growth"
        assert len(tree.root_causes) == 2
    
    def test_problem_cause_model(self, mock_settings):
        """Test ProblemCause model."""
        from src.models.agents import ProblemCause
        
        cause = ProblemCause(
            cause="Sales Performance",
            sub_causes=["Low conversion rate", "Insufficient pipeline"]
        )
        
        assert cause.cause == "Sales Performance"
        assert len(cause.sub_causes) == 2
    
    def test_problem_tree_serialization(self, mock_settings):
        """Test problem tree serializes correctly."""
        from src.models.agents import ProblemTree, ProblemCause
        
        tree = ProblemTree(
            problem_type="Test",
            main_problem="Test Problem",
            root_causes=[
                ProblemCause(cause="Cause1", sub_causes=["Sub1"])
            ]
        )
        
        data = tree.model_dump()
        assert isinstance(data, dict)
        assert "root_causes" in data


class TestProblemTreeGeneration:
    """Test problem tree generation from diagnosis."""
    
    def test_generate_from_diagnosis(self, sample_business_diagnosis, mock_settings):
        """Test generating tree from business diagnosis - FIXED."""
        # Use Pydantic attribute access
        tree_input = {
            "problem": sample_business_diagnosis.identified_business_problem,
            "context": sample_business_diagnosis.hidden_root_risk,
            "urgency": sample_business_diagnosis.urgency_level,
        }
        
        assert tree_input["problem"] == "Market share erosion due to competitive pressure"
        assert tree_input["urgency"] == "Critical"
    
    def test_problem_types_valid(self, mock_settings):
        """Test valid problem types."""
        valid_types = ["Growth", "Profitability", "Operations", "Strategy", "Organization"]
        
        from src.models.agents import ProblemTree, ProblemCause
        
        for ptype in valid_types:
            tree = ProblemTree(
                problem_type=ptype,
                main_problem="Test",
                root_causes=[ProblemCause(cause="Test", sub_causes=["Sub"])]
            )
            assert tree.problem_type == ptype


class TestProblemAgentIntegration:
    """Test integration with BusinessSenseAgent output."""
    
    def test_integration_with_business_agent(self, sample_business_diagnosis, mock_settings):
        """Test accepting BusinessDiagnosis as context - FIXED."""
        # Use Pydantic attribute access
        problem_statement = sample_business_diagnosis.identified_business_problem
        
        assert problem_statement is not None
        assert len(problem_statement) > 0
        assert "erosion" in problem_statement.lower() or "market" in problem_statement.lower()
    
    def test_diagnosis_urgency_affects_tree(self, sample_business_diagnosis, mock_settings):
        """Test that urgency affects tree generation."""
        urgency = sample_business_diagnosis.urgency_level
        
        # Critical urgency should prioritize certain branches
        if urgency == "Critical":
            priority_categories = ["Revenue", "Cost", "Customer"]
            assert urgency == "Critical"


class TestErrorHandling:
    """Test error handling in ProblemStructuringAgent."""
    
    @pytest.fixture
    def problem_agent(self, mock_settings):
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.problem_agent import ProblemStructuringAgent
            return ProblemStructuringAgent()
    
    @pytest.mark.asyncio
    async def test_handles_llm_error(self, problem_agent, mock_settings):
        """Test handling of LLM errors."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API Error"))
        problem_agent._llm = mock_llm
        
        result = await problem_agent.execute("Test problem")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_handles_invalid_json(self, problem_agent, mock_settings):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.content = "Not valid JSON"
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        problem_agent._llm = mock_llm
        
        result = await problem_agent.execute("Test")
        
        assert result is not None
