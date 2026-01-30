"""Utility functions for internal use."""

from harmony_client import StringThread


def stringify_thread(thread: StringThread, sep: str = "\n\n") -> str:
    """Convert StringThread to readable text format."""
    turns = thread.get_turns()
    return sep.join([f"[{turn.role}]\n{turn.content}" for turn in turns])
