
from typing import List, Optional, Union, Dict
from pydantic import BaseModel
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPBasic
import secrets

class AuthConfig(BaseModel):
    enabled: bool = False
    api_keys: List[str] = []
    jwt_secret: Optional[str] = None
    jwt_algo: str = "HS256"

class Auth:
    def __init__(self, config: AuthConfig):
        self.config = config
        self._api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

    @classmethod
    def api_key(cls, header: str = "X-API-Key", keys: List[str] = None) -> AuthConfig:
        return AuthConfig(enabled=True, api_keys=keys or [])

    async def verify_request(self, request: Request):
        if not self.config.enabled:
            return True

        # 1. API Key Check
        if self.config.api_keys:
            key = request.headers.get("X-API-Key")
            if key and key in self.config.api_keys:
                return True
        
        # 2. JWT (mock placeholder for now)
        if self.config.jwt_secret:
             # Add JWT logic here
             pass

        raise HTTPException(status_code=401, detail="Invalid credentials")
