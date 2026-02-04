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
        self.root.geometry("1000x800")  # size increase to allow for resets

        self.current_path = None
        self.original_image = None  # original backup used for reset all
        self.cv_image = None  # image with adjustments
        self.base_image = None  # image with rotate/flip
        self.dirty = False  # unsaved changes flag

        self.processor = ImageProcessor()
        self.history = HistoryManager()
        self.restoring_state = False
        self.is_grayscale = False  # implement non destructive grayscale

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

        self.image_label = tk.Label(
            self.main_frame, text="Open an image to begin")
        self.image_label.pack(side="left", fill="both", expand=True)

        self.controls = tk.LabelFrame(
            self.main_frame, text="Controls", width=280)
        self.controls.pack(side="right", fill="y")

        self.adjustments_frame = tk.LabelFrame(
            self.controls,
            text="Image Adjustments",
            padx=10,
            pady=10
        )

        #  TRANSFORMATION BUTTONS 
        # Grayscale toggle button
        btn = tk.Button(self.controls, text="Grayscale",
                        command=self.apply_grayscale)
        btn.pack(pady=4)
        self.control_widgets.append(btn)

        # Rotation buttons - 90, 180, and 270 degree options
        btn = tk.Button(self.controls, text="Rotate 90°",
                        command=lambda: self.apply_rotate(90))
        btn.pack(pady=4)
        self.control_widgets.append(btn)

        btn = tk.Button(self.controls, text="Rotate 180°",
                        command=lambda: self.apply_rotate(180))
        btn.pack(pady=4)
        self.control_widgets.append(btn)

        btn = tk.Button(self.controls, text="Rotate 270°",
                        command=lambda: self.apply_rotate(270))
        btn.pack(pady=4)
        self.control_widgets.append(btn)

        # Flip buttons - horizontal and vertical options
        btn = tk.Button(self.controls, text="Flip Horizontal",
                        command=lambda: self.apply_flip("horizontal"))
        btn.pack(pady=4)
        self.control_widgets.append(btn)

        btn = tk.Button(self.controls, text="Flip Vertical",
                        command=lambda: self.apply_flip("vertical"))
        btn.pack(pady=4)
        self.control_widgets.append(btn)

        self.adjustments_frame.pack(fill="x", pady=12)
        
        # BLUR SLIDER 
        tk.Label(self.adjustments_frame,
                 text="Blur Intensity").pack(pady=(12, 0))
        self.blur_slider = tk.Scale(
            self.adjustments_frame,
            from_=0,
            to=10,
            orient="horizontal",
            command=self.apply_adjustments_all
        )
        self.blur_slider.set(0)
        self.blur_slider.pack(fill="x")
        self.control_widgets.append(self.blur_slider)
        # Push state to history only when slider is released, not on every movement
        self.blur_slider.bind("<ButtonRelease-1>", lambda e: self._push_state())

        # BRIGHTNESS & CONTRAST SLIDERS ""
        tk.Label(self.adjustments_frame, text="Brightness").pack(pady=(12, 0))

        self.brightness_slider = tk.Scale(
            self.adjustments_frame,
            from_=-100,
            to=100,
            orient="horizontal",
            command=self.apply_adjustments_all
        )
        self.brightness_slider.set(0)
        self.brightness_slider.pack(fill="x")
        self.control_widgets.append(self.brightness_slider)
        self.brightness_slider.bind(
            "<ButtonRelease-1>", lambda e: self._push_state())

        tk.Label(self.adjustments_frame, text="Contrast").pack(pady=(12, 0))
        self.contrast_slider = tk.Scale(
            self.adjustments_frame,
            from_=0.5,
            to=3.0,
            resolution=0.1,
            orient="horizontal",
            command=self.apply_adjustments_all)
        self.contrast_slider.set(1.0)
        self.contrast_slider.pack(fill="x")
        self.control_widgets.append(self.contrast_slider)
        self.contrast_slider.bind(
            "<ButtonRelease-1>", lambda e: self._push_state())

        # Reset button - resets only adjustments, keeps transformations (rotate/flip)
        btn = tk.Button(  # resets just the image adjustments
            self.adjustments_frame,
            text="Reset Adjustments",
            command=self.reset_adjustments
        )
        btn.pack(pady=5)
        self.control_widgets.append(btn)

        # EDGE DETECTION 
        tk.Label(self.controls, text="Edge Detection (Canny)").pack(
            pady=(12, 0))
        btn = tk.Button(self.controls, text="Apply Edge Detection",
                        command=self.apply_edges)
        btn.pack(pady=4)
        self.control_widgets.append(btn)

        #RESIZE SECTION 
        tk.Label(self.controls, text="Resize").pack(pady=(12, 0))

        # Width and height input fields for resize operation
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

        btn = tk.Button(self.controls, text="Apply Resize",
                        command=self.apply_resize)
        btn.pack(pady=4)
        self.control_widgets.append(btn)

        # RESET ALL BUTTON 
        # Fully resets image to original state, clears all transformations and adjustments
        btn = tk.Button(
            self.controls,
            text="Reset All",
            command=self.reset_all
        )
        btn.pack(pady=5)
        self.control_widgets.append(btn)

        # STATUS BAR 
        # Display status messages and image information at bottom of window
        self.status_var = tk.StringVar()
        self.status_var.set("No image loaded")
        self.status_bar = tk.Label(
            self.root, textvariable=self.status_var, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        # Placeholder for current image displayed in GUI
        self.tk_image = None

        # Start with controls disabled until an image is loaded
        self._set_controls_enabled(False)
        self._update_title_and_status()

    # UI HELPERS - enable/disable + status/title + dirty

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

    def _apply_and_refresh(self, action_text="Edited", sync_resize=False):
        self.display_image(self.cv_image)
        self._mark_dirty(True)
        self._update_title_and_status(action_text)
        if sync_resize:
            self._sync_resize_fields()

    # CORE METHODS - Application lifecycle

    def run(self):
        """Start the GUI event loop"""
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
        """Open an image file and initialize all image states"""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp"),
            ("All files", "*.*")
        ]

        path = filedialog.askopenfilename(
            title="Open Image", filetypes=filetypes)
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

        # set sliders to default
        self.restoring_state = True
        try:
            self.blur_slider.set(0)
            self.brightness_slider.set(0)
            self.contrast_slider.set(1.0)
            self.is_grayscale = False
        finally:
            self.restoring_state = False

        # reset history for new image
        self.history.clear()
        self._push_state()

        # pre-fill resize boxes
        self._sync_resize_fields()

        self.display_image(self.cv_image)

        self._set_controls_enabled(True)
        self._mark_dirty(False)
        self._update_title_and_status("Loaded")

    def save_image(self):
        """Save current image to existing file"""
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
        """Save current image with a new filename"""
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
        """Convert OpenCV image to PhotoImage and display in GUI"""
        if len(cv_img.shape) == 2:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(rgb)
        pil_img.thumbnail((650, 520))

        self.tk_image = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=self.tk_image, text="")

    # UNDO / REDO - History management

    def undo(self):
        """Undo last action by restoring previous state"""
        if self.cv_image is None:
            return
        state = self.history.undo()
        if state is None:
            return
        self._restore_state(state)
        self._mark_dirty(True)
        self._update_title_and_status("Undo")
        self._sync_resize_fields()

    def redo(self):
        """Redo last undone action"""
        if self.cv_image is None:
            return
        if not self.history.redo_stack:
            return
        state = self.history.redo()
        self._restore_state(state)
        self._mark_dirty(True)
        self._update_title_and_status("Redo")
        self._sync_resize_fields()

    # FILTER & ADJUSTMENT METHODS

    def _push_state(self):
        """Save current state to undo history"""
        if self.cv_image is None:
            return
        state = (
            self.cv_image.copy(),
            self.base_image.copy(),
            self.blur_slider.get(),
            self.brightness_slider.get(),
            self.contrast_slider.get(),
            self.is_grayscale
        )
        self.history.push(state)

    def apply_grayscale(self):
        """Toggle grayscale effect non-destructively"""
        if self.original_image is None:
            return
        self.is_grayscale = not self.is_grayscale
        self.apply_adjustments_all()
        self._push_state()

    def apply_rotate(self, angle):
        """Rotate image by specified angle (90, 180, 270 degrees)"""
        if self.cv_image is None:
            return

        self.processor.set_image(self.base_image)
        self.processor.rotate(angle)
        self.base_image = self.processor.get_image()
        self.apply_adjustments_all()
        self._push_state()
        self._mark_dirty(True)
        self._update_title_and_status(f"Rotate {angle}°")
        self._sync_resize_fields()

    def apply_flip(self, mode):
        """Flip image horizontally or vertically"""
        if self.cv_image is None:
            return
        self.processor.set_image(self.base_image)
        self.processor.flip(mode)
        self.base_image = self.processor.get_image()
        self.apply_adjustments_all()
        self._push_state()
        self._mark_dirty(True)
        self._update_title_and_status(f"Flip {mode}")

    # applys all adjustment setting to the base image
    def apply_adjustments_all(self, _=None):
        """Apply all active adjustments (blur, brightness, contrast, grayscale) to base image"""
        if self.cv_image is None:
            return
        if getattr(self, "restoring_state", False):
            return
        blur = self.blur_slider.get()
        brightness = self.brightness_slider.get()
        contrast = self.contrast_slider.get()
        img = self.base_image.copy()
        if self.is_grayscale:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.processor.set_image(img)
        if blur > 0:
            self.processor.blur(int(blur) * 3)
        self.processor.brightness(brightness)
        self.processor.contrast(contrast)

        self.cv_image = self.processor.get_image()
        self._apply_and_refresh("Adjustments")

        # Only mark dirty if an image is loaded
        if self.cv_image is not None:
            self._mark_dirty(True)

        # Hayden Note: allows all sliders to be used at the same time

    # resets only visual adjustment, without losing rotations/flips
    def reset_adjustments(self):
        """Reset only visual adjustments while keeping rotations/flips"""
        if self.cv_image is None:
            return
        self.blur_slider.set(0)
        self.brightness_slider.set(0)
        self.contrast_slider.set(1.0)
        self.is_grayscale = False
        self.apply_adjustments_all()
        self._push_state()
        self._mark_dirty(True)
        self._update_title_and_status("Reset Adjustments")

    def apply_edges(self):
        """Apply Canny edge detection filter to image"""
        if self.cv_image is None:
            return

        self.processor.set_image(self.cv_image)
        self.processor.edge_detection(100, 200)
        self.cv_image = self.processor.get_image()
        self.display_image(self.cv_image)
        self._push_state()
        self._mark_dirty(True)
        self._update_title_and_status("Edges")

    def apply_resize(self):
        """Resize image to dimensions specified in width/height entry fields"""
        if self.cv_image is None:
            return

        try:
            w = int(self.width_entry.get())
            h = int(self.height_entry.get())
        except ValueError:
            messagebox.showerror(
                "Error", "Width and Height must be whole numbers.")
            return

        if w <= 0 or h <= 0:
            messagebox.showerror(
                "Error", "Width and Height must be greater than 0.")
            return

        self.processor.set_image(self.base_image)
        self.processor.resize(w, h)
        self.base_image = self.processor.get_image()
        self.apply_adjustments_all()
        self._push_state()
        self._mark_dirty(True)
        self._update_title_and_status("Resize")
        self._sync_resize_fields()

    def reset_all(self):
        """Fully reset editor to original image state"""
        if self.original_image is None:
            return
        self.blur_slider.set(0)
        self.brightness_slider.set(0)
        self.contrast_slider.set(1.0)
        self.is_grayscale = False
        self.base_image = self.original_image.copy()
        self.cv_image = self.original_image.copy()
        self.display_image(self.cv_image)
        self.history.clear()
        self._push_state()
        self._mark_dirty(False)
        self._update_title_and_status("Reset All")
        self._sync_resize_fields()

    def _restore_state(self, state):
        """Restore a previously saved state (used for undo/redo)"""
        img, base_image, blur, brightness, contrast, grayscale = state
        self.restoring_state = True
        try:
            self.base_image = base_image.copy()
            self.cv_image = img.copy()
            self.is_grayscale = grayscale
            self.blur_slider.set(blur)
            self.brightness_slider.set(brightness)
            self.contrast_slider.set(contrast)
        finally:
            self.restoring_state = False

        self.display_image(self.cv_image)
        self._update_title_and_status("Restored")
