
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from .server import ServerConfig
import time
import os
import json
import asyncio
import uuid
from .logging import get_logger
from .state import StateManager, FileStateBackend
from .core import ExecutionContext, StepResult

@dataclass
class StepResult:
    name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None
    duration: float = 0.0
    started_at: float = 0.0
    finished_at: float = 0.0
    retries: int = 0
    from_cache: bool = False # Track if result came from cache

    def to_dict(self):
        return {
            "name": self.name,
            "success": self.success,
            "data": str(self.data) if self.data else None,
            "error": str(self.error) if self.error else None,
            "duration": self.duration,
            "retries": self.retries,
            "from_cache": self.from_cache
        }

@dataclass
class RunReport:
    workflow_name: str
    success: bool
    step_results: List[StepResult]
    started_at: float
    finished_at: float
    run_id: str
    
    @property
    def duration(self) -> float:
        return self.finished_at - self.started_at

    def to_dict(self):
        return {
            "workflow": self.workflow_name,
            "run_id": self.run_id,
            "success": self.success,
            "duration": self.duration,
            "steps": [s.to_dict() for s in self.step_results]
        }
        
    def save_dict(self):
        return self.to_dict()

    def save_json(self, path: Path):
        data = self.to_dict()
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

from .policy import RetryPolicy, CircuitBreaker

class Step(ABC):
    """Abstract base class for all steps."""
    
    def __init__(
        self, 
        name: str, 
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        timeout_seconds: Optional[float] = None,
        # Legacy/Simple fields fallback
        max_retries: int = 1, 
        retry_backoff_seconds: float = 1.0, 
    ):
        self.name = name
        self.circuit_breaker = circuit_breaker
        self.timeout_seconds = timeout_seconds
        
        # Guard against positional mismatch from legacy calls
        if isinstance(retry_policy, int):
             # Detected legacy call: super().__init__(name, max_retries, ...)
             # Shift args map
             max_retries = retry_policy
             retry_policy = None
             if isinstance(circuit_breaker, float):
                 retry_backoff_seconds = circuit_breaker
                 circuit_breaker = None
             if isinstance(timeout_seconds, (int, float)):
                 pass # timeout_seconds matches
        
        if retry_policy:
            self.retry_policy = retry_policy
        else:
            # Backwards compatibility / Default simple policy
            from .policy import RetryPolicy, BackoffStrategy
            self.retry_policy = RetryPolicy(
                max_attempts=max_retries + 1, # Attempts = retries + 1
                backoff_strategy=BackoffStrategy.FIXED,
                initial_delay=retry_backoff_seconds
            )
             
        self.cache_config: Optional[dict] = None

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> StepResult:
        pass

    async def run(self, context: ExecutionContext) -> StepResult:
        return await self.execute(context)

class Workflow:
    def __init__(self, name: str, cache_backend: Any = None):
        self.name = name
        self.steps: List[Step] = []
        self._state_manager = StateManager(FileStateBackend())
        self.cache_backend = cache_backend
        
        # Default cache if not provided?
        # Maybe allow user to set later.
        # But if we want automatic default:
        # from .cache import get_cache_backend
        # if not self.cache_backend: self.cache_backend = get_cache_backend("file")
        # Let's keep it explicit for now.

    def add(self, step: Step) -> "Workflow":
        self.steps.append(step)
        return self

    async def run(
        self, 
        initial_data: Optional[Dict[str, Any]] = None, 
        env_file: Optional[str] = None,
        config_file: Optional[str] = None,
        artifacts_dir: Optional[str] = None,
        resume_run_id: Optional[str] = None
    ) -> RunReport:
        logger = get_logger()
        started_at = time.time()
        
        # Init State Manager
        state_backend = FileStateBackend() # could be config
        state_mgr = StateManager(state_backend)
        
        # Load state if resuming
        run_id = str(uuid.uuid4())
        completed_steps = set()
        context_data = initial_data or {}
        
        if resume_run_id:
            if resume_run_id == "last":
                resume_run_id = state_mgr.get_latest_run(self.name)
            
            if resume_run_id:
                logger.info(f"Resuming from run_id: {resume_run_id}")
                ckpt = state_mgr.load_checkpoint(self.name, resume_run_id)
                if ckpt:
                    run_id = resume_run_id # Continue same ID
                    completed_steps = set(ckpt.get("completed_steps", []))
                    context_data.update(ckpt.get("context_data", {}))
                else:
                    logger.warning(f"Checkpoint not found for {resume_run_id}, starting fresh.")
            else:
                logger.warning("No previous run found to resume.")

        # Initialize Context logic
        env_vars = dict(os.environ)
        if env_file and os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        k, v = line.strip().split('=', 1)
                        env_vars[k] = v
        
        config = {}
        if config_file and os.path.exists(config_file):
            if config_file.endswith(('.yml', '.yaml')):
                try:
                    import yaml
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                except ImportError:
                    logger.warning("PyYAML not installed. Cannot load .yaml config.")
            elif config_file.endswith('.json'):
                with open(config_file, 'r') as f:
                    config = json.load(f)

        a_dir = Path(artifacts_dir) if artifacts_dir else Path("artifacts")
        a_dir.mkdir(parents=True, exist_ok=True)

        context = ExecutionContext(
            data=context_data,
            env=env_vars,
            config=config,
            artifacts_dir=a_dir
        )

        from .resources import ResourcePool
        
        # Determine resource needs (hardcoded pool size for now or from config)
        pool_size = context.config.get("resources", {}).get("browsers", 2)
        resources = ResourcePool(browser_count=pool_size)
        await resources.initialize()
        context.resources = resources

        results: List[StepResult] = []
        is_success = True

        logger.info(f"Starting workflow: {self.name} (ID: {run_id})")
        
        try: # Try/Finally block for resource cleanup
 
            for step in self.steps:
                if step.name in completed_steps:
                    logger.info(f"Skipping completed step '{step.name}'")
                    continue

                # Circuit Breaker Check
                if step.circuit_breaker and not step.circuit_breaker.allow_request():
                    logger.error(f"Step '{step.name}' blocked by Circuit Breaker (State: {step.circuit_breaker.state})")
                    is_success = False
                    break # Stop workflow? Or skip? Usually stop if critical.

                # Caching Logic
                cached_data = None
                cache_key = ""
                
                if step.cache_config and self.cache_backend:
                    key_parts = [self.name, step.name]
                    if step.cache_config.get("key_by"):
                        for k in step.cache_config["key_by"]:
                            # Resolve context value
                            val = context.get(k) if hasattr(context, "get") else context.data.get(k)
                            key_parts.append(str(val))
                    
                    cache_key = "_".join(key_parts)
                    cached_data = self.cache_backend.get(cache_key)
                
                if cached_data:
                    logger.info(f"Step '{step.name}' CACHE HIT")
                    # Update context
                    if hasattr(context.data, "__dict__") or (hasattr(context.data, "model_dump") and not isinstance(context.data, dict)):
                        for k, v in cached_data.items():
                            if hasattr(context.data, k):
                                setattr(context.data, k, v)
                    else:
                        context.data.update(cached_data)
                    
                    results.append(StepResult(
                        name=step.name, 
                        success=True, 
                        data=cached_data, 
                        from_cache=True
                    ))
                    continue

                # Execution Logic
                attempts = 0
                result: Optional[StepResult] = None
                while True:
                    attempts += 1
                    logger.info(f"Step '{step.name}' [Attempt {attempts}]")
                    start_time = time.time()
                    
                    try:
                        if step.timeout_seconds:
                            res = await asyncio.wait_for(step.execute(context), timeout=step.timeout_seconds)
                        else:
                            res = await step.execute(context)
                        
                        res.duration = time.time() - start_time
                        res.retries = attempts - 1
                        
                        if res.success:
                            # Cache Save logic
                            if step.cache_config and self.cache_backend and res.data:
                                try:
                                    self.cache_backend.set(cache_key, res.data, ttl=step.cache_config.get("ttl", 3600))
                                except Exception as e:
                                    logger.error(f"Cache Save Failed: {e}")
                            
                            logger.info(f"Step '{step.name}' SUCCESS")
                            
                            if step.circuit_breaker:
                                step.circuit_breaker.record_success()
                            break
                        else:
                            raise RuntimeError(f"Step returned failure: {res.error}")

                    except Exception as e:
                        # TimeoutError is an Exception, so caught here
                        is_timeout = isinstance(e, asyncio.TimeoutError)
                        error_msg = "Timed Out" if is_timeout else str(e)
                        
                        logger.error(f"Step '{step.name}' FAILED: {error_msg}")
                        
                        if step.circuit_breaker:
                            step.circuit_breaker.record_failure()
                        
                        result = StepResult(name=step.name, success=False, error=e, started_at=start_time, finished_at=time.time())
                        
                        # Check Retry Policy
                        if step.retry_policy.should_retry(attempts, e):
                            delay = step.retry_policy.get_delay(attempts)
                            logger.info(f"Retrying '{step.name}' in {delay:.2f}s...")
                            await asyncio.sleep(delay)
                        else:
                            break
                
                if result:
                    results.append(result)
                    if not result.success:
                        logger.error(f"Workflow stopping due to failure in step '{step.name}'")
                        is_success = False
                        break
                    else:
                        completed_steps.add(step.name)
                        state_mgr.save_checkpoint(
                            self.name, 
                            run_id, 
                            list(completed_steps), 
                            context.data
                        )

        finally:
            await resources.cleanup()

        logger.info(f"Workflow finished")
        finished_at = time.time()
        
        return RunReport(
            workflow_name=self.name,
            run_id=run_id,
            success=is_success,
            step_results=results,
            started_at=started_at,
            finished_at=finished_at
        )

    def serve(self, host: str = "0.0.0.0", port: int = 8000, config: Any = None):
        """Serve workflow as a REST API."""
        from .server import serve_workflow, ServerConfig
        # If config is passed, it overrides host/port arg or respects them?
        # Let's say config object takes precedence if fully set, but host/port args 
        # modify default config if config is None.
        if config is None:
            config = ServerConfig(host=host, port=port)
        
        serve_workflow(self, host=host, port=port, config=config)
