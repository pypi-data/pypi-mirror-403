"""mitmproxy-based HTTP interceptor"""

import threading
import time
from typing import Optional, Set
from mitmproxy import http, options
from mitmproxy.tools.dump import DumpMaster

from vallignus.rules import RulesEngine
from vallignus.logger import FlightLogger


class VallignusProxy:
    """HTTP/HTTPS proxy that intercepts and filters requests"""
    
    def __init__(
        self,
        allowed_domains: Set[str],
        budget: Optional[float] = None,
        logger: Optional[FlightLogger] = None,
        rules: Optional[RulesEngine] = None
    ):
        self.allowed_domains = allowed_domains
        self.budget = budget
        self.logger = logger or FlightLogger()
        self.rules = rules or RulesEngine(allowed_domains, budget)
        self.master: Optional[DumpMaster] = None
        self.proxy_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.blocked_count = 0
        self.allowed_count = 0
        self._should_terminate = False
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Intercept outgoing HTTP requests"""
        url = flow.request.pretty_url
        method = flow.request.method
        
        # Check if domain is allowed (don't update spending here)
        is_allowed = self.rules.is_allowed(url)
        
        if not is_allowed:
            self.blocked_count += 1
            flow.response = http.Response.make(
                403,
                b"Blocked by Vallignus: Domain not in allowlist",
                {"Content-Type": "text/plain"}
            )
            # Log blocked request immediately
            self.logger.log_request(
                method=method,
                url=url,
                status=403,
                blocked=True,
                allowed=False,
                estimated_cost=0.0
            )
        else:
            self.allowed_count += 1
            # Don't log yet - wait for response to get final status and cost
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Intercept HTTP responses"""
        if flow.response:
            url = flow.request.pretty_url
            method = flow.request.method
            status = flow.response.status_code
            
            # Only process if request wasn't blocked (blocked requests don't reach here)
            is_allowed = self.rules.is_allowed(url)
            if is_allowed:
                # Check request and update spending (this adds to total_spend)
                should_block, is_allowed_domain, estimated_cost = self.rules.check_request(
                    method, url, status
                )
                
                # Log the allowed request with final status and cost
                self.logger.log_request(
                    method=method,
                    url=url,
                    status=status,
                    blocked=False,
                    allowed=True,
                    estimated_cost=estimated_cost
                )
                
                # Check budget after response
                if self.rules.is_budget_exceeded() and not self._should_terminate:
                    self._should_terminate = True
    
    def start(self, port: int = 8080) -> int:
        """Start the proxy server"""
        self.is_running = True
        self._port = port
        
        def run_proxy():
            import asyncio
            
            async def run_master():
                opts = options.Options(listen_port=port)
                self.master = DumpMaster(opts)
                self.master.addons.add(self)
                await self.master.run()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_master())
            except Exception:
                pass
        
        self.proxy_thread = threading.Thread(target=run_proxy, daemon=True)
        self.proxy_thread.start()
        
        time.sleep(1.0)
        return port
    
    def stop(self):
        """Stop the proxy server"""
        self.is_running = False
        if self.master:
            self.master.shutdown()
