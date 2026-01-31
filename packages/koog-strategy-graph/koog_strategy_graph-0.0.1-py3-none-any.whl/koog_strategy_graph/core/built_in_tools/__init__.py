"""
Safe, minimal built-in tools.

These are intentionally conservative (no filesystem/network by default).
"""

from .echo import echo_tool
from .time import utc_now_tool

__all__ = ["echo_tool", "utc_now_tool"]

