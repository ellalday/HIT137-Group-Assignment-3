"""Processor - documentation note

- Added brief file-level description for readability (docs/processor-comments)
"""

import cv2


class ImageProcessor:
    def __init__(self):
        self.image = None

    def set_image(self, image):
        self.image = image

    def get_image(self):
        return self.image

    # ---------------- FILTERS ----------------

    def grayscale(self):
        if self.image is not None:
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def rotate(self, angle):
        if self.image is None:
            return

        if angle == 90:
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            self.image = cv2.rotate(self.image, cv2.ROTATE_180)
        elif angle == 270:
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    def flip(self, mode):
        if self.image is None:
            return

        if mode == "horizontal":
            self.image = cv2.flip(self.image, 1)
        elif mode == "vertical":
            self.image = cv2.flip(self.image, 0)

    def blur(self, intensity):
        if self.image is None:
            return

        intensity = int(intensity)
        if intensity <= 0:
            return

        k = intensity * 2 + 1
        self.image = cv2.GaussianBlur(self.image, (k, k), 0)

    def brightness(self, value):
        if self.image is None:
            return

        value = float(value)
        img = self.image.astype("float32")
        img = img + value
        img = img.clip(0, 255)
        self.image = img.astype("uint8")

    def contrast(self, alpha):
        if self.image is None:
            return

        alpha = float(alpha)
        img = self.image.astype("float32")
        img = 128 + alpha * (img - 128)
        img = img.clip(0, 255)
        self.image = img.astype("uint8")

    def edge_detection(self, low=100, high=200):
        """
        Canny edge detection.
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
        Resize to exact width/height.
        """
        if self.image is None:
            return

        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            return

        self.image = cv2.resize(self.image, (width, height), interpolation=cv2.INTER_AREA)