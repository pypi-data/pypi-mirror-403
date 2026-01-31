"""
Hexarch Admin CLI (hexarch-ctl)

Operational command-line interface for managing policies, querying decisions, 
and monitoring provider performance metrics.

Version: 0.3.0
"""

__version__ = "0.3.1"
__author__ = "Noir Stack LLC"
__license__ = "MIT"

from hexarch_cli.cli import cli

__all__ = ["cli"]
