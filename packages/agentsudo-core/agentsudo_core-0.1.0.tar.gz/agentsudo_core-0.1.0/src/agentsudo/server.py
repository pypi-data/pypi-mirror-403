"""
AgentSudo Server - Zero Config Local Guard
==========================================
Pip-installable FastAPI server that auto-detects config
or runs with sensible defaults.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .core.policy_engine import PolicyEngine, PolicyDecision, DecisionType
from .core.budget import BudgetTracker, InMemoryBudgetStorage

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("AgentSudo")

# Config file search order
CONFIG_SEARCH_PATHS = [
    "agentsudo.config.yaml",
    "agentsudo.yaml",
    "policies.yaml",
    ".agentsudo/config.yaml",
]


class AppState:
    """Application state container."""
    policy_engine: PolicyEngine
    budget_tracker: BudgetTracker


state = AppState()


def _find_config_file() -> Optional[Path]:
    """Search for config file in common locations."""
    for config_path in CONFIG_SEARCH_PATHS:
        path = Path(config_path)
        if path.exists():
            logger.info(f"?? Found config: {path}")
            return path
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application state."""
    # 1. Find or use default config
    config_path = _find_config_file()
    
    if config_path:
        state.policy_engine = PolicyEngine(policies_path=str(config_path))
    else:
        logger.warning("??  No config file found, using permissive defaults")
        state.policy_engine = PolicyEngine()  # Uses built-in defaults
    
    # 2. Initialize budget tracker (in-memory for local use)
    state.budget_tracker = BudgetTracker(storage=InMemoryBudgetStorage())
    
    logger.info("???  AgentSudo Guard is Active")
    logger.info(f"?? Endpoints: POST /check, GET /health")
    
    yield
    
    logger.info("?? AgentSudo Guard Stopped")


app = FastAPI(
    title="AgentSudo Local Guard",
    description="Zero Trust Middleware for AI Agents",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Request/Response Models ---

class AccessRequest(BaseModel):
    """Request to check agent access."""
    agent_id: str
    tool_name: str
    intent: str
    cost: Optional[float] = 0.0


class AccessResponse(BaseModel):
    """Response from access check."""
    allowed: bool
    token: Optional[str] = None
    reason: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    config_loaded: bool


# --- Endpoints ---

@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "AgentSudo",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "check": "POST /check",
            "health": "GET /health",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        config_loaded=state.policy_engine is not None,
    )


@app.post("/check", response_model=AccessResponse)
async def check_access(req: AccessRequest):
    """
    Main decision endpoint.
    
    1. Checks Policy (Intent Analysis)
    2. Checks Budget (Redis/Memory)
    """
    # 1. Policy Check
    decision: PolicyDecision = state.policy_engine.evaluate(
        agent_id=req.agent_id,
        tool_name=req.tool_name,
        intent=req.intent,
    )

    if decision.decision == DecisionType.BLOCK:
        logger.warning(f"?? BLOCKED: {req.agent_id} -> {req.tool_name} | {decision.reasons}")
        raise HTTPException(
            status_code=403,
            detail=f"Policy Blocked: {', '.join(decision.reasons)}",
        )

    # 2. Budget Check
    # TODO: Fetch limit from PolicyEngine per-agent config
    default_budget_limit = 5.00
    
    allowed = await state.budget_tracker.check_and_spend(
        agent_id=req.agent_id,
        cost=req.cost or 0.0,
        limit=default_budget_limit,
    )

    if not allowed:
        logger.warning(f"?? BUDGET EXCEEDED: {req.agent_id}")
        raise HTTPException(
            status_code=429,
            detail="Hourly budget exceeded",
        )

    logger.info(f"? ALLOWED: {req.agent_id} -> {req.tool_name}")
    
    return AccessResponse(
        allowed=True,
        token="jit-token-placeholder",  # TODO: Generate real JIT token
        reason="Approved",
    )


# --- Entry Point for CLI ---

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Start the AgentSudo server.
    
    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to listen on (default: 8000)
        reload: Enable auto-reload for development
    """
    uvicorn.run(
        "agentsudo.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    start_server()
