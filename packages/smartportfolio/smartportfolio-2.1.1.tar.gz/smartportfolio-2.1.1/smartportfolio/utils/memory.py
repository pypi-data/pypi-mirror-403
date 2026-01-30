"""
Memory Management Utilities

Functions for monitoring and optimizing memory usage.
"""

import gc
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def get_memory_usage() -> float:
    """
    Get current memory usage in MB.
    
    Returns:
        Memory usage in megabytes
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback using sys
        return sum(sys.getsizeof(obj) for obj in gc.get_objects()) / (1024 * 1024)


def clear_memory() -> None:
    """
    Aggressively clear memory.
    
    Runs garbage collection multiple times.
    """
    for _ in range(3):
        gc.collect()
    logger.debug(f"Memory cleared. Current usage: {get_memory_usage():.1f} MB")


def check_memory_threshold(threshold_mb: float = 6000) -> bool:
    """
    Check if memory usage is below threshold.
    
    Args:
        threshold_mb: Maximum allowed memory in MB
        
    Returns:
        True if memory usage is acceptable
    """
    current = get_memory_usage()
    
    if current > threshold_mb:
        logger.warning(f"Memory usage {current:.1f}MB exceeds threshold {threshold_mb:.1f}MB")
        clear_memory()
        return False
    
    return True


def optimize_batch_size(
    default_size: int,
    sample_size_mb: float,
    target_memory_mb: float = 4000,
) -> int:
    """
    Calculate optimal batch size based on available memory.
    
    Args:
        default_size: Default batch size
        sample_size_mb: Memory per sample in MB
        target_memory_mb: Target memory usage in MB
        
    Returns:
        Optimized batch size
    """
    current = get_memory_usage()
    available = target_memory_mb - current
    
    if available <= 0:
        clear_memory()
        available = 1000  # Conservative estimate after clearing
    
    # Calculate max batch size
    max_batch = int(available / (sample_size_mb + 0.001))
    
    # Return minimum of default and calculated max
    return min(default_size, max(1, max_batch))


class MemoryTracker:
    """
    Context manager for tracking memory usage.
    """
    
    def __init__(self, label: str = "Operation"):
        self.label = label
        self.start_memory = 0.0
    
    def __enter__(self):
        self.start_memory = get_memory_usage()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_memory = get_memory_usage()
        delta = end_memory - self.start_memory
        
        if delta > 100:  # Log if more than 100MB change
            logger.info(
                f"{self.label}: Memory {self.start_memory:.1f}MB -> "
                f"{end_memory:.1f}MB (delta: {delta:+.1f}MB)"
            )
        
        return False
