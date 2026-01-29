"""
WowBits CLI Package

Command-line interface for managing agents, skills, connectors, and other WowBits resources.
"""

from .wowbits import main, create_parser
from .setup import run_setup

__all__ = [
    "run_setup",
]
