import subprocess
from pathlib import Path

def get_repo_root() -> Path:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return Path(root)
    except Exception:
        raise RuntimeError("Not inside a git repository")

def get_repo_id() -> str:
    try:
        return subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        raise RuntimeError("Not a git repository or no remote origin found")