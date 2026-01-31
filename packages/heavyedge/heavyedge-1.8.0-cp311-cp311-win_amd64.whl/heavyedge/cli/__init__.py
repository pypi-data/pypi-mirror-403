"""Command line interface tools."""

__all__ = [
    "register_command",
    "Command",
    "ConfigArgumentParser",
    "deprecate_command",
]

from .command import Command, deprecate_command, register_command
from .parser import ConfigArgumentParser
