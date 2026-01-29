"""Flight recorder - logs all requests to JSON"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class FlightLogger:
    """Logs all HTTP requests to a JSON file"""
    
    def __init__(
        self,
        log_file: str = "flight_log.json",
        agent_id: Optional[str] = None,
        owner: Optional[str] = None,
        policy_id: Optional[str] = None,
        policy_version: Optional[int] = None,
        jti: Optional[str] = None
    ):
        self.log_file = Path(log_file)
        self.entries = []
        self.agent_id = agent_id
        self.owner = owner
        self.policy_id = policy_id
        self.policy_version = policy_version
        self.jti = jti
        
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    self.entries = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.entries = []
    
    def log_request(
        self,
        method: str,
        url: str,
        status: int = None,
        blocked: bool = False,
        allowed: bool = True,
        estimated_cost: float = 0.0,
        deny_reason: Optional[str] = None,
        **kwargs
    ):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "url": url,
            "status": status,
            "blocked": blocked,
            "allowed": allowed,
            "estimated_cost": estimated_cost,
            "decision": "deny" if blocked else "allow",
        }
        
        if self.agent_id:
            entry["agent_id"] = self.agent_id
        if self.owner:
            entry["owner"] = self.owner
        if self.policy_id:
            entry["policy_id"] = self.policy_id
        if self.policy_version is not None:
            entry["policy_version"] = self.policy_version
        if self.jti:
            entry["jti"] = self.jti
        
        if blocked and deny_reason:
            entry["deny_reason"] = deny_reason
        elif blocked:
            entry["deny_reason"] = "domain_not_allowed"
        
        entry.update(kwargs)
        self.entries.append(entry)
        self._save()
    
    def _save(self):
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.entries, f, indent=2)
        except IOError:
            pass
    
    def get_total_cost(self) -> float:
        return sum(entry.get("estimated_cost", 0.0) for entry in self.entries)