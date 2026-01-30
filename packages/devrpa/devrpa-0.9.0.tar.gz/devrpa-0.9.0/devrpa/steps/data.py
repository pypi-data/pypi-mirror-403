
from typing import Any, Callable, List, Optional, Union
from ..workflow import Step, StepResult, ExecutionContext
from ..logging import get_logger

class TransformStep(Step):
    """Applies a transformation function to data in context."""
    def __init__(
        self, 
        name: str, 
        transform: Callable[[Any], Any],
        input_key: str,
        output_key: str
    ):
        """
        Args:
            transform: Function taking input data and returning transformed data.
            input_key: Context key to read from (supports dot notation lookup handled by context access utils if we add them, 
                       for now basic resolve of key name from data dict).
            output_key: Context key to write result to.
        """
        super().__init__(name)
        self.transform = transform
        self.input_key = input_key
        self.output_key = output_key

    async def execute(self, context: ExecutionContext) -> StepResult:
        if self.input_key:
            data = context.get_path(self.input_key)
            if data is None:
                 return StepResult(name=self.name, success=False, error=Exception(f"Input key '{self.input_key}' not found"))
        else:
            data = None

        try:
            result = self.transform(data)
            context.set(self.output_key, result)
            return StepResult(name=self.name, success=True, data={self.output_key: result})
        except Exception as e:
            return StepResult(name=self.name, success=False, error=e)

class FilterStep(Step):
    """Filters a list based on a condition."""
    def __init__(
        self, 
        name: str, 
        condition: Callable[[Any], bool],
        input_key: str,
        output_key: str
    ):
        super().__init__(name)
        self.condition = condition
        self.input_key = input_key
        self.output_key = output_key

    async def execute(self, context: ExecutionContext) -> StepResult:
        data = context.get_path(self.input_key)
        if not isinstance(data, list):
            return StepResult(name=self.name, success=False, error=Exception(f"Input '{self.input_key}' is not a list"))

        try:
            filtered = [item for item in data if self.condition(item)]
            context.set(self.output_key, filtered)
            return StepResult(name=self.name, success=True, data={self.output_key: filtered})
        except Exception as e:
            return StepResult(name=self.name, success=False, error=e)

class AggregateStep(Step):
    """Aggregates a list of data."""
    def __init__(
        self,
        name: str,
        input_key: str,
        output_key: str,
        group_by: Optional[str] = None,
        aggregate: str = "count" # count, sum, avg... 
    ):
        super().__init__(name)
        self.input_key = input_key
        self.output_key = output_key
        self.group_by = group_by
        self.aggregate = aggregate

    async def execute(self, context: ExecutionContext) -> StepResult:
        data = context.get_path(self.input_key)
        if not isinstance(data, list):
             return StepResult(name=self.name, success=False, error=Exception(f"Input '{self.input_key}' is not a list"))
        
        result = {}
        
        if self.group_by:
            # Simple grouping
            groups = {}
            for item in data:
                key = item.get(self.group_by)
                if key not in groups: groups[key] = []
                groups[key].append(item)
            
            for k, v in groups.items():
                if self.aggregate == "count":
                    result[k] = len(v)
        else:
            if self.aggregate == "count":
                result = len(data)

        context.set(self.output_key, result)
        return StepResult(name=self.name, success=True, data={self.output_key: result})
