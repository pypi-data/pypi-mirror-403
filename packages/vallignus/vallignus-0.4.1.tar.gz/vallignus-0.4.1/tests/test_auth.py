"""Vallignus Authority - Sprint 2 P0 Tests"""

import json
import shutil
import time
import pytest
from pathlib import Path

@pytest.fixture(autouse=True)
def temp_vallignus_dir(tmp_path, monkeypatch):
    """Use a temporary directory for all tests"""
    test_dir = tmp_path / ".vallignus"
    monkeypatch.setattr('vallignus.auth.VALLIGNUS_DIR', test_dir)
    monkeypatch.setattr('vallignus.auth.AGENTS_DIR', test_dir / "agents")
    monkeypatch.setattr('vallignus.auth.POLICIES_DIR', test_dir / "policies")
    monkeypatch.setattr('vallignus.auth.KEYS_DIR', test_dir / "keys")
    monkeypatch.setattr('vallignus.auth.REVOKED_DIR', test_dir / "revoked")
    monkeypatch.setattr('vallignus.auth.LEGACY_SECRET_KEY_FILE', test_dir / "secret.key")
    yield test_dir

from vallignus import auth


class TestInit:
    def test_init_creates_dirs(self, temp_vallignus_dir):
        success, _ = auth.init_auth()
        assert success
        assert (temp_vallignus_dir / "keys" / "k0001.key").exists()


class TestPolicyVersioning:
    def test_create_policy_v1(self, temp_vallignus_dir):
        auth.init_auth()
        success, msg = auth.create_policy("test", 10.0, "api.openai.com")
        assert success
        assert "v1" in msg
    
    def test_update_creates_v2(self, temp_vallignus_dir):
        auth.init_auth()
        auth.create_policy("test", 10.0, "api.openai.com")
        success, msg = auth.update_policy("test", max_spend_usd=50.0)
        assert success
        assert "v2" in msg
    
    def test_v1_token_enforces_v1(self, temp_vallignus_dir):
        auth.init_auth()
        auth.create_agent("agent", "owner")
        auth.create_policy("test", 10.0, "api.openai.com")
        
        token_v1 = auth.issue_token("agent", "test")
        auth.update_policy("test", allowed_domains="api.openai.com,github.com")
        
        payload, policy = auth.verify_token_with_policy(token_v1)
        assert policy.version == 1
        assert "github.com" not in policy.allowed_domains


class TestTokenRevocation:
    def test_revoke_token(self, temp_vallignus_dir):
        auth.init_auth()
        auth.create_agent("agent", "owner")
        auth.create_policy("test", 10.0, "api.openai.com")
        
        token = auth.issue_token("agent", "test")
        decoded = auth.decode_token_payload(token)
        jti = decoded["payload"]["jti"]
        
        auth.revoke_token(jti)
        
        with pytest.raises(auth.AuthError) as exc:
            auth.verify_token(token)
        assert "TOKEN_REVOKED" in str(exc.value)


class TestKeyRotation:
    def test_old_token_valid_after_rotation(self, temp_vallignus_dir):
        auth.init_auth()
        auth.create_agent("agent", "owner")
        auth.create_policy("test", 10.0, "api.openai.com")
        
        token_old = auth.issue_token("agent", "test")
        auth.rotate_key()
        
        payload = auth.verify_token(token_old)
        assert payload.agent_id == "agent"


class TestExpiry:
    def test_expired_token_fails(self, temp_vallignus_dir):
        auth.init_auth()
        auth.create_agent("agent", "owner")
        auth.create_policy("test", 10.0, "api.openai.com")
        
        token = auth.issue_token("agent", "test", ttl_seconds=1)
        time.sleep(2)
        
        with pytest.raises(auth.AuthError) as exc:
            auth.verify_token(token)
        assert "expired" in str(exc.value).lower()