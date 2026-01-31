"""
CLI wrapper for the afm binary.

This module provides the entry point for the `afm` command when installed via pip.
It locates and executes the native macOS binary bundled with the package.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


def get_binary_path() -> Path:
    """
    Get the path to the afm binary.

    Returns:
        Path to the afm binary

    Raises:
        RuntimeError: If the binary is not found or platform is unsupported
    """
    if platform.system() != "Darwin":
        raise RuntimeError(
            "macafm is only supported on macOS. "
            "Apple Foundation Models require macOS 26+ on Apple Silicon."
        )

    # Check architecture
    machine = platform.machine()
    if machine not in ("arm64", "aarch64"):
        raise RuntimeError(
            f"macafm requires Apple Silicon (arm64). "
            f"Detected architecture: {machine}"
        )

    # Binary is in the bin/ subdirectory of this package
    package_dir = Path(__file__).parent
    binary_path = package_dir / "bin" / "afm"

    if not binary_path.exists():
        raise RuntimeError(
            f"afm binary not found at {binary_path}. "
            "The package may not have been installed correctly. "
            "Try reinstalling: pip install --force-reinstall macafm"
        )

    if not os.access(binary_path, os.X_OK):
        raise RuntimeError(
            f"afm binary at {binary_path} is not executable. "
            "Try reinstalling: pip install --force-reinstall macafm"
        )

    return binary_path


def main() -> int:
    """
    Main entry point for the afm command.

    Passes all arguments through to the native afm binary.

    Returns:
        Exit code from the afm binary
    """
    try:
        binary_path = get_binary_path()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Pass all arguments to the binary
    args = [str(binary_path)] + sys.argv[1:]

    # Execute the binary, replacing this process
    # Use subprocess for better signal handling
    try:
        result = subprocess.run(args, stdin=sys.stdin)
        return result.returncode
    except KeyboardInterrupt:
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Error running afm: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
