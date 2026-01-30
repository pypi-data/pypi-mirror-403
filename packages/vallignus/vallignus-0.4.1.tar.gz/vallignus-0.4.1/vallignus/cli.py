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
from vallignus import sessions


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


# =============================================================================
# SESSIONS COMMANDS
# =============================================================================

@cli.group()
def sessions_cmd():
    """Manage agent sessions and replay"""
    pass

cli.add_command(sessions_cmd, name='sessions')


@sessions_cmd.command('list')
@click.option('--limit', type=int, default=20, help='Maximum number of sessions to show')
def sessions_list(limit: int):
    """List recent sessions"""
    session_list = sessions.SessionManager.list_sessions(limit)
    
    if not session_list:
        console.print("[yellow]No sessions found[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Session ID", style="cyan")
    table.add_column("Exit", justify="center")
    table.add_column("Duration", justify="right")
    table.add_column("Command")
    
    for s in session_list:
        # Format exit code with color
        if s.exit_code is None:
            exit_str = Text("...", style="yellow")
        elif s.exit_code == 0:
            exit_str = Text("0", style="green")
        else:
            exit_str = Text(str(s.exit_code), style="red")
        
        # Format duration
        if s.duration_ms is not None:
            if s.duration_ms < 1000:
                duration_str = f"{s.duration_ms}ms"
            elif s.duration_ms < 60000:
                duration_str = f"{s.duration_ms/1000:.1f}s"
            else:
                duration_str = f"{s.duration_ms/60000:.1f}m"
        else:
            duration_str = "-"
        
        # Format command (truncate if too long)
        cmd_str = ' '.join(s.command)
        if len(cmd_str) > 50:
            cmd_str = cmd_str[:47] + "..."
        
        table.add_row(s.session_id, exit_str, duration_str, cmd_str)
    
    console.print(table)


@sessions_cmd.command('show')
@click.argument('session_id')
@click.option('--events', type=int, default=20, help='Number of events to show')
def sessions_show(session_id: str, events: int):
    """Show session details and recent events"""
    metadata = sessions.SessionManager.load(session_id)
    
    if not metadata:
        console.print(f"[red]Session not found: {session_id}[/red]")
        sys.exit(1)
    
    # Session metadata table
    console.print(f"\n[bold cyan]Session: {session_id}[/bold cyan]\n")
    
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    
    table.add_row("Started", metadata.started_at_iso)
    if metadata.finished_at_iso:
        table.add_row("Finished", metadata.finished_at_iso)
    table.add_row("Command", ' '.join(metadata.command))
    table.add_row("CWD", metadata.cwd)
    
    if metadata.exit_code is not None:
        exit_style = "green" if metadata.exit_code == 0 else "red"
        table.add_row("Exit Code", Text(str(metadata.exit_code), style=exit_style))
    else:
        table.add_row("Exit Code", Text("running...", style="yellow"))
    
    if metadata.duration_ms is not None:
        table.add_row("Duration", f"{metadata.duration_ms}ms ({metadata.duration_ms/1000:.2f}s)")
    
    table.add_row("Stdout Lines", str(metadata.stdout_lines))
    table.add_row("Stderr Lines", str(metadata.stderr_lines))
    
    # Sprint 1: Show termination info if present
    if metadata.termination_reason:
        table.add_row("", "")  # Spacer
        table.add_row("Termination", Text(metadata.termination_reason, style="red bold"))
        if metadata.termination_limit_value is not None:
            table.add_row("  Limit", str(metadata.termination_limit_value))
        if metadata.termination_observed_value is not None:
            table.add_row("  Observed", str(metadata.termination_observed_value))
    
    # Sprint 1: Show request counts if present (firewall mode)
    if metadata.total_requests is not None:
        table.add_row("", "")  # Spacer
        table.add_row("Total Requests", str(metadata.total_requests))
        table.add_row("  Allowed", Text(str(metadata.allowed_requests or 0), style="green"))
        table.add_row("  Denied", Text(str(metadata.denied_requests or 0), style="red"))
    
    console.print(table)
    
    # Show recent events
    all_events = sessions.SessionManager.load_events(session_id)
    
    if all_events:
        console.print(f"\n[bold]Last {min(events, len(all_events))} events:[/bold]\n")
        
        # Get last N events
        recent_events = all_events[-events:] if len(all_events) > events else all_events
        
        for event in recent_events:
            event_type = event.get('type', 'unknown')
            ts_ms = event.get('ts_ms', 0)
            
            # Format timestamp relative to first event
            if all_events:
                start_ts = all_events[0].get('ts_ms', ts_ms)
                relative = (ts_ms - start_ts) / 1000
                ts_str = f"[dim]+{relative:.3f}s[/dim]"
            else:
                ts_str = ""
            
            if event_type == 'stdout_line':
                line = event.get('line', '')
                console.print(f"  {ts_str} [green]stdout[/green]: {line}")
            elif event_type == 'stderr_line':
                line = event.get('line', '')
                console.print(f"  {ts_str} [red]stderr[/red]: {line}")
            elif event_type == 'run_started':
                console.print(f"  {ts_str} [cyan]run_started[/cyan]")
            elif event_type == 'process_started':
                console.print(f"  {ts_str} [cyan]process_started[/cyan]")
            elif event_type == 'process_exited':
                exit_code = event.get('exit_code', '?')
                console.print(f"  {ts_str} [cyan]process_exited[/cyan] (code={exit_code})")
            elif event_type == 'run_finished':
                duration = event.get('duration_ms', 0)
                console.print(f"  {ts_str} [cyan]run_finished[/cyan] (duration={duration}ms)")
            elif event_type == 'run_terminated':
                reason = event.get('reason', '?')
                limit_val = event.get('limit_value', '?')
                observed_val = event.get('observed_value', '?')
                console.print(f"  {ts_str} [red bold]run_terminated[/red bold] reason={reason} limit={limit_val} observed={observed_val}")
            else:
                console.print(f"  {ts_str} [dim]{event_type}[/dim]")


@cli.command()
@click.argument('session_id')
@click.option('--no-timestamps', is_flag=True, help='Hide timestamps')
def replay(session_id: str, no_timestamps: bool):
    """Replay a session's output to console"""
    try:
        all_events = sessions.SessionManager.load_events(session_id)
        
        if not all_events:
            console.print(f"[red]No events found for session: {session_id}[/red]")
            sys.exit(1)
        
        metadata = sessions.SessionManager.load(session_id)
        if metadata:
            console.print(f"[dim]Replaying session: {session_id}[/dim]")
            console.print(f"[dim]Command: {' '.join(metadata.command)}[/dim]")
            console.print()
        
        start_ts = all_events[0].get('ts_ms', 0) if all_events else 0
        
        for event in all_events:
            event_type = event.get('type', '')
            ts_ms = event.get('ts_ms', 0)
            relative_s = (ts_ms - start_ts) / 1000
            
            if event_type == 'stdout_line':
                line = event.get('line', '')
                if no_timestamps:
                    print(line)
                else:
                    print(f"[{relative_s:>7.3f}s] {line}")
            
            elif event_type == 'stderr_line':
                line = event.get('line', '')
                if no_timestamps:
                    console.print(f"[red]{line}[/red]")
                else:
                    console.print(f"[dim][{relative_s:>7.3f}s][/dim] [red]{line}[/red]")
        
        console.print()
        if metadata and metadata.exit_code is not None:
            style = "green" if metadata.exit_code == 0 else "red"
            console.print(f"[dim]Exit code:[/dim] [{style}]{metadata.exit_code}[/{style}]")
        if metadata and metadata.duration_ms is not None:
            console.print(f"[dim]Duration:[/dim] {metadata.duration_ms}ms")
    
    except Exception as e:
        console.print(f"[red]Error replaying session: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--token', envvar='VALLIGNUS_TOKEN', required=False, help='Auth token (optional, enables firewall)')
@click.option('--port', type=int, default=8080, help='Proxy port (firewall mode)')
@click.option('--log', type=str, default='flight_log.json', help='Firewall log file path')
@click.option('--no-session', is_flag=True, help='Disable session logging')
@click.option('--max-runtime', type=int, default=None, help='Maximum runtime in seconds before termination')
@click.option('--max-output-lines', type=int, default=None, help='Maximum stdout+stderr lines before termination')
@click.option('--max-requests', type=int, default=None, help='Maximum HTTP requests before termination (firewall mode only)')
@click.argument('command', nargs=-1, required=True)
def run(token: Optional[str], port: int, log: str, no_session: bool, 
        max_runtime: Optional[int], max_output_lines: Optional[int], 
        max_requests: Optional[int], command: List[str]):
    """
    Run a command with session logging (and optional firewall).
    
    Without --token: Creates a session with logs and replay support.
    
    With --token: Also enforces firewall policies via proxy.
    
    Limits (all optional):
    
      --max-runtime: Kill process after N seconds
    
      --max-output-lines: Kill after N total output lines
    
      --max-requests: Kill after N HTTP requests (firewall mode only)
    """
    global _subprocess
    
    if not command:
        console.print("[red]Error: Command is required[/red]")
        sys.exit(1)
    
    # Warn if --max-requests used without firewall mode
    if max_requests is not None and token is None:
        console.print("[yellow]Warning: --max-requests only works in firewall mode (with --token)[/yellow]")
        max_requests = None
    
    # Initialize session
    session_manager = None
    if not no_session:
        session_manager = sessions.SessionManager()
        session_manager.create(list(command))
        console.print(f"[dim]Session: {session_manager.session_id}[/dim]")
    
    # Print limits if set
    limits_active = []
    if max_runtime:
        limits_active.append(f"runtime={max_runtime}s")
    if max_output_lines:
        limits_active.append(f"output={max_output_lines} lines")
    if max_requests:
        limits_active.append(f"requests={max_requests}")
    if limits_active:
        console.print(f"[dim]Limits: {', '.join(limits_active)}[/dim]")
    
    # Check if firewall mode (token provided)
    firewall_mode = token is not None
    token_payload = None
    policy = None
    proxy = None
    rules = None
    
    if firewall_mode:
        try:
            token_payload, policy = auth.verify_token_with_policy(token)
        except auth.AuthError as e:
            if session_manager:
                session_manager.finish(-1)
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
            if session_manager:
                session_manager.finish(-1)
            console.print(f"[red]Error starting proxy: {e}[/red]")
            sys.exit(1)
    
    # Set up environment
    env = os.environ.copy()
    if firewall_mode and proxy:
        actual_port = proxy._port if hasattr(proxy, '_port') else port
        env['HTTP_PROXY'] = f'http://127.0.0.1:{actual_port}'
        env['HTTPS_PROXY'] = f'http://127.0.0.1:{actual_port}'
        env['http_proxy'] = f'http://127.0.0.1:{actual_port}'
        env['https_proxy'] = f'http://127.0.0.1:{actual_port}'
        env['PYTHONWARNINGS'] = 'ignore'
    
    console.print(f"[cyan]Starting: {' '.join(command)}[/cyan]")
    
    # Shared state for termination
    termination_reason = None
    termination_limit = None
    termination_observed = None
    should_terminate = False
    
    try:
        # Start subprocess with output capture for sessions
        _subprocess = subprocess.Popen(
            list(command),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        if session_manager:
            session_manager.process_started()
        
        # Thread-safe output handling
        import threading
        output_lock = threading.Lock()
        
        def read_stdout():
            nonlocal should_terminate, termination_reason, termination_limit, termination_observed
            try:
                for line in iter(_subprocess.stdout.readline, ''):
                    if should_terminate:
                        break
                    line = line.rstrip('\n\r')
                    with output_lock:
                        print(line)
                        sys.stdout.flush()
                    if session_manager:
                        total_lines = session_manager.log_stdout(line)
                        # Check output line limit
                        if max_output_lines and total_lines >= max_output_lines and not should_terminate:
                            should_terminate = True
                            termination_reason = "max_output_lines"
                            termination_limit = max_output_lines
                            termination_observed = total_lines
            except:
                pass
        
        def read_stderr():
            nonlocal should_terminate, termination_reason, termination_limit, termination_observed
            try:
                for line in iter(_subprocess.stderr.readline, ''):
                    if should_terminate:
                        break
                    line = line.rstrip('\n\r')
                    with output_lock:
                        console.print(f"[red]{line}[/red]")
                    if session_manager:
                        total_lines = session_manager.log_stderr(line)
                        # Check output line limit
                        if max_output_lines and total_lines >= max_output_lines and not should_terminate:
                            should_terminate = True
                            termination_reason = "max_output_lines"
                            termination_limit = max_output_lines
                            termination_observed = total_lines
            except:
                pass
        
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        
    except Exception as e:
        if session_manager:
            session_manager.finish(-1)
        console.print(f"[red]Error starting command: {e}[/red]")
        if proxy:
            proxy.stop()
        sys.exit(1)
    
    def signal_handler(sig, frame):
        console.print("\n[yellow]Shutting down...[/yellow]")
        if _subprocess:
            _subprocess.terminate()
        if proxy:
            proxy.stop()
        if session_manager:
            session_manager.finish(-15)  # SIGTERM
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    exit_code = 0
    start_time = time.time()
    
    try:
        while _subprocess.poll() is None:
            # Check budget exceeded (firewall mode)
            if firewall_mode and proxy and proxy._should_terminate:
                console.print("\n[red]⚠️  Budget exceeded![/red]")
                should_terminate = True
                termination_reason = "budget_exceeded"
            
            # Check max runtime
            if max_runtime:
                elapsed = time.time() - start_time
                if elapsed >= max_runtime and not should_terminate:
                    should_terminate = True
                    termination_reason = "max_runtime"
                    termination_limit = max_runtime
                    termination_observed = int(elapsed)
            
            # Check max requests (firewall mode)
            if max_requests and firewall_mode and proxy:
                total_requests = proxy.allowed_count + proxy.blocked_count
                if total_requests >= max_requests and not should_terminate:
                    should_terminate = True
                    termination_reason = "max_requests"
                    termination_limit = max_requests
                    termination_observed = total_requests
            
            # Perform termination if needed
            if should_terminate:
                console.print(f"\n[red]⚠️  Terminating: {termination_reason}[/red]")
                if termination_limit:
                    console.print(f"[red]   Limit: {termination_limit}, Observed: {termination_observed}[/red]")
                
                # Record termination in session
                if session_manager and termination_reason and termination_reason != "budget_exceeded":
                    session_manager.terminate(termination_reason, termination_limit or 0, termination_observed or 0)
                
                # Graceful terminate first
                _subprocess.terminate()
                
                # Wait up to 2 seconds for graceful shutdown
                try:
                    _subprocess.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    # Force kill if still running
                    console.print("[red]   Process did not exit, sending SIGKILL...[/red]")
                    _subprocess.kill()
                    _subprocess.wait(timeout=1.0)
                
                break
            
            time.sleep(0.1)
        
        # Wait for output threads to finish
        stdout_thread.join(timeout=1.0)
        stderr_thread.join(timeout=1.0)
        
        exit_code = _subprocess.returncode or 0
        
        # Record request counts from firewall
        if session_manager and firewall_mode and proxy:
            session_manager.set_request_counts(proxy.allowed_count, proxy.blocked_count)
        
        # Finalize session
        if session_manager:
            session_manager.finish(exit_code)
            console.print(f"\n[dim]Session saved: {session_manager.session_id}[/dim]")
            console.print(f"[dim]Replay with: vallignus replay {session_manager.session_id}[/dim]")
            if termination_reason:
                console.print(f"[dim]Termination: {termination_reason}[/dim]")
        
        # Show firewall summary if in firewall mode
        if firewall_mode and rules:
            status_table = create_status_table(proxy, rules, token_payload)
            console.print(Panel(status_table, title="Vallignus Firewall", border_style="blue"))
            console.print(f"\n[cyan]Flight log saved to: {log}[/cyan]")
        
        # Exit with non-zero if terminated
        if termination_reason:
            sys.exit(1)
        
    finally:
        if proxy:
            proxy.stop()
        if _subprocess and _subprocess.poll() is None:
            _subprocess.terminate()


def main():
    cli()


if __name__ == '__main__':
    main()