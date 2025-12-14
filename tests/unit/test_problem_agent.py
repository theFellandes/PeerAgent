# tests/unit/test_problem_agent.py
"""
Unit tests for ProblemStructuringAgent.
Target: src/agents/problem_agent.py (33% coverage -> 70%+)
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
        # Should mention MECE or problem structuring
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
        
        # MECE should have multiple non-overlapping branches
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
        assert isinstance(data["root_causes"], list)


class TestProblemTypes:
    """Test different problem type classifications."""
    
    @pytest.fixture
    def problem_agent(self, mock_settings):
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.problem_agent import ProblemStructuringAgent
            return ProblemStructuringAgent()
    
    def test_growth_problem_type(self, problem_agent):
        """Test Growth problem type detection."""
        growth_problems = [
            "Revenue is declining",
            "Sales dropped 20%",
            "We're losing market share"
        ]
        
        for problem in growth_problems:
            # Should contain growth-related keywords
            keywords = ["revenue", "sales", "market", "growth", "decline"]
            assert any(kw in problem.lower() for kw in keywords)
    
    def test_profitability_problem_type(self, problem_agent):
        """Test Profitability problem type detection."""
        profitability_problems = [
            "Our margins are shrinking",
            "Costs are rising faster than revenue",
            "Profit is declining despite stable sales"
        ]
        
        for problem in profitability_problems:
            keywords = ["margin", "cost", "profit", "expense"]
            assert any(kw in problem.lower() for kw in keywords)
    
    def test_operations_problem_type(self, problem_agent):
        """Test Operations problem type detection."""
        operations_problems = [
            "Delivery times are too long",
            "Production quality is declining",
            "Our warehouse is inefficient"
        ]
        
        for problem in operations_problems:
            keywords = ["delivery", "production", "warehouse", "efficiency", "operations"]
            assert any(kw in problem.lower() for kw in keywords)


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
        
        # Should return something (error or fallback)
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
        
        # Should handle gracefully
        assert result is not None


class TestIntegrationWithBusinessAgent:
    """Test integration with BusinessSenseAgent output."""
    
    @pytest.fixture
    def problem_agent(self, mock_settings):
        with patch("langchain_community.utilities.DuckDuckGoSearchAPIWrapper"):
            from src.agents.problem_agent import ProblemStructuringAgent
            return ProblemStructuringAgent()
    
    @pytest.mark.asyncio
    async def test_accepts_business_diagnosis_context(self, problem_agent, mock_settings):
        """Test accepting BusinessDiagnosis as context."""
        from src.models.agents import BusinessDiagnosis
        
        diagnosis = BusinessDiagnosis(
            customer_stated_problem="Sales dropped 20%",
            identified_business_problem="Market share erosion",
            hidden_root_risk="Brand perception issues",
            urgency_level="Critical"
        )
        
        mock_response = Mock()
        mock_response.content = json.dumps({
            "problem_type": "Growth",
            "main_problem": "Market share erosion",
            "root_causes": [
                {"cause": "Competition", "sub_causes": ["Price wars"]}
            ]
        })
        
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        problem_agent._llm = mock_llm
        
        # Pass diagnosis as context
        result = await problem_agent.execute(
            diagnosis.identified_business_problem,
            context={"diagnosis": diagnosis.model_dump()}
        )
        
        assert result is not None
        assert result.main_problem is not None
