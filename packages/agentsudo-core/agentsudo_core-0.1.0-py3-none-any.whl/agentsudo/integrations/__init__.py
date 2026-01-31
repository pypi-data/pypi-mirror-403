"""Third-party integrations for AgentSudo.
=========================================

Usage:
    from agentsudo.integrations import SudoChatOpenAI  # LangChain
    from agentsudo.integrations import SudoOpenAIChat  # Phidata
"""

# LangChain integration
try:
    from .langchain import SudoChatOpenAI, AgentSudoToolWrapper
except ImportError:
    SudoChatOpenAI = None  # type: ignore
    AgentSudoToolWrapper = None  # type: ignore

# Phidata integration
try:
    from .phidata import SudoOpenAIChat, SudoAgent, SudoTool, create_agentsudo_toolkit
except ImportError:
    SudoOpenAIChat = None  # type: ignore
    SudoAgent = None  # type: ignore
    SudoTool = None  # type: ignore
    create_agentsudo_toolkit = None  # type: ignore

__all__ = [
    # LangChain
    "SudoChatOpenAI",
    "AgentSudoToolWrapper",
    # Phidata
    "SudoOpenAIChat",
    "SudoAgent",
    "SudoTool",
    "create_agentsudo_toolkit",
]
