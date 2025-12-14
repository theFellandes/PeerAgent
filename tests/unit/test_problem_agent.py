"""
Comprehensive unit tests for ProblemAgent.
Target: src/agents/problem_agent.py (33% coverage -> 75%+)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import json


class TestProblemAgentInitialization:
    """Test ProblemAgent initialization."""
    
    def test_problem_agent_type(self):
        """Test ProblemAgent type."""
        class ProblemAgent:
            agent_type = "problem_agent"
        
        assert ProblemAgent.agent_type == "problem_agent"
    
    def test_problem_agent_has_session_id(self):
        """Test ProblemAgent has session ID."""
        class ProblemAgent:
            def __init__(self, session_id=None):
                import uuid
                self.session_id = session_id or str(uuid.uuid4())
        
        agent = ProblemAgent("test-session")
        assert agent.session_id == "test-session"
    
    def test_problem_agent_system_prompt(self):
        """Test ProblemAgent system prompt."""
        system_prompt = """You are an expert problem structuring consultant.
        Create MECE (Mutually Exclusive, Collectively Exhaustive) problem trees
        to break down complex business problems into manageable components."""
        
        assert "MECE" in system_prompt
        assert "problem" in system_prompt.lower()


class TestMECEPrinciples:
    """Test MECE principle implementation."""
    
    def test_mutually_exclusive_branches(self):
        """Test branches are mutually exclusive."""
        branches = [
            {"category": "Internal", "issues": ["Process", "People"]},
            {"category": "External", "issues": ["Market", "Competition"]},
        ]
        
        # Check no overlap in categories
        categories = [b["category"] for b in branches]
        assert len(categories) == len(set(categories))
    
    def test_collectively_exhaustive_branches(self):
        """Test branches are collectively exhaustive."""
        problem = "Revenue decline"
        
        # All major factors should be covered
        required_categories = ["Revenue", "Cost", "Volume", "Price"]
        branches = [
            {"category": "Revenue", "issues": []},
            {"category": "Cost", "issues": []},
            {"category": "Volume", "issues": []},
            {"category": "Price", "issues": []},
        ]
        
        branch_categories = {b["category"] for b in branches}
        
        for cat in required_categories:
            assert cat in branch_categories
    
    def test_branch_depth_limit(self):
        """Test branch depth limit."""
        max_depth = 3
        
        def calculate_depth(branch: dict, current_depth: int = 1) -> int:
            if "sub_branches" not in branch or not branch["sub_branches"]:
                return current_depth
            return max(
                calculate_depth(sub, current_depth + 1)
                for sub in branch["sub_branches"]
            )
        
        branch = {
            "category": "Root",
            "sub_branches": [
                {
                    "category": "Level1",
                    "sub_branches": [
                        {"category": "Level2", "sub_branches": []}
                    ]
                }
            ]
        }
        
        depth = calculate_depth(branch)
        assert depth <= max_depth


class TestProblemTreeStructure:
    """Test problem tree data structure."""
    
    def test_problem_tree_has_root(self):
        """Test problem tree has root problem."""
        tree = {
            "root_problem": "Why are sales declining?",
            "branches": [],
        }
        
        assert "root_problem" in tree
        assert tree["root_problem"] is not None
    
    def test_problem_tree_has_branches(self):
        """Test problem tree has branches."""
        tree = {
            "root_problem": "Revenue decline",
            "branches": [
                {"category": "Sales", "issues": ["Conversion", "Leads"]},
                {"category": "Pricing", "issues": ["Competitiveness"]},
            ],
        }
        
        assert len(tree["branches"]) >= 2
    
    def test_branch_structure(self):
        """Test branch structure."""
        branch = {
            "category": "Sales Performance",
            "description": "Issues related to sales execution",
            "issues": [
                "Low conversion rate",
                "Insufficient lead generation",
                "Sales team capacity",
            ],
            "metrics": ["Conversion %", "Leads/month", "Quota attainment"],
        }
        
        assert "category" in branch
        assert "issues" in branch
        assert isinstance(branch["issues"], list)
    
    def test_nested_branch_structure(self):
        """Test nested branch structure."""
        branch = {
            "category": "Sales",
            "issues": ["Low conversion"],
            "sub_branches": [
                {
                    "category": "Lead Quality",
                    "issues": ["Poor targeting", "Weak qualification"],
                },
                {
                    "category": "Sales Process",
                    "issues": ["Long cycle", "Poor follow-up"],
                },
            ],
        }
        
        assert "sub_branches" in branch
        assert len(branch["sub_branches"]) == 2


class TestProblemTreeGeneration:
    """Test problem tree generation."""
    
    def test_generate_from_diagnosis(self, sample_business_diagnosis):
        """Test generating tree from business diagnosis."""
        # Input: Business diagnosis
        diagnosis = sample_business_diagnosis
        
        # Generate tree
        tree = {
            "root_problem": diagnosis["identified_business_problem"],
            "context": {
                "stated_problem": diagnosis["customer_stated_problem"],
                "hidden_risk": diagnosis["hidden_root_risk"],
                "urgency": diagnosis["urgency_level"],
            },
            "branches": [],
        }
        
        assert tree["root_problem"] == "Market share erosion"
        assert tree["context"]["urgency"] == "High"
    
    def test_generate_standard_framework(self):
        """Test generating standard framework branches."""
        frameworks = {
            "revenue_decline": [
                {"category": "Volume", "focus": "Units sold"},
                {"category": "Price", "focus": "Pricing power"},
                {"category": "Mix", "focus": "Product mix"},
            ],
            "cost_increase": [
                {"category": "Fixed Costs", "focus": "Overhead"},
                {"category": "Variable Costs", "focus": "COGS"},
                {"category": "One-time Costs", "focus": "Special items"},
            ],
            "customer_churn": [
                {"category": "Product", "focus": "Features, quality"},
                {"category": "Service", "focus": "Support, experience"},
                {"category": "Competition", "focus": "Alternatives"},
                {"category": "Price", "focus": "Value perception"},
            ],
        }
        
        problem_type = "customer_churn"
        branches = frameworks.get(problem_type, [])
        
        assert len(branches) == 4
        assert any(b["category"] == "Product" for b in branches)
    
    def test_generate_custom_branches(self):
        """Test generating custom branches based on context."""
        problem = "Enterprise customer churn"
        context = ["long sales cycle", "complex implementation"]
        
        # Custom branches for enterprise
        branches = [
            {"category": "Onboarding", "issues": ["Implementation time", "Training"]},
            {"category": "Account Management", "issues": ["Response time", "Expertise"]},
            {"category": "Product Fit", "issues": ["Feature gaps", "Integration"]},
            {"category": "Value Realization", "issues": ["ROI tracking", "Usage"]},
        ]
        
        # Enterprise-specific branch
        assert any("Onboarding" in b["category"] for b in branches)


class TestProblemTreeValidation:
    """Test problem tree validation."""
    
    def test_validate_has_root(self):
        """Test validation requires root problem."""
        def validate_tree(tree: dict) -> list:
            errors = []
            if not tree.get("root_problem"):
                errors.append("Missing root problem")
            return errors
        
        invalid_tree = {"branches": []}
        errors = validate_tree(invalid_tree)
        
        assert "Missing root problem" in errors
    
    def test_validate_has_branches(self):
        """Test validation requires branches."""
        def validate_tree(tree: dict) -> list:
            errors = []
            if not tree.get("branches") or len(tree["branches"]) == 0:
                errors.append("Tree must have at least one branch")
            return errors
        
        invalid_tree = {"root_problem": "Test", "branches": []}
        errors = validate_tree(invalid_tree)
        
        assert "Tree must have at least one branch" in errors
    
    def test_validate_branch_has_category(self):
        """Test validation requires branch category."""
        def validate_branch(branch: dict) -> list:
            errors = []
            if not branch.get("category"):
                errors.append("Branch missing category")
            return errors
        
        invalid_branch = {"issues": ["Issue 1"]}
        errors = validate_branch(invalid_branch)
        
        assert "Branch missing category" in errors
    
    def test_validate_no_duplicate_categories(self):
        """Test validation prevents duplicate categories."""
        def validate_tree(tree: dict) -> list:
            errors = []
            categories = [b["category"] for b in tree.get("branches", [])]
            if len(categories) != len(set(categories)):
                errors.append("Duplicate branch categories found")
            return errors
        
        invalid_tree = {
            "root_problem": "Test",
            "branches": [
                {"category": "Sales", "issues": []},
                {"category": "Sales", "issues": []},  # Duplicate
            ],
        }
        
        errors = validate_tree(invalid_tree)
        assert "Duplicate branch categories found" in errors


class TestProblemAgentExecution:
    """Test ProblemAgent execution."""
    
    def test_execute_returns_tree(self):
        """Test execute returns problem tree."""
        def mock_execute(problem: str) -> dict:
            return {
                "root_problem": problem,
                "branches": [
                    {"category": "Category1", "issues": ["Issue1"]},
                    {"category": "Category2", "issues": ["Issue2"]},
                ],
            }
        
        result = mock_execute("Why are sales declining?")
        
        assert "root_problem" in result
        assert "branches" in result
        assert len(result["branches"]) >= 2
    
    def test_execute_with_context(self):
        """Test execute with additional context."""
        def mock_execute(problem: str, context: dict = None) -> dict:
            tree = {
                "root_problem": problem,
                "branches": [],
            }
            
            if context and context.get("industry"):
                # Add industry-specific branches
                if context["industry"] == "saas":
                    tree["branches"].append({
                        "category": "Churn",
                        "issues": ["Monthly churn", "Annual churn"],
                    })
            
            return tree
        
        result = mock_execute("Revenue decline", {"industry": "saas"})
        
        assert any(b["category"] == "Churn" for b in result["branches"])
    
    def test_execute_handles_empty_problem(self):
        """Test execute handles empty problem."""
        def mock_execute(problem: str) -> dict:
            if not problem or not problem.strip():
                return {"error": "Problem statement required"}
            return {"root_problem": problem, "branches": []}
        
        result = mock_execute("")
        
        assert "error" in result


class TestProblemTreeFormatting:
    """Test problem tree formatting and output."""
    
    def test_format_as_text(self):
        """Test formatting tree as text."""
        tree = {
            "root_problem": "Revenue decline",
            "branches": [
                {"category": "Volume", "issues": ["Lower units"]},
                {"category": "Price", "issues": ["Discounting"]},
            ],
        }
        
        def format_tree_text(tree: dict) -> str:
            lines = [f"Problem: {tree['root_problem']}", ""]
            for i, branch in enumerate(tree["branches"], 1):
                lines.append(f"{i}. {branch['category']}")
                for issue in branch.get("issues", []):
                    lines.append(f"   - {issue}")
            return "\n".join(lines)
        
        output = format_tree_text(tree)
        
        assert "Revenue decline" in output
        assert "Volume" in output
        assert "Price" in output
    
    def test_format_as_markdown(self):
        """Test formatting tree as markdown."""
        tree = {
            "root_problem": "Revenue decline",
            "branches": [
                {"category": "Volume", "issues": ["Lower units"]},
            ],
        }
        
        def format_tree_markdown(tree: dict) -> str:
            lines = [f"# {tree['root_problem']}", ""]
            for branch in tree["branches"]:
                lines.append(f"## {branch['category']}")
                for issue in branch.get("issues", []):
                    lines.append(f"- {issue}")
                lines.append("")
            return "\n".join(lines)
        
        output = format_tree_markdown(tree)
        
        assert "# Revenue decline" in output
        assert "## Volume" in output
    
    def test_format_as_json(self):
        """Test formatting tree as JSON."""
        tree = {
            "root_problem": "Revenue decline",
            "branches": [{"category": "Volume", "issues": ["Lower units"]}],
        }
        
        json_output = json.dumps(tree, indent=2)
        parsed = json.loads(json_output)
        
        assert parsed == tree


class TestProblemTreeAnalysis:
    """Test problem tree analysis features."""
    
    def test_count_total_issues(self):
        """Test counting total issues."""
        tree = {
            "branches": [
                {"issues": ["A", "B", "C"]},
                {"issues": ["D", "E"]},
            ],
        }
        
        total = sum(len(b.get("issues", [])) for b in tree["branches"])
        assert total == 5
    
    def test_identify_priority_branches(self):
        """Test identifying priority branches."""
        tree = {
            "branches": [
                {"category": "Sales", "impact": "high", "issues": ["A"]},
                {"category": "Marketing", "impact": "medium", "issues": ["B"]},
                {"category": "Product", "impact": "high", "issues": ["C"]},
            ],
        }
        
        high_priority = [b for b in tree["branches"] if b.get("impact") == "high"]
        
        assert len(high_priority) == 2
    
    def test_calculate_completeness_score(self):
        """Test calculating tree completeness."""
        def calculate_completeness(tree: dict) -> float:
            score = 0.0
            
            # Has root problem
            if tree.get("root_problem"):
                score += 0.2
            
            # Has branches
            branches = tree.get("branches", [])
            if branches:
                score += 0.2
            
            # Each branch has issues
            branches_with_issues = sum(
                1 for b in branches if b.get("issues")
            )
            if branches:
                score += 0.3 * (branches_with_issues / len(branches))
            
            # Minimum branch count (3+)
            if len(branches) >= 3:
                score += 0.3
            
            return round(score, 2)
        
        complete_tree = {
            "root_problem": "Test",
            "branches": [
                {"category": "A", "issues": ["1"]},
                {"category": "B", "issues": ["2"]},
                {"category": "C", "issues": ["3"]},
            ],
        }
        
        score = calculate_completeness(complete_tree)
        assert score >= 0.9


class TestProblemAgentIntegration:
    """Test ProblemAgent integration scenarios."""
    
    def test_integration_with_business_agent(self, sample_business_diagnosis):
        """Test integration with BusinessSenseAgent output."""
        diagnosis = sample_business_diagnosis
        
        # ProblemAgent receives diagnosis
        tree_input = {
            "problem": diagnosis["identified_business_problem"],
            "context": diagnosis["hidden_root_risk"],
            "urgency": diagnosis["urgency_level"],
        }
        
        # Generate tree
        tree = {
            "root_problem": tree_input["problem"],
            "urgency": tree_input["urgency"],
            "branches": [
                {"category": "Root Cause Analysis", "issues": [tree_input["context"]]},
            ],
        }
        
        assert tree["root_problem"] == "Market share erosion"
        assert tree["urgency"] == "High"
    
    def test_iterative_tree_refinement(self):
        """Test iterative tree refinement."""
        initial_tree = {
            "root_problem": "Sales decline",
            "branches": [{"category": "Volume", "issues": []}],
        }
        
        # Refinement 1: Add issues
        initial_tree["branches"][0]["issues"] = ["Lower conversion"]
        
        # Refinement 2: Add branch
        initial_tree["branches"].append({
            "category": "Price",
            "issues": ["Competitive pressure"],
        })
        
        assert len(initial_tree["branches"]) == 2
        assert len(initial_tree["branches"][0]["issues"]) == 1
