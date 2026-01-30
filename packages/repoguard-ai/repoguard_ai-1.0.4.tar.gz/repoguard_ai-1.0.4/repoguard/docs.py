from pathlib import Path
from typing import Optional
from repoguard.repo import get_repo_root

def find_file(prefix: str) -> Optional[str]:
    repo_root = get_repo_root()
    prefix = prefix.lower()

    for path in repo_root.iterdir():
        if path.is_file() and path.name.lower().startswith(prefix):
            return path.read_text(encoding="utf-8")

    return None


def load_repo_docs():
    readme = find_file("readme")
    contributing = find_file("contributing")
    coc = find_file("code_of_conduct")

    if not readme or not contributing:
        raise RuntimeError(
            "README and CONTRIBUTING files are required (case-insensitive)"
        )

    return readme, contributing, coc
