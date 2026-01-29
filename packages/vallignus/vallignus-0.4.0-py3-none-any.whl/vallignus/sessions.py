"""Vallignus Sessions - Agent Runtime with sessions and event logging

Sprint 0 Features:
- Session creation with unique IDs (YYYYMMDD-HHMMSS-<random6>)
- Structured event logging (JSONL)
- Session metadata (session.json)
- stdout/stderr capture
- Session listing and replay

Sprint 1 Features:
- Runtime caps and termination controls
- Output line limits
- Request counting (firewall mode)
- Termination event logging
"""

import json
import os
import random
import string
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable


# Storage paths
VALLIGNUS_DIR = Path.home() / ".vallignus"
SESSIONS_DIR = VALLIGNUS_DIR / "sessions"


@dataclass
class SessionMetadata:
    """Session metadata stored in session.json"""
    session_id: str
    started_at_iso: str
    command: List[str]
    cwd: str
    env_summary: Dict[str, str]
    exit_code: Optional[int] = None
    duration_ms: Optional[int] = None
    finished_at_iso: Optional[str] = None
    stdout_lines: int = 0
    stderr_lines: int = 0
    # Sprint 1: Termination tracking
    termination_reason: Optional[str] = None  # "max_runtime", "max_output_lines", "max_requests"
    termination_limit_value: Optional[int] = None
    termination_observed_value: Optional[int] = None
    # Sprint 1: Request counters (firewall mode)
    allowed_requests: Optional[int] = None
    denied_requests: Optional[int] = None
    total_requests: Optional[int] = None


@dataclass 
class SessionEvent:
    """A single event in the session event stream"""
    ts_ms: int
    session_id: str
    type: str
    line: Optional[str] = None
    exit_code: Optional[int] = None
    command: Optional[List[str]] = None
    cwd: Optional[str] = None
    duration_ms: Optional[int] = None
    # Sprint 1: Termination event fields
    reason: Optional[str] = None
    limit_value: Optional[int] = None
    observed_value: Optional[int] = None
    
    def to_json(self) -> str:
        """Serialize event to JSON, excluding None values"""
        data = {k: v for k, v in asdict(self).items() if v is not None}
        return json.dumps(data, separators=(',', ':'))


def generate_session_id() -> str:
    """
    Generate a unique session ID in format: YYYYMMDD-HHMMSS-<random6>
    
    Example: 20250124-153045-a1b2c3
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{timestamp}-{random_suffix}"


def get_session_dir(session_id: str) -> Path:
    """Get the directory path for a session"""
    return SESSIONS_DIR / session_id


def get_safe_env_summary(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Extract safe environment variables for logging.
    Only includes non-sensitive keys.
    """
    if env is None:
        env = dict(os.environ)
    
    # Safe keys to include
    safe_prefixes = ('PATH', 'HOME', 'USER', 'SHELL', 'TERM', 'LANG', 'LC_', 
                     'PYTHONPATH', 'VIRTUAL_ENV', 'CONDA_', 'NODE_', 'NPM_')
    safe_exact = {'PWD', 'OLDPWD', 'SHLVL', 'HOSTNAME', 'LOGNAME'}
    
    result = {}
    for key, value in env.items():
        if key in safe_exact or any(key.startswith(p) for p in safe_prefixes):
            # Truncate long values
            if len(value) > 200:
                value = value[:200] + "..."
            result[key] = value
    
    return result


class EventLogger:
    """Append-only event logger that writes to events.jsonl"""
    
    def __init__(self, session_dir: Path, session_id: str):
        self.session_dir = session_dir
        self.session_id = session_id
        self.events_file = session_dir / "events.jsonl"
        self._lock = threading.Lock()
    
    def _now_ms(self) -> int:
        """Get current timestamp in milliseconds"""
        return int(time.time() * 1000)
    
    def log(self, event_type: str, **kwargs) -> SessionEvent:
        """Log an event to the JSONL file"""
        event = SessionEvent(
            ts_ms=self._now_ms(),
            session_id=self.session_id,
            type=event_type,
            **kwargs
        )
        
        with self._lock:
            with open(self.events_file, 'a') as f:
                f.write(event.to_json() + '\n')
        
        return event
    
    def run_started(self, command: List[str], cwd: str) -> SessionEvent:
        """Log run_started event"""
        return self.log('run_started', command=command, cwd=cwd)
    
    def process_started(self) -> SessionEvent:
        """Log process_started event"""
        return self.log('process_started')
    
    def stdout_line(self, line: str) -> SessionEvent:
        """Log stdout_line event"""
        return self.log('stdout_line', line=line)
    
    def stderr_line(self, line: str) -> SessionEvent:
        """Log stderr_line event"""
        return self.log('stderr_line', line=line)
    
    def process_exited(self, exit_code: int) -> SessionEvent:
        """Log process_exited event"""
        return self.log('process_exited', exit_code=exit_code)
    
    def run_terminated(self, reason: str, limit_value: int, observed_value: int) -> SessionEvent:
        """Log run_terminated event when process is killed due to limits"""
        return self.log('run_terminated', reason=reason, limit_value=limit_value, observed_value=observed_value)
    
    def run_finished(self, duration_ms: int) -> SessionEvent:
        """Log run_finished event"""
        return self.log('run_finished', duration_ms=duration_ms)


class SessionManager:
    """Manages session lifecycle, directories, and metadata"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or generate_session_id()
        self.session_dir = get_session_dir(self.session_id)
        self.event_logger: Optional[EventLogger] = None
        self.metadata: Optional[SessionMetadata] = None
        self._start_time: Optional[float] = None
        self._stdout_lines = 0
        self._stderr_lines = 0
        self._stdout_file: Optional[Any] = None
        self._stderr_file: Optional[Any] = None
        # Sprint 1: Termination tracking
        self._termination_reason: Optional[str] = None
        self._termination_limit_value: Optional[int] = None
        self._termination_observed_value: Optional[int] = None
        # Sprint 1: Request counters
        self._allowed_requests: int = 0
        self._denied_requests: int = 0
    
    @property
    def total_output_lines(self) -> int:
        """Get total output lines (stdout + stderr)"""
        return self._stdout_lines + self._stderr_lines
    
    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time since session started"""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
    
    def create(self, command: List[str], cwd: Optional[str] = None, 
               env: Optional[Dict[str, str]] = None) -> 'SessionManager':
        """Create a new session directory and initialize files"""
        # Ensure sessions directory exists
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create session directory
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize event logger
        self.event_logger = EventLogger(self.session_dir, self.session_id)
        
        # Create initial metadata
        cwd = cwd or os.getcwd()
        self.metadata = SessionMetadata(
            session_id=self.session_id,
            started_at_iso=datetime.now().isoformat(),
            command=command,
            cwd=cwd,
            env_summary=get_safe_env_summary(env)
        )
        
        # Open stdout/stderr log files
        self._stdout_file = open(self.session_dir / "stdout.log", 'w')
        self._stderr_file = open(self.session_dir / "stderr.log", 'w')
        
        # Write initial session.json
        self._save_metadata()
        
        # Record start time
        self._start_time = time.time()
        
        # Log run_started event
        self.event_logger.run_started(command, cwd)
        
        return self
    
    def _save_metadata(self):
        """Save current metadata to session.json, excluding None values"""
        data = {k: v for k, v in asdict(self.metadata).items() if v is not None}
        with open(self.session_dir / "session.json", 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_stdout(self, line: str) -> int:
        """Log a stdout line. Returns total output lines."""
        self._stdout_lines += 1
        if self.event_logger:
            self.event_logger.stdout_line(line)
        if self._stdout_file:
            self._stdout_file.write(line + '\n')
            self._stdout_file.flush()
        return self.total_output_lines
    
    def log_stderr(self, line: str) -> int:
        """Log a stderr line. Returns total output lines."""
        self._stderr_lines += 1
        if self.event_logger:
            self.event_logger.stderr_line(line)
        if self._stderr_file:
            self._stderr_file.write(line + '\n')
            self._stderr_file.flush()
        return self.total_output_lines
    
    def process_started(self):
        """Log that the subprocess has started"""
        if self.event_logger:
            self.event_logger.process_started()
    
    def terminate(self, reason: str, limit_value: int, observed_value: int):
        """
        Record that the session was terminated due to a limit.
        
        Args:
            reason: One of "max_runtime", "max_output_lines", "max_requests"
            limit_value: The configured limit
            observed_value: The actual value that triggered termination
        """
        self._termination_reason = reason
        self._termination_limit_value = limit_value
        self._termination_observed_value = observed_value
        
        if self.event_logger:
            self.event_logger.run_terminated(reason, limit_value, observed_value)
    
    def set_request_counts(self, allowed: int, denied: int):
        """Set request counters from firewall mode"""
        self._allowed_requests = allowed
        self._denied_requests = denied
    
    def finish(self, exit_code: int):
        """Finalize the session with exit code and duration"""
        if self._start_time is None:
            return
        
        duration_ms = int((time.time() - self._start_time) * 1000)
        
        # Log process_exited and run_finished events
        if self.event_logger:
            self.event_logger.process_exited(exit_code)
            self.event_logger.run_finished(duration_ms)
        
        # Update and save metadata
        if self.metadata:
            self.metadata.exit_code = exit_code
            self.metadata.duration_ms = duration_ms
            self.metadata.finished_at_iso = datetime.now().isoformat()
            self.metadata.stdout_lines = self._stdout_lines
            self.metadata.stderr_lines = self._stderr_lines
            # Sprint 1: Termination info
            if self._termination_reason:
                self.metadata.termination_reason = self._termination_reason
                self.metadata.termination_limit_value = self._termination_limit_value
                self.metadata.termination_observed_value = self._termination_observed_value
            # Sprint 1: Request counters (only if firewall mode was active)
            if self._allowed_requests > 0 or self._denied_requests > 0:
                self.metadata.allowed_requests = self._allowed_requests
                self.metadata.denied_requests = self._denied_requests
                self.metadata.total_requests = self._allowed_requests + self._denied_requests
            self._save_metadata()
        
        # Close log files
        if self._stdout_file:
            self._stdout_file.close()
        if self._stderr_file:
            self._stderr_file.close()
    
    @staticmethod
    def load(session_id: str) -> Optional[SessionMetadata]:
        """Load session metadata from disk"""
        session_dir = get_session_dir(session_id)
        session_json = session_dir / "session.json"
        
        if not session_json.exists():
            return None
        
        try:
            with open(session_json, 'r') as f:
                data = json.load(f)
            # Handle missing optional fields by filtering to known fields
            known_fields = {f.name for f in SessionMetadata.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in known_fields}
            return SessionMetadata(**filtered_data)
        except Exception:
            return None
    
    @staticmethod
    def load_events(session_id: str) -> List[Dict[str, Any]]:
        """Load all events for a session"""
        session_dir = get_session_dir(session_id)
        events_file = session_dir / "events.jsonl"
        
        if not events_file.exists():
            return []
        
        events = []
        with open(events_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return events
    
    @staticmethod
    def list_sessions(limit: int = 20) -> List[SessionMetadata]:
        """
        List recent sessions, sorted by most recent first.
        Returns up to `limit` sessions.
        """
        if not SESSIONS_DIR.exists():
            return []
        
        sessions = []
        
        for session_dir in SESSIONS_DIR.iterdir():
            if session_dir.is_dir():
                metadata = SessionManager.load(session_dir.name)
                if metadata:
                    sessions.append(metadata)
        
        # Sort by started_at_iso descending (most recent first)
        sessions.sort(key=lambda s: s.started_at_iso, reverse=True)
        
        return sessions[:limit]


def run_with_session(command: List[str], env: Optional[Dict[str, str]] = None,
                     stdout_callback: Optional[Callable[[str], None]] = None,
                     stderr_callback: Optional[Callable[[str], None]] = None) -> tuple:
    """
    Run a command with session tracking.
    
    Args:
        command: Command to run as a list of strings
        env: Environment variables to use (defaults to os.environ)
        stdout_callback: Optional callback for each stdout line
        stderr_callback: Optional callback for each stderr line
    
    Returns:
        (session_id, exit_code)
    """
    session = SessionManager().create(command, env=env)
    
    if env is None:
        env = os.environ.copy()
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1
        )
        
        session.process_started()
        
        # Create threads to read stdout and stderr
        def read_stdout():
            for line in iter(process.stdout.readline, ''):
                line = line.rstrip('\n\r')
                session.log_stdout(line)
                if stdout_callback:
                    stdout_callback(line)
        
        def read_stderr():
            for line in iter(process.stderr.readline, ''):
                line = line.rstrip('\n\r')
                session.log_stderr(line)
                if stderr_callback:
                    stderr_callback(line)
        
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for process to complete
        exit_code = process.wait()
        
        # Wait for threads to finish reading
        stdout_thread.join(timeout=1.0)
        stderr_thread.join(timeout=1.0)
        
        session.finish(exit_code)
        
        return session.session_id, exit_code
    
    except Exception as e:
        session.finish(-1)
        raise


def replay_session(session_id: str, output_callback: Optional[Callable[[str, str, int], None]] = None):
    """
    Replay a session's events to the console.
    
    Args:
        session_id: The session to replay
        output_callback: Optional callback(event_type, line, ts_ms) for custom output handling
    """
    events = SessionManager.load_events(session_id)
    
    if not events:
        raise ValueError(f"No events found for session {session_id}")
    
    start_ts = None
    
    for event in events:
        event_type = event.get('type')
        ts_ms = event.get('ts_ms', 0)
        
        if start_ts is None:
            start_ts = ts_ms
        
        relative_ms = ts_ms - start_ts
        
        if event_type in ('stdout_line', 'stderr_line'):
            line = event.get('line', '')
            if output_callback:
                output_callback(event_type, line, relative_ms)
            else:
                # Default output: print with timestamp
                prefix = '[stdout]' if event_type == 'stdout_line' else '[stderr]'
                timestamp = f"[{relative_ms/1000:.3f}s]"
                print(f"{timestamp} {prefix} {line}")
        
        elif event_type == 'run_started':
            cmd = event.get('command', [])
            cwd = event.get('cwd', '')
            if output_callback:
                output_callback(event_type, f"Command: {' '.join(cmd)}", relative_ms)
            else:
                print(f"[{relative_ms/1000:.3f}s] [run_started] Command: {' '.join(cmd)}")
                print(f"[{relative_ms/1000:.3f}s] [run_started] CWD: {cwd}")
        
        elif event_type == 'process_started':
            if output_callback:
                output_callback(event_type, 'Process started', relative_ms)
            else:
                print(f"[{relative_ms/1000:.3f}s] [process_started]")
        
        elif event_type == 'process_exited':
            exit_code = event.get('exit_code', 'unknown')
            if output_callback:
                output_callback(event_type, f"Exit code: {exit_code}", relative_ms)
            else:
                print(f"[{relative_ms/1000:.3f}s] [process_exited] Exit code: {exit_code}")
        
        elif event_type == 'run_finished':
            duration = event.get('duration_ms', 0)
            if output_callback:
                output_callback(event_type, f"Duration: {duration}ms", relative_ms)
            else:
                print(f"[{relative_ms/1000:.3f}s] [run_finished] Duration: {duration}ms")