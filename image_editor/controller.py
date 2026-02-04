import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import os

from processor import ImageProcessor
from history import HistoryManager


class EditorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HIT137 Image Editor")
        self.root.geometry("1000x800")

        # File / image state
        self.current_path = None
        self.original_image = None   # full reset reference
        self.base_image = None       # after rotate/flip/resize (transformations)
        self.cv_image = None         # final image after adjustments (sliders/grayscale/edges)

        # Helpers
        self.processor = ImageProcessor()
        self.history = HistoryManager()

        # Flags
        self.restoring_state = False
        self.is_grayscale = False

        # ---------------- MENU ----------------
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_image)
        file_menu.add_command(label="Save As", command=self.save_image_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.confirm_exit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # ---------------- LAYOUT ----------------
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.image_label = tk.Label(self.main_frame, text="Open an image to begin")
        self.image_label.pack(side="left", fill="both", expand=True)

        self.controls = tk.LabelFrame(self.main_frame, text="Controls", width=280, padx=10, pady=10)
        self.controls.pack(side="right", fill="y")

        # ---------------- TRANSFORMS ----------------
        tk.Button(self.controls, text="Grayscale (Toggle)", command=self.apply_grayscale).pack(pady=4, fill="x")

        tk.Button(self.controls, text="Rotate 90°", command=lambda: self.apply_rotate(90)).pack(pady=4, fill="x")
        tk.Button(self.controls, text="Rotate 180°", command=lambda: self.apply_rotate(180)).pack(pady=4, fill="x")
        tk.Button(self.controls, text="Rotate 270°", command=lambda: self.apply_rotate(270)).pack(pady=4, fill="x")

        tk.Button(self.controls, text="Flip Horizontal", command=lambda: self.apply_flip("horizontal")).pack(pady=4, fill="x")
        tk.Button(self.controls, text="Flip Vertical", command=lambda: self.apply_flip("vertical")).pack(pady=4, fill="x")

        # ---------------- ADJUSTMENTS FRAME ----------------
        self.adjustments_frame = tk.LabelFrame(self.controls, text="Image Adjustments", padx=10, pady=10)
        self.adjustments_frame.pack(fill="x", pady=12)

        # Blur slider
        tk.Label(self.adjustments_frame, text="Blur Intensity").pack(pady=(0, 0), anchor="w")
        self.blur_slider = tk.Scale(
            self.adjustments_frame,
            from_=0,
            to=10,
            orient="horizontal",
            command=self.apply_adjustments_all
        )
        self.blur_slider.set(0)
        self.blur_slider.pack(fill="x")
        self.blur_slider.bind("<ButtonPress-1>", lambda e: self._push_state())  # push BEFORE user changes

        # Brightness slider
        tk.Label(self.adjustments_frame, text="Brightness").pack(pady=(10, 0), anchor="w")
        self.brightness_slider = tk.Scale(
            self.adjustments_frame,
            from_=-100,
            to=100,
            orient="horizontal",
            command=self.apply_adjustments_all
        )
        self.brightness_slider.set(0)
        self.brightness_slider.pack(fill="x")
        self.brightness_slider.bind("<ButtonPress-1>", lambda e: self._push_state())

        # Contrast slider
        tk.Label(self.adjustments_frame, text="Contrast").pack(pady=(10, 0), anchor="w")
        self.contrast_slider = tk.Scale(
            self.adjustments_frame,
            from_=0.5,
            to=3.0,
            resolution=0.1,
            orient="horizontal",
            command=self.apply_adjustments_all
        )
        self.contrast_slider.set(1.0)
        self.contrast_slider.pack(fill="x")
        self.contrast_slider.bind("<ButtonPress-1>", lambda e: self._push_state())

        tk.Button(self.adjustments_frame, text="Reset Adjustments", command=self.reset_adjustments).pack(pady=8, fill="x")

        # ---------------- EDGE ----------------
        tk.Label(self.controls, text="Edge Detection (Canny)").pack(pady=(10, 0), anchor="w")
        tk.Button(self.controls, text="Apply Edge Detection", command=self.apply_edges).pack(pady=4, fill="x")

        # ---------------- RESIZE ----------------
        tk.Label(self.controls, text="Resize").pack(pady=(12, 0), anchor="w")
        resize_frame = tk.Frame(self.controls)
        resize_frame.pack(pady=4)

        tk.Label(resize_frame, text="W").grid(row=0, column=0, padx=3)
        self.width_entry = tk.Entry(resize_frame, width=6)
        self.width_entry.grid(row=0, column=1, padx=3)

        tk.Label(resize_frame, text="H").grid(row=0, column=2, padx=3)
        self.height_entry = tk.Entry(resize_frame, width=6)
        self.height_entry.grid(row=0, column=3, padx=3)

        tk.Button(self.controls, text="Apply Resize", command=self.apply_resize).pack(pady=4, fill="x")

        # ---------------- RESET ALL ----------------
        tk.Button(self.controls, text="Reset All", command=self.reset_all).pack(pady=8, fill="x")

        # ---------------- STATUS BAR ----------------
        self.status_var = tk.StringVar()
        self.status_var.set("No image loaded")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.tk_image = None

    # =========================================================
    # CORE
    # =========================================================

    def run(self):
        self.root.mainloop()

    def _image_info(self):
        if self.cv_image is None:
            return "No image loaded"
        h, w = self.cv_image.shape[:2]
        name = os.path.basename(self.current_path) if self.current_path else "Untitled"
        return f"{name} | {w} x {h}px"

    def _update_status(self, action=""):
        base = self._image_info()
        self.status_var.set(f"{action} — {base}" if action else base)

    def confirm_exit(self):
        if self.cv_image is None:
            self.root.destroy()
            return
        if messagebox.askyesno("Exit", "Exit the application? Unsaved changes may be lost."):
            self.root.destroy()

    def open_image(self):
        filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Open Image", filetypes=filetypes)
        if not path:
            return

        img = cv2.imread(path)
        if img is None:
            messagebox.showerror("Error", "Could not open image.")
            return

        self.current_path = path
        self.original_image = img.copy()
        self.base_image = img.copy()
        self.cv_image = img.copy()

        # reset sliders without triggering apply
        self.restoring_state = True
        try:
            self.blur_slider.set(0)
            self.brightness_slider.set(0)
            self.contrast_slider.set(1.0)
            self.is_grayscale = False
        finally:
            self.restoring_state = False

        # reset history and push initial state
        self.history.clear()
        self._push_state()

        # pre-fill resize entries
        h, w = self.cv_image.shape[:2]
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(w))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(h))

        self.display_image(self.cv_image)
        self._update_status("Loaded")

    def save_image(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return

        if not self.current_path:
            self.save_image_as()
            return

        success = cv2.imwrite(self.current_path, self.cv_image)
        if success:
            self._update_status("Saved")
        else:
            messagebox.showerror("Error", "Could not save image.")

    def save_image_as(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return

        filetypes = [("PNG", "*.png"), ("JPG", "*.jpg"), ("BMP", "*.bmp")]
        path = filedialog.asksaveasfilename(
            title="Save Image As",
            defaultextension=".png",
            filetypes=filetypes
        )
        if not path:
            return

        success = cv2.imwrite(path, self.cv_image)
        if success:
            self.current_path = path
            self._update_status("Saved As")
        else:
            messagebox.showerror("Error", "Could not save image.")

    def display_image(self, cv_img):
        if cv_img is None:
            return
        if len(cv_img.shape) == 2:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(rgb)
        pil_img.thumbnail((650, 520))
        self.tk_image = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=self.tk_image, text="")

    # =========================================================
    # UNDO / REDO (expects HistoryManager storing state tuples)
    # =========================================================

    def _push_state(self):
        if self.cv_image is None or self.base_image is None:
            return
        state = (
            self.cv_image.copy(),
            self.base_image.copy(),
            int(self.blur_slider.get()),
            int(self.brightness_slider.get()),
            float(self.contrast_slider.get()),
            bool(self.is_grayscale)
        )
        self.history.push(state)

    def _restore_state(self, state):
        img, base_img, blur, brightness, contrast, grayscale = state
        self.restoring_state = True
        try:
            self.base_image = base_img.copy()
            self.cv_image = img.copy()
            self.is_grayscale = grayscale
            self.blur_slider.set(blur)
            self.brightness_slider.set(brightness)
            self.contrast_slider.set(contrast)
        finally:
            self.restoring_state = False

        self.display_image(self.cv_image)

    def undo(self):
        if self.cv_image is None:
            return
        state = self.history.undo()
        if state is None:
            return
        self._restore_state(state)
        self._update_status("Undo")

    def redo(self):
        if self.cv_image is None:
            return
        state = self.history.redo()
        if state is None:
            return
        self._restore_state(state)
        self._update_status("Redo")

    # =========================================================
    # FILTERS / TRANSFORMS
    # =========================================================

    def apply_grayscale(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        self._push_state()
        self.is_grayscale = not self.is_grayscale
        self.apply_adjustments_all()
        self._update_status("Grayscale toggled")

    def apply_rotate(self, angle):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        self._push_state()
        self.processor.set_image(self.base_image.copy())
        self.processor.rotate(angle)
        self.base_image = self.processor.get_image()
        self.apply_adjustments_all()
        self._update_status(f"Rotated {angle}°")

    def apply_flip(self, mode):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        self._push_state()
        self.processor.set_image(self.base_image.copy())
        self.processor.flip(mode)
        self.base_image = self.processor.get_image()
        self.apply_adjustments_all()
        self._update_status(f"Flipped {mode}")

    def apply_adjustments_all(self, _=None):
        # live updates from sliders
        if self.cv_image is None or self.base_image is None:
            return
        if getattr(self, "restoring_state", False):
            return

        blur = int(self.blur_slider.get())
        brightness = int(self.brightness_slider.get())
        contrast = float(self.contrast_slider.get())

        img = self.base_image.copy()

        if self.is_grayscale and len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        self.processor.set_image(img)

        # Keep blur mild; map 0-10 to kernel sizes via processor (or scale intensity)
        if blur > 0:
            self.processor.blur(blur)  # processor turns intensity into odd kernel

        self.processor.brightness(brightness)
        self.processor.contrast(contrast)

        self.cv_image = self.processor.get_image()
        self.display_image(self.cv_image)
        self._update_status("Adjusted")

    def reset_adjustments(self):
        if self.cv_image is None:
            return
        self._push_state()
        self.restoring_state = True
        try:
            self.blur_slider.set(0)
            self.brightness_slider.set(0)
            self.contrast_slider.set(1.0)
            self.is_grayscale = False
        finally:
            self.restoring_state = False
        self.apply_adjustments_all()
        self._update_status("Adjustments reset")

    def apply_edges(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return
        self._push_state()
        self.processor.set_image(self.cv_image.copy())
        self.processor.edge_detection(100, 200)
        self.cv_image = self.processor.get_image()
        self.display_image(self.cv_image)
        self._update_status("Edge detection applied")

    def apply_resize(self):
        if self.cv_image is None or self.base_image is None:
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

        self._push_state()
        self.processor.set_image(self.base_image.copy())
        self.processor.resize(w, h)
        self.base_image = self.processor.get_image()
        self.apply_adjustments_all()
        self._update_status("Resized")

    def reset_all(self):
        if self.original_image is None:
            return

        self.restoring_state = True
        try:
            self.blur_slider.set(0)
            self.brightness_slider.set(0)
            self.contrast_slider.set(1.0)
            self.is_grayscale = False
        finally:
            self.restoring_state = False

        self.base_image = self.original_image.copy()
        self.cv_image = self.original_image.copy()

        # refresh resize entries
        h, w = self.cv_image.shape[:2]
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(w))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(h))

        self.history.clear()
        self._push_state()

        self.display_image(self.cv_image)
        self._update_status("Reset all")
