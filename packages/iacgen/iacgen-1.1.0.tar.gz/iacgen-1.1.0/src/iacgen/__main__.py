"""
Entry point for running iacgen as a module.

Enables usage: python -m iacgen <command> [options]
"""

from iacgen.cli import app

if __name__ == "__main__":
    app()
