
import time
from fastapi import Request, HTTPException
from typing import Dict, Tuple

class RateLimiter:
    def __init__(self, requests: int, per: str = "minute"):
        self.limit = requests
        self.per = per
        self.window = 60 if per == "minute" else 3600
        self._tokens: Dict[str, Tuple[float, int]] = {} # Client -> (last_refill, tokens)

    def check(self, identifier: str) -> bool:
        now = time.time()
        last_refill, tokens = self._tokens.get(identifier, (now, self.limit))
        
        # Refill logic
        elapsed = now - last_refill
        refill = elapsed * (self.limit / self.window)
        tokens = min(self.limit, tokens + refill)
        
        if tokens >= 1.0:
            self._tokens[identifier] = (now, tokens - 1.0)
            return True
        else:
            self._tokens[identifier] = (last_refill, tokens) # No change
            return False

async def check_rate_limit(request: Request, limiter: RateLimiter):
    # Identify by IP for now
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.check(client_ip):
         raise HTTPException(
             status_code=429, 
             detail="Rate limit exceeded",
             headers={"Retry-After": str(limiter.window)}
         )
