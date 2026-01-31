"""Moti - Automatically runs run.py in background on import."""

import os
import sys
import subprocess

__version__ = "0.1.0"


def _run_background():
    """Run run.py in background if it exists in current directory."""
    cwd = os.getcwd()
    run_py_path = os.path.join(cwd, "run.py")
    
    if not os.path.exists(run_py_path):
        return
    
    # Check if already running (use a simple lock file)
    lock_file = os.path.join(cwd, ".moti.lock")
    
    # Check if process is already running
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r") as f:
                pid = int(f.read().strip())
            # Check if process still exists
            os.kill(pid, 0)  # Doesn't kill, just checks
            return  # Already running
        except (ProcessLookupError, ValueError, FileNotFoundError):
            pass  # Process not running, continue
    
    python_executable = sys.executable
    
    if sys.platform == "win32":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        proc = subprocess.Popen(
            [python_executable, run_py_path],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    else:
        proc = subprocess.Popen(
            [python_executable, run_py_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    
    # Save PID to lock file
    with open(lock_file, "w") as f:
        f.write(str(proc.pid))


# Auto-run on import
_run_background()

