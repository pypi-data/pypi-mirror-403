
from typing import Any, Dict, Optional
import httpx
from ..workflow import Step
from ..core import StepResult, ExecutionContext

class ApiStep(Step):
    def __init__(
        self, 
        name: str, 
        method: str, 
        url: str, 
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 2,
        retry_backoff_seconds: float = 2.0
    ):
        super().__init__(name=name, max_retries=max_retries, retry_backoff_seconds=retry_backoff_seconds)
        self.method = method
        self.url = url
        self.json = json
        self.headers = headers

    async def execute(self, context: ExecutionContext) -> StepResult:
        # Resolve variables
        final_url = context.resolve(self.url)
        final_headers = {k: context.resolve(v) for k, v in (self.headers or {}).items()}
        
        final_json = None
        if self.json:
            final_json = {}
            for k, v in self.json.items():
                if isinstance(v, str):
                    final_json[k] = context.resolve(v)
                else:
                    final_json[k] = v
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.request(
                    method=self.method.upper(),
                    url=final_url,
                    json=final_json,
                    headers=final_headers,
                    timeout=30.0,
                )
                resp.raise_for_status()
                
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    try:
                        resp_data = resp.json()
                    except ValueError:
                        resp_data = resp.text
                else:
                    resp_data = resp.text
                
                output_data = {
                    f"{self.name}_response": resp_data,
                    f"{self.name}_status": resp.status_code
                }
                return StepResult(name=self.name, success=True, data=output_data)
            
        except httpx.HTTPError as e:
             return StepResult(name=self.name, success=False, error=e)
