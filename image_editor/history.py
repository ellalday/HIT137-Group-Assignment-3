# HistoryManager class for undo/redo functionality
class HistoryManager:
    def __init__(self):
        """Initialize undo and redo stacks"""
        self.undo_stack = []
        self.redo_stack = []

    def push(self, state):
        """Add a state to the undo stack and clear redo stack."""
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def undo(self):
        """Restore previous state."""
        if len(self.undo_stack) < 2:
            return None
        current = self.undo_stack.pop()
        self.redo_stack.append(current)
        return self.undo_stack[-1]

    def redo(self):
        """Reapply previously undone state."""
        if not self.redo_stack:
            return None
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        return state

    def clear(self):
        """Clear all history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
