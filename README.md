# HIT137 Group Assignment 3 — Image Editor (Tkinter + OpenCV)

A desktop image editor built with **Python**, **Tkinter**, and **OpenCV**.  
Supports loading, editing, undo/redo history, and saving common image formats.

## Features

This application includes the following OpenCV-based image operations:

1. **Grayscale**
2. **Blur** (adjustable via slider)
3. **Edge Detection** (Canny)
4. **Brightness Adjustment**
5. **Contrast Adjustment**
6. **Rotate** (90° / 180° / 270°)
7. **Flip** (Horizontal / Vertical)
8. **Resize / Scale**

Additional UI features:

- Menu bar: **File (Open / Save / Save As / Exit)** and **Edit (Undo / Redo)**
- Image preview/display area
- Control panel for applying filters
- Status bar showing filename and image size
- Error handling via message boxes (invalid inputs, missing image, etc.)

---

## Requirements

- Python **3.11+** (recommended: **3.12**)
- Packages:
  - `opencv-python`
  - `pillow`

Install dependencies:

    pip install -r requirements.txt

> If you have issues installing OpenCV on Python 3.14, use Python 3.12.

---

## Running the App

From the project root:

    python app.py

---

## How to Use

1. **File → Open** to load an image.
2. Apply edits using the buttons and sliders.
3. Use **Edit → Undo / Redo** to navigate edit history.
4. **File → Save** or **Save As** to export the edited image.

Supported formats depend on your system/OpenCV build, but commonly include:

- `.png`, `.jpg`, `.jpeg`, `.bmp`

---

## Project Structure (OOP Design)

- `app.py`  
  Entry point (creates and runs the GUI).

- `image_editor/controller.py`  
  Tkinter GUI controller (menus, buttons, sliders, image display).

- `image_editor/processor.py`  
  `ImageProcessor` class containing OpenCV image operations.

- `image_editor/history.py`  
  `HistoryManager` class for undo/redo stacks.

---

## GitHub & Submission Notes

- Repo is maintained with regular commits showing team contribution.
- The GitHub repository link is included in `github_link.txt` for submission.

---

## Credits

Built by HIT137 Group 20 (Summer Semester 2025).
