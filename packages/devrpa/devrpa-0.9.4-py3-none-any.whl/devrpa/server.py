
import asyncio
import time
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, WebSocket, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import json
import httpx # For webhooks

from .workflow import Workflow, RunReport
from .auth import Auth, AuthConfig
from .throttling import RateLimiter, check_rate_limit
from .telemetry import metrics_endpoint, REQUEST_COUNT, WORKFLOW_RUNS

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors: bool = True
    auth: Optional[AuthConfig] = None
    rate_limit_requests: int = 100 # per minute global

class RunRequest(BaseModel):
    context: Dict[str, Any] = {}
    sync: bool = False
    callback_url: Optional[str] = None

class RunResponse(BaseModel):
    run_id: str
    status: str
    result: Optional[Dict[str, Any]] = None

def create_app(workflow: Workflow, config: ServerConfig = ServerConfig()) -> FastAPI:
    app = FastAPI(title=f"devrpa: {workflow.name}", version="0.8.0")

    # Auth
    auth_handler = Auth(config.auth or AuthConfig())

    # Rate Limiter
    limiter = RateLimiter(config.rate_limit_requests, "minute")

    if config.cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    executions: Dict[str, dict] = {} 

    async def _send_webhook(url: str, payload: dict):
        try:
           async with httpx.AsyncClient() as client:
               await client.post(url, json=payload, timeout=10.0)
        except Exception as e:
            print(f"Webhook failed: {e}")

    async def _run_workflow(run_id: str, context: dict, callback_url: str = None):
        executions[run_id]["status"] = "running"
        success = False
        try:
            report: RunReport = await workflow.run(initial_data=context, resume_run_id=None)
            success = report.success
            executions[run_id]["status"] = "completed" if success else "failed"
            executions[run_id]["result"] = report.save_dict()
        except Exception as e:
            executions[run_id]["status"] = "failed"
            executions[run_id]["error"] = str(e)
        
        # Telemetry
        status_label = "success" if success else "failure"
        WORKFLOW_RUNS.labels(workflow=workflow.name, status=status_label).inc()

        # Webhook
        if callback_url:
            payload = {
                "run_id": run_id,
                "status": executions[run_id]["status"],
                "result": executions[run_id].get("result"),
                "error": executions[run_id].get("error")
            }
            await _send_webhook(callback_url, payload)

    @app.middleware("http")
    async def global_middleware(request: Request, call_next):
        start = time.time()
        
        # Metrics count
        # Note: Middleware runs before routing, so endpoint might be unknown if use request.url.path
        response = await call_next(request)
        
        duration = time.time() - start
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
        
        return response

    @app.get("/metrics")
    async def metrics():
        return metrics_endpoint()

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "devrpa-api"}

    @app.post("/run", response_model=RunResponse)
    async def run_workflow(
        req: RunRequest, 
        request: Request,
        background_tasks: BackgroundTasks
    ):
        # Auth Check
        await auth_handler.verify_request(request)
        
        # Rate Limit Check
        await check_rate_limit(request, limiter)

        run_id = str(uuid.uuid4())
        executions[run_id] = {
            "id": run_id,
            "status": "pending",
            "context": req.context
        }
        
        if req.sync:
            await _run_workflow(run_id, req.context, req.callback_url)
            data = executions[run_id]
            return RunResponse(
                run_id=run_id, 
                status=data["status"], 
                result=data.get("result")
            )
        else:
            background_tasks.add_task(_run_workflow, run_id, req.context, req.callback_url)
            return RunResponse(run_id=run_id, status="pending")

    @app.get("/status/{run_id}")
    async def get_status(run_id: str, request: Request):
        await auth_handler.verify_request(request)
        if run_id not in executions:
            raise HTTPException(status_code=404, detail="Run not found")
        return executions[run_id]

    @app.get("/runs")
    async def list_runs(request: Request):
        await auth_handler.verify_request(request)
        return list(executions.values())

    return app

def serve_workflow(workflow: Workflow, host: str = "0.0.0.0", port: int = 8000, config: ServerConfig = None):
    conf = config or ServerConfig(host=host, port=port)
    app = create_app(workflow, conf)
    uvicorn.run(app, host=host, port=port)
