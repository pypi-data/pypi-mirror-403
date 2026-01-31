"""
CPU Optimizations
=================

CPU-specific optimizations for faster training.
"""

import os
import numpy as np
from typing import Optional
import threading


class CPUOptimizer:
    """
    CPU optimization manager.
    
    Features:
    - Thread pool management
    - Memory optimization
    - Vectorization hints
    - BLAS optimization
    """
    
    def __init__(self, num_threads: Optional[int] = None):
        self.num_threads = num_threads or min(4, os.cpu_count() or 1)
        self._apply_optimizations()
    
    def _apply_optimizations(self):
        """Apply CPU optimizations."""
        # Set thread count for NumPy
        os.environ['OMP_NUM_THREADS'] = str(self.num_threads)
        os.environ['MKL_NUM_THREADS'] = str(self.num_threads)
        os.environ['OPENBLAS_NUM_THREADS'] = str(self.num_threads)
        
        # NumPy optimizations
        try:
            # Use faster FFT
            np.seterr(all='ignore')  # Suppress warnings for speed
        except:
            pass
    
    def optimize_memory(self):
        """Optimize memory usage."""
        # Force garbage collection
        import gc
        gc.collect()
    
    def get_thread_count(self) -> int:
        """Get optimal thread count."""
        return self.num_threads


# Global CPU optimizer instance
_cpu_optimizer = None


def get_cpu_optimizer() -> CPUOptimizer:
    """Get global CPU optimizer instance."""
    global _cpu_optimizer
    if _cpu_optimizer is None:
        _cpu_optimizer = CPUOptimizer()
    return _cpu_optimizer


def optimize_for_cpu():
    """Apply CPU optimizations globally."""
    optimizer = get_cpu_optimizer()
    optimizer._apply_optimizations()
    return optimizer
