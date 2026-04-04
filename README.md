# SortMyMedia

A GUI application for manually sorting files from source folders to destination folders with media preview.

## Features

- **Startup wizard**: Select source and destination folders when the app starts
- **Media preview**: View images (PNG, JPG, GIF, BMP, WebP) and PDFs directly in the app
- **Carousel view**: Browse through files one at a time
- **Quick sorting**: Click a destination folder button to move the current file
- **Skip files**: Skip files you don't want to sort

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m src.main
```

1. When the app starts, select one or more **source folders** (where your files are)
2. Add one or more **destination folders** (where you want to sort files)
3. Click **Start Sorting**
4. Use the destination buttons to sort files, or **SKIP** to move to the next file
5. Use **< Previous** and **Next >** to navigate

## Requirements

- Python 3.10+
- Optional: Pillow (for image preview)
- Optional: PyMuPDF (for PDF preview)
