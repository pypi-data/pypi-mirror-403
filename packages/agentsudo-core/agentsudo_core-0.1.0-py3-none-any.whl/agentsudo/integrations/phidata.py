"""
Phidata Integration for AgentSudo
==================================
Secure wrappers for Phidata that enforce AgentSudo policies.

Usage:
    from agentsudo.integrations.phidata import SudoOpenAIChat
    from phi.agent import Agent
    
    agent = Agent(
        model=SudoOpenAIChat(agent_name="research-bot", id="gpt-4"),
        tools=[...],
    )
    agent.run("Summarize this document")
"""

from __future__ import annotations

from typing import Any, Callable, Iterator, List, Optional

try:
    from phi.model.openai import OpenAIChat
    PHIDATA_AVAILABLE = True
except ImportError:
    PHIDATA_AVAILABLE = False
    class OpenAIChat:  # type: ignore
        """Placeholder when phidata is not installed."""
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError(
                "Phidata integration requires phi. "
                "Install with: pip install phidata"
            )

from ..client import AgentSudo, SecurityBlockError


class SudoOpenAIChat(OpenAIChat):
    """
    A secure wrapper for Phidata's OpenAIChat model.
    
    This class intercepts all model invocations and checks with the AgentSudo
    Guard server before allowing the request to proceed.
    """
    
    def __init__(self, agent_name: str, id: str = "gpt-4", **kwargs: Any) -> None:
        if not PHIDATA_AVAILABLE:
            raise ImportError(
                "Phidata integration requires phi. "
                "Install with: pip install phidata"
            )
        
        super().__init__(id=id, **kwargs)
        self.agent_name = agent_name
        self.sudo = AgentSudo()
    
    def _extract_intent(self, messages: List[Any]) -> str:
        """Extract intent from messages."""
        if not messages:
            return "Unknown intent"
        
        last_message = messages[-1]
        if isinstance(last_message, dict):
            return str(last_message.get("content", "Unknown"))
        elif hasattr(last_message, "content"):
            return str(last_message.content)
        return str(last_message)
    
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
            raise PermissionError(f"🛡️ AgentSudo Blocked: {e}")
    
    def invoke(self, messages: List[Any], **kwargs: Any) -> Any:
        """Intercepts the model invocation to enforce security policies."""
        intent = self._extract_intent(messages)
        self._check_permission(intent, cost=0.01)
        return super().invoke(messages, **kwargs)
    
    async def ainvoke(self, messages: List[Any], **kwargs: Any) -> Any:
        """Async version for modern agents."""
        intent = self._extract_intent(messages)
        self._check_permission(intent, cost=0.01)
        return await super().ainvoke(messages, **kwargs)


class SudoAgent:
    """A secure wrapper for Phidata Agent that enforces AgentSudo policies."""
    
    def __init__(self, agent_name: str, **kwargs: Any) -> None:
        try:
            from phi.agent import Agent
        except ImportError as e:
            raise ImportError(
                "Phidata integration requires phi. "
                "Install with: pip install phidata"
            ) from e
        
        self.agent_name = agent_name
        self.sudo = AgentSudo()
        self._agent = Agent(**kwargs)
    
    def _check_permission(self, intent: str, tool: str = "phidata", cost: float = 0.01) -> None:
        try:
            self.sudo.request_access(
                agent_name=self.agent_name,
                tool=tool,
                intent=intent,
                cost=cost,
            )
        except SecurityBlockError as e:
            raise PermissionError(f"🛡️ AgentSudo Blocked: {e}")
    
    def run(self, message: str, *, stream: bool = False, **kwargs: Any) -> Any:
        self._check_permission(intent=message, tool="phidata")
        return self._agent.run(message, stream=stream, **kwargs)
    
    def print_response(self, message: str, *, stream: bool = True, **kwargs: Any) -> None:
        self._check_permission(intent=message, tool="phidata")
        self._agent.print_response(message, stream=stream, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)


class SudoTool:
    """A secure wrapper for individual Phidata tools."""
    
    def __init__(self, agent_name: str, tool: Any, tool_name: str) -> None:
        self.agent_name = agent_name
        self.tool_name = tool_name
        self._tool = tool
        self.sudo = AgentSudo()
    
    def _wrap_function(self, func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            intent = str(args[0]) if args else str(kwargs)
            try:
                self.sudo.request_access(
                    agent_name=self.agent_name,
                    tool=self.tool_name,
                    intent=intent,
                    cost=0.01,
                )
            except SecurityBlockError as e:
                raise PermissionError(f"🛡️ AgentSudo Blocked: {e}")
            return func(*args, **kwargs)
        return wrapped
    
    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._tool, name)
        if callable(attr):
            return self._wrap_function(attr)
        return attr


def create_agentsudo_toolkit(agent_name: str, tools: list[Any]) -> list[Any]:
    """Wrap a list of Phidata tools with AgentSudo protection."""
    wrapped_tools = []
    for tool in tools:
        tool_name = getattr(tool, "name", type(tool).__name__)
        wrapped_tools.append(SudoTool(agent_name, tool, tool_name))
    return wrapped_tools
