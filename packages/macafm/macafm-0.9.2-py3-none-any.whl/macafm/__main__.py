"""
Allow running the package as a module: python -m macafm
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
