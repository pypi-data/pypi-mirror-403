"""Vallignus Sessions - Sprint 0 Unit Tests"""

import json
import os
import re
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from vallignus import sessions


@pytest.fixture(autouse=True)
def temp_sessions_dir(tmp_path, monkeypatch):
    """Use a temporary directory for all tests"""
    test_dir = tmp_path / ".vallignus"
    sessions_dir = test_dir / "sessions"
    monkeypatch.setattr('vallignus.sessions.VALLIGNUS_DIR', test_dir)
    monkeypatch.setattr('vallignus.sessions.SESSIONS_DIR', sessions_dir)
    yield sessions_dir


class TestSessionIdGeneration:
    """Tests for session ID generation"""
    
    def test_session_id_format(self):
        """Session ID should follow YYYYMMDD-HHMMSS-<random6> format"""
        session_id = sessions.generate_session_id()
        
        # Pattern: YYYYMMDD-HHMMSS-xxxxxx
        pattern = r'^\d{8}-\d{6}-[a-z0-9]{6}$'
        assert re.match(pattern, session_id), f"Session ID '{session_id}' does not match expected format"
    
    def test_session_id_uniqueness(self):
        """Each generated session ID should be unique"""
        ids = [sessions.generate_session_id() for _ in range(100)]
        assert len(ids) == len(set(ids)), "Generated session IDs are not unique"
    
    def test_session_id_timestamp_valid(self):
        """Session ID timestamp portion should be valid"""
        session_id = sessions.generate_session_id()
        date_part, time_part, _ = session_id.split('-', 2)
        
        # Validate date (basic check)
        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])
        
        assert 2020 <= year <= 2100
        assert 1 <= month <= 12
        assert 1 <= day <= 31
        
        # Validate time
        hour = int(time_part[:2])
        minute = int(time_part[2:4])
        second = int(time_part[4:6])
        
        assert 0 <= hour <= 23
        assert 0 <= minute <= 59
        assert 0 <= second <= 59


class TestSessionDirectory:
    """Tests for session directory creation"""
    
    def test_creates_session_directory(self, temp_sessions_dir):
        """Creating a session should create the session directory"""
        manager = sessions.SessionManager()
        manager.create(['echo', 'hello'])
        
        assert manager.session_dir.exists()
        assert manager.session_dir.is_dir()
    
    def test_creates_session_json(self, temp_sessions_dir):
        """Creating a session should create session.json"""
        manager = sessions.SessionManager()
        manager.create(['echo', 'hello'])
        
        session_json = manager.session_dir / "session.json"
        assert session_json.exists()
        
        # Verify it's valid JSON
        data = json.loads(session_json.read_text())
        assert data['session_id'] == manager.session_id
        assert data['command'] == ['echo', 'hello']
    
    def test_creates_events_jsonl(self, temp_sessions_dir):
        """Creating a session should create events.jsonl"""
        manager = sessions.SessionManager()
        manager.create(['echo', 'hello'])
        
        events_file = manager.session_dir / "events.jsonl"
        assert events_file.exists()
    
    def test_creates_stdout_log(self, temp_sessions_dir):
        """Creating a session should create stdout.log"""
        manager = sessions.SessionManager()
        manager.create(['echo', 'hello'])
        
        stdout_log = manager.session_dir / "stdout.log"
        assert stdout_log.exists()
    
    def test_creates_stderr_log(self, temp_sessions_dir):
        """Creating a session should create stderr.log"""
        manager = sessions.SessionManager()
        manager.create(['echo', 'hello'])
        
        stderr_log = manager.session_dir / "stderr.log"
        assert stderr_log.exists()
    
    def test_session_dir_path_correct(self, temp_sessions_dir):
        """Session directory should be in the correct location"""
        manager = sessions.SessionManager()
        manager.create(['test', 'command'])
        
        expected_path = temp_sessions_dir / manager.session_id
        assert manager.session_dir == expected_path


class TestEventsJsonl:
    """Tests for events.jsonl format and appending"""
    
    def test_run_started_event(self, temp_sessions_dir):
        """run_started event should be logged on session creation"""
        manager = sessions.SessionManager()
        manager.create(['python', 'test.py'])
        
        events = sessions.SessionManager.load_events(manager.session_id)
        
        assert len(events) >= 1
        first_event = events[0]
        assert first_event['type'] == 'run_started'
        assert first_event['session_id'] == manager.session_id
        assert 'ts_ms' in first_event
        assert first_event['command'] == ['python', 'test.py']
    
    def test_stdout_event_appended(self, temp_sessions_dir):
        """stdout_line events should be appended correctly"""
        manager = sessions.SessionManager()
        manager.create(['echo', 'test'])
        
        manager.log_stdout("Hello World")
        manager.log_stdout("Second line")
        
        events = sessions.SessionManager.load_events(manager.session_id)
        
        stdout_events = [e for e in events if e['type'] == 'stdout_line']
        assert len(stdout_events) == 2
        assert stdout_events[0]['line'] == "Hello World"
        assert stdout_events[1]['line'] == "Second line"
    
    def test_stderr_event_appended(self, temp_sessions_dir):
        """stderr_line events should be appended correctly"""
        manager = sessions.SessionManager()
        manager.create(['echo', 'test'])
        
        manager.log_stderr("Error message")
        
        events = sessions.SessionManager.load_events(manager.session_id)
        
        stderr_events = [e for e in events if e['type'] == 'stderr_line']
        assert len(stderr_events) == 1
        assert stderr_events[0]['line'] == "Error message"
    
    def test_event_has_required_fields(self, temp_sessions_dir):
        """Every event should have ts_ms, session_id, and type"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.log_stdout("test line")
        manager.process_started()
        manager.finish(0)
        
        events = sessions.SessionManager.load_events(manager.session_id)
        
        for event in events:
            assert 'ts_ms' in event, f"Event missing ts_ms: {event}"
            assert 'session_id' in event, f"Event missing session_id: {event}"
            assert 'type' in event, f"Event missing type: {event}"
            assert isinstance(event['ts_ms'], int)
    
    def test_events_chronologically_ordered(self, temp_sessions_dir):
        """Events should have increasing timestamps"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        
        time.sleep(0.01)  # Small delay to ensure different timestamps
        manager.log_stdout("line 1")
        time.sleep(0.01)
        manager.log_stdout("line 2")
        time.sleep(0.01)
        manager.finish(0)
        
        events = sessions.SessionManager.load_events(manager.session_id)
        timestamps = [e['ts_ms'] for e in events]
        
        assert timestamps == sorted(timestamps), "Events are not chronologically ordered"
    
    def test_jsonl_format_one_json_per_line(self, temp_sessions_dir):
        """events.jsonl should have exactly one JSON object per line"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.log_stdout("line 1")
        manager.log_stdout("line 2")
        manager.finish(0)
        
        events_file = manager.session_dir / "events.jsonl"
        content = events_file.read_text()
        lines = content.strip().split('\n')
        
        for i, line in enumerate(lines):
            try:
                obj = json.loads(line)
                assert isinstance(obj, dict), f"Line {i+1} is not a JSON object"
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {i+1} is not valid JSON: {line[:50]}... Error: {e}")
    
    def test_finish_logs_process_exited_and_run_finished(self, temp_sessions_dir):
        """finish() should log process_exited and run_finished events"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.finish(42)
        
        events = sessions.SessionManager.load_events(manager.session_id)
        event_types = [e['type'] for e in events]
        
        assert 'process_exited' in event_types
        assert 'run_finished' in event_types
        
        exit_event = next(e for e in events if e['type'] == 'process_exited')
        assert exit_event['exit_code'] == 42


class TestSessionsListOrdering:
    """Tests for sessions list ordering"""
    
    def test_list_returns_most_recent_first(self, temp_sessions_dir):
        """Sessions should be listed with most recent first"""
        # Create sessions with small delays to ensure different timestamps
        session_ids = []
        for i in range(3):
            manager = sessions.SessionManager()
            manager.create([f'command_{i}'])
            session_ids.append(manager.session_id)
            manager.finish(0)
            time.sleep(0.01)  # Small delay
        
        # Get list
        listed = sessions.SessionManager.list_sessions()
        listed_ids = [s.session_id for s in listed]
        
        # Most recent (last created) should be first
        assert listed_ids[0] == session_ids[-1]
        assert listed_ids[-1] == session_ids[0]
    
    def test_list_respects_limit(self, temp_sessions_dir):
        """list_sessions should respect the limit parameter"""
        # Create 5 sessions
        for i in range(5):
            manager = sessions.SessionManager()
            manager.create([f'command_{i}'])
            manager.finish(0)
        
        # Request only 3
        listed = sessions.SessionManager.list_sessions(limit=3)
        assert len(listed) == 3
    
    def test_list_returns_empty_when_no_sessions(self, temp_sessions_dir):
        """list_sessions should return empty list when no sessions exist"""
        listed = sessions.SessionManager.list_sessions()
        assert listed == []
    
    def test_list_returns_all_when_fewer_than_limit(self, temp_sessions_dir):
        """list_sessions should return all sessions when fewer than limit"""
        # Create 2 sessions
        for i in range(2):
            manager = sessions.SessionManager()
            manager.create([f'command_{i}'])
            manager.finish(0)
        
        # Request 20 (default limit)
        listed = sessions.SessionManager.list_sessions(limit=20)
        assert len(listed) == 2


class TestSessionMetadata:
    """Tests for session metadata (session.json)"""
    
    def test_metadata_contains_required_fields(self, temp_sessions_dir):
        """session.json should contain all required fields"""
        manager = sessions.SessionManager()
        manager.create(['python', 'test.py'], cwd='/test/dir')
        manager.log_stdout("line 1")
        manager.log_stderr("error 1")
        manager.finish(0)
        
        metadata = sessions.SessionManager.load(manager.session_id)
        
        assert metadata.session_id == manager.session_id
        assert metadata.command == ['python', 'test.py']
        assert metadata.cwd == '/test/dir'
        assert metadata.exit_code == 0
        assert metadata.duration_ms is not None
        assert metadata.stdout_lines == 1
        assert metadata.stderr_lines == 1
        assert metadata.started_at_iso is not None
        assert metadata.finished_at_iso is not None
    
    def test_env_summary_excludes_sensitive_keys(self, temp_sessions_dir):
        """env_summary should not include sensitive environment variables"""
        # Set up mock environment with sensitive data
        mock_env = {
            'PATH': '/usr/bin',
            'HOME': '/home/test',
            'AWS_SECRET_ACCESS_KEY': 'secret123',
            'DATABASE_PASSWORD': 'password123',
            'VALLIGNUS_TOKEN': 'token123',
            'API_KEY': 'key123',
        }
        
        summary = sessions.get_safe_env_summary(mock_env)
        
        assert 'PATH' in summary
        assert 'HOME' in summary
        assert 'AWS_SECRET_ACCESS_KEY' not in summary
        assert 'DATABASE_PASSWORD' not in summary
        assert 'VALLIGNUS_TOKEN' not in summary
        assert 'API_KEY' not in summary


class TestEventLogger:
    """Tests for the EventLogger class"""
    
    def test_event_logger_thread_safe(self, temp_sessions_dir):
        """EventLogger should handle concurrent writes safely"""
        import threading
        
        manager = sessions.SessionManager()
        manager.create(['test'])
        
        errors = []
        
        def log_many(prefix, count):
            try:
                for i in range(count):
                    manager.log_stdout(f"{prefix}_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=log_many, args=('thread1', 50)),
            threading.Thread(target=log_many, args=('thread2', 50)),
            threading.Thread(target=log_many, args=('thread3', 50)),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        
        events = sessions.SessionManager.load_events(manager.session_id)
        stdout_events = [e for e in events if e['type'] == 'stdout_line']
        
        # Should have all 150 events (50 * 3)
        assert len(stdout_events) == 150


class TestReplaySession:
    """Tests for session replay functionality"""
    
    def test_replay_returns_all_events(self, temp_sessions_dir):
        """replay_session should process all events"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.log_stdout("line 1")
        manager.log_stdout("line 2")
        manager.log_stderr("error 1")
        manager.finish(0)
        
        captured_events = []
        
        def callback(event_type, line, ts_ms):
            captured_events.append((event_type, line))
        
        sessions.replay_session(manager.session_id, output_callback=callback)
        
        # Should have: run_started, stdout, stdout, stderr, process_exited, run_finished
        assert len(captured_events) == 6
    
    def test_replay_raises_for_invalid_session(self, temp_sessions_dir):
        """replay_session should raise for non-existent session"""
        with pytest.raises(ValueError):
            sessions.replay_session("nonexistent-session-id")


# =============================================================================
# SPRINT 1 TESTS
# =============================================================================

class TestTermination:
    """Tests for session termination tracking (Sprint 1)"""
    
    def test_terminate_records_reason(self, temp_sessions_dir):
        """terminate() should record termination reason in session"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.terminate("max_runtime", 60, 65)
        manager.finish(-15)
        
        metadata = sessions.SessionManager.load(manager.session_id)
        assert metadata.termination_reason == "max_runtime"
        assert metadata.termination_limit_value == 60
        assert metadata.termination_observed_value == 65
    
    def test_terminate_creates_event(self, temp_sessions_dir):
        """terminate() should create run_terminated event"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.terminate("max_output_lines", 100, 105)
        manager.finish(-15)
        
        events = sessions.SessionManager.load_events(manager.session_id)
        terminated_events = [e for e in events if e['type'] == 'run_terminated']
        
        assert len(terminated_events) == 1
        event = terminated_events[0]
        assert event['reason'] == "max_output_lines"
        assert event['limit_value'] == 100
        assert event['observed_value'] == 105
    
    def test_terminate_event_has_required_fields(self, temp_sessions_dir):
        """run_terminated event should have ts_ms, session_id, type"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.terminate("max_requests", 50, 51)
        manager.finish(-15)
        
        events = sessions.SessionManager.load_events(manager.session_id)
        terminated_event = next(e for e in events if e['type'] == 'run_terminated')
        
        assert 'ts_ms' in terminated_event
        assert terminated_event['session_id'] == manager.session_id
        assert terminated_event['type'] == 'run_terminated'
    
    def test_session_without_termination_has_no_termination_fields(self, temp_sessions_dir):
        """Normal session should not have termination fields in JSON"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.finish(0)
        
        # Read raw JSON to check fields are not present
        session_json = manager.session_dir / "session.json"
        data = json.loads(session_json.read_text())
        
        assert 'termination_reason' not in data
        assert 'termination_limit_value' not in data
        assert 'termination_observed_value' not in data


class TestMaxOutputLines:
    """Tests for max output lines termination"""
    
    def test_log_stdout_returns_total_count(self, temp_sessions_dir):
        """log_stdout should return total output line count"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        
        count1 = manager.log_stdout("line 1")
        count2 = manager.log_stdout("line 2")
        count3 = manager.log_stderr("error 1")
        
        assert count1 == 1
        assert count2 == 2
        assert count3 == 3  # stdout + stderr combined
    
    def test_total_output_lines_property(self, temp_sessions_dir):
        """total_output_lines should return combined count"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        
        manager.log_stdout("line 1")
        manager.log_stdout("line 2")
        manager.log_stderr("error 1")
        
        assert manager.total_output_lines == 3


class TestElapsedTime:
    """Tests for elapsed time tracking"""
    
    def test_elapsed_seconds_before_create(self, temp_sessions_dir):
        """elapsed_seconds should return 0 before session starts"""
        manager = sessions.SessionManager()
        assert manager.elapsed_seconds == 0.0
    
    def test_elapsed_seconds_after_create(self, temp_sessions_dir):
        """elapsed_seconds should return positive value after session starts"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        
        time.sleep(0.1)
        
        assert manager.elapsed_seconds >= 0.1
        assert manager.elapsed_seconds < 1.0  # Sanity check


class TestRequestCounters:
    """Tests for request counting (Sprint 1 P1)"""
    
    def test_set_request_counts(self, temp_sessions_dir):
        """set_request_counts should store counts"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.set_request_counts(10, 3)
        manager.finish(0)
        
        metadata = sessions.SessionManager.load(manager.session_id)
        assert metadata.allowed_requests == 10
        assert metadata.denied_requests == 3
        assert metadata.total_requests == 13
    
    def test_request_counts_not_present_when_zero(self, temp_sessions_dir):
        """Request counts should not be in JSON when not set"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.finish(0)
        
        # Read raw JSON
        session_json = manager.session_dir / "session.json"
        data = json.loads(session_json.read_text())
        
        assert 'allowed_requests' not in data
        assert 'denied_requests' not in data
        assert 'total_requests' not in data
    
    def test_request_counts_present_when_set(self, temp_sessions_dir):
        """Request counts should be in JSON when set"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.set_request_counts(5, 2)
        manager.finish(0)
        
        # Read raw JSON
        session_json = manager.session_dir / "session.json"
        data = json.loads(session_json.read_text())
        
        assert data['allowed_requests'] == 5
        assert data['denied_requests'] == 2
        assert data['total_requests'] == 7


class TestTerminationReasons:
    """Tests for different termination reasons"""
    
    def test_max_runtime_termination(self, temp_sessions_dir):
        """max_runtime termination should be recorded correctly"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.terminate("max_runtime", 30, 35)
        manager.finish(-15)
        
        metadata = sessions.SessionManager.load(manager.session_id)
        assert metadata.termination_reason == "max_runtime"
    
    def test_max_output_lines_termination(self, temp_sessions_dir):
        """max_output_lines termination should be recorded correctly"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.terminate("max_output_lines", 1000, 1001)
        manager.finish(-15)
        
        metadata = sessions.SessionManager.load(manager.session_id)
        assert metadata.termination_reason == "max_output_lines"
    
    def test_max_requests_termination(self, temp_sessions_dir):
        """max_requests termination should be recorded correctly"""
        manager = sessions.SessionManager()
        manager.create(['test'])
        manager.terminate("max_requests", 100, 100)
        manager.finish(-15)
        
        metadata = sessions.SessionManager.load(manager.session_id)
        assert metadata.termination_reason == "max_requests"


class TestBackwardsCompatibility:
    """Tests for loading sessions created before Sprint 1"""
    
    def test_load_session_without_new_fields(self, temp_sessions_dir):
        """Should load sessions that don't have Sprint 1 fields"""
        # Create a session with only Sprint 0 fields
        session_id = sessions.generate_session_id()
        session_dir = sessions.get_session_dir(session_id)
        session_dir.mkdir(parents=True)
        
        # Write minimal session.json (Sprint 0 style)
        old_style_data = {
            "session_id": session_id,
            "started_at_iso": "2026-01-24T12:00:00",
            "command": ["test"],
            "cwd": "/tmp",
            "env_summary": {},
            "exit_code": 0,
            "duration_ms": 100,
            "stdout_lines": 5,
            "stderr_lines": 0
        }
        
        with open(session_dir / "session.json", 'w') as f:
            json.dump(old_style_data, f)
        
        # Should load without error
        metadata = sessions.SessionManager.load(session_id)
        
        assert metadata is not None
        assert metadata.session_id == session_id
        assert metadata.termination_reason is None
        assert metadata.allowed_requests is None