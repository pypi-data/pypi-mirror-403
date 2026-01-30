
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path
import time
from .core import StepResult

class StateBackend(ABC):
    @abstractmethod
    def save(self, workflow_name: str, run_id: str, state: Dict[str, Any]):
        pass

    @abstractmethod
    def load(self, workflow_name: str, run_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_latest_run_id(self, workflow_name: str) -> Optional[str]:
        pass

class FileStateBackend(StateBackend):
    def __init__(self, base_dir: str = ".devrpa_state"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, workflow_name: str, run_id: str) -> Path:
        return self.base_dir / f"{workflow_name}_{run_id}.json"

    def save(self, workflow_name: str, run_id: str, state: Dict[str, Any]):
        path = self._get_path(workflow_name, run_id)
        # atomic write? for now direct
        with open(path, "w") as f:
            json.dump(state, f, indent=2, default=str)

    def load(self, workflow_name: str, run_id: str) -> Optional[Dict[str, Any]]:
        path = self._get_path(workflow_name, run_id)
        if not path.exists():
            return None
        with open(path, "r") as f:
            return json.load(f)

    def get_latest_run_id(self, workflow_name: str) -> Optional[str]:
        # List files matching workflow_name_*.json
        # simple heuristic: sort by mtime
        matches = list(self.base_dir.glob(f"{workflow_name}_*.json"))
        if not matches:
            return None
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        # parse run_id from filename? 
        # Filename: name_runid.json. 
        # If name has underscores, this is ambiguous.
        # But let's assume valid UUID or timestamp run_id.
        latest = matches[0]
        # remove suffix and prefix
        # prefix len is len(workflow_name) + 1 (_)
        return latest.stem[len(workflow_name)+1:]

class StateManager:
    def __init__(self, backend: StateBackend):
        self.backend = backend

    def save_checkpoint(
        self, 
        workflow_name: str, 
        run_id: str, 
        completed_steps: List[str], 
        context_data: Dict[str, Any]
    ):
        state = {
            "workflow": workflow_name,
            "run_id": run_id,
            "updated_at": time.time(),
            "completed_steps": completed_steps,
            "context_data": context_data
        }
        self.backend.save(workflow_name, run_id, state)

    def load_checkpoint(self, workflow_name: str, run_id: str):
        return self.backend.load(workflow_name, run_id)
    
    def get_latest_run(self, workflow_name: str):
        return self.backend.get_latest_run_id(workflow_name)
