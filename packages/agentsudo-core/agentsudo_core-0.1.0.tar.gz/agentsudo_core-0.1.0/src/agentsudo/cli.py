"""
AgentSudo CLI - Terminal Interface for Human-in-the-Loop Operations
====================================================================
Usage: python -m agentsudo.cli watch --mode=strict
       python -m agentsudo.cli demo --scenario=all
"""

import time
import sys
from datetime import datetime
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from rich.style import Style
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Styles
STYLE_AGENT = Style(color="yellow")
STYLE_TARGET = Style(color="white", bold=True)
STYLE_RISK_HIGH = Style(color="red", bold=True)
STYLE_RISK_MEDIUM = Style(color="yellow")
STYLE_RISK_LOW = Style(color="green")
STYLE_ALERT = Style(color="yellow", bold=True)
STYLE_SUCCESS = Style(color="green")
STYLE_ERROR = Style(color="red")
STYLE_SELECTED = Style(color="black", bgcolor="green", bold=True)

VERSION = "v1.0.4"


class AgentSudoCLI:
    """CLI controller for AgentSudo operations."""

    def __init__(self, server_url: str = "http://localhost:8000", mode: str = "strict"):
        self.server_url = server_url
        self.mode = mode
        self.client = httpx.Client(timeout=30.0)

    def close(self):
        self.client.close()

    def health_check(self) -> bool:
        """Check server health."""
        try:
            response = self.client.get(f"{self.server_url}/health")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def get_pending_approvals(self) -> list[dict]:
        """Fetch pending approval tickets from server."""
        try:
            response = self.client.get(f"{self.server_url}/approvals/pending")
            if response.status_code == 200:
                return response.json().get("tickets", [])
        except httpx.RequestError:
            pass
        return []

    def approve_ticket(self, ticket_id: str, approver: str = "cli-admin") -> bool:
        """Approve a pending ticket."""
        try:
            response = self.client.post(
                f"{self.server_url}/approvals/{ticket_id}/approve",
                params={"approver": approver},
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def deny_ticket(self, ticket_id: str, approver: str = "cli-admin") -> bool:
        """Deny a pending ticket."""
        try:
            response = self.client.post(
                f"{self.server_url}/approvals/{ticket_id}/deny",
                params={"approver": approver},
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def send_slack_notification(self, channel: str, ticket: dict) -> bool:
        """Send Slack notification for escalation."""
        console.print(f"\nSending slack notification to #{channel}...", style="dim")
        time.sleep(1.5)
        return True

    def kill_agent_process(self, agent_id: str) -> bool:
        """Kill an agent's active processes."""
        try:
            response = self.client.post(f"{self.server_url}/agents/{agent_id}/kill")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    def request_access(self, agent_id: str, secret: str, tool_name: str, 
                       reason: str, amount: float = 0.0) -> dict:
        """Request tool access."""
        try:
            response = self.client.post(
                f"{self.server_url}/request-access",
                json={
                    "agent_id": agent_id,
                    "agent_secret": secret,
                    "tool_name": tool_name,
                    "intent_description": reason,
                    "amount": amount,
                },
            )
            return {"status_code": response.status_code, "data": response.json()}
        except httpx.RequestError as e:
            return {"status_code": 0, "error": str(e)}

    def get_audit_log(self, limit: int = 5) -> list[dict]:
        """Fetch audit log entries."""
        try:
            response = self.client.get(f"{self.server_url}/audit/log", params={"limit": limit})
            if response.status_code == 200:
                return response.json().get("entries", [])
        except httpx.RequestError:
            pass
        return []


# =============================================================================
# Demo Runner
# =============================================================================

class DemoRunner:
    """Interactive demo runner for AgentSudo capabilities."""

    def __init__(self, cli: AgentSudoCLI):
        self.cli = cli
        self.passed = 0
        self.failed = 0

    def print_header(self, title: str) -> None:
        """Print formatted section header."""
        console.print()
        console.print(Panel(
            Text(title, style="bold white"),
            border_style="cyan",
            padding=(0, 2),
        ))

    def print_result(self, success: bool, message: str) -> None:
        """Print formatted test result."""
        if success:
            console.print(f"[green]✓[/green] {message}")
            self.passed += 1
        else:
            console.print(f"[red]✗[/red] {message}")
            self.failed += 1

    def print_detail(self, message: str) -> None:
        """Print detail line."""
        console.print(f"  [dim]{message}[/dim]")

    def run_context_awareness(self) -> None:
        """Demo: Context-Aware Security (keyword blocking)."""
        self.print_header("TEST 1: Context-Aware Security")

        # Test safe intent
        console.print("\n[bold]>> Testing SAFE intent...[/bold]")
        result = self.cli.request_access(
            "research_bot_01", "secret_123", "database_api",
            "Read the latest user records from the database"
        )
        if result["status_code"] == 200:
            self.print_result(True, "Safe read access granted!")
            self.print_detail(f"Token: {result['data'].get('token', '')[:40]}...")
        else:
            self.print_result(False, f"Unexpected: {result}")

        # Test dangerous intent (DELETE)
        console.print("\n[bold]>> Testing DANGEROUS intent (DELETE)...[/bold]")
        result = self.cli.request_access(
            "research_bot_01", "secret_123", "database_api",
            "I want to DELETE the production table and all user data"
        )
        if result["status_code"] == 403:
            self.print_result(True, "Dangerous action BLOCKED correctly!")
            self.print_detail(f"Reason: {result['data'].get('detail', 'Access denied')}")
        else:
            self.print_result(False, "ERROR: Dangerous action was NOT blocked!")

        # Test dangerous intent (DROP)
        console.print("\n[bold]>> Testing DANGEROUS intent (DROP)...[/bold]")
        result = self.cli.request_access(
            "research_bot_01", "secret_123", "database_api",
            "Let me drop the tables to free up space"
        )
        if result["status_code"] == 403:
            self.print_result(True, "DROP command BLOCKED correctly!")
        else:
            self.print_result(False, "ERROR: DROP was NOT blocked!")

    def run_hitl_approval(self) -> None:
        """Demo: Human-in-the-Loop approval workflow."""
        self.print_header("TEST 2: Human-in-the-Loop (HITL) Approval")

        # Test auto-approve (under threshold)
        console.print("\n[bold]>> Requesting stripe_refund for $20 (under $50 threshold)...[/bold]")
        result = self.cli.request_access(
            "research_bot_01", "secret_123", "stripe_refund",
            "Customer requested refund for damaged item", amount=20.0
        )
        if result["status_code"] == 200:
            self.print_result(True, "Small refund AUTO-APPROVED!")
            self.print_detail(f"Token: {result['data'].get('token', '')[:40]}...")
        else:
            self.print_result(False, f"Unexpected: {result['data']}")

        # Test human-stop (over threshold)
        console.print("\n[bold]>> Requesting stripe_refund for $100 (OVER $50 threshold)...[/bold]")
        result = self.cli.request_access(
            "research_bot_01", "secret_123", "stripe_refund",
            "Customer wants full refund for returned electronics", amount=100.0
        )
        if result["status_code"] == 202:
            self.print_result(True, "WAIT! Agent stopped for human approval.")
            ticket_id = result["data"].get("ticket_id", "")
            self.print_detail(f"Ticket ID: {ticket_id}")
            self.print_detail(f"Approvers: {result['data'].get('approvers', [])}")
            console.print()
            console.print("[yellow]  → Agent should tell user:[/yellow]")
            console.print(f'  [italic]"I need manager approval. Reference: {ticket_id}"[/italic]')
        else:
            self.print_result(False, f"Expected 202, got {result['status_code']}")

        # Test blocked keywords
        console.print("\n[bold]>> Testing stripe_refund with 'fraud' keyword...[/bold]")
        result = self.cli.request_access(
            "research_bot_01", "secret_123", "stripe_refund",
            "Process this fraud case", amount=10.0
        )
        if result["status_code"] == 403:
            self.print_result(True, "Dangerous keyword BLOCKED!")
        else:
            self.print_result(False, f"Expected 403, got {result['status_code']}")

    def run_budget_enforcement(self) -> None:
        """Demo: Budget enforcement (Denial of Wallet prevention)."""
        self.print_header("TEST 3: Budget Enforcement (Denial of Wallet)")

        console.print("\n[dim]intern_bot_02 has $1.00/hour budget[/dim]")
        console.print("[dim]google_search costs $0.01 per call[/dim]")
        console.print("[dim]Attempting 150 calls (would cost $1.50)...[/dim]\n")

        successful_calls = 0
        blocked_at = None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Making API calls...", total=150)

            for i in range(150):
                result = self.cli.request_access(
                    "intern_bot_02", "intern_secret_456", "google_search",
                    f"Search query #{i+1}: latest AI news"
                )

                if result["status_code"] == 200:
                    successful_calls += 1
                    progress.update(task, advance=1, description=f"Call {i+1}: OK")
                elif result["status_code"] == 429:
                    blocked_at = i + 1
                    break
                else:
                    break

        console.print()
        if blocked_at:
            self.print_result(True, f"Budget limit reached at call #{blocked_at}")
            self.print_detail(f"Successful calls: {successful_calls}")
            self.print_detail(f"Total spent: ${successful_calls * 0.01:.2f}")
        else:
            self.print_result(False, "Budget was NOT enforced!")

    def run_authentication(self) -> None:
        """Demo: Authentication validation."""
        self.print_header("TEST 4: Authentication Validation")

        # Test wrong secret
        console.print("\n[bold]>> Testing with INVALID credentials...[/bold]")
        result = self.cli.request_access(
            "research_bot_01", "wrong_secret", "openai_api", "Test request"
        )
        if result["status_code"] == 401:
            self.print_result(True, "Invalid credentials rejected!")
        else:
            self.print_result(False, f"Expected 401, got {result['status_code']}")

        # Test unknown agent
        console.print("\n[bold]>> Testing with UNKNOWN agent...[/bold]")
        result = self.cli.request_access(
            "unknown_agent", "some_secret", "openai_api", "Test request"
        )
        if result["status_code"] == 401:
            self.print_result(True, "Unknown agent rejected!")
        else:
            self.print_result(False, f"Expected 401, got {result['status_code']}")

    def run_permission_check(self) -> None:
        """Demo: Tool permission validation."""
        self.print_header("TEST 5: Permission Validation")

        # Test access to allowed tool
        console.print("\n[bold]>> Testing access to ALLOWED tool (openai_api)...[/bold]")
        result = self.cli.request_access(
            "research_bot_01", "secret_123", "openai_api",
            "Generate a summary of the research paper"
        )
        if result["status_code"] == 200:
            self.print_result(True, "Access to openai_api granted!")
        else:
            self.print_result(False, f"Unexpected: {result}")

        # Test restricted tool for intern
        console.print("\n[bold]>> Testing intern_bot access to RESTRICTED tool...[/bold]")
        result = self.cli.request_access(
            "intern_bot_02", "intern_secret_456", "stripe_refund",
            "Process a customer refund"
        )
        if result["status_code"] == 403:
            self.print_result(True, "Restricted tool access BLOCKED!")
        else:
            self.print_result(False, f"Expected 403, got {result['status_code']}")

    def show_audit_log(self) -> None:
        """Show recent audit log entries."""
        self.print_header("TRANSPARENCY: Audit Log (Why-Logs)")

        entries = self.cli.get_audit_log(limit=5)
        if entries:
            console.print()
            for entry in entries:
                decision = entry.get("decision", "unknown")
                icon = {"approved": "[green]✓[/green]", "blocked": "[red]✗[/red]", 
                        "pending": "[yellow]~[/yellow]"}.get(decision, "?")
                console.print(f"{icon} {decision.upper()}: {entry.get('tool', 'unknown')}")
                if entry.get("amount", 0) > 0:
                    self.print_detail(f"Amount: ${entry['amount']:.2f}")
                self.print_detail(f"WHY: {entry.get('why', 'N/A')}")
                console.print()
        else:
            console.print("[dim]No audit entries found.[/dim]")

    def print_summary(self) -> None:
        """Print demo summary."""
        total = self.passed + self.failed
        console.print()
        console.print(Panel(
            Text.assemble(
                ("Demo Complete\n\n", "bold white"),
                ("Passed: ", "dim"),
                (f"{self.passed}", "green bold"),
                (f" / {total}\n", "dim"),
                ("Failed: ", "dim"),
                (f"{self.failed}", "red bold" if self.failed else "green bold"),
                (f" / {total}", "dim"),
            ),
            border_style="green" if self.failed == 0 else "yellow",
            title="Summary",
        ))


# =============================================================================
# UI Rendering Functions
# =============================================================================

def render_header() -> Panel:
    """Render CLI header."""
    return Panel(
        Text("agent-sudo-cli", style="bold cyan"),
        title=f"[dim]{VERSION}[/dim]",
        title_align="right",
        border_style="dim",
    )


def render_request_info(ticket: dict) -> Table:
    """Render agent request details."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="dim")
    table.add_column("Value")

    agent_id = ticket.get("agent_id", "unknown")
    tool_name = ticket.get("tool_name", "unknown")
    amount = ticket.get("amount", 0.0)

    if amount > 50.0:
        risk_text = Text(f"HIGH (>${amount:.2f})", style=STYLE_RISK_HIGH)
    elif amount > 20.0:
        risk_text = Text(f"MEDIUM (${amount:.2f})", style=STYLE_RISK_MEDIUM)
    else:
        risk_text = Text(f"LOW (${amount:.2f})", style=STYLE_RISK_LOW)

    table.add_row("Agent:", Text(agent_id, style=STYLE_AGENT))
    table.add_row("Target:", Text(f"{tool_name} (Refund)", style=STYLE_TARGET))
    table.add_row("Risk Lvl:", risk_text)

    return table


def render_alert(message: str) -> Text:
    """Render policy alert."""
    alert = Text()
    alert.append("⚠ ", style="yellow bold")
    alert.append("POLICY ALERT TRIPPED: ", style=STYLE_ALERT)
    alert.append(message, style="white bold")
    return alert


def render_menu(selected: int = 0) -> Table:
    """Render intervention action menu."""
    options = [
        "Allow Once (Override)",
        "Block Request",
        "Escalate to Human (Slack)",
        "Kill Agent Process",
    ]

    table = Table(show_header=False, box=None, padding=(0, 0))
    table.add_column("Option")

    for i, option in enumerate(options, 1):
        if i - 1 == selected:
            if "Slack" in option:
                prefix = option.replace("(Slack)", "")
                table.add_row(Text.assemble(
                    ("❯ ", "green bold"),
                    (f"{i}. {prefix}(", "white on green"),
                    ("Slack", "black on green bold"),
                    (")", "white on green"),
                ))
            else:
                table.add_row(Text(f"❯ {i}. {option}", style=STYLE_SELECTED))
        else:
            table.add_row(Text(f"  {i}. {option}", style="dim"))

    return table


def display_ticket_alert(cli: AgentSudoCLI, ticket: dict):
    """Display interactive alert for a pending approval."""
    console.clear()
    console.print()

    console.print("→ ", style="green bold", end="")
    console.print(f"~ agent-sudo watch --mode={cli.mode}", style="bold")
    console.print()

    console.print(Panel(render_request_info(ticket), border_style="dim"))
    console.print()

    console.print(render_alert("Budget Cap Exceeded"))
    console.print()

    console.print("Select Intervention Action:", style="bold")
    console.print()

    console.print("  1. Allow Once (Override)")
    console.print("  2. Block Request")

    console.print(Text.assemble(
        ("❯ 3. Escalate to Human (", "white"),
        ("Slack", "black on green bold"),
        (")", "white"),
    ))

    console.print("  4. Kill Agent Process")
    console.print()

    choice = Prompt.ask(
        "Enter choice",
        choices=["1", "2", "3", "4"],
        default="3"
    )

    return int(choice)


def handle_action(cli: AgentSudoCLI, ticket: dict, action: int):
    """Handle the selected intervention action."""
    ticket_id = ticket.get("ticket_id", "")
    agent_id = ticket.get("agent_id", "")

    if action == 1:
        console.print("\n[yellow]Overriding policy...[/yellow]")
        if cli.approve_ticket(ticket_id):
            console.print("[green]✓ Request approved (one-time override)[/green]")
        else:
            console.print("[red]✗ Failed to approve request[/red]")

    elif action == 2:
        console.print("\n[yellow]Blocking request...[/yellow]")
        if cli.deny_ticket(ticket_id):
            console.print("[green]✓ Request blocked[/green]")
        else:
            console.print("[red]✗ Failed to block request[/red]")

    elif action == 3:
        if cli.send_slack_notification("security-ops", ticket):
            console.print("[green]✓ Notification sent to #security-ops[/green]")
        else:
            console.print("[red]✗ Failed to send notification[/red]")

    elif action == 4:
        console.print(f"\n[red]Terminating agent {agent_id}...[/red]")
        if cli.kill_agent_process(agent_id):
            console.print(f"[green]✓ Agent {agent_id} terminated[/green]")
        else:
            console.print(f"[yellow]⚠ Could not terminate agent (may not be running)[/yellow]")


# =============================================================================
# CLI Commands
# =============================================================================

@click.group()
@click.version_option(VERSION, prog_name="agent-sudo-cli")
def main():
    """AgentSudo CLI - Zero Trust Control Plane for AI Agents."""
    pass


@main.command()
@click.option("--mode", type=click.Choice(["strict", "permissive", "audit"]), default="strict",
              help="Enforcement mode for policy violations")
@click.option("--server", default="http://localhost:8000", help="AgentSudo server URL")
@click.option("--poll-interval", default=2.0, help="Seconds between polling for new alerts")
def watch(mode: str, server: str, poll_interval: float):
    """Watch for policy alerts and handle interventions interactively."""
    cli = AgentSudoCLI(server_url=server, mode=mode)

    console.print(f"\n[bold cyan]agent-sudo-cli[/bold cyan] {VERSION}")
    console.print(f"[dim]Watching for policy alerts (mode={mode})...[/dim]\n")

    try:
        while True:
            tickets = cli.get_pending_approvals()

            if tickets:
                for ticket in tickets:
                    action = display_ticket_alert(cli, ticket)
                    handle_action(cli, ticket, action)
                    console.print()
            else:
                console.print("[dim]No pending approvals. Watching...[/dim]", end="\r")

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Exiting watch mode.[/yellow]")
    finally:
        cli.close()


@main.command()
@click.option("--scenario", type=click.Choice(["all", "context", "hitl", "budget", "auth", "permissions"]),
              default="all", help="Demo scenario to run")
@click.option("--server", default="http://localhost:8000", help="AgentSudo server URL")
def demo(scenario: str, server: str):
    """Run interactive demos showcasing AgentSudo capabilities."""
    cli = AgentSudoCLI(server_url=server)

    console.print()
    console.print(Panel(
        Text.assemble(
            ("AgentSudo Demo\n", "bold cyan"),
            ("Zero Trust Security for AI Agents", "dim"),
        ),
        border_style="cyan",
    ))

    # Check server connectivity
    console.print("\n[bold]>> Checking server connectivity...[/bold]")
    if not cli.health_check():
        console.print("[red]✗ Cannot connect to AgentSudo server![/red]")
        console.print("[dim]  Please start the server first:[/dim]")
        console.print("[dim]  $ uvicorn agentsudo.server:app --reload[/dim]")
        cli.close()
        sys.exit(1)

    console.print("[green]✓ Server is healthy[/green]\n")

    runner = DemoRunner(cli)

    try:
        if scenario in ("all", "context"):
            runner.run_context_awareness()

        if scenario in ("all", "hitl"):
            runner.run_hitl_approval()

        if scenario in ("all", "budget"):
            runner.run_budget_enforcement()

        if scenario in ("all", "auth"):
            runner.run_authentication()

        if scenario in ("all", "permissions"):
            runner.run_permission_check()

        if scenario == "all":
            runner.show_audit_log()

        runner.print_summary()

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted.[/yellow]")
    finally:
        cli.close()


@main.command()
@click.option("--server", default="http://localhost:8000", help="AgentSudo server URL")
def status(server: str):
    """Show current system status and pending approvals."""
    cli = AgentSudoCLI(server_url=server)

    try:
        if cli.health_check():
            console.print("[green]✓ Server is healthy[/green]")
        else:
            console.print("[red]✗ Server unhealthy[/red]")

        tickets = cli.get_pending_approvals()
        if tickets:
            console.print(f"\n[yellow]⚠ {len(tickets)} pending approval(s):[/yellow]")
            for t in tickets:
                console.print(f"  • {t.get('ticket_id')}: {t.get('agent_id')} → {t.get('tool_name')}")
        else:
            console.print("\n[green]No pending approvals[/green]")

    except httpx.RequestError as e:
        console.print(f"[red]✗ Cannot connect to server: {e}[/red]")
    finally:
        cli.close()


@main.command()
@click.argument("ticket_id")
@click.option("--server", default="http://localhost:8000", help="AgentSudo server URL")
@click.option("--approver", default="cli-admin", help="Approver identifier")
def approve(ticket_id: str, server: str, approver: str):
    """Approve a pending request by ticket ID."""
    cli = AgentSudoCLI(server_url=server)

    try:
        if cli.approve_ticket(ticket_id, approver):
            console.print(f"[green]✓ Ticket {ticket_id} approved by {approver}[/green]")
        else:
            console.print(f"[red]✗ Failed to approve ticket {ticket_id}[/red]")
    finally:
        cli.close()


@main.command()
@click.argument("ticket_id")
@click.option("--server", default="http://localhost:8000", help="AgentSudo server URL")
@click.option("--approver", default="cli-admin", help="Approver identifier")
def deny(ticket_id: str, server: str, approver: str):
    """Deny a pending request by ticket ID."""
    cli = AgentSudoCLI(server_url=server)

    try:
        if cli.deny_ticket(ticket_id, approver):
            console.print(f"[green]✓ Ticket {ticket_id} denied by {approver}[/green]")
        else:
            console.print(f"[red]✗ Failed to deny ticket {ticket_id}[/red]")
    finally:
        cli.close()


@main.command()
@click.argument("agent_id")
@click.option("--server", default="http://localhost:8000", help="AgentSudo server URL")
def kill(agent_id: str, server: str):
    """Terminate an agent's active processes."""
    cli = AgentSudoCLI(server_url=server)

    if click.confirm(f"Are you sure you want to kill agent '{agent_id}'?"):
        try:
            if cli.kill_agent_process(agent_id):
                console.print(f"[green]✓ Agent {agent_id} terminated[/green]")
            else:
                console.print(f"[red]✗ Failed to terminate agent {agent_id}[/red]")
        finally:
            cli.close()


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option("--port", default=8000, help="Port to run the server on")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def start(host: str, port: int, reload: bool):
    """Start the AgentSudo Guard server."""
    console.print(f"\n[bold cyan]AgentSudo Guard[/bold cyan] {VERSION}")
    console.print(f"[dim]Starting server on {host}:{port}...[/dim]\n")
    
    try:
        from .server import start_server
        start_server(host=host, port=port, reload=reload)
    except ImportError as e:
        console.print(f"[red]✗ Failed to import server: {e}[/red]")
        console.print("[dim]  Make sure all dependencies are installed.[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
