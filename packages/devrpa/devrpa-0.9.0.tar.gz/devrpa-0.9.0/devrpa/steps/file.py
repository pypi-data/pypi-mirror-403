
from typing import Any, Dict, List, Callable, Union
import subprocess
import shutil
import os
from pathlib import Path
import asyncio
from ..workflow import Step
from ..core import StepResult, ExecutionContext

# Action now async? Or sync run in thread?
# Making action signature generic: can be sync or async, handled by wrapper.
Action = Callable[[ExecutionContext], Any] 

class FileStep(Step):
    def __init__(self, name: str, actions: List[Action] = None):
        super().__init__(name)
        self.actions = actions or []

    async def execute(self, context: ExecutionContext) -> StepResult:
        try:
            for act in self.actions:
                if asyncio.iscoroutinefunction(act):
                    await act(context)
                else:
                    await asyncio.to_thread(act, context)
            return StepResult(name=self.name, success=True)
        except Exception as e:
            return StepResult(name=self.name, success=False, error=e)

    @classmethod
    def run_python(cls, name: str, script_path: str, args: List[str] = []) -> "FileStep":
        def _act(ctx: ExecutionContext):
            resolved_path = ctx.resolve(script_path)
            import sys
            cmd = [sys.executable, resolved_path] + [ctx.resolve(a) for a in args]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        step = cls(name)
        step.actions.append(_act)
        return step

    @classmethod
    def run_shell(cls, name: str, command: str) -> "FileStep":
        def _act(ctx: ExecutionContext):
            resolved_cmd = ctx.resolve(command)
            subprocess.run(resolved_cmd, shell=True, check=True, capture_output=True, text=True)
        
        step = cls(name)
        step.actions.append(_act)
        return step
        
    @classmethod
    def copy(cls, name: str, src: str, dest: str) -> "FileStep":
        def _act(ctx: ExecutionContext):
            s = ctx.resolve(src)
            d = ctx.resolve(dest)
            shutil.copy2(s, d)
        
        step = cls(name)
        step.actions.append(_act)
        return step
