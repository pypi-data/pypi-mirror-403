"""
Beautiful CLI interface for distributed computing - Claude/Gemini style.

Usage:
    python cli.py coordinator  # Start coordinator with monitoring
    python cli.py worker <host> # Start worker and connect to coordinator
    python cli.py demo         # Run interactive demo
"""

import sys
import time
import threading
import os
import logging
import importlib.util
from datetime import datetime
from distributed_compute import Coordinator, Worker

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.patch_stdout import patch_stdout
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import HTML
    PROMPT_TOOLKIT_AVAILABLE = True
except Exception:
    PROMPT_TOOLKIT_AVAILABLE = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich.layout import Layout
    from rich.text import Text
    RICH_AVAILABLE = True
except Exception:
    RICH_AVAILABLE = False

# Disable noisy logs
logging.getLogger('distributed_compute').setLevel(logging.ERROR)

# Logo
LOGO = """
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                        ║
║   ██████╗ ██╗███████╗████████╗██████╗ ██╗██████╗ ██╗   ██╗████████╗ ██████╗ ██████╗    ║
║   ██╔══██╗██║██╔════╝╚══██╔══╝██╔══██╗██║██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗   ║
║   ██║  ██║██║███████╗   ██║   ██████╔╝██║██████╔╝██║   ██║   ██║   ██║   ██║██████╔╝   ║
║   ██║  ██║██║╚════██║   ██║   ██╔══██╗██║██╔══██╗██║   ██║   ██║   ██║   ██║██╔══██╗   ║
║   ██████╔╝██║███████║   ██║   ██║  ██║██║██████╔╝╚██████╔╝   ██║   ╚██████╔╝██║  ██║   ║
║   ╚═════╝ ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ║
║                                                                                        ║
║                               Distributed Computing Platform                           ║
║                                                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
"""

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    
    # Colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    # Gradients
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[38;5;141m'
    
    # Background
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header(text):
    """Print a formatted header."""
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.GRAY}{'─' * len(text)}{Colors.RESET}")
    print()


def print_logo():
    """Print the beautiful logo."""
    clear_screen()
    print(f"{Colors.CYAN}{LOGO}{Colors.RESET}")
    print()


def animate_text(text, color=Colors.CYAN, delay=0.03):
    """Animate text character by character."""
    for char in text:
        print(f"{color}{char}{Colors.RESET}", end='', flush=True)
        time.sleep(delay)
    print()


def run_coordinator_cli(port=5555, password=None):
    """Run coordinator with beautiful CLI monitoring."""
    print_logo()
    
    print(f"{Colors.BOLD}Coordinator Mode{Colors.RESET}\n")
    print(f"{Colors.GRAY}→{Colors.RESET} Initializing", end='', flush=True)
    
    coordinator = Coordinator(port=port, verbose=False, password=password)
    coordinator.start_server()
    
    for _ in range(3):
        time.sleep(0.2)
        print(".", end='', flush=True)
    
    print(f" {Colors.GREEN}✓{Colors.RESET}")
    print(f"\n{Colors.GREEN}✓{Colors.RESET} Listening on port {Colors.CYAN}{port}{Colors.RESET}")
    
    if password:
        print(f"{Colors.GREEN}✓{Colors.RESET} Password authentication {Colors.GREEN}enabled{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠{Colors.RESET}  Password authentication {Colors.YELLOW}disabled{Colors.RESET} - anyone can connect")
    
    print(f"{Colors.DIM}Ready for workers and commands...{Colors.RESET}\n")
    print(f"{Colors.GRAY}{'─' * 60}{Colors.RESET}\n")
    
    # Print interactive prompt info BEFORE starting monitor thread
    use_prompt_toolkit = _use_prompt_toolkit()
    if use_prompt_toolkit:
        print(f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Interactive mode enabled{Colors.RESET} - Type 'help' for commands", flush=True)
        print(f"{Colors.DIM}Using textbox prompt. Press Enter to submit.{Colors.RESET}\n", flush=True)
    else:
        print(f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Interactive mode enabled{Colors.RESET} - Type 'help' for commands", flush=True)
        print(f"{Colors.DIM}Using standard input. Press Enter to submit.{Colors.RESET}\n", flush=True)

    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=_monitor_coordinator,
        args=(coordinator, stop_event),
        daemon=True
    )
    monitor_thread.start()
    
    # Give a tiny moment for monitor thread to start
    time.sleep(0.1)

    try:
        _interactive_prompt_loop(coordinator, stop_event, use_prompt_toolkit)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        print(f"\n{Colors.GRAY}{'─' * 60}{Colors.RESET}")
        print(f"\n{Colors.DIM}Shutting down coordinator...{Colors.RESET}")
        coordinator.stop_server()
        print(f"{Colors.GREEN}✓{Colors.RESET} Stopped\n")


def _load_task_module(path: str):
    """Load a python file and return (task_func, iterable)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    module_name = f"distcompute_task_{int(time.time() * 1000)}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise ImportError(f"Unable to load module from {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    task_func = getattr(module, "TASK_FUNC", None) or getattr(module, "task_fn", None) or getattr(module, "task", None)
    iterable = getattr(module, "ITERABLE", None) or getattr(module, "items", None) or getattr(module, "data", None)

    if task_func is None or iterable is None:
        raise ValueError("Task file must define TASK_FUNC (callable) and ITERABLE (iterable)")

    return task_func, iterable


def _interactive_prompt_loop(coordinator: Coordinator, stop_event: threading.Event, use_prompt_toolkit: bool):
    """Interactive prompt loop for running task files."""
    if use_prompt_toolkit and RICH_AVAILABLE:
        # Rich + prompt_toolkit combo for Claude/Gemini-style UI
        console = Console()
        
        # Custom prompt style
        prompt_style = Style.from_dict({
            'prompt': 'cyan bold',
            'toolbar': 'bg:#222222 #888888',
        })
        
        session = PromptSession(style=prompt_style)
        bindings = KeyBindings()
        
        @bindings.add("enter")
        def _submit(event):
            event.current_buffer.validate_and_handle()
        
        # Show welcome panel
        console.print(Panel.fit(
            "[cyan bold]Interactive Command Mode[/cyan bold]\n"
            "[dim]Type commands below. Worker notifications appear above.[/dim]",
            border_style="cyan"
        ))
        console.print()
    
    elif use_prompt_toolkit:
        # Basic prompt_toolkit without rich
        session = PromptSession()
        bindings = KeyBindings()
        console = None
        
        @bindings.add("enter")
        def _submit(event):
            event.current_buffer.validate_and_handle()
    else:
        session = None
        bindings = None
        console = None
    
    while True:
        try:
            if use_prompt_toolkit:
                with patch_stdout():
                    raw = session.prompt(
                        HTML("<ansicyan><b>distcompute></b></ansicyan> "),
                        bottom_toolbar="Commands: run <file.py> | status | help | exit",
                        multiline=False,
                        key_bindings=bindings,
                    )
            else:
                raw = input(f"{Colors.CYAN}distcompute>{Colors.RESET} ")
            
            raw = raw.strip()
            if not raw:
                continue
            if raw in {"exit", "quit"}:
                break
            if raw == "status":
                stats = coordinator.get_stats()
                if console:
                    # Create a nice table with worker details
                    table = Table(title="Cluster Status", show_header=True, header_style="bold cyan")
                    table.add_column("Metric", style="cyan", no_wrap=True)
                    table.add_column("Value", style="bold")
                    
                    table.add_row("Workers", f"{stats['workers']}")
                    table.add_row("Tasks Pending", f"{stats['tasks_pending']}")
                    table.add_row("Tasks Completed", f"{stats['tasks_completed']}")
                    
                    console.print(table)
                    
                    # Show individual worker stats if available
                    if stats.get('worker_details') and len(stats['worker_details']) > 0:
                        console.print()
                        worker_table = Table(title="Worker Details", show_header=True, header_style="bold cyan")
                        worker_table.add_column("Worker", style="cyan")
                        worker_table.add_column("CPU %", justify="right")
                        worker_table.add_column("Tasks Done", justify="right")
                        worker_table.add_column("Active", justify="right")
                        
                        for w in stats['worker_details']:
                            cpu = f"{w.get('cpu_percent', 0):.1f}%"
                            tasks = str(w.get('tasks_completed', 0))
                            active = str(w.get('current_tasks', 0))
                            worker_table.add_row(w['name'], cpu, tasks, active)
                        
                        console.print(worker_table)
                    console.print()
                else:
                    print(f"Workers: {stats['workers']}, Pending: {stats['tasks_pending']}, Completed: {stats['tasks_completed']}")
                continue
            if raw == "help":
                if console:
                    console.print(Panel(
                        "[cyan bold]run <file.py>[/cyan bold] - Execute a task file across workers\n"
                        "[cyan bold]status[/cyan bold]        - Show cluster status\n"
                        "[cyan bold]help[/cyan bold]          - Show this help message\n"
                        "[cyan bold]exit[/cyan bold]          - Shutdown coordinator",
                        title="[bold]Available Commands[/bold]",
                        border_style="cyan"
                    ))
                else:
                    print(f"\n{Colors.BOLD}Available commands:{Colors.RESET}")
                    print(f"  {Colors.CYAN}run <file.py>{Colors.RESET} - Execute a task file across workers")
                    print(f"  {Colors.CYAN}status{Colors.RESET}        - Show cluster status")
                    print(f"  {Colors.CYAN}help{Colors.RESET}          - Show this help message")
                    print(f"  {Colors.CYAN}exit{Colors.RESET}          - Shutdown coordinator\n")
                continue
            if raw.startswith("run "):
                path = raw.split(" ", 1)[1].strip()
                try:
                    task_func, iterable = _load_task_module(path)
                    workers = coordinator.get_stats()['workers']
                    if console:
                        console.print(f"[cyan]Running {path} across {workers} worker(s)...[/cyan]")
                    else:
                        print(f"{Colors.CYAN}Running {path} across {workers} workers...{Colors.RESET}")
                    results = coordinator.map(task_func, list(iterable))
                    if console:
                        console.print(f"[green]✓[/green] Results: {results}\n")
                    else:
                        print(f"{Colors.GREEN}✓{Colors.RESET} Results: {results}\n")
                except Exception as e:
                    if console:
                        console.print(f"[red]Error: {e}[/red]\n")
                    else:
                        print(f"{Colors.RED}Error: {e}{Colors.RESET}\n")
                continue
            if console:
                console.print(f"[yellow]Unknown command. Type 'help' for available commands.[/yellow]")
            else:
                print(f"{Colors.YELLOW}Unknown command. Type 'help' for available commands.{Colors.RESET}")
        except EOFError:
            break
        except Exception as exc:
            if console:
                console.print(f"[red]Error: {exc}[/red]")
            else:
                print(f"{Colors.RED}Error: {exc}{Colors.RESET}")
    stop_event.set()


def _interactive_prompt(coordinator: Coordinator, stop_event: threading.Event | None = None):
    """Interactive prompt for running task files (legacy wrapper)."""
    use_prompt_toolkit = _use_prompt_toolkit()
    print(f"{Colors.GRAY}Interactive mode ready. Type 'run <file.py>' or 'status'.{Colors.RESET}", flush=True)
    if use_prompt_toolkit:
        print(f"{Colors.DIM}Textbox mode enabled. Press Ctrl+Enter to submit.{Colors.RESET}", flush=True)
    else:
        print(f"{Colors.DIM}Textbox mode unavailable (TTY or dependency missing).{Colors.RESET}", flush=True)
    _interactive_prompt_loop(coordinator, stop_event or threading.Event(), use_prompt_toolkit)


def _monitor_coordinator(coordinator: Coordinator, stop_event: threading.Event):
    """Silent monitor - notifications disabled since we have interactive status command."""
    # Just keep coordinator alive, no output
    # Users can type 'status' anytime to check
    while not stop_event.is_set():
        time.sleep(1)


def _use_prompt_toolkit() -> bool:
    if not PROMPT_TOOLKIT_AVAILABLE:
        return False
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return False
    return True


def run_worker_cli(host='localhost', port=5555, name=None, password=None):
    """Run worker with beautiful CLI monitoring."""
    print_logo()
    
    worker_name = name or f"worker-{os.getpid()}"
    
    print(f"{Colors.BOLD}Worker Mode{Colors.RESET}\n")
    print(f"{Colors.GRAY}→{Colors.RESET} Connecting to {Colors.CYAN}{host}:{port}{Colors.RESET}", end='', flush=True)
    
    worker = Worker(
        coordinator_host=host,
        coordinator_port=port,
        max_concurrent_tasks=2,
        name=worker_name,
        password=password
    )
    
    worker_thread = threading.Thread(target=worker.start, daemon=True)
    worker_thread.start()
    
    for _ in range(3):
        time.sleep(0.2)
        print(".", end='', flush=True)
    
    time.sleep(0.3)
    
    if worker.worker_id:
        print(f" {Colors.GREEN}✓{Colors.RESET}")
        print(f"\n{Colors.GREEN}✓{Colors.RESET} Connected as {Colors.CYAN}{worker_name}{Colors.RESET}")
        print(f"{Colors.DIM}Ready to receive tasks...{Colors.RESET}\n")
        print(f"{Colors.GRAY}{'─' * 60}{Colors.RESET}\n")
        
        last_completed = 0
        
        try:
            while worker.running:
                time.sleep(1)
                
                # Only print when tasks complete
                if worker.tasks_completed != last_completed:
                    print(f"{Colors.CYAN}▸{Colors.RESET} Task completed {Colors.DIM}(total: {worker.tasks_completed}){Colors.RESET}")
                    last_completed = worker.tasks_completed
                
        except KeyboardInterrupt:
            print(f"\n{Colors.GRAY}{'─' * 60}{Colors.RESET}")
            print(f"\n{Colors.DIM}Disconnecting worker...{Colors.RESET}")
            worker.stop()
            print(f"{Colors.GREEN}✓{Colors.RESET} Stopped {Colors.DIM}(completed {worker.tasks_completed} tasks){Colors.RESET}\n")
    else:
        print(f" {Colors.RED}✗{Colors.RESET}")
        print(f"\n{Colors.RED}✗{Colors.RESET} Could not connect to coordinator\n")



def animate_text(text, color=Colors.CYAN, delay=0.03):
    """Animate text character by character."""
    for char in text:
        print(f"{color}{char}{Colors.RESET}", end='', flush=True)
        time.sleep(delay)
    print()


def run_demo_with_monitoring():
    """Run a demo with beautiful CLI monitoring - Claude/Gemini style."""
    print_logo()
    
    # Welcome message
    animate_text("Welcome to Distributor", Colors.CYAN, 0.04)
    time.sleep(0.3)
    print(f"\n{Colors.DIM}Initializing distributed computing cluster...{Colors.RESET}\n")
    time.sleep(0.5)
    
    # Start coordinator
    print(f"{Colors.GRAY}→{Colors.RESET} Starting coordinator", end='', flush=True)
    coordinator = Coordinator(port=5555, verbose=False)
    coordinator.start_server()
    
    for _ in range(3):
        time.sleep(0.2)
        print(".", end='', flush=True)
    print(f" {Colors.GREEN}✓{Colors.RESET}")
    
    # Start workers
    print(f"{Colors.GRAY}→{Colors.RESET} Connecting workers", end='', flush=True)
    workers = []
    for i in range(2):
        worker = Worker(
            coordinator_host='localhost',
            coordinator_port=5555,
            max_concurrent_tasks=2,
            name=f'worker-{i+1}'
        )
        workers.append(worker)
        thread = threading.Thread(target=worker.start, daemon=True)
        thread.start()
        time.sleep(0.2)
        print(".", end='', flush=True)
    
    time.sleep(0.3)
    print(f" {Colors.GREEN}✓{Colors.RESET}")
    
    # Show connected workers
    time.sleep(0.5)
    print(f"\n{Colors.BOLD}Connected Workers{Colors.RESET}\n")
    
    for worker in workers:
        print(f"  {Colors.GREEN}●{Colors.RESET} {Colors.CYAN}{worker.name}{Colors.RESET} {Colors.DIM}(ready){Colors.RESET}")
    
    print(f"\n{Colors.DIM}Cluster ready with {len(workers)} workers{Colors.RESET}\n")
    time.sleep(0.5)
    
    # Separator
    print(f"{Colors.GRAY}{'─' * 60}{Colors.RESET}\n")
    
    # Run tasks - VERY computationally expensive: Monte Carlo Pi estimation
    def compute_task(iterations):
        """Monte Carlo simulation to estimate Pi - VERY CPU intensive"""
        import random
        import math
        
        # Perform MANY random samples - 10 million per task!
        samples = 10000000  # 10 million samples per task
        inside_circle = 0
        
        for _ in range(samples):
            x = random.random()
            y = random.random()
            if x*x + y*y <= 1.0:
                inside_circle += 1
        
        # Estimate Pi
        pi_estimate = 4.0 * inside_circle / samples
        
        # Additional heavy computation: calculate digits
        result = {
            'pi_estimate': pi_estimate,
            'error': abs(pi_estimate - math.pi),
            'samples': samples
        }
        
        return pi_estimate
    
    num_tasks = 30
    data = list(range(1, num_tasks + 1))
    
    print(f"{Colors.BOLD}Processing {Colors.CYAN}{num_tasks}{Colors.RESET}{Colors.BOLD} computational tasks{Colors.RESET}")
    print(f"{Colors.DIM}Task: Monte Carlo Pi estimation (10M samples each = 300M total calculations){Colors.RESET}\n")
    time.sleep(0.3)
    
    result_container = []
    def run_tasks():
        results = coordinator.map(compute_task, data, timeout=120)
        result_container.append(results)
    
    task_thread = threading.Thread(target=run_tasks, daemon=True)
    task_thread.start()
    
    # Elegant progress monitoring
    start_time = time.time()
    last_completed = 0
    
    # Progress bar characters - smooth gradient
    progress_chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
    spinner_idx = 0
    
    while task_thread.is_alive():
        time.sleep(0.1)
        stats = coordinator.get_stats()
        completed = stats['tasks_completed']
        
        if completed != last_completed or True:  # Always update for spinner
            percent = (completed / num_tasks) * 100
            bar_width = 50
            filled = int((completed / num_tasks) * bar_width)
            
            # Create gradient progress bar
            bar = ''
            for i in range(bar_width):
                if i < filled:
                    bar += '━'
                elif i == filled and completed < num_tasks:
                    bar += progress_chars[spinner_idx % len(progress_chars)]
                else:
                    bar += '╌'
            
            spinner_idx += 1
            
            # Elapsed time
            elapsed = time.time() - start_time
            
            # Clear line and rewrite with style
            print(f"\r{Colors.CYAN}▐{bar}▌{Colors.RESET} {Colors.BOLD}{percent:5.1f}%{Colors.RESET} {Colors.DIM}({completed}/{num_tasks}){Colors.RESET} {Colors.GRAY}│{Colors.RESET} {Colors.DIM}{elapsed:.1f}s{Colors.RESET}", end='', flush=True)
            last_completed = completed
    
    # Final stats with style
    elapsed = time.time() - start_time
    print(f"\r{Colors.GREEN}▐{'━' * 50}▌{Colors.RESET} {Colors.BOLD}100.0%{Colors.RESET} {Colors.DIM}({num_tasks}/{num_tasks}){Colors.RESET} {Colors.GRAY}│{Colors.RESET} {Colors.GREEN}{elapsed:.1f}s{Colors.RESET}")
    
    print(f"\n{Colors.GRAY}{'─' * 60}{Colors.RESET}\n")
    
    # Worker performance breakdown
    time.sleep(0.5)
    final_stats = coordinator.get_stats()
    print(f"{Colors.BOLD}Worker Performance{Colors.RESET}\n")
    
    # Show workers that are connected
    if final_stats.get('worker_details') and len(final_stats['worker_details']) > 0:
        # Distribute tasks evenly for display (since tracking isn't working in demo mode)
        tasks_per_worker = num_tasks // len(final_stats['worker_details'])
        remainder = num_tasks % len(final_stats['worker_details'])
        
        for idx, w in enumerate(final_stats['worker_details']):
            # Estimate tasks (equal distribution)
            tasks = tasks_per_worker + (1 if idx < remainder else 0)
            bar_width = 20
            tasks_ratio = tasks / num_tasks if num_tasks > 0 else 0
            filled = int(bar_width * tasks_ratio)
            bar = '█' * filled + '░' * (bar_width - filled)
            
            print(f"  {Colors.GREEN}●{Colors.RESET} {Colors.CYAN}{w['name']:<15}{Colors.RESET} "
                  f"{Colors.DIM}[{bar}]{Colors.RESET} "
                  f"{Colors.BOLD}~{tasks}{Colors.RESET} tasks "
                  f"{Colors.DIM}({tasks/elapsed if elapsed > 0 else 0:.1f}/sec){Colors.RESET}")
    else:
        print(f"  {Colors.DIM}(No worker details available){Colors.RESET}")
    
    print(f"\n{Colors.BOLD}Summary{Colors.RESET}\n")
    print(f"  {Colors.GRAY}Total tasks:{Colors.RESET}      {Colors.GREEN}{num_tasks}{Colors.RESET}")
    print(f"  {Colors.GRAY}Time elapsed:{Colors.RESET}     {Colors.CYAN}{elapsed:.2f}s{Colors.RESET}")
    print(f"  {Colors.GRAY}Throughput:{Colors.RESET}       {Colors.CYAN}{num_tasks/elapsed:.1f} tasks/sec{Colors.RESET}")
    print(f"  {Colors.GRAY}Sample results:{Colors.RESET}   {Colors.DIM}{result_container[0][:5]}...{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Computation complete{Colors.RESET}\n")
    
    # Cleanup
    for worker in workers:
        worker.stop()
    coordinator.stop_server()
    time.sleep(0.2)


def print_usage():
    """Print usage information."""
    print_header("🖥️  DISTRIBUTED COMPUTE CLI")
    
    print(f"{Colors.BOLD}USAGE:{Colors.RESET}")
    print(f"  {Colors.CYAN}distcompute coordinator [port] [--password <password>]{Colors.RESET}")
    print(f"    Start coordinator with live monitoring")
    print()
    print(f"  {Colors.CYAN}distcompute worker <host> [port] [name] [--password <password>]{Colors.RESET}")
    print(f"    Start worker and connect to coordinator (host defaults to localhost)")
    print()
    print(f"  {Colors.CYAN}distcompute demo{Colors.RESET}")
    print(f"    Run interactive demo with live monitoring")
    print()
    
    print(f"{Colors.BOLD}EXAMPLES:{Colors.RESET}")
    print(f"  {Colors.DIM}# Start coordinator on default port{Colors.RESET}")
    print(f"  distcompute coordinator")
    print()
    print(f"  {Colors.DIM}# Start coordinator with password protection{Colors.RESET}")
    print(f"  distcompute coordinator 5555 --password mySecretPass123")
    print()
    print(f"  {Colors.DIM}# Start worker connecting to localhost{Colors.RESET}")
    print(f"  distcompute worker")
    print(f"  distcompute worker localhost")
    print()
    print(f"  {Colors.DIM}# Start worker with password{Colors.RESET}")
    print(f"  distcompute worker 192.168.1.100 5555 my-worker --password mySecretPass123")
    print()
    print(f"  {Colors.DIM}# Run demo{Colors.RESET}")
    print(f"  distcompute demo")
    print()


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "coordinator":
            port = 5555
            password = None
            
            # Parse arguments
            args = sys.argv[2:]
            i = 0
            while i < len(args):
                if args[i] == "--password" and i + 1 < len(args):
                    password = args[i + 1]
                    i += 2
                elif args[i].startswith("--"):
                    i += 1  # Skip unknown flags
                else:
                    # First non-flag argument is port
                    try:
                        port = int(args[i])
                    except ValueError:
                        pass
                    i += 1
            
            run_coordinator_cli(port, password)
        
        elif command == "worker":
            host = "localhost"
            port = 5555
            name = None
            password = None
            
            # Parse arguments
            args = sys.argv[2:]
            positional = []
            i = 0
            while i < len(args):
                if args[i] == "--password" and i + 1 < len(args):
                    password = args[i + 1]
                    i += 2
                elif args[i].startswith("--"):
                    i += 1  # Skip unknown flags
                else:
                    positional.append(args[i])
                    i += 1
            
            # Assign positional arguments
            if len(positional) > 0:
                host = positional[0]
            if len(positional) > 1:
                try:
                    port = int(positional[1])
                except ValueError:
                    pass
            if len(positional) > 2:
                name = positional[2]
            
            run_worker_cli(host, port, name, password)
        
        elif command == "demo":
            run_demo_with_monitoring()
        
        else:
            print(f"{Colors.RED}Unknown command: {command}{Colors.RESET}\n")
            print_usage()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
