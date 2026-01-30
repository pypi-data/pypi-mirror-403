import subprocess

def get_diff():
    result = subprocess.run(
        ["git", "diff"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError("Failed to get git diff")

    return result.stdout
