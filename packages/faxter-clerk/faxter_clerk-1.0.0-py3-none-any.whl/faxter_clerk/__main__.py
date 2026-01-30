"""
Entry point for running the CLI as a module.

This allows running the CLI using:
    python -m faxter_clerk
"""

from .clerk import main

if __name__ == "__main__":
    main()
