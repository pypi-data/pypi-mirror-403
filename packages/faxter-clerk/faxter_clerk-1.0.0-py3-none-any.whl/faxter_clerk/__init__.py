"""
Faxter Clerk - Command-line interface for the Accounting OS.

This package provides a user-friendly CLI for interacting with the AI Accounting
system using natural language. It supports OTP authentication, file uploads,
real-time progress updates, and multi-format outputs.

Talk to your books like you're texting a friend.
"""

from .clerk import AccountingChatCLI

__version__ = "1.0.0"
__all__ = ["AccountingChatCLI"]
