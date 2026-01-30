
from typing import List, Optional, Callable, Any, Dict
import asyncio
import re
from ..workflow import Step
from ..core import StepResult, ExecutionContext
from ..logging import get_logger

class IfStep(Step):
    """Conditional execution step."""
    def __init__(
            self, 
            name: str, 
            condition: Callable[[ExecutionContext], Any], 
            then_steps: List[Step], 
            else_steps: Optional[List[Step]] = None
    ):
        super().__init__(name)
        self.condition = condition
        self.then_steps = then_steps
        self.else_steps = else_steps or []

    async def execute(self, context: ExecutionContext) -> StepResult:
        logger = get_logger()
        
        try:
            if asyncio.iscoroutinefunction(self.condition):
                cond_result = await self.condition(context)
            else:
                cond_result = self.condition(context)
                
            logger.info(f"IfStep '{self.name}' condition: {cond_result}")
            
            steps_to_run = self.then_steps if cond_result else self.else_steps
            
            for step in steps_to_run:
                logger.info(f"  -> Running sub-step '{step.name}'")
                res = await step.run(context)
                if not res.success:
                    return StepResult(name=self.name, success=False, error=res.error)
                
                if res.data:
                    context.data.update(res.data)

            return StepResult(name=self.name, success=True)
            
        except Exception as e:
             return StepResult(name=self.name, success=False, error=e)

class SwitchStep(Step):
    """Routes execution based on a value."""
    def __init__(
        self,
        name: str,
        value: str,
        cases: Dict[str, Step],
        default: Optional[Step] = None
    ):
        super().__init__(name)
        self.value = value
        self.cases = cases
        self.default = default

    async def execute(self, context: ExecutionContext) -> StepResult:
        logger = get_logger()
        resolved_val = context.resolve(self.value)
        logger.info(f"SwitchStep '{self.name}' value: '{resolved_val}'")

        # Exact match first
        selected_step = self.cases.get(resolved_val)
        
        # Regex match if not exact? (As per prompt suggestions, nice to have)
        if not selected_step:
            for pattern, step in self.cases.items():
                if hasattr(pattern, "match") or ("*" in pattern or "." in pattern): # simple heuristic for regex
                    try:
                        if re.fullmatch(pattern, resolved_val):
                            selected_step = step
                            break
                    except re.error:
                        pass
        
        target = selected_step or self.default
        
        if target:
            logger.info(f"  -> Routing to step '{target.name}'")
            return await target.run(context)
        else:
            logger.info(f"  -> No case matched and no default.")
            return StepResult(name=self.name, success=True)

class ParallelStep(Step):
    """Executes multiple steps concurrently."""
    def __init__(
        self,
        name: str,
        steps: List[Step],
        max_concurrency: int = 5
    ):
        super().__init__(name)
        self.steps = steps
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def execute(self, context: ExecutionContext) -> StepResult:
        logger = get_logger()
        logger.info(f"ParallelStep '{self.name}' starting {len(self.steps)} steps")
        
        async def run_one(step: Step):
            async with self.semaphore:
                return await step.run(context)

        results = await asyncio.gather(*[run_one(s) for s in self.steps], return_exceptions=True)
        
        failed = False
        errors = []
        for res in results:
            if isinstance(res, Exception):
                failed = True
                errors.append(str(res))
            elif isinstance(res, StepResult):
                if not res.success:
                    failed = True
                    errors.append(f"{res.name}: {res.error}")
                elif res.data:
                    context.data.update(res.data)
        
        if failed:
            return StepResult(name=self.name, success=False, error=Exception(f"Parallel failures: {errors}"))
        
        return StepResult(name=self.name, success=True)

class MapStep(Step):
    """Applies a step to a list of items."""
    def __init__(
        self,
        name: str,
        step: Step,
        items: List[Any] | str,
        max_concurrency: int = 5,
        collect_results: bool = True
    ):
        super().__init__(name)
        self.step = step
        self.items = items
        self.max_concurrency = max_concurrency
        self.collect_results = collect_results
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def execute(self, context: ExecutionContext) -> StepResult:
        logger = get_logger()
        
        # Resolve items
        input_list = []
        if isinstance(self.items, str):
            # Resolve from context data
            val = context.resolve(self.items)
            # Check if it resolved to a list directly (if passed as obj) or parsed string?
            # context.resolve returns str. 
            # We need to access context.data directly for objects!
            # Let's fix ExecutionContext to allow retrieving raw objects. context.get() logic.
            # For now, simplistic access:
            key = self.items.strip("{}")
            if key in context.data:
                possible_list = context.data[key]
                if isinstance(possible_list, list):
                    input_list = possible_list
                else:
                    input_list = [possible_list] # Treat single as list of 1?
            else:
                input_list = [] # Or error?
        else:
            input_list = self.items

        logger.info(f"MapStep '{self.name}' processing {len(input_list)} items")
        
        results_list = [None] * len(input_list) # preserve order

        async def run_item(idx, item):
            async with self.semaphore:
                # We need a context copy or just temp inject 'item'?
                # Sharing context is problematic if steps overwrite 'item'.
                # Ideally: Create a lightweight context scope.
                # Since ExecutionContext is a dataclass, shallow copy is easy.
                from dataclasses import replace
                
                # Copy context data to avoid polluting main context processing other items
                child_data = context.data.copy()
                child_data["item"] = item # Default variable name
                
                # Also allow {item} style if we supported it, but dictionary key is 'item'
                
                child_ctx = replace(context, data=child_data)
                
                # Execute step
                res = await self.step.run(child_ctx)
                return idx, res

        tasks = [run_item(i, item) for i, item in enumerate(input_list)]
        run_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        failed = False
        errors = []
        
        for r in run_results:
            if isinstance(r, Exception):
                failed = True
                errors.append(str(r))
            else:
                idx, res = r
                if self.collect_results:
                    # We might want the DATA from the result, not just StepResult object
                    results_list[idx] = res.data if res.data else {}
                
                if not res.success:
                    failed = True
                    errors.append(f"Item {idx}: {res.error}")

        if failed:
            return StepResult(name=self.name, success=False, error=Exception(f"Map failures: {errors}"))

        # output results
        return StepResult(name=self.name, success=True, data={self.name: results_list})
