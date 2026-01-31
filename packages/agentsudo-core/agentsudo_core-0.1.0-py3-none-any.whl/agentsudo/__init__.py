"""
AgentSudo - Zero Trust Security for AI Agents
==============================================

Usage:
    from agentsudo import AgentSudo, SecurityBlockError
    
    client = AgentSudo()
    client.request_access("my-agent", "openai", "Summarize document")
"""

from agentsudo.client import (
    # Client
    AgentSudo,
    # Response models
    SessionToken,
    ApprovalTicket,
    AccessResult,
    # Exceptions
    AgentSudoError,
    SecurityBlockError,
    AuthenticationError,
    AccessDeniedError,
    BudgetExceededError,
    ServerConnectionError,
    ApprovalRequiredError,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "AgentSudo",
    # Response models
    "SessionToken",
    "ApprovalTicket",
    "AccessResult",
    # Exceptions
    "AgentSudoError",
    "SecurityBlockError",
    "AuthenticationError",
    "AccessDeniedError",
    "BudgetExceededError",
    "ServerConnectionError",
    "ApprovalRequiredError",
    # Version
    "__version__",
]
