"""
AgentSudo SDK - Zero Trust Client Library for AI Agents
========================================================

Simple, clean client for communicating with the AgentSudo Guard server.

Usage:
    from agentsudo import AgentSudo
    
    client = AgentSudo()
    client.request_access("my-agent", "openai", "Summarize document")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("AgentSudo.SDK")


# =============================================================================
# Exceptions
# =============================================================================

class AgentSudoError(Exception):
    """Base exception for AgentSudo SDK."""
    pass


class SecurityBlockError(AgentSudoError):
    """Raised when access is blocked by policy or budget."""
    pass


class AuthenticationError(AgentSudoError):
    """Raised when agent authentication fails."""
    pass


class AccessDeniedError(SecurityBlockError):
    """Raised when access is denied by policy."""
    pass


class BudgetExceededError(SecurityBlockError):
    """Raised when agent has exceeded their budget limit."""
    pass


class ServerConnectionError(AgentSudoError):
    """Raised when unable to connect to AgentSudo server."""
    pass


class ApprovalRequiredError(AgentSudoError):
    """Raised when the requested action requires human approval."""
    
    def __init__(self, message: str, ticket_id: str, approvers: list[str] | None = None):
        super().__init__(message)
        self.ticket_id = ticket_id
        self.approvers = approvers or []
    
    def __str__(self) -> str:
        return f"{self.args[0]} (Ticket: {self.ticket_id})"


# =============================================================================
# Response Models
# =============================================================================

@dataclass
class SessionToken:
    """Represents a JIT access token."""
    token: str
    tool: str
    expires_in_seconds: int = 300
    remaining_budget_usd: float = 0.0


@dataclass
class ApprovalTicket:
    """Represents a pending human approval request."""
    ticket_id: str
    status: str
    message: str
    approvers: list[str]


@dataclass
class AccessResult:
    """Result of an access request."""
    allowed: bool
    token: Optional[str] = None
    reason: str = ""


# =============================================================================
# Main Client
# =============================================================================

class AgentSudo:
    """
    Zero Trust SDK for AI Agents.
    
    Simple client that communicates with the local AgentSudo Guard server.
    """
    
    DEFAULT_SERVER_URL = "http://localhost:8000"
    REQUEST_TIMEOUT = 5.0
    
    def __init__(
        self,
        server_url: str | None = None,
        timeout: float | None = None,
        fail_open: bool = False,
    ) -> None:
        """
        Initialize the AgentSudo client.
        
        Args:
            server_url: URL of the AgentSudo Guard server
            timeout: Request timeout in seconds
            fail_open: If True, allow access when server is unreachable
                      (DANGEROUS - only for development)
        """
        self.server_url = server_url or os.getenv("AGENTSUDO_SERVER_URL", self.DEFAULT_SERVER_URL)
        self.timeout = timeout or self.REQUEST_TIMEOUT
        self.fail_open = fail_open
        self._client = httpx.Client(base_url=self.server_url, timeout=self.timeout)
        logger.debug(f"AgentSudo client initialized: {self.server_url}")
    
    def __enter__(self) -> AgentSudo:
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
    
    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
    
    def request_access(
        self,
        agent_name: str,
        tool: str,
        intent: str,
        cost: float = 0.0,
    ) -> bool:
        """
        Request access to a tool from the Guard server.
        
        Args:
            agent_name: Identifier for the agent making the request
            tool: Name of the tool/resource being accessed
            intent: Description of what the agent intends to do
            cost: Estimated cost in USD (for budget tracking)
        
        Returns:
            True if access is granted
        
        Raises:
            AccessDeniedError: If blocked by policy
            BudgetExceededError: If budget limit exceeded
            ServerConnectionError: If cannot connect to server
        """
        try:
            response = self._client.post("/check", json={
                "agent_id": agent_name,
                "tool_name": tool,
                "intent": intent,
                "cost": cost,
            })
            return self._handle_response(response)
        except httpx.ConnectError as e:
            return self._handle_connection_error(e)
        except httpx.TimeoutException as e:
            return self._handle_connection_error(e)
    
    def _handle_response(self, response: httpx.Response) -> bool:
        """Handle the server response."""
        if response.status_code == 200:
            logger.debug("Access granted")
            return True
        
        try:
            detail = response.json().get("detail", "Unknown error")
        except Exception:
            detail = response.text or "Unknown error"
        
        if response.status_code == 403:
            logger.warning(f"Access denied: {detail}")
            raise AccessDeniedError(f"Policy Blocked: {detail}")
        
        if response.status_code == 429:
            logger.warning("Budget exceeded")
            raise BudgetExceededError("Hourly budget exceeded")
        
        if response.status_code == 401:
            raise AuthenticationError(detail)
        
        if response.status_code == 202:
            data = response.json()
            raise ApprovalRequiredError(
                message=data.get("message", "Human approval required"),
                ticket_id=data.get("ticket_id", "unknown"),
                approvers=data.get("approvers", []),
            )
        
        raise AgentSudoError(f"Unexpected error ({response.status_code}): {detail}")
    
    def _handle_connection_error(self, error: Exception) -> bool:
        """Handle connection errors based on fail_open setting."""
        if self.fail_open:
            logger.warning(f"Guard unreachable, fail-open enabled: {error}")
            return True
        raise ServerConnectionError(
            "Could not connect to AgentSudo Guard. Is 'agentsudo start' running?"
        ) from error
    
    def health_check(self) -> bool:
        """Check if the Guard server is healthy."""
        try:
            response = self._client.get("/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_session(
        self,
        tool_name: str,
        reason: str,
        amount: float = 0.0,
    ) -> SessionToken:
        """
        Request JIT access and get a session token (legacy API).
        
        Args:
            tool_name: Name of the tool to access
            reason: Intent description
            amount: Estimated cost in USD
        
        Returns:
            SessionToken with access credentials
        """
        agent_id = os.getenv("AGENTSUDO_AGENT_ID", "default-agent")
        self.request_access(agent_id, tool_name, reason, amount)
        return SessionToken(
            token="jit-token-placeholder",
            tool=tool_name,
            expires_in_seconds=300,
            remaining_budget_usd=5.0,
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "AgentSudo",
    "SessionToken",
    "ApprovalTicket",
    "AccessResult",
    "AgentSudoError",
    "SecurityBlockError",
    "AuthenticationError",
    "AccessDeniedError",
    "BudgetExceededError",
    "ServerConnectionError",
    "ApprovalRequiredError",
]
