"""
LangChain Integration for AgentSudo
====================================
Secure wrappers for LangChain that enforce AgentSudo policies.

Usage:
    from agentsudo.integrations.langchain import SudoChatOpenAI
    
    chat = SudoChatOpenAI(
        agent_name="research-bot",
        model="gpt-4",
    )
    response = chat.invoke("Summarize this document")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import ChatResult

from ..client import AgentSudo, SecurityBlockError


class SudoChatOpenAI:
    """
    A secure wrapper for ChatOpenAI that enforces AgentSudo policies.
    
    This class intercepts all LLM calls and checks with the AgentSudo
    Guard server before allowing the request to proceed.
    
    Usage:
        chat = SudoChatOpenAI(
            agent_name="research-bot",
            model="gpt-4",
            budget_limit=5.00
        )
        response = chat.invoke([HumanMessage(content="Hello")])
    """
    
    agent_name: str
    sudo: AgentSudo
    
    def __init__(self, agent_name: str, **kwargs: Any) -> None:
        """
        Initialize the secure ChatOpenAI wrapper.
        
        Args:
            agent_name: Identifier for this agent in AgentSudo policies
            **kwargs: All standard ChatOpenAI arguments (model, temperature, etc.)
        """
        # Lazy import to avoid requiring langchain as a dependency
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            raise ImportError(
                "LangChain integration requires langchain-openai. "
                "Install with: pip install langchain-openai"
            ) from e
        
        # Store our security config
        self.agent_name = agent_name
        self.sudo = AgentSudo()
        
        # Create the underlying ChatOpenAI instance
        self._chat = ChatOpenAI(**kwargs)
    
    def _check_permission(self, intent: str, cost: float = 0.01) -> None:
        """Check permission with AgentSudo Guard."""
        try:
            self.sudo.request_access(
                agent_name=self.agent_name,
                tool="openai",
                intent=intent,
                cost=cost,
            )
        except SecurityBlockError as e:
            raise ValueError(f"🛡️ Security Block: {e}")
    
    def _extract_intent(self, messages: List[BaseMessage]) -> str:
        """Extract intent from the last message."""
        if not messages:
            return "Unknown intent"
        
        content = messages[-1].content
        # Handle multimodal content (list of content blocks)
        if isinstance(content, list):
            return str(content)
        return str(content)
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Intercepts the generation call to enforce security policies."""
        intent = self._extract_intent(messages)
        self._check_permission(intent, cost=0.01)
        return self._chat._generate(messages, stop, run_manager, **kwargs)
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async version for modern agents."""
        intent = self._extract_intent(messages)
        self._check_permission(intent, cost=0.01)
        return await self._chat._agenerate(messages, stop, run_manager, **kwargs)
    
    def invoke(self, messages: Any, **kwargs: Any) -> Any:
        """Invoke the chat model with security checks."""
        if isinstance(messages, str):
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=messages)]
        
        intent = self._extract_intent(messages)
        self._check_permission(intent, cost=0.01)
        return self._chat.invoke(messages, **kwargs)
    
    async def ainvoke(self, messages: Any, **kwargs: Any) -> Any:
        """Async invoke with security checks."""
        if isinstance(messages, str):
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=messages)]
        
        intent = self._extract_intent(messages)
        self._check_permission(intent, cost=0.01)
        return await self._chat.ainvoke(messages, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to the underlying ChatOpenAI."""
        return getattr(self._chat, name)


# Legacy wrapper for backward compatibility
class AgentSudoToolWrapper:
    """Wraps LangChain tools with AgentSudo credential injection."""
    
    def __init__(
        self,
        client: AgentSudo,
        tool_name: str,
        scope: list[str] | None = None,
    ) -> None:
        self.client = client
        self.tool_name = tool_name
        self.scope = scope or []
    
    def wrap(self, tool: Any) -> Any:
        """Wrap a LangChain tool with JIT credentials."""
        raise NotImplementedError("Generic tool wrapping coming soon")
