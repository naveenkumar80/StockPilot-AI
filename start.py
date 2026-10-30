#!/usr/bin/env python3
"""
StockPilot AI — Unified Development Server Launcher
Launches both the FastAPI backend and Next.js frontend concurrently with a single command,
unified color-coded logging, health monitoring, and graceful teardown on Ctrl+C.

Usage:
    python start.py
    python start.py --open     (automatically opens the browser when ready)
"""

import os
import sys
import time
import signal
import socket
import argparse
import platform
import subprocess
import threading
import urllib.request
import webbrowser

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
DIM = "\033[2m"

# Windows VT100 color support
if platform.system() == "Windows":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks whether a TCP port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def stream_output(process: subprocess.Popen, prefix: str, color: str):
    """Streams child process stdout/stderr line-by-line with color-coded prefix."""
    try:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            clean_line = line.rstrip()
            if clean_line:
                print(f"{color}{BOLD}{prefix}{RESET} {clean_line}", flush=True)
    except (ValueError, OSError):
        pass


def kill_process_tree(proc: subprocess.Popen):
    """Forcefully and cleanly kills process and any child processes spawned by it."""
    if proc is None or proc.poll() is not None:
        return

    pid = proc.pid
    if platform.system() == "Windows":
        try:
            # /F = force, /T = terminate entire process tree, /PID = target pid
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass


def wait_for_health(url: str, timeout: int = 25) -> bool:
    """Polls backend health check until it responds 200 OK."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StockPilot-HealthCheck"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(description="StockPilot AI Unified Service Runner")
    parser.add_argument("--open", "-o", action="store_true", help="Automatically open browser when web app is ready")
    parser.add_argument("--backend-port", type=int, default=8000, help="Port for FastAPI backend (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=3000, help="Port for Next.js frontend (default: 3000)")
    args = parser.parse_args()

    root_dir = os.path.abspath(os.path.dirname(__file__))
    web_dir = os.path.join(root_dir, "apps", "web")
    api_dir = os.path.join(root_dir, "services", "api")

    # Banner
    print(f"""
{CYAN}{BOLD}================================================================={RESET}
{CYAN}{BOLD}  StockPilot AI — Unified Development Environment               {RESET}
{DIM}  Quantitative Forecasting & Paper Trading Platform for Indian Equities{RESET}
{CYAN}{BOLD}================================================================={RESET}
""")

    # Check port availability
    if is_port_in_use(args.backend_port):
        print(f"{YELLOW}Warning: Port {args.backend_port} is already in use. Terminating existing process or using another port may be necessary.{RESET}")
    if is_port_in_use(args.frontend_port):
        print(f"{YELLOW}Warning: Port {args.frontend_port} is already in use. Next.js will likely prompt to use port 3001.{RESET}")

    # Prepare environment variables
    backend_env = os.environ.copy()
    existing_pythonpath = backend_env.get("PYTHONPATH", "")
    separator = ";" if platform.system() == "Windows" else ":"
    backend_env["PYTHONPATH"] = f"{root_dir}{separator}{api_dir}{separator}{existing_pythonpath}"

    frontend_env = os.environ.copy()
    frontend_env["NEXT_PUBLIC_API_URL"] = f"http://localhost:{args.backend_port}/api/v1"
    frontend_env["PORT"] = str(args.frontend_port)

    # 1. Start Backend (FastAPI via Uvicorn)
    print(f"{CYAN}{BOLD}[1/2] Starting FastAPI Backend on port {args.backend_port}...{RESET}")
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "services/api",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.backend_port),
        "--reload",
        "--reload-dir",
        os.path.join(root_dir, "services", "api"),
    ]

    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=root_dir,
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    t_api = threading.Thread(
        target=stream_output,
        args=(backend_proc, "[API]", CYAN),
        daemon=True,
    )
    t_api.start()

    # 2. Start Frontend (Next.js)
    print(f"{GREEN}{BOLD}[2/2] Starting Next.js Web Frontend on port {args.frontend_port}...{RESET}")
    frontend_cmd = ["npm", "run", "dev"]

    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=web_dir,
        env=frontend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=(platform.system() == "Windows"),
    )

    t_web = threading.Thread(
        target=stream_output,
        args=(frontend_proc, "[WEB]", GREEN),
        daemon=True,
    )
    t_web.start()

    # Wait for backend health probe in background
    def announce_ready():
        health_url = f"http://127.0.0.1:{args.backend_port}/api/v1/health"
        if wait_for_health(health_url, timeout=20):
            time.sleep(1.0)
            print(f"""
{GREEN}{BOLD}-----------------------------------------------------------------{RESET}
{GREEN}{BOLD}  SUCCESS: Both StockPilot AI services are running!              {RESET}
{GREEN}{BOLD}-----------------------------------------------------------------{RESET}
  {BOLD}• Web Dashboard:{RESET}    {GREEN}http://localhost:{args.frontend_port}{RESET}
  {BOLD}• Backend API:{RESET}      {CYAN}http://127.0.0.1:{args.backend_port}/api/v1{RESET}
  {BOLD}• Interactive Docs:{RESET} {CYAN}http://127.0.0.1:{args.backend_port}/docs{RESET}
{DIM}  Press Ctrl+C in this terminal to safely stop all services.{RESET}
{GREEN}{BOLD}-----------------------------------------------------------------{RESET}
""")
            if args.open:
                try:
                    webbrowser.open(f"http://localhost:{args.frontend_port}")
                except Exception:
                    pass

    t_ready = threading.Thread(target=announce_ready, daemon=True)
    t_ready.start()

    # Clean shutdown handler
    def handle_exit(sig=None, frame=None):
        print(f"\n{YELLOW}{BOLD}Shutting down StockPilot AI services...{RESET}")
        kill_process_tree(backend_proc)
        kill_process_tree(frontend_proc)
        print(f"{GREEN}All services stopped cleanly. Goodbye!{RESET}")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Keep main thread alive monitoring children
    try:
        while True:
            if backend_proc.poll() is not None:
                print(f"{RED}[API] Backend process terminated unexpectedly with code {backend_proc.poll()}{RESET}")
                handle_exit()
                break
            if frontend_proc.poll() is not None:
                print(f"{RED}[WEB] Frontend process terminated with code {frontend_proc.poll()}{RESET}")
                handle_exit()
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        handle_exit()


if __name__ == "__main__":
    main()

