
from typing import Optional, Type, List, Any, Union, Callable
from .workflow import Workflow, Step
from .core import ExecutionContext
from .steps.api import ApiStep
from .steps.files_extended import GenerateCSVStep, ParseCSVStep
from .steps.data import TransformStep, FilterStep
from .steps.web import WebStep
from .steps.flow import ParallelStep

try:
    from pydantic import BaseModel
except ImportError:
    class BaseModel: pass

from .integrations.github import GitHub
from .integrations.slack import Slack
import urllib.parse
import re

class FlowBuilder:
    def __init__(self, name: str, context_model: Optional[Type[BaseModel]] = None):
        self._workflow = Workflow(name)
        self._context_model = context_model
        self._step_counter = 0

    def _auto_name(self, prefix: str, target: str = "") -> str:
        self._step_counter += 1
        clean_target = re.sub(r'[^a-zA-Z0-9]', '_', target).strip('_')
        if clean_target:
            return f"{prefix}_{clean_target}"
        return f"{prefix}_{self._step_counter}"

    def add(self, step: Step) -> "FlowBuilder":
        if not step.name:
            step.name = self._auto_name(step.__class__.__name__)
        self._workflow.add(step)
        return self

    def from_api(self, url: str, output: str = None, method: str = "GET", headers: dict = None) -> "FlowBuilder":
        """Fetch data from an API."""
        # Smart name from URL hostname/path
        if not output:
             try:
                 parsed = urllib.parse.urlparse(url)
                 # e.g. api.com/users -> api_com_users
                 domain = parsed.netloc.replace('.', '_')
                 path = parsed.path.replace('/', '_').strip('_')
                 output = f"{domain}_{path}"
             except:
                 output = f"api_call_{self._step_counter}"
        
        step = ApiStep(
            name=output,
            url=url,
            method=method,
            headers=headers
        )
        self._workflow.add(step)
        return self

    def transform(self, fn: Callable, input: str = None, output: str = None) -> "FlowBuilder":
        """Transform data."""
        if not output:
             output = f"transform_{fn.__name__}"
        if not input:
             # Default to last output? Too magic for now. 
             # Let's require input or have a default "current" concept?
             # For now, simplistic auto-naming requires valid input ref.
             pass 

        step = TransformStep(
            name=output, # Step name = output key for now logic
            transform=fn,
            input_key=input,
            output_key=output
        )
        self._workflow.add(step)
        return self
    
    def cache(self, ttl: Union[int, str] = 3600, key_by: List[str] = None) -> "FlowBuilder":
        """Enable caching for the last added step."""
        if not self._workflow.steps:
            raise ValueError("No steps to cache. Call .cache() after adding a step.")
        
        last_step = self._workflow.steps[-1]
        
        # Parse TTL string "1 hour" -> int seconds
        ttl_seconds = ttl
        if isinstance(ttl, str):
            if "hour" in ttl:
                ttl_seconds = int(ttl.split()[0]) * 3600
            elif "minute" in ttl:
                ttl_seconds = int(ttl.split()[0]) * 60
            elif "day" in ttl:
                ttl_seconds = int(ttl.split()[0]) * 86400
            else:
                ttl_seconds = int(ttl) # assumes seconds

        last_step.cache_config = {
            "ttl": ttl_seconds,
            "key_by": key_by or []
        }

        # Auto-initialize workflow cache backend if needed
        # This is a bit side-effecty but fluent API implies configuration
        if not self._workflow.cache_backend:
             from .cache import get_cache_backend
             self._workflow.cache_backend = get_cache_backend("file")

        return self

    # --- Integrations ---
    
    def github_get_repo(self, owner: str, repo: str, output: str = None) -> "FlowBuilder":
        step = GitHub.get_repo(owner, repo, output)
        return self.add(step)

    def github_list_issues(self, owner: str, repo: str, state: str = "open", output: str = None) -> "FlowBuilder":
        step = GitHub.list_issues(owner, repo, state, output)
        return self.add(step)

    def slack_notify(self, channel: str, message: str) -> "FlowBuilder":
        step = Slack.post_message(channel, message)
        return self.add(step)
    
    def serve(self, host: str = "0.0.0.0", port: int = 8000, config: Any = None):
        """Serve workflow as a REST API."""
        return self._workflow.serve(host=host, port=port, config=config)
    
    # --- Selectors ---

    def where(self, expression: str, input: str = None, output: str = None) -> "FlowBuilder":
        """Filter data using a string expression."""
        from .selectors import Selector
        cond = Selector.compile_condition(expression)
        
        if not output:
            output = f"filter_{self._step_counter}_{hash(expression) % 1000}"
        
        # Use FilterStep
        step = FilterStep(
            name=output,
            condition=cond,
            input_key=input, # Must be provided or inferred
            output_key=output
        )
        self._workflow.add(step)
        return self

    def select(self, fields: Union[List[str], Dict[str, str]], input: str = None, output: str = None) -> "FlowBuilder":
        """Select/Rename fields in data."""
        from .selectors import Selector
        transform = lambda data: [Selector.compile_selector(fields)(item) for item in data]
        
        if not output:
            output = f"select_{self._step_counter}"
            
        step = TransformStep(
            name=output,
            transform=transform,
            input_key=input, # Must be provided
            output_key=output
        )
        self._workflow.add(step)
        return self

    def filter(self, fn: Callable, input: str, output: str) -> "FlowBuilder":
        """Filter list data."""
        step = FilterStep(
            name=f"filter_{output}",
            condition=fn,
            input_key=input,
            output_key=output
        )
        self._workflow.add(step)
        return self

    def to_csv(self, path: str, input: str) -> "FlowBuilder":
        """Write data to CSV."""
        step = GenerateCSVStep(
            name=f"write_csv_{input}",
            data_key=input,
            output_path=path
        )
        self._workflow.add(step)
        return self

    def parallel(self, flows: List["FlowBuilder"], name: str = "parallel_group") -> "FlowBuilder":
        """Run multiple flows in parallel."""

        pass # Placeholder: Implementing fully correct parallel flow merging is non-trivial without GroupStep.
        return self 

    def build(self) -> Workflow:
        return self._workflow
    
    # Forward run call for convenience
    async def run(self, *args, **kwargs):
        return await self._workflow.run(*args, **kwargs)

# Function alias for cleaner usage
def flow(name: str, context_model: Optional[Type[BaseModel]] = None) -> FlowBuilder:
    return FlowBuilder(name, context_model)
