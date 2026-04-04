# SortMyMedia

A modern GUI application for manually sorting files from source folders to destination folders with real-time media preview.

![Dark themed interface with PyQt6](https://img.shields.io/badge/PyQt6-Dark%20Theme-2d2d2d?style=for-the-badge)

## Features

### Media Preview
- **Images**: PNG, JPG, JPEG, GIF, BMP, WebP - automatic scaling to fit viewport
- **Videos**: MP4, WebM, MOV, AVI, MKV, FLV - with built-in player controls
- **PDFs**: First page preview using PyMuPDF

### Video Player Controls
- Play/Pause toggle
- Progress slider with seek functionality
- Volume control
- Current time / Total duration display

### Configuration System
- **Save configurations**: Store your folder selections with custom names
- **Load configurations**: Quick switch between saved setups
- **Import/Export**: Share configurations as YAML files
- Configurations stored in `~/.sortmymedia/configs/`

### File Management
- **Multi-source support**: Add multiple source folders
- **Named destinations**: Each destination shows its real folder name
- **Quick sorting**: One-click to move current file to destination
- **Navigation**: Previous/Next buttons to browse files
- **Progress tracking**: See processed vs remaining files

### User Interface
- **Dark theme**: Modern dark UI with Fusion style
- **Single-window design**: Setup and sorting in one window
- **Configurable**: Return to setup anytime with "← Config" button
- **Native file dialogs**: Uses system file picker on Windows/macOS/Linux

## Installation

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python -m src.main
```

### Quick Start

1. **Configure Folders**
   - Click **+ Add Source** to select source folder(s)
   - Click **+ Add Destination** to select destination folder(s)
   - Click **⚙️ Config** to save/load configurations

2. **Start Sorting**
   - Click **Start Sorting**
   - Use destination buttons to move files
   - Use **◀ Previous** / **Next ▶** to navigate

3. **Return to Setup**
   - Click **← Config** in the header to change folders

### Configuration Management

- **Save**: Store current setup with a custom name
- **Load**: Switch between saved configurations
- **Rename/Delete**: Manage your saved configurations
- **Export**: Save configuration to a YAML file
- **Import**: Load configuration from external YAML file

## Requirements

| Package | Required | Purpose |
|---------|----------|---------|
| Python | 3.10+ | Runtime |
| PyQt6 | Yes | GUI Framework |
| Pillow | Recommended | Image preview |
| PyMuPDF | Recommended | PDF preview |
| PyYAML | Yes | Config storage |

## Keyboard Shortcuts

Coming soon!

## License

MIT License
