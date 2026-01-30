
import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Type, Callable, Any
from enum import Enum

class BackoffStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"

@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_strategy: BackoffStrategy = BackoffStrategy.FIXED
    initial_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = False
    retry_on: List[Type[Exception]] = field(default_factory=lambda: [Exception])
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        if attempt >= self.max_attempts:
            return False
        return any(isinstance(exception, t) for t in self.retry_on)

    def get_delay(self, attempt: int) -> float:
        if self.backoff_strategy == BackoffStrategy.FIXED:
            delay = self.initial_delay
        else:
            delay = min(self.initial_delay * (2 ** (attempt - 1)), self.max_delay)
        
        if self.jitter:
            delay = delay * random.uniform(0.5, 1.5)
        
        return delay

class CircuitState(Enum):
    CLOSED = "closed"     # Normal operation
    OPEN = "open"         # Failing, failing fast
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    def __init__(
        self, 
        failure_threshold: int = 5, 
        recovery_timeout: float = 60.0,
        half_open_attempts: int = 1
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_attempts = half_open_attempts
        
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time = 0.0
        self._half_open_successes = 0

    @property
    def state(self):
        # Auto-transition to half-open if time passed
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_successes = 0
        return self._state

    def record_success(self):
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_successes += 1
            if self._half_open_successes >= self.half_open_attempts:
                self._state = CircuitState.CLOSED
                self._failures = 0
        elif self._state == CircuitState.CLOSED:
            # Optional: decay failures over time? keeping simple for now
            self._failures = 0

    def record_failure(self):
        self._failures += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.CLOSED:
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
        elif self._state == CircuitState.HALF_OPEN:
            # One failure back to open
            self._state = CircuitState.OPEN

    def allow_request(self) -> bool:
        return self.state != CircuitState.OPEN
