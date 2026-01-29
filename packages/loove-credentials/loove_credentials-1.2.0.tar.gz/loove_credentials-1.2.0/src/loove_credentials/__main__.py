"""
Allow running the credential CLI as a module.

Usage:
    python -m integration_validation.credential status
    python -m integration_validation.credential verify
    python -m integration_validation.credential setup
"""

from .cli import main

if __name__ == "__main__":
    exit(main())
