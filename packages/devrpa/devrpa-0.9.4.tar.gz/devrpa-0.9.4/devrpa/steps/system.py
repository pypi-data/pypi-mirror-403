
from typing import List
import subprocess
import asyncio
from ..workflow import Step
from ..core import StepResult, ExecutionContext

class ShellStep(Step):
    def __init__(self, name: str, command: str):
        super().__init__(name)
        self.command = command

    async def execute(self, context: ExecutionContext) -> StepResult:
        resolved_cmd = context.resolve(self.command)
        
        def _run():
             return subprocess.run(
                resolved_cmd, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True
            )

        try:
            # Use to_thread for blocking IO
            result = await asyncio.to_thread(_run)
            
            return StepResult(
                name=self.name, 
                success=True, 
                data={
                    f"{self.name}_stdout": result.stdout,
                    f"{self.name}_stderr": result.stderr
                }
            )
        except subprocess.CalledProcessError as e:
            return StepResult(
                name=self.name, 
                success=False, 
                error=Exception(f"Command failed with code {e.returncode}: {e.stderr}"),
                data={f"{self.name}_stderr": e.stderr}
            )
