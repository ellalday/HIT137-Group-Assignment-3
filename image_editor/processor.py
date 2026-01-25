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

