import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import os

from image_editor.processor import ImageProcessor
from image_editor.history import HistoryManager


class EditorApp:
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HIT137 Image Editor")
        self.root.geometry("900x750")

        self.current_path = None
        self.original_image = None   # snapshot from when the image was opened
        self.cv_image = None         # current working image
        self.dirty = False           # unsaved changes flag

        self.processor = ImageProcessor()
        self.history = HistoryManager()

        # Track all interactive widgets so we can disable/enable them cleanly
        self.control_widgets = []

        # MENU 
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_image)
        file_menu.add_command(label="Save As", command=self.save_image_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # Confirm on window close as well
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # LAYOUT 
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.image_label = tk.Label(self.main_frame, text="Open an image to begin")
        self.image_label.pack(side="left", fill="both", expand=True)

        self.controls = tk.Frame(self.main_frame, width=280)
        self.controls.pack(side="right", fill="y")

        tk.Label(self.controls, text="Controls").pack(pady=10)

        # BUTTONS 
        self._add_button("Grayscale", self.apply_grayscale)

        self._add_button("Rotate 90°", lambda: self.apply_rotate(90))
        self._add_button("Rotate 180°", lambda: self.apply_rotate(180))
        self._add_button("Rotate 270°", lambda: self.apply_rotate(270))

        self._add_button("Flip Horizontal", lambda: self.apply_flip("horizontal"))
        self._add_button("Flip Vertical", lambda: self.apply_flip("vertical"))

        # Reset button (nice usability)
        self._add_button("Reset to Original", self.reset_to_original, pady=8)

        # BLUR 
        tk.Label(self.controls, text="Blur Intensity").pack(pady=(12, 0))
        self.blur_slider = tk.Scale(self.controls, from_=0, to=10, orient="horizontal")
        self.blur_slider.set(0)
        self.blur_slider.pack()
        self.control_widgets.append(self.blur_slider)

        self._add_button("Apply Blur", self.apply_blur)

        # BRIGHTNESS + CONTRAST 
        tk.Label(self.controls, text="Brightness").pack(pady=(12, 0))
        self.brightness_slider = tk.Scale(self.controls, from_=-100, to=100, orient="horizontal")
        self.brightness_slider.set(0)
        self.brightness_slider.pack()
        self.control_widgets.append(self.brightness_slider)

        tk.Label(self.controls, text="Contrast").pack(pady=(12, 0))
        self.contrast_slider = tk.Scale(self.controls, from_=0.5, to=3.0, resolution=0.1, orient="horizontal")
        self.contrast_slider.set(1.0)
        self.contrast_slider.pack()
        self.control_widgets.append(self.contrast_slider)

        self._add_button("Apply Brightness + Contrast", self.apply_adjustments, pady=6)

        # EDGE DETECTION 
        tk.Label(self.controls, text="Edge Detection (Canny)").pack(pady=(12, 0))
        self._add_button("Apply Edge Detection", self.apply_edges)

        # RESIZE 
        tk.Label(self.controls, text="Resize").pack(pady=(12, 0))

        resize_frame = tk.Frame(self.controls)
        resize_frame.pack(pady=4)

        tk.Label(resize_frame, text="W").grid(row=0, column=0, padx=3)
        self.width_entry = tk.Entry(resize_frame, width=6)
        self.width_entry.grid(row=0, column=1, padx=3)
        self.control_widgets.append(self.width_entry)

        tk.Label(resize_frame, text="H").grid(row=0, column=2, padx=3)
        self.height_entry = tk.Entry(resize_frame, width=6)
        self.height_entry.grid(row=0, column=3, padx=3)
        self.control_widgets.append(self.height_entry)

        self._add_button("Apply Resize", self.apply_resize)

        # STATUS BAR 
        self.status_var = tk.StringVar()
        self.status_var.set("No image loaded")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.tk_image = None

        # Start with controls disabled until an image is loaded
        self._set_controls_enabled(False)
        self._update_title_and_status()

    # SMALL UI HELPERS

    def _add_button(self, text, command, pady=4):
        btn = tk.Button(self.controls, text=text, command=command)
        btn.pack(pady=pady)
        self.control_widgets.append(btn)
        return btn

    def _set_controls_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        for w in self.control_widgets:
            try:
                w.configure(state=state)
            except tk.TclError:
                pass

    def _sync_resize_fields(self):
        if self.cv_image is None:
            return
        h, w = self.cv_image.shape[:2]
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(w))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(h))

    def _mark_dirty(self, value=True):
        self.dirty = bool(value)
        self._update_title_and_status()

    def _update_title_and_status(self, action_text=""):
        if self.cv_image is None:
            self.root.title("HIT137 Image Editor")
            self.status_var.set("No image loaded")
            return

        h, w = self.cv_image.shape[:2]
        name = os.path.basename(self.current_path) if self.current_path else "Unsaved"
        mode = "GRAY" if len(self.cv_image.shape) == 2 else "BGR"
        star = "*" if self.dirty else ""
        self.root.title(f"HIT137 Image Editor - {name}{star}")

        suffix = f" | {action_text}" if action_text else ""
        self.status_var.set(f"{name}{star} | {w} x {h}px | {mode}{suffix}")

    # CORE METHODS

    def run(self):
        self.root.mainloop()

    def on_exit(self):
        """Prompt to save if there are unsaved edits."""
        if self.cv_image is None or not self.dirty:
            self.root.destroy()
            return

        choice = messagebox.askyesnocancel(
            "Unsaved changes",
            "You have unsaved changes.\n\nYes = Save\nNo = Don't Save\nCancel = Stay"
        )

        if choice is None:
            return  # Cancel

        if choice is True:
            self.save_image()
            # If save succeeded, dirty becomes False
            if not self.dirty:
                self.root.destroy()
        else:
            self.root.destroy()

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

        # reset history for new image
        self.history.clear()

        # pre-fill resize boxes
        self._sync_resize_fields()

        self.display_image(self.cv_image)

        self._set_controls_enabled(True)
        self._mark_dirty(False)
        self._update_title_and_status("Loaded")

    def save_image(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return

        if not self.current_path:
            self.save_image_as()
            return

        success = cv2.imwrite(self.current_path, self.cv_image)
        if success:
            self._mark_dirty(False)
            self._update_title_and_status("Saved")
        else:
            messagebox.showerror("Error", "Could not save image.")

    def save_image_as(self):
        if self.cv_image is None:
            messagebox.showerror("Error", "No image loaded.")
            return

        filetypes = [
            ("PNG", "*.png"),
            ("JPG", "*.jpg"),
            ("BMP", "*.bmp"),
        ]

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
            self._mark_dirty(False)
            self._update_title_and_status("Saved As")
        else:
            messagebox.showerror("Error", "Could not save image.")

    def display_image(self, cv_img):
        if len(cv_img.shape) == 2:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(rgb)
        pil_img.thumbnail((650, 520))

        self.tk_image = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=self.tk_image, text="")

    # UNDO / REDO

    def undo(self):
        if self.cv_image is None:
            return
        self.cv_image = self.history.undo(self.cv_image)
        self.display_image(self.cv_image)
        self._mark_dirty(True)
        self._update_title_and_status("Undo")
        self._sync_resize_fields()

    def redo(self):
        if self.cv_image is None:
            return
        self.cv_image = self.history.redo(self.cv_image)
        self.display_image(self.cv_image)
        self._mark_dirty(True)
        self._update_title_and_status("Redo")
        self._sync_resize_fields()

    # FILTER METHODS (push state BEFORE change)

    def _push_state(self):
        self.history.push(self.cv_image)

    def _apply_and_refresh(self, action_text="Edited", sync_resize=False):
        self.display_image(self.cv_image)
        self._mark_dirty(True)
        self._update_title_and_status(action_text)
        if sync_resize:
            self._sync_resize_fields()

    def reset_to_original(self):
        if self.original_image is None:
            return
        self._push_state()
        self.cv_image = self.original_image.copy()
        self._apply_and_refresh("Reset", sync_resize=True)
        # Resetting back to original usually means "no unsaved changes" relative to load
        self._mark_dirty(False)
        self._update_title_and_status("Reset to Original")

    def apply_grayscale(self):
        if self.cv_image is None:
            return
        self._push_state()
        self.processor.set_image(self.cv_image)
        self.processor.grayscale()
        self.cv_image = self.processor.get_image()
        self._apply_and_refresh("Grayscale")

    def apply_rotate(self, angle):
        if self.cv_image is None:
            return
        self._push_state()
        self.processor.set_image(self.cv_image)
        self.processor.rotate(angle)
        self.cv_image = self.processor.get_image()
        self._apply_and_refresh(f"Rotate {angle}°", sync_resize=True)

    def apply_flip(self, mode):
        if self.cv_image is None:
            return
        self._push_state()
        self.processor.set_image(self.cv_image)
        self.processor.flip(mode)
        self.cv_image = self.processor.get_image()
        self._apply_and_refresh(f"Flip {mode}")

    def apply_blur(self):
        if self.cv_image is None:
            return
        intensity = self.blur_slider.get()
        if intensity <= 0:
            self._update_title_and_status("Blur (no change)")
            return

        self._push_state()
        self.processor.set_image(self.cv_image)
        self.processor.blur(intensity)
        self.cv_image = self.processor.get_image()
        self._apply_and_refresh(f"Blur {intensity}")

    def apply_adjustments(self):
        if self.cv_image is None:
            return

        brightness_value = self.brightness_slider.get()
        contrast_value = self.contrast_slider.get()

        if brightness_value == 0 and abs(contrast_value - 1.0) < 1e-9:
            self._update_title_and_status("Adjust (no change)")
            return

        self._push_state()
        self.processor.set_image(self.cv_image)
        self.processor.brightness(brightness_value)
        self.processor.contrast(contrast_value)
        self.cv_image = self.processor.get_image()
        self._apply_and_refresh(f"B {brightness_value}, C {contrast_value}")

    def apply_edges(self):
        if self.cv_image is None:
            return
        self._push_state()
        self.processor.set_image(self.cv_image)
        self.processor.edge_detection(100, 200)
        self.cv_image = self.processor.get_image()
        self._apply_and_refresh("Edges")

    def apply_resize(self):
        if self.cv_image is None:
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
        self.processor.set_image(self.cv_image)
        self.processor.resize(w, h)
        self.cv_image = self.processor.get_image()
        self._apply_and_refresh("Resize", sync_resize=True)
