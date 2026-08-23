"""
Command Pattern Undo/Redo Manager for Timeline Editor
"""

from typing import Callable, Any


class Command:
    def __init__(self, description: str, execute_fn: Callable, undo_fn: Callable):
        self.description = description
        self.execute_fn = execute_fn
        self.undo_fn = undo_fn

    def execute(self):
        self.execute_fn()

    def undo(self):
        self.undo_fn()


class UndoManager:
    """Manages reversible actions with history stack."""

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []

    def execute_command(self, command: Command):
        command.execute()
        self._undo_stack.append(command)
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def undo(self) -> str:
        if not self.can_undo():
            return ""
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        return cmd.description

    def redo(self) -> str:
        if not self.can_redo():
            return ""
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        return cmd.description

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
