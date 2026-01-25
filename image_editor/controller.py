import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2

from image_editor.processor import ImageProcessor


class EditorApp:
    def __init__(self):
        # Main window
        self.root = tk.Tk()
        self.root.title("HIT137 Image Editor")
        self.root.geometry("900x600")

        self.current_path = None
        self.cv_image = None

        # Create processor
        self.processor = ImageProcessor()

        # Menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Main layout
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Image display area
        self.image_label = tk.Label(self.main_frame, text="Open an image to begin")
        self.image_label.pack(side="left", fill="both", expand=True)

        # Control panel
        self.controls = tk.Frame(self.main_frame, width=200)
        self.controls.pack(side="right", fill="y")

        tk.Label(self.controls, text="Controls").pack(pady=10)

        tk.Button(self.controls, text="Grayscale",
                  command=self.apply_grayscale).pack(pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("No image loaded")
        self.status_bar = tk.Label(self.root,
                                   textvariable=self.status_var,
                                   anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.tk_image = None

    def run(self):
        self.root.mainloop()

    def open_image(self):
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp"),
            ("All files", "*.*")
        ]

        path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=filetypes
        )

        if not path:
            return

        img = cv2.imread(path)

        if img is None:
            messagebox.showerror("Error", "Could not open image.")
            return

        self.current_path = path
        self.cv_image = img

        self.display_image(self.cv_image)

        h, w = self.cv_image.shape[:2]
        self.status_var.set(f"Loaded: {path} | {w} x {h}px")

    def display_image(self, cv_img):
        # Handle grayscale or colour
        if len(cv_img.shape) == 2:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(rgb)
        pil_img.thumbnail((650, 520))

        self.tk_image = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=self.tk_image, text="")

    def apply_grayscale(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return

        self.processor.set_image(self.cv_image)
        self.processor.grayscale()
        self.cv_image = self.processor.get_image()

        self.display_image(self.cv_image)

        h, w = self.cv_image.shape[:2]
        self.status_var.set(f"Grayscale applied | {w} x {h}px")
