"""
FinVista Command Line Interface.

Usage:
    finvista quote <symbols>...
    finvista history <symbol> [--start=<date>] [--end=<date>]
    finvista search <keyword>
    finvista health
"""

from finvista.cli.main import cli_entry, main

__all__ = ["main", "cli_entry"]
