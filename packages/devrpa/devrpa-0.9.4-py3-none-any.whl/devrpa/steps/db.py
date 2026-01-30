
from typing import Any, List, Dict
import sqlite3
import asyncio
from ..workflow import Step
from ..core import StepResult, ExecutionContext

class DatabaseStep(Step):
    def __init__(self, name: str, connection_string: str, query: str, parameters: tuple = ()):
        super().__init__(name)
        self.connection_string = connection_string
        self.query = query
        self.parameters = parameters

    async def execute(self, context: ExecutionContext) -> StepResult:
        conn_str = context.resolve(self.connection_string)
        query = context.resolve(self.query)
        
        def _db_op():
            # Basic SQLite implementation
            with sqlite3.connect(conn_str) as conn:
                cursor = conn.cursor()
                cursor.execute(query, self.parameters)
                rows = cursor.fetchall() if cursor.description else []
                conn.commit()
                return rows
        
        try:
            rows = await asyncio.to_thread(_db_op)
            return StepResult(name=self.name, success=True, data={f"{self.name}_rows": rows})
        except Exception as e:
            return StepResult(name=self.name, success=False, error=e)
