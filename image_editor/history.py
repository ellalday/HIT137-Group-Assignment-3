import cv2


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
        """Pop from undo stack and push to redo stack."""
        if not self.undo_stack:
            return None
        state = self.undo_stack.pop()
        self.redo_stack.append(state)
        return self.undo_stack[-1] if self.undo_stack else None

    def redo(self):
        """Pop from redo stack and push to undo stack."""
        if not self.redo_stack:
            return None
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        return state

    def clear(self):
        """Clear all history."""
        self.undo_stack.clear()
        self.redo_stack.clear()


# ImageProcessor class for image manipulation
class ImageProcessor:
    def __init__(self):
        """Initialize image processor"""
        self.image = None

    def set_image(self, image):
        """Set the image to process"""
        self.image = image

    def get_image(self):
        """Get the processed image"""
        return self.image

    # ---- FILTERS ----

    def grayscale(self):
        """Convert image to grayscale"""
        if self.image is not None:
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def rotate(self, angle):
        """Rotate image by specified angle (90, 180, 270)"""
        if self.image is None:
            return

        if angle == 90:
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            self.image = cv2.rotate(self.image, cv2.ROTATE_180)
        elif angle == 270:
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    def flip(self, mode):
        """Flip image horizontally or vertically"""
        if self.image is None:
            return

        if mode == "horizontal":
            self.image = cv2.flip(self.image, 1)
        elif mode == "vertical":
            self.image = cv2.flip(self.image, 0)

    def blur(self, intensity):
        """Apply Gaussian blur with specified intensity"""
        if self.image is None:
            return

        intensity = int(intensity)
        if intensity <= 0:
            return

        k = intensity * 2 + 1
        self.image = cv2.GaussianBlur(self.image, (k, k), 0)

    def brightness(self, value):
        """Adjust brightness of image"""
        if self.image is None:
            return

        value = float(value)
        img = self.image.astype("float32")
        img = img + value
        img = img.clip(0, 255)
        self.image = img.astype("uint8")

    def contrast(self, alpha):
        """Adjust contrast of image"""
        if self.image is None:
            return

        alpha = float(alpha)
        img = self.image.astype("float32")
        img = 128 + alpha * (img - 128)
        img = img.clip(0, 255)
        self.image = img.astype("uint8")

    def edge_detection(self, low=100, high=200):
        """
        Apply Canny edge detection.
        Converts to grayscale first if needed.
        """
        if self.image is None:
            return

        if len(self.image.shape) == 3:
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        else:
            gray = self.image

        edges = cv2.Canny(gray, int(low), int(high))
        self.image = edges

    def resize(self, width, height):
        """
        Resize image to exact width/height.
        """
        if self.image is None:
            return

        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            return

        self.image = cv2.resize(self.image, (width, height), interpolation=cv2.INTER_AREA)