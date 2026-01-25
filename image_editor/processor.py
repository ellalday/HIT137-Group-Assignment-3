import cv2


class ImageProcessor:
    def __init__(self):
        self.image = None

    def set_image(self, image):
        self.image = image

    def get_image(self):
        return self.image

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
        """
        Gaussian blur with adjustable intensity.
        intensity should be an integer from 0 upwards.
        0 means no blur.
        """
        if self.image is None:
            return

        intensity = int(intensity)
        if intensity <= 0:
            return

        # Kernel must be odd: 1,3,5,7...
        k = intensity * 2 + 1
        self.image = cv2.GaussianBlur(self.image, (k, k), 0)




