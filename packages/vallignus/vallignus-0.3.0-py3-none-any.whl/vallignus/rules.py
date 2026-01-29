"""Domain allowlist, budget tracking, and request blocking logic"""

from typing import Set, Optional, Tuple
from urllib.parse import urlparse


class RulesEngine:
    """Manages domain allowlist, budget tracking, and request blocking"""
    
    def __init__(self, allowed_domains: Set[str], budget: float = None):
        self.allowed_domains = allowed_domains
        self.budget = budget
        self.total_spend = 0.0
        self.request_count = 0
    
    def is_allowed(self, url: str) -> bool:
        """Check if a URL's domain is in the allowlist"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # Check exact match or subdomain
            if domain in self.allowed_domains:
                return True
            
            # Check if it's a subdomain of an allowed domain
            for allowed in self.allowed_domains:
                if domain.endswith('.' + allowed):
                    return True
            
            return False
        except Exception:
            return False
    
    def estimate_request_cost(self, method: str, url: str, status: int = None) -> float:
        """Estimate the cost of an API request"""
        # Simple heuristic: count requests to api.openai.com
        # Rough estimate: $0.002 per request (very conservative)
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if 'api.openai.com' in domain or 'openai.azure.com' in domain:
                # Very rough estimate: $0.002 per request
                # In reality, cost depends on tokens, model, etc.
                return 0.002
            
            return 0.0
        except Exception:
            return 0.0
    
    def check_request(
        self,
        method: str,
        url: str,
        status: int = None
    ) -> Tuple[bool, bool, float]:
        """
        Check if a request should be allowed.
        Returns: (should_block, is_allowed, estimated_cost)
        """
        is_allowed_domain = self.is_allowed(url)
        estimated_cost = self.estimate_request_cost(method, url, status)
        
        # Block if domain not in allowlist
        should_block = not is_allowed_domain
        
        # Update spending if request is allowed and completed
        if is_allowed_domain and status and status < 500:
            self.total_spend += estimated_cost
            self.request_count += 1
        
        return should_block, is_allowed_domain, estimated_cost
    
    def is_budget_exceeded(self) -> bool:
        """Check if budget has been exceeded"""
        if self.budget is None:
            return False
        return self.total_spend >= self.budget
    
    def get_budget_status(self) -> Tuple[float, float, float]:
        """Get (spend, budget, remaining)"""
        remaining = None
        if self.budget is not None:
            remaining = max(0.0, self.budget - self.total_spend)
        return self.total_spend, self.budget, remaining
