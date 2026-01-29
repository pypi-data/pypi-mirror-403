"""
CLI wrapper for Lumecode.
Provides the `lumecode` command when installed via pip.
"""

import os
import sys
import subprocess

from .installer import ensure_installed, get_binary_path


def main():
    """Main entry point for the lumecode CLI."""
    try:
        # Ensure binary is installed
        binary_path = ensure_installed()
        
        # Forward all arguments to the Go binary
        result = subprocess.run(
            [str(binary_path)] + sys.argv[1:],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
