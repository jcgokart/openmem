"""
Metrics module for OpenMem
"""

import logging
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger("openmem")


@dataclass
class Metrics:
    """
    Metrics for monitoring query performance.
    
    Attributes:
        total_queries: Total number of queries executed
        slow_queries: Number of queries exceeding threshold
        errors: Number of errors encountered
        slow_threshold_ms: Threshold for slow query warning (default: 100ms)
    """
    total_queries: int = 0
    slow_queries: int = 0
    errors: int = 0
    slow_threshold_ms: float = 100.0
    
    def record_query(self, duration_ms: float) -> None:
        """
        Record a query execution.
        
        Args:
            duration_ms: Query duration in milliseconds
        """
        self.total_queries += 1
        if duration_ms > self.slow_threshold_ms:
            self.slow_queries += 1
            logger.warning(f"Slow query detected: {duration_ms:.2f}ms")
    
    def record_error(self) -> None:
        """Record an error occurrence"""
        self.errors += 1
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.total_queries = 0
        self.slow_queries = 0
        self.errors = 0
    
    def to_dict(self) -> dict:
        """Convert metrics to dictionary"""
        return {
            "total_queries": self.total_queries,
            "slow_queries": self.slow_queries,
            "errors": self.errors,
            "slow_threshold_ms": self.slow_threshold_ms
        }


metrics = Metrics()


def timed_query(func: Callable) -> Callable:
    """
    Decorator to measure and record query execution time.
    
    Usage:
        @timed_query
        def get_memory(memory_id: int):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            metrics.record_error()
            raise
        finally:
            duration = (time.perf_counter() - start) * 1000
            metrics.record_query(duration)
    return wrapper
