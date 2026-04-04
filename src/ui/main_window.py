from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QListWidget, QFrame, QMessageBox,
    QSizePolicy, QScrollArea, QStatusBar, QStackedWidget, QInputDialog,
    QListWidgetItem, QDialog
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QIcon, QImage
from pathlib import Path
from typing import Optional
import sys
import os

from src.logic.session import Session
from src.models.folder_config import FolderConfig
from src.logic.file_manager import FileManager
from src.logic.config_manager import ConfigManager

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


DARK_STYLE = """
QMainWindow {
    background-color: #1e1e1e;
}
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 13px;
}
QPushButton {
    background-color: #3a3a3a;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #4a4a4a;
}
QPushButton:pressed {
    background-color: #2a2a2a;
}
QPushButton:disabled {
    background-color: #2a2a2a;
    color: #666666;
}
QLabel {
    background-color: transparent;
    color: #e0e0e0;
}
QFrame#viewer {
    background-color: #121212;
    border-radius: 8px;
}
QFrame#sortButton {
    background-color: #2a2a2a;
    border-radius: 8px;
    padding: 10px;
}
QStatusBar {
    background-color: #1a1a1a;
    color: #888888;
}
QScrollArea {
    border: none;
}
"""


class ConfigDialog(QDialog):
    config_loaded = pyqtSignal(object, str)
    config_saved = pyqtSignal(str)
    
    def __init__(self, config_manager, parent=None, active_config_name=None):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.parent_setup = parent
        self.active_config_name = active_config_name
        
        self.setWindowTitle("Configurations")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(DARK_STYLE)
        
        self._create_layout()
        self._refresh_list()
    
    def _create_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Saved Configurations")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4fc3f7;")
        layout.addWidget(title)
        
        self.config_list = QListWidget()
        self.config_list.setStyleSheet("""
            QListWidget {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                outline: 0;
            }
            QListWidget::item {
                background: transparent;
                color: #e0e0e0;
                padding: 10px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background: #0d47a1;
                color: #ffffff;
            }
            QListWidget::item:hover:!selected {
                background: #3a3a3a;
            }
        """)
        layout.addWidget(self.config_list, stretch=1)
        
        btn_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load Selected")
        load_btn.setStyleSheet("background-color: #1976d2; color: white;")
        load_btn.clicked.connect(self._on_load)
        btn_layout.addWidget(load_btn)
        
        new_btn = QPushButton("+ New")
        new_btn.setStyleSheet("background-color: #27ae60; color: white;")
        new_btn.clicked.connect(self._on_new)
        btn_layout.addWidget(new_btn)
        
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self._on_rename)
        btn_layout.addWidget(rename_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #c0392b; color: white;")
        delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _refresh_list(self) -> None:
        self.config_list.clear()
        configs = self.config_manager.list_configs()
        
        for config in configs:
            item = QListWidgetItem(f"📁 {config['name']}  ({config['sources']} sources, {config['destinations']} dests)")
            item.setData(1, config['name'])
            self.config_list.addItem(item)
        
        if not configs:
            self.config_list.addItem("No saved configurations")
        
        if self.active_config_name:
            for i in range(self.config_list.count()):
                item = self.config_list.item(i)
                if item.data(1) == self.active_config_name:
                    item.setSelected(True)
                    self.config_list.setCurrentItem(item)
                    break
    
    def _on_new(self) -> None:
        name, ok = QInputDialog.getText(self, "New Configuration", "Enter configuration name:")
        if ok and name:
            if self.parent_setup and hasattr(self.parent_setup, '_save_as_config'):
                if self.parent_setup._save_as_config(name):
                    self.config_saved.emit(name)
                    self._refresh_list()
                    QMessageBox.information(self, "Success", f"Configuration '{name}' saved.")
                else:
                    QMessageBox.warning(self, "Warning", "Add at least one source and one destination folder first.")
    
    def _on_load(self) -> None:
        current = self.config_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Warning", "Select a configuration first.")
            return
        
        name = current.data(1)
        if not name:
            return
        
        config = self.config_manager.load(name)
        if config:
            self.config_loaded.emit(config, name)
            self.close()
    
    def _on_rename(self) -> None:
        current = self.config_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Warning", "Select a configuration first.")
            return
        
        old_name = current.data(1)
        if not old_name:
            return
        
        new_name, ok = QInputDialog.getText(self, "Rename Configuration", "Enter new name:", text=old_name)
        if ok and new_name and new_name != old_name:
            if self.config_manager.rename(old_name, new_name):
                self._refresh_list()
                QMessageBox.information(self, "Success", f"Renamed to '{new_name}'.")
            else:
                QMessageBox.warning(self, "Error", "Could not rename. Name might already exist.")
    
    def _on_delete(self) -> None:
        current = self.config_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Warning", "Select a configuration first.")
            return
        
        name = current.data(1)
        if not name:
            return
        
        if self.config_manager.delete(name):
            self._refresh_list()


class SetupPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_folders: list[Path] = []
        self.dest_folders: list[tuple[str, Path]] = []
        self.folder_count = 0
        self.config_manager = ConfigManager()
        self.active_config_name: Optional[str] = None
        
        self._create_layout()
        
    def _create_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)
        
        title_layout = QHBoxLayout()
        title = QLabel("SortMyMedia")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4fc3f7;")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        self.config_name_label = QLabel("")
        self.config_name_label.setStyleSheet("color: #888888; font-size: 12px;")
        title_layout.addWidget(self.config_name_label)
        
        config_btn = QPushButton("⚙️ Config")
        config_btn.clicked.connect(self._show_config_menu)
        title_layout.addWidget(config_btn)
        
        layout.addLayout(title_layout)
        
        subtitle = QLabel("Sort your files into destination folders")
        subtitle.setStyleSheet("color: #888888;")
        layout.addWidget(subtitle)
        
        folders_container = QWidget()
        folders_layout = QHBoxLayout(folders_container)
        folders_layout.setContentsMargins(0, 15, 0, 0)
        
        sources_widget = QWidget()
        sources_layout = QVBoxLayout(sources_widget)
        sources_layout.setContentsMargins(0, 0, 10, 0)
        
        sources_label = QLabel("Source Folders")
        sources_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        sources_layout.addWidget(sources_label)
        
        self.source_list = QListWidget()
        self.source_list.setStyleSheet("""
            QListWidget {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                outline: 0;
            }
            QListWidget::item {
                background: transparent;
                color: #e0e0e0;
                padding: 10px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background: #0d47a1;
                color: #ffffff;
            }
            QListWidget::item:hover:!selected {
                background: #3a3a3a;
            }
        """)
        sources_layout.addWidget(self.source_list)
        
        sources_btn_layout = QHBoxLayout()
        add_source_btn = QPushButton("+ Add Source")
        add_source_btn.clicked.connect(self._add_source)
        sources_btn_layout.addWidget(add_source_btn)
        
        remove_source_btn = QPushButton("- Remove")
        remove_source_btn.setStyleSheet("background-color: #c0392b;")
        remove_source_btn.clicked.connect(self._remove_source)
        sources_btn_layout.addWidget(remove_source_btn)
        sources_layout.addLayout(sources_btn_layout)
        
        dests_widget = QWidget()
        dests_layout = QVBoxLayout(dests_widget)
        dests_layout.setContentsMargins(10, 0, 0, 0)
        
        dests_label = QLabel("Destination Folders")
        dests_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        dests_layout.addWidget(dests_label)
        
        self.dest_list = QListWidget()
        self.dest_list.setStyleSheet("""
            QListWidget {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                outline: 0;
            }
            QListWidget::item {
                background: transparent;
                color: #e0e0e0;
                padding: 10px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background: #0d47a1;
                color: #ffffff;
            }
            QListWidget::item:hover:!selected {
                background: #3a3a3a;
            }
        """)
        dests_layout.addWidget(self.dest_list)
        
        dests_btn_layout = QHBoxLayout()
        add_dest_btn = QPushButton("+ Add Destination")
        add_dest_btn.clicked.connect(self._add_destination)
        dests_btn_layout.addWidget(add_dest_btn)
        
        remove_dest_btn = QPushButton("- Remove")
        remove_dest_btn.setStyleSheet("background-color: #c0392b;")
        remove_dest_btn.clicked.connect(self._remove_destination)
        dests_btn_layout.addWidget(remove_dest_btn)
        dests_layout.addLayout(dests_btn_layout)
        
        folders_layout.addWidget(sources_widget)
        folders_layout.addWidget(dests_widget)
        layout.addWidget(folders_container, stretch=1)
        
        bottom_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Reset Selections")
        clear_btn.setStyleSheet("background-color: #555555;")
        clear_btn.clicked.connect(self._clear_config)
        bottom_layout.addWidget(clear_btn)
        
        self.status_label = QLabel("Add at least one source and one destination folder")
        self.status_label.setStyleSheet("color: #888888;")
        bottom_layout.addWidget(self.status_label)
        
        bottom_layout.addStretch()
        
        self.start_btn = QPushButton("Start Sorting")
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("background-color: #1976d2; color: white;")
        bottom_layout.addWidget(self.start_btn)
        
        layout.addLayout(bottom_layout)
    
    def _show_config_menu(self) -> None:
        dialog = ConfigDialog(self.config_manager, self, self.active_config_name)
        dialog.setModal(True)
        dialog.config_loaded.connect(self._on_config_loaded)
        dialog.config_saved.connect(self._on_config_saved)
        dialog.exec()
    
    def _on_config_loaded(self, config, name) -> None:
        self.source_folders = []
        self.dest_folders = []
        self.source_list.clear()
        self.dest_list.clear()
        self.folder_count = 0
        self.active_config_name = name
        
        for path_str in config.sources:
            path = Path(path_str)
            if path.exists():
                self.source_folders.append(path)
                self.source_list.addItem(f"📁 {path.name}")
        
        for dest in config.destinations:
            dest_path = Path(dest.path)
            if dest_path.exists():
                self.folder_count += 1
                self.dest_folders.append((dest.name, dest_path))
                self.dest_list.addItem(f"📂 {dest.name} ({dest_path.name})")
        
        self._check_ready()
        self._update_config_label()
    
    def _on_config_saved(self, name: str) -> None:
        self.active_config_name = name
        self._update_config_label()

    def _update_config_label(self) -> None:
        if self.active_config_name:
            self.config_name_label.setText(f"📂 {self.active_config_name}")
            self.config_name_label.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold;")
        else:
            self.config_name_label.setText("No config loaded")
            self.config_name_label.setStyleSheet("color: #888888; font-size: 12px;")

    def _clear_config(self) -> None:
        self.source_folders = []
        self.dest_folders = []
        self.source_list.clear()
        self.dest_list.clear()
        self.folder_count = 0
        self.active_config_name = None
        self._update_config_label()
        self._check_ready()

    def _save_as_config(self, name: str) -> bool:
        if not self.source_folders or not self.dest_folders:
            return False
        self.config_manager.save(self.source_folders, self.dest_folders, name)
        return True
    
    def _export_config(self) -> None:
        if not self.source_folders or not self.dest_folders:
            QMessageBox.warning(self, "Warning", "Add at least one source and one destination folder first.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "", 
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if path:
            export_path = Path(path)
            if export_path.suffix not in ['.yaml', '.yml']:
                export_path = export_path.with_suffix('.yaml')
            
            self.config_manager.export_to_file(self.source_folders, self.dest_folders, export_path)
            QMessageBox.information(self, "Success", f"Configuration exported to:\n{export_path}")
    
    def _import_config(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "",
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if path:
            config = self.config_manager.import_from_file(Path(path))
            if config is None:
                QMessageBox.warning(self, "Error", "Failed to load configuration from file.")
                return
            
            name, ok = QInputDialog.getText(self, "Import Configuration", "Enter a name for this configuration:")
            if not ok or not name:
                return
            
            self.source_folders = []
            self.dest_folders = []
            self.source_list.clear()
            self.dest_list.clear()
            self.folder_count = 0
            
            for path_str in config.sources:
                path_obj = Path(path_str)
                if path_obj.exists():
                    self.source_folders.append(path_obj)
                    self.source_list.addItem(f"📁 {path_obj.name}")
            
            for dest in config.destinations:
                dest_path = Path(dest.path)
                if dest_path.exists():
                    self.folder_count += 1
                    self.dest_folders.append((dest.name, dest_path))
                    self.dest_list.addItem(f"📂 {dest.name} ({dest_path.name})")
            
            self.config_manager.save(self.source_folders, self.dest_folders, name)
            self._check_ready()
            QMessageBox.information(self, "Success", f"Configuration '{name}' imported and saved.")
        
    def _add_source(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if path:
            path = Path(path)
            if path not in self.source_folders:
                self.source_folders.append(path)
                self.source_list.addItem(f"📁 {path.name}")
                self._check_ready()
    
    def _add_destination(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if path:
            path = Path(path)
            name = path.name
            self.dest_folders.append((name, path))
            self.dest_list.addItem(f"📂 {name}")
            self._check_ready()
    
    def _remove_source(self) -> None:
        row = self.source_list.currentRow()
        if row >= 0:
            self.source_list.takeItem(row)
            del self.source_folders[row]
            self._check_ready()
    
    def _remove_destination(self) -> None:
        row = self.dest_list.currentRow()
        if row >= 0:
            self.dest_list.takeItem(row)
            del self.dest_folders[row]
            self._check_ready()
    
    def _check_ready(self) -> None:
        if self.source_folders and self.dest_folders:
            self.start_btn.setEnabled(True)
            self.status_label.setText(f"Ready! {len(self.source_folders)} source(s), {len(self.dest_folders)} destination(s)")
            self.status_label.setStyleSheet("color: #4caf50;")
        else:
            self.start_btn.setEnabled(False)
            self.status_label.setStyleSheet("color: #888888;")
            if not self.source_folders and not self.dest_folders:
                self.status_label.setText("Add at least one source and one destination folder")
            elif not self.source_folders:
                self.status_label.setText("Add at least one source folder")
            else:
                self.status_label.setText("Add at least one destination folder")


class ImageViewer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #121212; border-radius: 8px;")
        self._pixmap: Optional[QPixmap] = None
    
    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()
    
    def clear(self) -> None:
        self._pixmap = None
        self.setText("No preview available")
        self.setStyleSheet("background-color: #121212; border-radius: 8px; color: #666666; font-size: 18px;")
    
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self._pixmap:
            scaled = self._pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter = QPainter(self)
            painter.drawPixmap(x, y, scaled)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.session = Session()
        self.file_manager = FileManager()
        self.current_pixmap: Optional[QPixmap] = None
        
        self.setWindowTitle("SortMyMedia")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(DARK_STYLE)
        
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        
        self.setup_page = SetupPage()
        self.setup_page.start_btn.clicked.connect(self._on_start_sorting)
        
        self.main_page = QWidget()
        self.pages.addWidget(self.setup_page)
        self.pages.addWidget(self.main_page)
        
    def _on_start_sorting(self) -> None:
        if not self.setup_page.source_folders:
            self.close()
            return
        
        for path in self.setup_page.source_folders:
            self.session.add_source_folder(path)
        
        for name, path in self.setup_page.dest_folders:
            self.session.add_destination_folder(path, name)
        
        self._create_main_layout()
        self.pages.setCurrentIndex(1)
        self._update_viewer()
    
    def _back_to_setup(self) -> None:
        self.pages.setCurrentIndex(0)
    
    def _create_main_layout(self) -> None:
        layout = QVBoxLayout(self.main_page)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        
        header = QWidget()
        header.setFixedHeight(50)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        back_btn = QPushButton("← Config")
        back_btn.setStyleSheet("background-color: #555555; padding: 5px 10px;")
        back_btn.clicked.connect(self._back_to_setup)
        header_layout.addWidget(back_btn)
        
        self.progress_label = QLabel("File 0/0")
        self.progress_label.setStyleSheet("font-size: 14px; margin-left: 10px;")
        header_layout.addWidget(self.progress_label)
        
        self.file_name_label = QLabel("")
        self.file_name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.file_name_label, stretch=1)
        
        self.file_size_label = QLabel("")
        self.file_size_label.setStyleSheet("color: #888888;")
        header_layout.addWidget(self.file_size_label)
        
        layout.addWidget(header)
        
        self.viewer = ImageViewer()
        self.viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.viewer, stretch=1)
        
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 10, 0, 10)
        
        nav_frame = QWidget()
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        prev_btn = QPushButton("◀ Previous")
        prev_btn.clicked.connect(self._previous_file)
        nav_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("Next ▶")
        next_btn.clicked.connect(self._next_file)
        nav_layout.addWidget(next_btn)
        
        controls_layout.addWidget(nav_frame)
        
        controls_layout.addStretch()
        
        self.sort_buttons_frame = QWidget()
        self.sort_buttons_layout = QHBoxLayout(self.sort_buttons_frame)
        self.sort_buttons_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(self.sort_buttons_frame)
        
        layout.addWidget(controls)
        
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background-color: #1a1a1a; color: #888888;")
        self.setStatusBar(self.status_bar)
    
    def _get_current_file(self) -> tuple[Optional[FolderConfig], Optional[Path]]:
        for source in self.session.source_folders:
            if source.current_file and source.current_file.exists():
                return source, source.current_file
        return None, None
    
    def _update_viewer(self) -> None:
        for i in reversed(range(self.sort_buttons_layout.count())):
            widget = self.sort_buttons_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        source, current = self._get_current_file()
        
        if current is None:
            self.viewer.clear()
            self.viewer.setText("🎉 All files have been sorted!")
            self.file_name_label.setText("All done!")
            self.file_size_label.setText("")
            self.progress_label.setText("File 0/0")
            return
        
        file_size = self.file_manager.get_file_size(current)
        self.file_name_label.setText(current.name)
        self.file_size_label.setText(file_size)
        
        total = self.session.get_total_files()
        processed = self.session.get_processed_files()
        self.progress_label.setText(f"File {processed + 1}/{total}")
        
        self._display_file(current)
        
        colors = ["#3498db", "#2ecc71", "#9b59b6", "#e74c3c", "#f39c12", "#1abc9c"]
        for i, dest in enumerate(self.session.destination_folders):
            btn = QPushButton(f"📂 {dest.name}")
            btn.setStyleSheet(f"background-color: {colors[i % len(colors)]}; border-radius: 6px; padding: 10px 15px;")
            btn.clicked.connect(lambda _, d=dest: self._sort_file(d))
            self.sort_buttons_layout.addWidget(btn)
        
        self._update_status()
    
    def _display_file(self, path: Path) -> None:
        ext = path.suffix.lower()
        image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
        
        if ext in image_exts:
            self._display_image(path)
        elif ext == '.pdf' and PYMUPDF_AVAILABLE:
            self._display_pdf(path)
        elif ext in video_exts:
            self.viewer.clear()
            self.viewer.setText(f"🎬 {ext.upper()[1:]} video\n\n{path.name}")
        else:
            self.viewer.clear()
            self.viewer.setText(f"📄 {ext.upper()} file")
    
    def _display_image(self, path: Path) -> None:
        if not PIL_AVAILABLE:
            self.viewer.clear()
            self.viewer.setText("📷 Image\n(PIL not installed)")
            return
        
        try:
            img = Image.open(path)
            canvas_w = self.viewer.width() or 800
            canvas_h = self.viewer.height() or 600
            
            img_w, img_h = img.size
            scale = min(canvas_w / img_w, canvas_h / img_h, 1.0)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            img_rgb = img.convert("RGB")
            qimage = QImage(img_rgb.tobytes(), new_w, new_h, new_w * 3, QImage.Format.Format_RGB888)
            self.current_pixmap = QPixmap.fromImage(qimage)
            self.viewer.set_pixmap(self.current_pixmap)
        except Exception as e:
            self.viewer.clear()
            self.viewer.setText(f"Error loading image\n{e}")
    
    def _display_pdf(self, path: Path) -> None:
        try:
            doc = fitz.open(path)
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            
            canvas_w = self.viewer.width() or 800
            canvas_h = self.viewer.height() or 600
            
            scale = min(canvas_w / pix.width, canvas_h / pix.height, 1.0)
            new_w = int(pix.width * scale)
            new_h = int(pix.height * scale)
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            qimage = QImage(img.tobytes(), new_w, new_h, new_w * 3, QImage.Format.Format_RGB888)
            self.current_pixmap = QPixmap.fromImage(qimage)
            self.viewer.set_pixmap(self.current_pixmap)
            
            doc.close()
        except Exception as e:
            self.viewer.clear()
            self.viewer.setText(f"Error loading PDF\n{e}")
    
    def _sort_file(self, dest: FolderConfig) -> None:
        source, current = self._get_current_file()
        if source is None or current is None:
            return
        
        success = self.session.move_file_to_destination(source, dest)
        
        if success:
            self._update_viewer()
        else:
            QMessageBox.critical(self, "Error", f"Failed to move file: {current.name}")
    
    def _skip_file(self) -> None:
        source, _ = self._get_current_file()
        if source and source.has_next:
            source.advance()
            self._update_viewer()
    
    def _previous_file(self) -> None:
        source, _ = self._get_current_file()
        if source and source.has_previous:
            source.retreat()
            self._update_viewer()
    
    def _next_file(self) -> None:
        source, _ = self._get_current_file()
        if source and source.has_next:
            source.advance()
            self._update_viewer()
    
    def _update_status(self) -> None:
        total = self.session.get_total_files()
        processed = self.session.get_processed_files()
        remaining = total - processed
        self.status_bar.showMessage(f"📁 Files: {remaining} remaining ({processed}/{total} processed)")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
