
from typing import Any, List, Optional
import os
import asyncio
from ..workflow import Step, StepResult, ExecutionContext

class ParseCSVStep(Step):
    def __init__(self, name: str, file_path: str, output_key: str):
        super().__init__(name)
        self.file_path = file_path
        self.output_key = output_key

    async def execute(self, context: ExecutionContext) -> StepResult:
        import pandas as pd
        path = context.resolve(self.file_path)
        
        def _read():
            df = pd.read_csv(path)
            # Convert to list of dicts
            return df.to_dict(orient="records")

        try:
            records = await asyncio.to_thread(_read)
            context.set(self.output_key, records)
            return StepResult(name=self.name, success=True, data={f"{self.output_key}_count": len(records)})
        except Exception as e:
            return StepResult(name=self.name, success=False, error=e)

class GenerateCSVStep(Step):
    def __init__(self, name: str, data_key: str, output_path: str):
        super().__init__(name)
        self.data_key = data_key
        self.output_path = output_path

    async def execute(self, context: ExecutionContext) -> StepResult:
        import pandas as pd
        
        # Resolve data from key
        # We need that helper again. For now, assume top level.
        # Improvement: Move _get_val to core.ExecutionContext method.
        # For now, simplistic.
        data = context.data.get(self.data_key)
        if not data:
             return StepResult(name=self.name, success=False, error=Exception(f"Data key '{self.data_key}' not found"))
        
        path = context.resolve(self.output_path)
        # Ensure dir
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        def _write():
            df = pd.DataFrame(data)
            df.to_csv(path, index=False)
        
        try:
            await asyncio.to_thread(_write)
            return StepResult(name=self.name, success=True, data={"output_path": path})
        except Exception as e:
            return StepResult(name=self.name, success=False, error=e)
