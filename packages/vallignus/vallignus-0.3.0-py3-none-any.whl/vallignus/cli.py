"""Click-based CLI entry point - Sprint 2 P0"""

import click
import json
import os
import signal
import subprocess
import sys
import time
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from vallignus.proxy import VallignusProxy
from vallignus.logger import FlightLogger
from vallignus.rules import RulesEngine
from vallignus import auth


console = Console()
_subprocess: Optional[subprocess.Popen] = None


def parse_domains(domains_str: str) -> set:
    """Parse comma-separated domains string into a set"""
    domains = [d.strip().lower() for d in domains_str.split(',') if d.strip()]
    return set(domains)


def create_status_table(proxy: VallignusProxy, rules: RulesEngine, token_payload=None) -> Table:
    """Create a rich table showing proxy status"""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    spend, budget, remaining = rules.get_budget_status()
    
    if token_payload:
        table.add_row("Agent", token_payload.agent_id)
        table.add_row("Owner", token_payload.owner)
        table.add_row("Policy", f"{token_payload.policy_id} v{token_payload.policy_version}")
        table.add_row("Token ID", token_payload.jti[:8] + "..." if token_payload.jti else "N/A")
        table.add_row("─" * 10, "─" * 15)
    
    table.add_row("Status", "🟢 Running" if proxy.is_running else "🔴 Stopped")
    table.add_row("Allowed Requests", str(proxy.allowed_count))
    table.add_row("Blocked Requests", str(proxy.blocked_count))
    
    if budget is not None:
        table.add_row("Budget", f"${budget:.2f}")
        table.add_row("Spent", f"${spend:.4f}")
        table.add_row("Remaining", f"${remaining:.2f}" if remaining is not None else "N/A")
        
        if remaining is not None:
            percent_used = (spend / budget) * 100 if budget > 0 else 0
            if percent_used >= 100:
                status_text = Text("⚠️  EXCEEDED", style="bold red")
            elif percent_used >= 80:
                status_text = Text(f"⚠️  {percent_used:.1f}%", style="bold yellow")
            else:
                status_text = Text(f"✓ {percent_used:.1f}%", style="green")
            table.add_row("Budget Usage", status_text)
    else:
        table.add_row("Budget", "Unlimited")
        table.add_row("Spent", f"${spend:.4f}")
    
    return table


@click.group()
def cli():
    """Vallignus - Infrastructure-grade firewall for AI agents"""
    pass


@cli.group()
def auth_cmd():
    """Manage agent identities, policies, and tokens"""
    pass

cli.add_command(auth_cmd, name='auth')


@auth_cmd.command('init')
def auth_init():
    """Initialize Vallignus auth (creates ~/.vallignus directories and keyring)"""
    success, message = auth.init_auth()
    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        sys.exit(1)


@auth_cmd.command('create-agent')
@click.option('--agent-id', required=True, help='Unique identifier for the agent')
@click.option('--owner', required=True, help='Owner of the agent')
@click.option('--description', default='', help='Optional description')
def auth_create_agent(agent_id: str, owner: str, description: str):
    """Create a new agent identity"""
    success, message = auth.create_agent(agent_id, owner, description)
    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        sys.exit(1)


@auth_cmd.command('list-agents')
def auth_list_agents():
    """List all registered agents"""
    agents = auth.list_agents()
    if not agents:
        console.print("[yellow]No agents registered[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Agent ID")
    table.add_column("Owner")
    table.add_column("Description")
    
    for a in agents:
        table.add_row(a["agent_id"], a["owner"], a.get("description", ""))
    
    console.print(table)


@auth_cmd.command('create-policy')
@click.option('--policy-id', required=True, help='Unique identifier for the policy')
@click.option('--max-spend-usd', type=float, default=None, help='Maximum spend in USD')
@click.option('--allowed-domains', required=True, help='Comma-separated list of allowed domains')
@click.option('--description', default='', help='Optional description')
def auth_create_policy(policy_id: str, max_spend_usd: Optional[float], allowed_domains: str, description: str):
    """Create a new permission policy (v1)"""
    success, message = auth.create_policy(policy_id, max_spend_usd, allowed_domains, description)
    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        sys.exit(1)


@auth_cmd.command('update-policy')
@click.option('--policy-id', required=True, help='Policy to update')
@click.option('--max-spend-usd', type=float, default=None, help='New maximum spend in USD')
@click.option('--allowed-domains', default=None, help='New comma-separated list of allowed domains')
@click.option('--description', default=None, help='New description')
def auth_update_policy(policy_id: str, max_spend_usd: Optional[float], allowed_domains: Optional[str], description: Optional[str]):
    """Update a policy (creates new version)"""
    if max_spend_usd is None and allowed_domains is None and description is None:
        console.print("[red]✗[/red] At least one field must be updated")
        sys.exit(1)
    
    success, message = auth.update_policy(policy_id, max_spend_usd, allowed_domains, description)
    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        sys.exit(1)


@auth_cmd.command('list-policies')
def auth_list_policies():
    """List all registered policies"""
    policies = auth.list_policies()
    if not policies:
        console.print("[yellow]No policies registered[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Policy ID")
    table.add_column("Version")
    table.add_column("Max Spend")
    table.add_column("Domains")
    
    for p in policies:
        spend = f"${p['max_spend_usd']:.2f}" if p.get("max_spend_usd") else "Unlimited"
        domains = ", ".join(p["allowed_domains"][:3])
        if len(p["allowed_domains"]) > 3:
            domains += f" (+{len(p['allowed_domains']) - 3} more)"
        table.add_row(p["policy_id"], f"v{p.get('version', 1)}", spend, domains)
    
    console.print(table)


@auth_cmd.command('issue-token')
@click.option('--agent-id', required=True, help='Agent to issue token for')
@click.option('--policy-id', required=True, help='Policy to bind to token')
@click.option('--ttl-seconds', type=int, default=3600, help='Token TTL in seconds')
def auth_issue_token(agent_id: str, policy_id: str, ttl_seconds: int):
    """Issue a signed token for an agent with a specific policy"""
    try:
        token = auth.issue_token(agent_id, policy_id, ttl_seconds)
        print(token)
    except auth.AuthError as e:
        console.print(f"[red]✗[/red] {e}")
        sys.exit(1)


@auth_cmd.command('verify-token')
@click.argument('token')
def auth_verify_token(token: str):
    """Verify a token and display its contents"""
    try:
        payload, policy = auth.verify_token_with_policy(token)
        console.print("[green]✓ Token valid[/green]\n")
        
        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        
        table.add_row("Agent ID", payload.agent_id)
        table.add_row("Owner", payload.owner)
        table.add_row("Policy", f"{payload.policy_id} v{payload.policy_version}")
        table.add_row("Token ID (jti)", payload.jti)
        table.add_row("Expires", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(payload.expires_at)))
        table.add_row("─" * 10, "─" * 30)
        table.add_row("Max Spend", f"${policy.max_spend_usd:.2f}" if policy.max_spend_usd else "Unlimited")
        table.add_row("Domains", ", ".join(sorted(policy.allowed_domains)))
        
        console.print(table)
    except auth.AuthError as e:
        console.print(f"[red]✗ {e}[/red]")
        sys.exit(1)


@auth_cmd.command('inspect-token')
@click.argument('token')
def auth_inspect_token(token: str):
    """Decode token WITHOUT verification (for debugging)"""
    try:
        decoded = auth.decode_token_payload(token)
        console.print("[yellow]⚠ Decoded (NOT verified)[/yellow]\n")
        console.print("[bold]Header:[/bold]")
        console.print(json.dumps(decoded["header"], indent=2))
        console.print("\n[bold]Payload:[/bold]")
        console.print(json.dumps(decoded["payload"], indent=2))
    except auth.AuthError as e:
        console.print(f"[red]✗ {e}[/red]")
        sys.exit(1)


@auth_cmd.command('revoke-token')
@click.option('--jti', required=True, help='Token ID (jti) to revoke')
def auth_revoke_token(jti: str):
    """Revoke a token by its JTI"""
    success, message = auth.revoke_token(jti)
    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        sys.exit(1)


@auth_cmd.command('rotate-key')
def auth_rotate_key():
    """Generate a new signing key (old tokens remain valid)"""
    success, message = auth.rotate_key()
    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        sys.exit(1)


@cli.command()
@click.option('--token', envvar='VALLIGNUS_TOKEN', required=True, help='Auth token')
@click.option('--port', type=int, default=8080, help='Proxy port')
@click.option('--log', type=str, default='flight_log.json', help='Log file path')
@click.argument('command', nargs=-1, required=True)
def run(token: str, port: int, log: str, command: List[str]):
    """Run a command through the Vallignus firewall proxy."""
    global _subprocess
    
    if not command:
        console.print("[red]Error: Command is required[/red]")
        sys.exit(1)
    
    try:
        token_payload, policy = auth.verify_token_with_policy(token)
    except auth.AuthError as e:
        if "TOKEN_REVOKED" in str(e):
            console.print(f"[red]✗ Token has been revoked[/red]")
        else:
            console.print(f"[red]✗ Token error: {e}[/red]")
        sys.exit(1)
    
    allowed_domains = policy.allowed_domains
    budget = policy.max_spend_usd
    
    console.print(f"[cyan]Agent:[/cyan] {token_payload.agent_id} ({token_payload.owner})")
    console.print(f"[cyan]Policy:[/cyan] {token_payload.policy_id} v{token_payload.policy_version}")
    console.print(f"[cyan]Budget:[/cyan] ${budget:.2f}" if budget else "[cyan]Budget:[/cyan] Unlimited")
    console.print(f"[cyan]Domains:[/cyan] {', '.join(sorted(allowed_domains))}")
    console.print()
    
    logger = FlightLogger(
        log_file=log,
        agent_id=token_payload.agent_id,
        owner=token_payload.owner,
        policy_id=token_payload.policy_id,
        policy_version=token_payload.policy_version,
        jti=token_payload.jti
    )
    rules = RulesEngine(allowed_domains, budget)
    proxy = VallignusProxy(allowed_domains, budget, logger, rules)
    
    try:
        actual_port = proxy.start(port)
        console.print(f"[green]✓[/green] Proxy started on port {actual_port}")
    except Exception as e:
        console.print(f"[red]Error starting proxy: {e}[/red]")
        sys.exit(1)
    
    env = os.environ.copy()
    env['HTTP_PROXY'] = f'http://127.0.0.1:{actual_port}'
    env['HTTPS_PROXY'] = f'http://127.0.0.1:{actual_port}'
    env['http_proxy'] = f'http://127.0.0.1:{actual_port}'
    env['https_proxy'] = f'http://127.0.0.1:{actual_port}'
    env['PYTHONWARNINGS'] = 'ignore'
    
    console.print(f"[cyan]Starting: {' '.join(command)}[/cyan]")
    try:
        _subprocess = subprocess.Popen(list(command), env=env)
    except Exception as e:
        console.print(f"[red]Error starting command: {e}[/red]")
        proxy.stop()
        sys.exit(1)
    
    def signal_handler(sig, frame):
        console.print("\n[yellow]Shutting down...[/yellow]")
        if _subprocess:
            _subprocess.terminate()
        proxy.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while _subprocess.poll() is None:
            if proxy._should_terminate:
                console.print("\n[red]⚠️  Budget exceeded![/red]")
                _subprocess.terminate()
                break
            time.sleep(0.1)
        
        status_table = create_status_table(proxy, rules, token_payload)
        console.print(Panel(status_table, title="Vallignus Firewall", border_style="blue"))
        console.print(f"\n[cyan]Flight log saved to: {log}[/cyan]")
    finally:
        proxy.stop()
        if _subprocess and _subprocess.poll() is None:
            _subprocess.terminate()


def main():
    cli()


if __name__ == '__main__':
    main()