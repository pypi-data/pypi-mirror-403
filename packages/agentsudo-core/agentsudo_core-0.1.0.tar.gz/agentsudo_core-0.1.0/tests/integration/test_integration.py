"""
Integration tests - requires server running on localhost:8000
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

import pytest
from agentsudo import (
    AgentSudo,
    SessionToken,
    AuthenticationError,
    AccessDeniedError,
    BudgetExceededError,
    ApprovalRequiredError,
    ServerConnectionError,
)

# Match the agent ID in policies.yaml
TEST_AGENT_ID = "test_bot"  # Changed from "test-bot" to "test_bot"
TEST_SECRET = "secret_123"


class TestAgentSudoIntegration:
    """Integration tests with running server."""
    
    @pytest.fixture
    def sdk(self):
        """Create SDK instance."""
        client = AgentSudo(
            agent_id=TEST_AGENT_ID,
            secret=TEST_SECRET,
            server_url="http://localhost:8000"
        )
        yield client
        client.close()
    
    def test_health_check(self, sdk):
        """Server should be healthy."""
        assert sdk.health_check() is True
    
    def test_successful_token_request(self, sdk):
        """Should get token for allowed tool."""
        token = sdk.get_session(
            tool_name="openai_api",
            reason="Summarize user document",
            amount=0.0
        )
        
        assert isinstance(token, SessionToken)
        assert token.tool == "openai_api"
        assert token.token.startswith("agentsudo_")
        assert token.expires_in_seconds > 0
    
    def test_invalid_credentials_rejected(self):
        """Invalid credentials should be rejected."""
        sdk = AgentSudo(
            agent_id=TEST_AGENT_ID,
            secret="wrong_secret",
            server_url="http://localhost:8000"
        )
        
        with pytest.raises(AuthenticationError):
            sdk.get_session("openai_api", "Test request")
        
        sdk.close()
    
    def test_unknown_agent_rejected(self):
        """Unknown agent should be rejected."""
        sdk = AgentSudo(
            agent_id="unknown-agent",
            secret="any_secret",
            server_url="http://localhost:8000"
        )
        
        with pytest.raises(AuthenticationError):
            sdk.get_session("openai_api", "Test request")
        
        sdk.close()
    
    def test_blocked_keyword_rejected(self, sdk):
        """Intent with blocked keywords should be rejected."""
        with pytest.raises(AccessDeniedError):
            sdk.get_session(
                tool_name="stripe_refund",
                reason="Process this fraud case",
                amount=10.0
            )
    
    def test_approval_required_for_high_amount(self, sdk):
        """High amount should require approval."""
        with pytest.raises(ApprovalRequiredError) as exc_info:
            sdk.get_session(
                tool_name="stripe_refund",
                reason="Refund customer order",
                amount=100.0  # Over $50 threshold
            )
        
        assert exc_info.value.ticket_id.startswith("HITL-")
    
    def test_auto_approve_under_threshold(self, sdk):
        """Amount under threshold should auto-approve."""
        token = sdk.get_session(
            tool_name="stripe_refund",
            reason="Small refund for customer",
            amount=25.0  # Under $50 threshold
        )
        
        assert isinstance(token, SessionToken)


# Quick manual test
if __name__ == "__main__":
    print("=" * 50)
    print("AgentSudo Integration Test")
    print("=" * 50)
    
    with AgentSudo(TEST_AGENT_ID, TEST_SECRET) as sdk:
        # Test 1: Health check
        print(f"\n1. Health check: {sdk.health_check()}")
        
        # Test 2: Get token
        token = sdk.get_session("openai_api", "Summarize document")
        print(f"2. Token granted: {token.token[:30]}...")
        
        # Test 3: Approval required
        try:
            sdk.get_session("stripe_refund", "Large refund", amount=100.0)
        except ApprovalRequiredError as e:
            print(f"3. Approval required: {e.ticket_id}")
        
        print("\n✅ All tests passed!")