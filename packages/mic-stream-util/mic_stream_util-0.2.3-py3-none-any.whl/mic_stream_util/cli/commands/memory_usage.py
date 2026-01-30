"""Memory usage monitoring command module."""

from __future__ import annotations

import os
import time

import click
import psutil
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def get_shared_memory_usage() -> dict[str, int | list[tuple[str, int]]]:
    """Get shared memory usage from /dev/shm."""
    shm_path = "/dev/shm"
    mic_buffers = []
    total_size = 0

    try:
        if os.path.exists(shm_path):
            for filename in os.listdir(shm_path):
                if "mic_buffer" in filename:
                    filepath = os.path.join(shm_path, filename)
                    size = os.path.getsize(filepath)
                    mic_buffers.append((filename, size))
                    total_size += size
    except Exception:
        pass

    return {
        "count": len(mic_buffers),
        "total_bytes": total_size,
        "buffers": mic_buffers,
    }


def find_process_by_name(pattern: str) -> int | None:
    """Find a process by name pattern."""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if cmdline and any(pattern.lower() in str(arg).lower() for arg in cmdline):
                return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("--interval", "-i", type=float, default=1.0, help="Update interval in seconds (default: 1.0)")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed memory information")
@click.option("--pid", type=int, help="Process ID to monitor")
@click.option("--process-name", "-p", type=str, help="Find process by name pattern (e.g., 'microphone')")
@click.option("--duration", type=float, default=0, help="Monitoring duration in seconds (0 for infinite)")
def memory_usage(interval: float, detailed: bool, pid: int | None, process_name: str | None, duration: float):
    """Monitor memory usage in real-time, optionally for a specific process."""
    console = Console()

    # Determine which process to monitor
    process: psutil.Process | None = None
    process_pid: int | None = None
    initial_memory: float | None = None
    last_memory: float | None = None
    start_time: float | None = None

    if pid is not None:
        try:
            process = psutil.Process(pid)
            process_pid = pid
            console.print(f"[bold green]Monitoring process PID {pid} ({process.name()})[/bold green]")
        except psutil.NoSuchProcess:
            console.print(f"[bold red]Process {pid} not found[/bold red]")
            raise click.Abort()
    elif process_name is not None:
        found_pid = find_process_by_name(process_name)
        if found_pid is None:
            console.print(f"[bold red]Could not find process matching '{process_name}'[/bold red]")
            raise click.Abort()
        try:
            process = psutil.Process(found_pid)
            process_pid = found_pid
            console.print(f"[bold green]Found process PID {found_pid} ({process.name()})[/bold green]")
        except psutil.NoSuchProcess:
            console.print(f"[bold red]Process {found_pid} not found[/bold red]")
            raise click.Abort()

    if process is not None:
        try:
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            last_memory = initial_memory
            start_time = time.time()
        except psutil.NoSuchProcess:
            console.print(f"[bold red]Process {process_pid} terminated[/bold red]")
            raise click.Abort()

    try:
        console.print("[bold blue]Memory Usage Monitor[/bold blue]")
        if process_pid:
            console.print(f"Process: PID {process_pid} ({process.name() if process else 'N/A'})")
        console.print(f"Update Interval: {interval:.1f}s")
        if duration > 0:
            console.print(f"Duration: {duration:.1f}s")
        console.print(f"Detailed Mode: {'Yes' if detailed else 'No'}")
        console.print("Press Ctrl+C to stop")
        console.print("-" * 40)

        def create_memory_display(
            memory_info: psutil.virtual_memory,
            swap_info: psutil.swap_memory,
            process_info: dict | None = None,
            shm_info: dict | None = None,
        ) -> Panel:
            """Create the memory usage display panel."""
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Metric", style="bold")
            table.add_column("Value", style="bold")
            table.add_column("Bar", style="bold")

            # Main memory usage
            mem_percent = memory_info.percent
            mem_bars = int(mem_percent * 50 / 100)
            mem_bar = "█" * min(mem_bars, 50)
            mem_color = "red" if mem_percent > 80 else "yellow" if mem_percent > 50 else "green"
            table.add_row("RAM", f"{mem_percent:.1f}%", f"[{mem_color}]{mem_bar:<50}[/{mem_color}]")

            # Memory details
            used_gb = memory_info.used / (1024**3)
            total_gb = memory_info.total / (1024**3)
            available_gb = memory_info.available / (1024**3)
            table.add_row("Used", f"{used_gb:.2f} GB", "")
            table.add_row("Total", f"{total_gb:.2f} GB", "")
            table.add_row("Available", f"{available_gb:.2f} GB", "")

            # Process-specific information
            if process_info:
                table.add_row("", "", "")  # Empty row for spacing
                proc_mem_mb = process_info["memory_mb"]
                proc_mem_gb = proc_mem_mb / 1024
                table.add_row("Process Memory", f"{proc_mem_gb:.2f} GB ({proc_mem_mb:.1f} MB)", "")
                if process_info["delta_mb"] is not None:
                    delta_color = "red" if process_info["delta_mb"] > 100 else "yellow" if process_info["delta_mb"] > 50 else "green"
                    delta_sign = "+" if process_info["delta_mb"] >= 0 else ""
                    table.add_row("Process Delta", f"[{delta_color}]{delta_sign}{process_info['delta_mb']:.1f} MB[/{delta_color}]", "")
                if process_info["threads"] is not None:
                    table.add_row("Threads", f"{process_info['threads']}", "")

            # Shared memory information
            if shm_info and shm_info["count"] > 0:
                table.add_row("", "", "")  # Empty row for spacing
                shm_total = format_bytes(shm_info["total_bytes"])
                table.add_row("[yellow]Shared Mem Buffers[/yellow]", f"[yellow]{shm_info['count']} ({shm_total})[/yellow]", "")

            # Swap usage
            table.add_row("", "", "")  # Empty row for spacing
            swap_percent = swap_info.percent
            swap_bars = int(swap_percent * 50 / 100)
            swap_bar = "█" * min(swap_bars, 50)
            swap_color = "red" if swap_percent > 80 else "yellow" if swap_percent > 50 else "green"
            table.add_row("Swap", f"{swap_percent:.1f}%", f"[{swap_color}]{swap_bar:<50}[/{swap_color}]")

            # Swap details
            swap_used_gb = swap_info.used / (1024**3)
            swap_total_gb = swap_info.total / (1024**3)
            table.add_row("Swap Used", f"{swap_used_gb:.2f} GB", "")
            table.add_row("Swap Total", f"{swap_total_gb:.2f} GB", "")

            if detailed:
                # Additional memory information
                table.add_row("", "", "")  # Empty row for spacing
                table.add_row("Cached", f"{memory_info.cached / (1024**3):.2f} GB", "")
                table.add_row("Buffers", f"{memory_info.buffers / (1024**3):.2f} GB", "")
                table.add_row("Shared", f"{memory_info.shared / (1024**3):.2f} GB", "")
                table.add_row("Slab", f"{memory_info.slab / (1024**3):.2f} GB", "")

            return Panel(table, title="[bold]Memory Usage[/bold]", border_style="blue")

        refresh_rate = max(1, int(1.0 / interval)) if interval > 0 else 2

        with Live(
            create_memory_display(psutil.virtual_memory(), psutil.swap_memory()),
            refresh_per_second=refresh_rate,
        ) as live:
            while True:
                try:
                    current_time = time.time()
                    if duration > 0 and start_time is not None and (current_time - start_time) >= duration:
                        break

                    # Get system memory information
                    memory_info = psutil.virtual_memory()
                    swap_info = psutil.swap_memory()

                    # Get process information if monitoring a process
                    process_info: dict | None = None
                    if process is not None:
                        try:
                            proc_mem_info = process.memory_info()
                            memory_mb = proc_mem_info.rss / 1024 / 1024
                            delta_mb = (memory_mb - initial_memory) if initial_memory is not None else None
                            thread_count = process.num_threads()

                            process_info = {
                                "memory_mb": memory_mb,
                                "delta_mb": delta_mb,
                                "threads": thread_count,
                            }

                            last_memory = memory_mb
                        except psutil.NoSuchProcess:
                            console.print(f"\n[bold red]Process {process_pid} terminated[/bold red]")
                            break

                    # Get shared memory information
                    shm_info = get_shared_memory_usage()

                    # Update display
                    live.update(create_memory_display(memory_info, swap_info, process_info, shm_info))

                    time.sleep(interval)

                except KeyboardInterrupt:
                    break

        # Final summary if monitoring a process
        if process is not None and initial_memory is not None and last_memory is not None and start_time is not None:
            console.print("\n" + "-" * 40)
            console.print("[bold]Monitoring Summary:[/bold]")
            elapsed = time.time() - start_time
            total_change = last_memory - initial_memory
            console.print(f"  Duration: {elapsed:.1f}s")
            console.print(f"  Initial memory: {initial_memory:.1f} MB")
            console.print(f"  Final memory: {last_memory:.1f} MB")
            console.print(f"  Total change: {total_change:+.1f} MB")
            if elapsed > 0:
                console.print(f"  Rate: {total_change / (elapsed / 60):.2f} MB/min")

            # Check shared memory for leaks
            shm_info = get_shared_memory_usage()
            if shm_info["count"] > 0:
                console.print(f"\n[bold yellow]Warning: {shm_info['count']} shared memory buffers still in /dev/shm:[/bold yellow]")
                for name, size in shm_info["buffers"]:
                    console.print(f"  - {name}: {format_bytes(size)}")

        console.print("\n[bold green]Memory monitoring stopped[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error during memory monitoring: {e}[/bold red]")
        raise click.Abort()
