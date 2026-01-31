import torch
import time
import psutil
from rich.console import Console
from rich.table import Table
from typing import Optional, Any
from contextlib import ContextDecorator

console = Console()

class monitor(ContextDecorator):
    """
    A Context Manager and Decorator that tracks VRAM usage before and after a block of code.
    
    Usage:
        @monitor("My Process")
        def my_func():
            ...
            
        with monitor("Training Step"):
            ...
    """
    def __init__(self, name: str = "Block"):
        self.name = name
        self.initial_allocated = 0
        self.initial_reserved = 0
        self.peak_allocated = 0
        self.peak_reserved = 0

def get_current_memory_usage():
    """
    Get the current MPS memory usage.
    
    Returns:
        tuple: (allocated_bytes, reserved_bytes)
    """
    if not torch.backends.mps.is_available():
        return 0, 0
    
    # Current allocated memory
    allocated = torch.mps.current_allocated_memory()
    # Reserved memory (driver allocated)
    reserved = torch.mps.driver_allocated_memory()
    return allocated, reserved

def get_system_memory():
    """
    Get system unified memory stats.
    
    Returns:
        dict: {
            "total": int,
            "available": int,
            "percent": float,
            "used": int
        }
    """
    vm = psutil.virtual_memory()
    return {
        "total": vm.total,
        "available": vm.available,
        "percent": vm.percent,
        "used": vm.used,
    }

class monitor(ContextDecorator):
    """
    A Context Manager and Decorator that tracks VRAM usage before and after a block of code.
    
    Usage:
        @monitor("My Process")
        def my_func():
            ...
            
        with monitor("Training Step"):
            ...
    """
    def __init__(self, name: str = "Block"):
        self.name = name
        self.initial_allocated = 0
        self.initial_reserved = 0
        self.peak_allocated = 0
        self.peak_reserved = 0

    def _get_memory_stats(self):
        return get_current_memory_usage()

    def __enter__(self):
        if torch.backends.mps.is_available():
            # Force synchronization to get accurate baseline
            torch.mps.synchronize()
        
        self.initial_allocated, self.initial_reserved = self._get_memory_stats()
        
        console.print(f"[bold blue]Starting monitoring:[/bold blue] {self.name}")
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        if torch.backends.mps.is_available():
             torch.mps.synchronize()
        
        final_allocated, final_reserved = self._get_memory_stats()
        
        table = Table(title=f"MPS Memory Usage: {self.name}", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Initial", justify="right")
        table.add_column("Final", justify="right")
        table.add_column("Delta", justify="right")
        
        def fmt_mb(bytes_val):
            return f"{bytes_val / (1024 * 1024):.2f} MB"

        table.add_row(
            "Allocated", 
            fmt_mb(self.initial_allocated), 
            fmt_mb(final_allocated), 
            fmt_mb(final_allocated - self.initial_allocated)
        )
        table.add_row(
            "Driver / Reserved", 
            fmt_mb(self.initial_reserved), 
            fmt_mb(final_reserved), 
            fmt_mb(final_reserved - self.initial_reserved)
        )

        console.print(table)
        console.print("") # Newline
