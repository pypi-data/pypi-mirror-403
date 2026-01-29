"""
CLI wrapper for polydup binary.

This module locates and executes the bundled polydup binary,
providing a seamless CLI experience after `pip install polydup`.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def _find_binary() -> Path:
    """
    Locate the polydup binary.

    Search order:
    1. Same bin directory as Python executable (typical for pip-installed scripts)
    2. System PATH (fallback for cargo-installed binary)

    Returns:
        Path to the polydup binary

    Raises:
        FileNotFoundError: If binary cannot be found
    """
    binary_name = "polydup.exe" if sys.platform == "win32" else "polydup"

    # Check bin directory alongside Python executable
    # This is where pip installs scripts from wheel's .data/scripts/
    python_bin = Path(sys.executable).parent
    candidate = python_bin / binary_name
    if candidate.exists():
        return candidate

    # Check PATH (fallback for cargo-installed binary)
    path_binary = shutil.which(binary_name)
    if path_binary:
        return Path(path_binary)

    raise FileNotFoundError(
        f"Could not find '{binary_name}' binary. "
        "The package may not have been installed correctly. "
        "Try reinstalling with: pip install --force-reinstall polydup"
    )


def main() -> int:
    """
    Execute the polydup CLI binary with all provided arguments.

    Returns:
        Exit code from the binary (0 = success, 1 = duplicates found, 2 = error)
    """
    try:
        binary = _find_binary()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    try:
        result = subprocess.run(
            [str(binary)] + sys.argv[1:],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return result.returncode
    except KeyboardInterrupt:
        return 130  # Standard exit code for SIGINT
    except OSError as e:
        print(f"Error executing polydup: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
