import time
import argparse
import sys

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box

from .core import get_system_memory

def get_mps_availability():
    try:
        import torch
        return torch.backends.mps.is_available(), torch.backends.mps.is_built()
    except ImportError:
        return False, False

def get_gpu_pressure_text():
    """
    Attempt to get memory pressure roughly. 
    There isn't a direct python API for system-wide metal memory usage without PyObjC.
    We will use psutil's virtual memory as a proxy for 'Unified Memory' pressure on Apple Silicon.
    """
    vm = psutil.virtual_memory()
    # On Apple Silicon, RAM is unified. High RAM usage = High GPU potential pressure.
    return f"{vm.percent}% System Memory Used"

def generate_dashboard():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats"),
    )

    # Header
    layout["header"].update(Panel("MPS Watch - Apple Silicon Memory Monitor", style="bold white on blue"))

    # Stats Table
    stats_table = Table(box=box.SIMPLE)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    # System Memory
    mem = get_system_memory()
    def fmt_gb(bytes_val):
        return f"{bytes_val / (1024**3):.2f} GB"

    stats_table.add_row("System Total RAM", fmt_gb(mem["total"]))
    stats_table.add_row("System Used RAM", fmt_gb(mem["used"]))
    stats_table.add_row("System Available RAM", fmt_gb(mem["available"]))
    stats_table.add_row("System Memory Pressure", f"{mem['percent']}%")

    # MPS Status
    is_avail, is_built = get_mps_availability()
    mps_status = "[bold green]Available[/bold green]" if is_avail else "[bold red]Not Available[/bold red]"
    if not is_built:
        mps_status += " (PyTorch not built with MPS)"
    
    stats_table.add_row("MPS Backend Status", mps_status)

    layout["stats"].update(Panel(stats_table, title="System Stats", border_style="blue"))
    
    return layout

def main():
    parser = argparse.ArgumentParser(description="Monitor Apple Silicon MPS memory usage.")
    parser.add_argument("--interval", "-i", type=float, default=1.0, help="Refresh interval in seconds")
    args = parser.parse_args()

    console = Console()
    
    with Live(generate_dashboard(), refresh_per_second=1/args.interval, console=console) as live:
        try:
            while True:
                live.update(generate_dashboard())
                time.sleep(args.interval)
        except KeyboardInterrupt:
            console.print("[bold yellow]Stopping monitor...[/bold yellow]")

if __name__ == "__main__":
    main()
