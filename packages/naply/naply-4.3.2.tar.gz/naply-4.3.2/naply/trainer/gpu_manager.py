"""
GPU and Device Management
========================

Auto-detection of available devices (GPU/CPU) with CPU optimization.
"""

import os
import numpy as np
from typing import Optional, Dict, Any
import threading


class DeviceManager:
    """
    Manages device selection and optimization.
    
    Automatically detects and optimizes for available hardware.
    """
    
    def __init__(self):
        self.device = self._detect_device()
        self.device_info = self._get_device_info()
    
    def _detect_device(self) -> str:
        """Detect best available device."""
        # Check for CUDA
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        
        # Check for MPS (Apple Silicon)
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        
        # Default to CPU with optimizations
        return "cpu"
    
    def _get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        info = {
            'device': self.device,
            'cpu_count': os.cpu_count() or 1,
            'threads': min(4, os.cpu_count() or 1),  # Optimize thread count
        }
        
        if self.device == "cuda":
            try:
                import torch
                info['gpu_name'] = torch.cuda.get_device_name(0)
                info['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory / 1e9
            except:
                pass
        
        return info
    
    def optimize_cpu(self):
        """Apply CPU optimizations."""
        # Set thread count for NumPy
        if hasattr(np, 'seterr'):
            np.seterr(all='ignore')  # Suppress warnings for speed
        
        # Set BLAS threads (if available)
        try:
            os.environ['OMP_NUM_THREADS'] = str(self.device_info['threads'])
            os.environ['MKL_NUM_THREADS'] = str(self.device_info['threads'])
        except:
            pass
    
    def get_device(self) -> str:
        """Get current device."""
        return self.device
    
    def is_cuda(self) -> bool:
        """Check if CUDA is available."""
        return self.device == "cuda"
    
    def is_cpu(self) -> bool:
        """Check if using CPU."""
        return self.device == "cpu"
    
    def __repr__(self) -> str:
        return f"DeviceManager(device={self.device}, info={self.device_info})"


class GPUManager:
    """
    GPU memory and computation management.
    
    Handles mixed precision, memory management, and optimization.
    """
    
    def __init__(self, device_manager: Optional[DeviceManager] = None):
        self.device_manager = device_manager or DeviceManager()
        self.use_amp = False  # Automatic Mixed Precision
        self.mixed_precision = False
        
        # Enable mixed precision if GPU available
        if self.device_manager.is_cuda():
            try:
                import torch
                self.use_amp = True
                self.mixed_precision = True
            except ImportError:
                pass
    
    def enable_amp(self, enable: bool = True):
        """Enable/disable Automatic Mixed Precision."""
        if self.device_manager.is_cuda():
            self.use_amp = enable
            self.mixed_precision = enable
        else:
            # CPU doesn't benefit from AMP, but we can simulate it
            self.use_amp = False
            self.mixed_precision = False
    
    def get_scaler(self):
        """Get gradient scaler for mixed precision."""
        if self.use_amp:
            try:
                import torch
                return torch.cuda.amp.GradScaler()
            except ImportError:
                return None
        return None
    
    def optimize_for_cpu(self):
        """Apply CPU-specific optimizations."""
        self.device_manager.optimize_cpu()
    
    def get_device(self) -> str:
        """Get current device."""
        return self.device_manager.get_device()
    
    def memory_info(self) -> Dict[str, Any]:
        """Get memory information."""
        info = self.device_manager.device_info.copy()
        
        if self.device_manager.is_cuda():
            try:
                import torch
                info['allocated'] = torch.cuda.memory_allocated() / 1e9
                info['reserved'] = torch.cuda.memory_reserved() / 1e9
            except:
                pass
        
        return info
