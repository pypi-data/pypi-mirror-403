"""
介面層 - 統一命令抽象
提供 MCP 和 CLI 的統一命令介面
"""

from .base_command import BaseCommand, CommandResult
from .command_registry import CommandRegistry, get_command_registry, register_command
from .formatters import Formatter, JsonFormatter, ConsoleFormatter, get_formatter

# 匯入所有命令以觸發自動註冊
from . import commands

__all__ = [
    "BaseCommand",
    "CommandResult",
    "CommandRegistry",
    "get_command_registry",
    "register_command",
    "Formatter",
    "JsonFormatter",
    "ConsoleFormatter",
    "get_formatter",
    "commands",
]
