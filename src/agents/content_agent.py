# ContentAgent - Web search and content generation with citations
from typing import Optional, List
import re
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

from src.agents.base import BaseAgent
from src.models.agents import ContentOutput
from src.utils.logger import get_logger


class ContentAgent(BaseAgent):
    """Agent specialized in web search and content creation with citations."""

    def __init__(self, session_id: Optional[str] = None):
        super().__init__(session_id)
        self.logger = get_logger("ContentAgent")
        try:
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
            self.search_wrapper = DuckDuckGoSearchAPIWrapper(max_results=5)
            self.search_tool = DuckDuckGoSearchResults(api_wrapper=self.search_wrapper)
        except ImportError:
            self.search_wrapper = None  # Fallback for testing
            self.search_tool = None

    
    @property
    def agent_type(self) -> str:
        return "content_agent"
    
    @property
    def system_prompt(self) -> str:
        return """You are a research specialist. Provide accurate, well-structured information.
Always cite sources when available.

IMPORTANT: Pay attention to the conversation history. If the user has been discussing a specific 
topic or context, use that information to provide more relevant and contextual responses."""
    
    async def _perform_search(self, query: str) -> tuple[str, List[str]]:
        """Perform web search and return results with URLs."""
        try:
            self.logger.info(f"Searching: {query}")
            results = self.search_tool.invoke(query)
            
            sources = []
            if isinstance(results, str):
                url_pattern = r'https?://[^\s\])]+' 
                sources = list(set(re.findall(url_pattern, results)))[:5]
            
            return results, sources
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return f"Search failed: {e}", []
    
    async def execute(
        self,
        task: str,
        search_query: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        chat_history: Optional[List[BaseMessage]] = None,
        **kwargs
    ) -> ContentOutput:
        """Generate content based on web search.
        
        Args:
            task: The content/research request
            search_query: Optional custom search query
            session_id: Session ID for tracking
            task_id: Task ID for tracking
            chat_history: Previous conversation messages for context
        """
        self.logger.info(f"ContentAgent executing: {task[:50]}...")
        
        try:
            query = search_query or task
            search_results, sources = await self._perform_search(query)
            
            # Build messages with chat history for context
            messages = [SystemMessage(content=self.system_prompt)]
            messages.append(SystemMessage(content=f"Search results:\n{search_results}"))
            
            # Include chat history for conversation context
            if chat_history:
                messages.extend(chat_history)
            
            messages.append(HumanMessage(content=task))
            
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            self.logger.info(f"ContentAgent completed with {len(sources)} sources")
            return ContentOutput(
                content=content,
                sources=sources
            )
            
        except Exception as e:
            self.logger.error(f"ContentAgent error: {e}")
            return ContentOutput(
                content=f"Error researching: {e}",
                sources=[]
            )
