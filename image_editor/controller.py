import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2

from image_editor.processor import ImageProcessor


class EditorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HIT137 Image Editor")
        self.root.geometry("900x750")

        self.current_path = None
        self.original_image = None
        self.cv_image = None
        self.processor = ImageProcessor()

        # ---------------- MENU ----------------
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # ---------------- LAYOUT ----------------
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.image_label = tk.Label(self.main_frame, text="Open an image to begin")
        self.image_label.pack(side="left", fill="both", expand=True)

        self.controls = tk.Frame(self.main_frame, width=280)
        self.controls.pack(side="right", fill="y")

        tk.Label(self.controls, text="Controls").pack(pady=10)

        # ---------------- BUTTONS ----------------
        tk.Button(self.controls, text="Grayscale", command=self.apply_grayscale).pack(pady=4)

        tk.Button(self.controls, text="Rotate 90°", command=lambda: self.apply_rotate(90)).pack(pady=4)
        tk.Button(self.controls, text="Rotate 180°", command=lambda: self.apply_rotate(180)).pack(pady=4)
        tk.Button(self.controls, text="Rotate 270°", command=lambda: self.apply_rotate(270)).pack(pady=4)

        tk.Button(self.controls, text="Flip Horizontal", command=lambda: self.apply_flip("horizontal")).pack(pady=4)
        tk.Button(self.controls, text="Flip Vertical", command=lambda: self.apply_flip("vertical")).pack(pady=4)

        # ---------------- BLUR ----------------
        tk.Label(self.controls, text="Blur Intensity").pack(pady=(12, 0))
        self.blur_slider = tk.Scale(self.controls, from_=0, to=10, orient="horizontal")
        self.blur_slider.set(0)
        self.blur_slider.pack()
        tk.Button(self.controls, text="Apply Blur", command=self.apply_blur).pack(pady=4)

        # ---------------- BRIGHTNESS + CONTRAST ----------------
        tk.Label(self.controls, text="Brightness").pack(pady=(12, 0))
        self.brightness_slider = tk.Scale(self.controls, from_=-100, to=100, orient="horizontal")
        self.brightness_slider.set(0)
        self.brightness_slider.pack()

        tk.Label(self.controls, text="Contrast").pack(pady=(12, 0))
        self.contrast_slider = tk.Scale(self.controls, from_=0.5, to=3.0, resolution=0.1, orient="horizontal")
        self.contrast_slider.set(1.0)
        self.contrast_slider.pack()

        tk.Button(self.controls, text="Apply Brightness + Contrast", command=self.apply_adjustments).pack(pady=6)

        # ---------------- EDGE DETECTION ----------------
        tk.Label(self.controls, text="Edge Detection (Canny)").pack(pady=(12, 0))
        tk.Button(self.controls, text="Apply Edge Detection", command=self.apply_edges).pack(pady=4)

        # ---------------- RESIZE ----------------
        tk.Label(self.controls, text="Resize").pack(pady=(12, 0))

        resize_frame = tk.Frame(self.controls)
        resize_frame.pack(pady=4)

        tk.Label(resize_frame, text="W").grid(row=0, column=0, padx=3)
        self.width_entry = tk.Entry(resize_frame, width=6)
        self.width_entry.grid(row=0, column=1, padx=3)

        tk.Label(resize_frame, text="H").grid(row=0, column=2, padx=3)
        self.height_entry = tk.Entry(resize_frame, width=6)
        self.height_entry.grid(row=0, column=3, padx=3)

        tk.Button(self.controls, text="Apply Resize", command=self.apply_resize).pack(pady=4)

        # ---------------- STATUS BAR ----------------
        self.status_var = tk.StringVar()
        self.status_var.set("No image loaded")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.tk_image = None

    # =========================================================
    # CORE METHODS
    # =========================================================

    def run(self):
        self.root.mainloop()

    def open_image(self):
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp"),
            ("All files", "*.*")
        ]

        path = filedialog.askopenfilename(title="Open Image", filetypes=filetypes)
        if not path:
            return

        img = cv2.imread(path)
        if img is None:
            messagebox.showerror("Error", "Could not open image.")
            return

        self.current_path = path
        self.original_image = img.copy()
        self.cv_image = img.copy()

        # pre-fill resize boxes with current dimensions
        h, w = self.cv_image.shape[:2]
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(w))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(h))

        self.display_image(self.cv_image)
        self.status_var.set(f"Loaded: {path} | {w} x {h}px")

    def display_image(self, cv_img):
        if len(cv_img.shape) == 2:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(rgb)
        pil_img.thumbnail((650, 520))

        self.tk_image = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=self.tk_image, text="")

    # =========================================================
    # FILTER METHODS
    # =========================================================

    def apply_grayscale(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        self.processor.set_image(self.cv_image)
        self.processor.grayscale()
        self.cv_image = self.processor.get_image()
        self.display_image(self.cv_image)

    def apply_rotate(self, angle):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        self.processor.set_image(self.cv_image)
        self.processor.rotate(angle)
        self.cv_image = self.processor.get_image()
        self.display_image(self.cv_image)

    def apply_flip(self, mode):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        self.processor.set_image(self.cv_image)
        self.processor.flip(mode)
        self.cv_image = self.processor.get_image()
        self.display_image(self.cv_image)

    def apply_blur(self):
        if self.original_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        intensity = self.blur_slider.get()
        self.processor.set_image(self.original_image.copy())
        self.processor.blur(intensity)
        self.cv_image = self.processor.get_image()
        self.display_image(self.cv_image)

    def apply_adjustments(self):
        if self.original_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return

        brightness_value = self.brightness_slider.get()
        contrast_value = self.contrast_slider.get()

        self.processor.set_image(self.original_image.copy())
        self.processor.brightness(brightness_value)
        self.processor.contrast(contrast_value)

        self.cv_image = self.processor.get_image()
        self.display_image(self.cv_image)

    def apply_edges(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return

        # Edge detection applies to current image
        self.processor.set_image(self.cv_image)
        self.processor.edge_detection(100, 200)
        self.cv_image = self.processor.get_image()
        self.display_image(self.cv_image)

        h, w = self.cv_image.shape[:2]
        self.status_var.set(f"Edge detection applied | {w} x {h}px")

    def apply_resize(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return

        try:
            w = int(self.width_entry.get())
            h = int(self.height_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Width and Height must be whole numbers.")
            return

        if w <= 0 or h <= 0:
            messagebox.showerror("Error", "Width and Height must be greater than 0.")
            return

        self.processor.set_image(self.cv_image)
        self.processor.resize(w, h)
        self.cv_image = self.processor.get_image()

        self.display_image(self.cv_image)
        self.status_var.set(f"Resized to {w} x {h}px")

