"""Identity manager for session persistence in testing automation"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from vallignus.identity.chrome import get_chrome_cookies


class IdentityManager:
    """
    Manages browser session persistence for testing automation.
    
    This class provides methods to save and restore browser sessions (cookies)
    for use in automated testing scenarios. Sessions are stored encrypted
    in the user's home directory.
    """
    
    def __init__(self, sessions_dir: Optional[Path] = None):
        """
        Initialize the IdentityManager.
        
        Args:
            sessions_dir: Optional custom path for session storage.
                         Defaults to ~/.vallignus/sessions/
        """
        if sessions_dir is None:
            home = Path.home()
            sessions_dir = home / ".vallignus" / "sessions"
        
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption key (derived from user's home directory)
        self._encryption_key = self._get_encryption_key()
    
    def _get_encryption_key(self) -> bytes:
        """
        Generate or retrieve encryption key for session storage.
        
        Uses a key derived from the user's home directory path for consistency.
        In production, you might want to use a user-provided password or keychain.
        """
        # Derive key from home directory (deterministic but user-specific)
        home_str = str(Path.home()).encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'vallignus_salt',  # In production, use a random salt per user
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(home_str))
        return key
    
    def _encrypt_data(self, data: Dict) -> bytes:
        """Encrypt session data before storage"""
        f = Fernet(self._encryption_key)
        json_data = json.dumps(data).encode('utf-8')
        return f.encrypt(json_data)
    
    def _decrypt_data(self, encrypted_data: bytes) -> Dict:
        """Decrypt session data after retrieval"""
        f = Fernet(self._encryption_key)
        decrypted = f.decrypt(encrypted_data)
        return json.loads(decrypted.decode('utf-8'))
    
    def snapshot(
        self,
        domain: str,
        browser: str = "chrome",
        profile: str = "Default"
    ) -> None:
        """
        Save current browser session for a domain.
        
        Extracts cookies from the specified browser profile and saves them
        encrypted for later use in testing automation.
        
        Args:
            domain: The domain to snapshot (e.g., "github.com")
            browser: Browser name (currently supports "chrome")
            profile: Browser profile name (default: "Default")
        
        Raises:
            ValueError: If browser is not supported
            FileNotFoundError: If browser profile not found
        """
        if browser.lower() != "chrome":
            raise ValueError(f"Unsupported browser: {browser}. Only 'chrome' is supported.")
        
        # Extract cookies from browser
        cookies = get_chrome_cookies(domain, profile)
        
        if not cookies:
            raise ValueError(f"No cookies found for domain: {domain}")
        
        # Prepare session data
        session_data = {
            "domain": domain,
            "browser": browser,
            "profile": profile,
            "cookies": cookies
        }
        
        # Encrypt and save
        encrypted = self._encrypt_data(session_data)
        session_file = self.sessions_dir / f"{domain}.json.enc"
        
        with open(session_file, 'wb') as f:
            f.write(encrypted)
    
    def restore(self, domain: str) -> Dict[str, str]:
        """
        Restore saved session cookies for a domain.
        
        Returns a dictionary of cookies ready for use with requests or playwright
        in testing automation scenarios.
        
        Args:
            domain: The domain to restore cookies for
        
        Returns:
            Dictionary of cookie name-value pairs
        
        Raises:
            FileNotFoundError: If no saved session exists for the domain
        """
        session_file = self.sessions_dir / f"{domain}.json.enc"
        
        if not session_file.exists():
            raise FileNotFoundError(f"No saved session found for domain: {domain}")
        
        # Read and decrypt
        with open(session_file, 'rb') as f:
            encrypted = f.read()
        
        session_data = self._decrypt_data(encrypted)
        return session_data.get("cookies", {})
    
    def list_sessions(self) -> List[str]:
        """
        List all saved session domains.
        
        Returns:
            List of domain names that have saved sessions
        """
        sessions = []
        for file in self.sessions_dir.glob("*.json.enc"):
            # Extract domain from filename (domain.json.enc)
            domain = file.stem.replace(".json", "")
            sessions.append(domain)
        return sorted(sessions)
    
    def delete(self, domain: str) -> None:
        """
        Delete a saved session.
        
        Args:
            domain: The domain to delete the session for
        
        Raises:
            FileNotFoundError: If no saved session exists for the domain
        """
        session_file = self.sessions_dir / f"{domain}.json.enc"
        
        if not session_file.exists():
            raise FileNotFoundError(f"No saved session found for domain: {domain}")
        
        session_file.unlink()
