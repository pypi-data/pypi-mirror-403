
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union
from pathlib import Path
import os
import re

# Try importing Pydantic
try:
    from pydantic import BaseModel
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    class BaseModel: pass # Dummy

@dataclass
class StepResult:
    name: str
    success: bool
    error: Optional[Exception] = None
    started_at: float = 0.0
    finished_at: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        return self.finished_at - self.started_at

    def to_dict(self):
        return {
            "name": self.name,
            "success": self.success,
            "error": str(self.error) if self.error else None,
            "duration": self.duration,
            "started_at": self.started_at,
            "finished_at": self.finished_at
        }

@dataclass
class ExecutionContext:
    """Holds the state for a workflow execution."""
    # Data can be a dict OR a Pydantic Model
    data: Union[Dict[str, Any], BaseModel] = field(default_factory=dict)
    env: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    artifacts_dir: Path = field(default_factory=lambda: Path("artifacts"))
    resources: Optional[Any] = None # ResourcePool

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from data, supporting dot notation for dicts or model attributes."""
        # Simple top-level access
        if HAS_PYDANTIC and isinstance(self.data, BaseModel):
            if hasattr(self.data, key):
                return getattr(self.data, key)
            return default
        else:
            return self.data.get(key, default)

    def resolve(self, text: str) -> str:
        """Resolve variables in text using data and env."""
        if not text:
            return ""
        
        def _get_value(path: str) -> Any:
            parts = path.split('.')
            curr = self.data
            
            # Start resolution
            # 1. Check if path is exact match in data
            if not isinstance(self.data, BaseModel) and path in self.data:
                return self.data[path]
            
            # 2. Start traversal
            head = parts[0]
            
            # Resolve head
            if head == "secrets":
                 return os.getenv(parts[1], "") if len(parts)>1 else ""
            
            if HAS_PYDANTIC and isinstance(self.data, BaseModel):
                if hasattr(self.data, head):
                    curr = getattr(self.data, head)
                elif head in self.env:
                    curr = self.env[head]
                else:
                    return "{" + path + "}"
            else:
                # Dict mode
                if head in self.data:
                    curr = self.data[head]
                elif head in self.env:
                    curr = self.env[head]
                else:
                    return "{" + path + "}"
            
            # Traverse remaining parts
            try:
                for p in parts[1:]:
                    if HAS_PYDANTIC and isinstance(curr, BaseModel):
                        if hasattr(curr, p):
                            curr = getattr(curr, p)
                        else:
                            return "{" + path + "}"
                    elif isinstance(curr, dict):
                        curr = curr.get(p)
                    elif isinstance(curr, list):
                        try:
                            idx = int(p)
                            curr = curr[idx]
                        except (ValueError, IndexError):
                            return "{" + path + "}"
                    else:
                        return "{" + path + "}" # path too deep
                    
                    if curr is None: break
                
                return str(curr)
            except Exception:
                return "{" + path + "}"

        return re.sub(r'\{([a-zA-Z0-9_.]+)\}', lambda m: _get_value(m.group(1)), text)

    def get_path(self, path: str) -> Any:
        """Get value at dot-notation path."""
        if not path:
            return None
            
        parts = path.split('.')
        curr = self.data
        
        # 1. Check if path is exact match in data (for flat dicts)
        if not isinstance(self.data, BaseModel) and path in self.data:
            return self.data[path]
        
        # 2. Start traversal
        head = parts[0]
        
        if head == "secrets":
             return os.getenv(parts[1], "") if len(parts)>1 else None
        
        if HAS_PYDANTIC and isinstance(self.data, BaseModel):
            if hasattr(self.data, head):
                curr = getattr(self.data, head)
            elif head in self.env:
                curr = self.env[head]
            else:
                return None
        else:
            if head in self.data:
                curr = self.data[head]
            elif head in self.env:
                curr = self.env[head]
            else:
                return None
        
        for p in parts[1:]:
            if HAS_PYDANTIC and isinstance(curr, BaseModel):
                if hasattr(curr, p):
                    curr = getattr(curr, p)
                else:
                    return None
            elif isinstance(curr, dict):
                curr = curr.get(p)
            elif isinstance(curr, list):
                try:
                    curr = curr[int(p)]
                except (ValueError, IndexError):
                    return None
            else:
                return None # too deep
            
            if curr is None: break
            
        return curr

    def set(self, key: str, value: Any) -> None:
        """Set value in data, supporting Pydantic attributes."""
        if HAS_PYDANTIC and isinstance(self.data, BaseModel):
            if hasattr(self.data, key):
                setattr(self.data, key, value)
            else:
                # If Strict, maybe error? Or ignore?
                # For now, try setting anyway if allowed (e.g. extra=allow), else warn/error.
                # Actually specific error "pydantic model does not have field" is good.
                # But let's try setattr first.
                try:
                    setattr(self.data, key, value)
                except Exception as e:
                    # Fallback or Error
                    raise ValueError(f"Cannot set '{key}' on Pydantic model {type(self.data).__name__}: {e}")
        else:
            self.data[key] = value
