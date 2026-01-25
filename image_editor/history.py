class HistoryManager:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    def push(self, image):
        if image is None:
            return
        self.undo_stack.append(image.copy())
        self.redo_stack.clear()

    def undo(self, current_image):
        if not self.undo_stack or current_image is None:
            return current_image
        self.redo_stack.append(current_image.copy())
        return self.undo_stack.pop()

    def redo(self, current_image):
        if not self.redo_stack or current_image is None:
            return current_image
        self.undo_stack.append(current_image.copy())
        return self.redo_stack.pop()
