"""Vallignus Authority - Identity, tokens, and policy management

Sprint 2 P0 Features:
- Policy versioning (v0001, v0002, etc.)
- Token revocation (jti)
- Key rotation (kid)
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import shutil
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Set, Tuple, Dict, Any


# Storage paths
VALLIGNUS_DIR = Path.home() / ".vallignus"
AGENTS_DIR = VALLIGNUS_DIR / "agents"
POLICIES_DIR = VALLIGNUS_DIR / "policies"
KEYS_DIR = VALLIGNUS_DIR / "keys"
REVOKED_DIR = VALLIGNUS_DIR / "revoked"

# Legacy paths (for migration)
LEGACY_SECRET_KEY_FILE = VALLIGNUS_DIR / "secret.key"


@dataclass
class Agent:
    """Agent identity"""
    agent_id: str
    owner: str
    created_at: float
    description: str = ""


@dataclass
class Policy:
    """Permission policy"""
    policy_id: str
    version: int
    max_spend_usd: Optional[float]
    allowed_domains: Set[str]
    created_at: str  # ISO format
    updated_at: str  # ISO format
    description: str = ""


@dataclass
class TokenPayload:
    """Decoded token payload"""
    agent_id: str
    owner: str
    policy_id: str
    policy_version: int
    issued_at: float
    expires_at: float
    permissions_hash: str
    jti: str  # Token ID for revocation


class AuthError(Exception):
    """Authentication/authorization error"""
    pass


# =============================================================================
# BASE64 URL ENCODING
# =============================================================================

def _b64url_encode(data: bytes) -> str:
    """Base64url encode without padding"""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64url_decode(s: str) -> bytes:
    """Base64url decode with padding restoration"""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    return base64.urlsafe_b64decode(s)


def _sanitize_id(id_str: str) -> str:
    """Sanitize ID for filesystem use"""
    return "".join(c if c.isalnum() or c in '-_' else '_' for c in id_str)


def _iso_now() -> str:
    """Get current time in ISO format"""
    return datetime.utcnow().isoformat()


# =============================================================================
# KEY MANAGEMENT (kid rotation)
# =============================================================================

def _get_active_kid() -> str:
    """Get the active key ID"""
    active_file = KEYS_DIR / "active"
    if not active_file.exists():
        raise AuthError("No active key. Run 'vallignus auth init' first.")
    return active_file.read_text().strip()


def _get_key_by_kid(kid: str) -> bytes:
    """Load a specific key by its ID"""
    key_file = KEYS_DIR / f"{kid}.key"
    if not key_file.exists():
        raise AuthError(f"Unknown key ID: {kid}")
    return key_file.read_bytes()


def _get_active_key() -> Tuple[str, bytes]:
    """Get the active key ID and key bytes"""
    kid = _get_active_kid()
    return kid, _get_key_by_kid(kid)


def _get_next_kid() -> str:
    """Generate the next key ID (k0001, k0002, etc.)"""
    if not KEYS_DIR.exists():
        return "k0001"
    
    existing = [f.stem for f in KEYS_DIR.glob("k*.key")]
    if not existing:
        return "k0001"
    
    max_num = max(int(k[1:]) for k in existing)
    return f"k{max_num + 1:04d}"


def rotate_key() -> Tuple[bool, str]:
    """Create a new key and set it as active"""
    try:
        if not KEYS_DIR.exists():
            return False, "Keys directory not initialized. Run 'vallignus auth init' first."
        
        new_kid = _get_next_kid()
        key = secrets.token_bytes(32)
        
        key_file = KEYS_DIR / f"{new_kid}.key"
        key_file.write_bytes(key)
        key_file.chmod(0o600)
        
        active_file = KEYS_DIR / "active"
        active_file.write_text(new_kid)
        
        return True, f"Rotated to new key: {new_kid}"
    except Exception as e:
        return False, f"Failed to rotate key: {e}"


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_auth() -> Tuple[bool, str]:
    """
    Initialize Vallignus auth directories and keys.
    Handles migration from legacy single secret.key to keyring.
    """
    try:
        VALLIGNUS_DIR.mkdir(mode=0o700, exist_ok=True)
        AGENTS_DIR.mkdir(mode=0o700, exist_ok=True)
        POLICIES_DIR.mkdir(mode=0o700, exist_ok=True)
        KEYS_DIR.mkdir(mode=0o700, exist_ok=True)
        REVOKED_DIR.mkdir(mode=0o700, exist_ok=True)
        
        active_file = KEYS_DIR / "active"
        
        # Check for legacy secret.key and migrate
        if LEGACY_SECRET_KEY_FILE.exists() and not active_file.exists():
            # Migrate legacy key to keyring
            legacy_key = LEGACY_SECRET_KEY_FILE.read_bytes()
            first_key_file = KEYS_DIR / "k0001.key"
            first_key_file.write_bytes(legacy_key)
            first_key_file.chmod(0o600)
            active_file.write_text("k0001")
            # Keep legacy file for now (user can delete manually)
            return True, f"Migrated legacy key to keyring at {KEYS_DIR}"
        
        if not active_file.exists():
            # Generate first key
            key = secrets.token_bytes(32)
            first_key_file = KEYS_DIR / "k0001.key"
            first_key_file.write_bytes(key)
            first_key_file.chmod(0o600)
            active_file.write_text("k0001")
            return True, f"Initialized Vallignus auth at {VALLIGNUS_DIR}"
        else:
            return True, f"Vallignus auth already initialized at {VALLIGNUS_DIR}"
    except Exception as e:
        return False, f"Failed to initialize: {e}"


# =============================================================================
# AGENT MANAGEMENT
# =============================================================================

def _get_agent_path(agent_id: str) -> Path:
    """Get path to agent JSON file"""
    return AGENTS_DIR / f"{_sanitize_id(agent_id)}.json"


def create_agent(agent_id: str, owner: str, description: str = "") -> Tuple[bool, str]:
    """Create a new agent identity"""
    path = _get_agent_path(agent_id)
    
    if path.exists():
        return False, f"Agent '{agent_id}' already exists"
    
    agent_data = {
        "agent_id": agent_id,
        "owner": owner,
        "description": description,
        "created_at": time.time()
    }
    
    try:
        path.write_text(json.dumps(agent_data, indent=2))
        return True, f"Created agent '{agent_id}' (owner: {owner})"
    except Exception as e:
        return False, f"Failed to create agent: {e}"


def load_agent(agent_id: str) -> Agent:
    """Load an agent from storage"""
    path = _get_agent_path(agent_id)
    
    if not path.exists():
        raise AuthError(f"Agent '{agent_id}' not found")
    
    try:
        data = json.loads(path.read_text())
        return Agent(
            agent_id=data["agent_id"],
            owner=data["owner"],
            created_at=data["created_at"],
            description=data.get("description", "")
        )
    except Exception as e:
        raise AuthError(f"Failed to load agent: {e}")


def list_agents() -> list:
    """List all agents"""
    if not AGENTS_DIR.exists():
        return []
    
    agents = []
    for f in AGENTS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            agents.append(data)
        except:
            pass
    return agents


# =============================================================================
# POLICY MANAGEMENT (Versioned)
# =============================================================================

def _get_policy_dir(policy_id: str) -> Path:
    """Get directory for versioned policy storage"""
    return POLICIES_DIR / _sanitize_id(policy_id)


def _get_policy_version_path(policy_id: str, version: int) -> Path:
    """Get path to specific policy version file"""
    return _get_policy_dir(policy_id) / f"v{version:04d}.json"


def _get_policy_latest_path(policy_id: str) -> Path:
    """Get path to latest.json for a policy"""
    return _get_policy_dir(policy_id) / "latest.json"


def _get_legacy_policy_path(policy_id: str) -> Path:
    """Get legacy flat policy path (for migration)"""
    return POLICIES_DIR / f"{_sanitize_id(policy_id)}.json"


def _migrate_legacy_policy(policy_id: str) -> Optional[int]:
    """
    Migrate a legacy flat policy file to versioned storage.
    Returns the version number (1) if migrated, None if no legacy file.
    """
    legacy_path = _get_legacy_policy_path(policy_id)
    if not legacy_path.exists():
        return None
    
    # Read legacy data
    legacy_data = json.loads(legacy_path.read_text())
    
    # Create versioned directory
    policy_dir = _get_policy_dir(policy_id)
    policy_dir.mkdir(mode=0o700, exist_ok=True)
    
    # Convert to versioned format
    now = _iso_now()
    versioned_data = {
        "policy_id": legacy_data["policy_id"],
        "version": 1,
        "max_spend_usd": legacy_data.get("max_spend_usd"),
        "allowed_domains": legacy_data["allowed_domains"],
        "description": legacy_data.get("description", ""),
        "created_at": legacy_data.get("created_at", now),
        "updated_at": now
    }
    
    # Handle old created_at format (float timestamp)
    if isinstance(versioned_data["created_at"], (int, float)):
        versioned_data["created_at"] = datetime.utcfromtimestamp(versioned_data["created_at"]).isoformat()
    
    # Write v0001 and latest
    v1_path = _get_policy_version_path(policy_id, 1)
    latest_path = _get_policy_latest_path(policy_id)
    
    policy_json = json.dumps(versioned_data, indent=2)
    v1_path.write_text(policy_json)
    latest_path.write_text(policy_json)
    
    # Remove legacy file
    legacy_path.unlink()
    
    return 1


def _get_latest_version(policy_id: str) -> int:
    """Get the latest version number for a policy"""
    policy_dir = _get_policy_dir(policy_id)
    if not policy_dir.exists():
        return 0
    
    versions = [int(f.stem[1:]) for f in policy_dir.glob("v*.json")]
    return max(versions) if versions else 0


def create_policy(
    policy_id: str,
    max_spend_usd: Optional[float],
    allowed_domains: str,
    description: str = ""
) -> Tuple[bool, str]:
    """Create a new permission policy (v0001)"""
    policy_dir = _get_policy_dir(policy_id)
    legacy_path = _get_legacy_policy_path(policy_id)
    
    # Check if policy already exists (versioned or legacy)
    if policy_dir.exists() or legacy_path.exists():
        return False, f"Policy '{policy_id}' already exists"
    
    # Parse domains
    domains = [d.strip().lower() for d in allowed_domains.split(',') if d.strip()]
    if not domains:
        return False, "At least one domain must be specified"
    
    now = _iso_now()
    policy_data = {
        "policy_id": policy_id,
        "version": 1,
        "max_spend_usd": max_spend_usd,
        "allowed_domains": sorted(domains),
        "description": description,
        "created_at": now,
        "updated_at": now
    }
    
    try:
        policy_dir.mkdir(mode=0o700, parents=True)
        
        policy_json = json.dumps(policy_data, indent=2)
        _get_policy_version_path(policy_id, 1).write_text(policy_json)
        _get_policy_latest_path(policy_id).write_text(policy_json)
        
        return True, f"Created policy '{policy_id}' v1 (budget: ${max_spend_usd or 'unlimited'}, domains: {len(domains)})"
    except Exception as e:
        return False, f"Failed to create policy: {e}"


def update_policy(
    policy_id: str,
    max_spend_usd: Optional[float] = None,
    allowed_domains: Optional[str] = None,
    description: Optional[str] = None
) -> Tuple[bool, str]:
    """Update a policy, creating a new version"""
    # Check for legacy and migrate if needed
    _migrate_legacy_policy(policy_id)
    
    policy_dir = _get_policy_dir(policy_id)
    if not policy_dir.exists():
        return False, f"Policy '{policy_id}' not found"
    
    # Load current latest
    latest_path = _get_policy_latest_path(policy_id)
    if not latest_path.exists():
        return False, f"Policy '{policy_id}' has no versions"
    
    current = json.loads(latest_path.read_text())
    current_version = current["version"]
    new_version = current_version + 1
    
    # Build new version (inherit unchanged fields)
    now = _iso_now()
    new_data = {
        "policy_id": policy_id,
        "version": new_version,
        "max_spend_usd": max_spend_usd if max_spend_usd is not None else current.get("max_spend_usd"),
        "allowed_domains": current["allowed_domains"],
        "description": description if description is not None else current.get("description", ""),
        "created_at": current["created_at"],
        "updated_at": now
    }
    
    # Update domains if provided
    if allowed_domains is not None:
        domains = [d.strip().lower() for d in allowed_domains.split(',') if d.strip()]
        if not domains:
            return False, "At least one domain must be specified"
        new_data["allowed_domains"] = sorted(domains)
    
    try:
        policy_json = json.dumps(new_data, indent=2)
        _get_policy_version_path(policy_id, new_version).write_text(policy_json)
        _get_policy_latest_path(policy_id).write_text(policy_json)
        
        return True, f"Updated policy '{policy_id}' to v{new_version}"
    except Exception as e:
        return False, f"Failed to update policy: {e}"


def load_policy(policy_id: str, version: Optional[int] = None) -> Policy:
    """
    Load a policy from storage.
    If version is None, loads latest.
    """
    # Check for legacy and migrate if needed
    migrated = _migrate_legacy_policy(policy_id)
    
    policy_dir = _get_policy_dir(policy_id)
    if not policy_dir.exists():
        raise AuthError(f"Policy '{policy_id}' not found")
    
    if version is None:
        path = _get_policy_latest_path(policy_id)
    else:
        path = _get_policy_version_path(policy_id, version)
    
    if not path.exists():
        raise AuthError(f"Policy '{policy_id}' version {version} not found")
    
    try:
        data = json.loads(path.read_text())
        return Policy(
            policy_id=data["policy_id"],
            version=data["version"],
            max_spend_usd=data.get("max_spend_usd"),
            allowed_domains=set(data["allowed_domains"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            description=data.get("description", "")
        )
    except Exception as e:
        raise AuthError(f"Failed to load policy: {e}")


def _get_policy_version_hash(policy_id: str, version: int) -> str:
    """Get SHA256 hash of a specific policy version"""
    path = _get_policy_version_path(policy_id, version)
    if not path.exists():
        raise AuthError(f"Policy '{policy_id}' version {version} not found")
    
    data = json.loads(path.read_text())
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()


def list_policies() -> list:
    """List all policies (latest versions)"""
    if not POLICIES_DIR.exists():
        return []
    
    policies = []
    
    # Check for versioned policies (directories)
    for d in POLICIES_DIR.iterdir():
        if d.is_dir():
            latest_path = d / "latest.json"
            if latest_path.exists():
                try:
                    data = json.loads(latest_path.read_text())
                    policies.append(data)
                except:
                    pass
    
    # Check for legacy policies (files) - but don't migrate here, just list
    for f in POLICIES_DIR.glob("*.json"):
        if f.is_file():
            try:
                data = json.loads(f.read_text())
                # Add version field for display if missing
                if "version" not in data:
                    data["version"] = 1
                policies.append(data)
            except:
                pass
    
    return policies


# =============================================================================
# TOKEN REVOCATION (jti)
# =============================================================================

def revoke_token(jti: str) -> Tuple[bool, str]:
    """Revoke a token by its JTI"""
    if not REVOKED_DIR.exists():
        REVOKED_DIR.mkdir(mode=0o700, exist_ok=True)
    
    revoked_file = REVOKED_DIR / jti
    if revoked_file.exists():
        return False, f"Token {jti} is already revoked"
    
    try:
        revoked_file.touch()
        return True, f"Revoked token {jti}"
    except Exception as e:
        return False, f"Failed to revoke token: {e}"


def is_token_revoked(jti: str) -> bool:
    """Check if a token is revoked"""
    return (REVOKED_DIR / jti).exists()


# =============================================================================
# TOKEN MINTING AND VERIFICATION
# =============================================================================

def issue_token(agent_id: str, policy_id: str, ttl_seconds: int = 3600) -> str:
    """
    Issue a signed token for an agent with a specific policy.
    Returns the token string.
    """
    # Verify agent exists
    agent = load_agent(agent_id)
    
    # Load latest policy (and migrate if needed)
    policy = load_policy(policy_id)
    
    # Get active key
    kid, secret_key = _get_active_key()
    
    now = time.time()
    jti = str(uuid.uuid4())
    
    # Header (includes kid)
    header = {"alg": "HS256", "typ": "VALLIGNUS", "kid": kid}
    header_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode())
    
    # Payload (includes policy_version and jti)
    payload = {
        "agent_id": agent.agent_id,
        "owner": agent.owner,
        "policy_id": policy_id,
        "policy_version": policy.version,
        "issued_at": now,
        "expires_at": now + ttl_seconds,
        "permissions_hash": _get_policy_version_hash(policy_id, policy.version),
        "jti": jti
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode())
    
    # Signature
    message = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret_key, message, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_token_payload(token: str) -> Dict[str, Any]:
    """Decode token payload without verification (for inspection)"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise AuthError("Invalid token format")
        
        header_b64, payload_b64, _ = parts
        
        header = json.loads(_b64url_decode(header_b64).decode())
        payload = json.loads(_b64url_decode(payload_b64).decode())
        
        return {"header": header, "payload": payload}
    except Exception as e:
        raise AuthError(f"Failed to decode token: {e}")


def verify_token(token: str) -> TokenPayload:
    """
    Verify a token and return its payload.
    Raises AuthError if invalid.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise AuthError("Invalid token format")
        
        header_b64, payload_b64, signature_b64 = parts
        
        # Decode header to get kid
        header = json.loads(_b64url_decode(header_b64).decode())
        kid = header.get("kid")
        
        # Get the appropriate key
        if kid:
            try:
                secret_key = _get_key_by_kid(kid)
            except AuthError:
                raise AuthError(f"Unknown signing key: {kid}")
        else:
            # Legacy token without kid - try active key or legacy key
            try:
                _, secret_key = _get_active_key()
            except AuthError:
                if LEGACY_SECRET_KEY_FILE.exists():
                    secret_key = LEGACY_SECRET_KEY_FILE.read_bytes()
                else:
                    raise
        
        # Verify signature
        message = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(secret_key, message, hashlib.sha256).digest()
        actual_sig = _b64url_decode(signature_b64)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise AuthError("Invalid token signature")
        
        # Decode payload
        payload = json.loads(_b64url_decode(payload_b64).decode())
        
        # Check expiry
        if time.time() > payload["expires_at"]:
            raise AuthError("Token expired")
        
        # Check revocation
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            raise AuthError("TOKEN_REVOKED")
        
        # Handle legacy tokens without policy_version
        policy_version = payload.get("policy_version", 1)
        
        return TokenPayload(
            agent_id=payload["agent_id"],
            owner=payload["owner"],
            policy_id=payload["policy_id"],
            policy_version=policy_version,
            issued_at=payload["issued_at"],
            expires_at=payload["expires_at"],
            permissions_hash=payload["permissions_hash"],
            jti=jti or ""
        )
    
    except AuthError:
        raise
    except Exception as e:
        raise AuthError(f"Token verification failed: {e}")


def verify_token_with_policy(token: str) -> Tuple[TokenPayload, Policy]:
    """
    Verify token and load + validate the associated policy version.
    Returns (payload, policy) or raises AuthError.
    """
    payload = verify_token(token)
    
    # Load the specific policy version the token was issued for
    policy = load_policy(payload.policy_id, payload.policy_version)
    
    # Verify permissions_hash matches that version
    current_hash = _get_policy_version_hash(payload.policy_id, payload.policy_version)
    if current_hash != payload.permissions_hash:
        raise AuthError(
            f"Policy '{payload.policy_id}' v{payload.policy_version} integrity check failed. "
            "The policy file may have been tampered with."
        )
    
    return payload, policy