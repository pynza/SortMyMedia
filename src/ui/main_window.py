from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QListWidget, QFrame, QMessageBox,
    QSizePolicy, QScrollArea, QStatusBar, QStackedWidget, QInputDialog,
    QListWidgetItem, QDialog, QSlider, QFormLayout, QLineEdit
)
from PyQt6.QtCore import pyqtSignal, QTimer, QUrl, Qt, QSize, QObject
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QIcon, QImage, QKeyEvent, QMouseEvent
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
QScrollBar:vertical {
    background: #2a2a2a;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #555555;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #666666;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: #2a2a2a;
    height: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #555555;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #666666;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""


class InputDialog(QDialog):
    def __init__(self, title, label, parent=None, default_text=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        self.setStyleSheet(DARK_STYLE + "QDialog { border-radius: 12px; }")
        self._result = ""
        
        central = QWidget()
        central.setObjectName("dialog_central")
        central.setStyleSheet("""
            QWidget#dialog_central {
                background-color: #1e1e1e;
                border-radius: 12px;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.addWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 14px;")
        layout.addWidget(lbl)
        
        self.input = QLineEdit(default_text)
        self.input.setStyleSheet("padding: 8px; font-size: 14px;")
        layout.addWidget(self.input)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("background-color: #1976d2;")
        ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_ok(self):
        self._result = self.input.text()
        if self._result:
            self.accept()
    
    def get_result(self):
        return self._result


class MessageDialog(QDialog):
    DIALOG_STYLES = {
        "info": "#4fc3f7",
        "warning": "#ffa726",
        "error": "#ef5350",
        "success": "#66bb6a",
    }
    
    def __init__(self, title, message, dialog_type="info", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        color = self.DIALOG_STYLES.get(dialog_type, "#4fc3f7")
        self.setStyleSheet(DARK_STYLE + f"""
            QDialog {{ border-radius: 12px; }}
            QLabel#icon {{ color: {color}; font-size: 32px; }}
        """)
        
        central = QWidget()
        central.setObjectName("dialog_central")
        central.setStyleSheet("""
            QWidget#dialog_central {
                background-color: #1e1e1e;
                border-radius: 12px;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.addWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
        icon_label = QLabel(icons.get(dialog_type, "ℹ️"))
        icon_label.setObjectName("icon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        msg_label = QLabel(message)
        msg_label.setStyleSheet("font-size: 13px; color: #e0e0e0;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("background-color: #1976d2;")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)


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
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(DARK_STYLE + "QDialog { border-radius: 12px; }")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        self._drag_pos = None
        self._create_layout()
        self._refresh_list()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        if self._drag_pos:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        
    def _create_layout(self) -> None:
        central = QWidget()
        central.setObjectName("dialog_central")
        central.setStyleSheet("""
            QWidget#dialog_central {
                background-color: #1e1e1e;
                border-radius: 12px;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.addWidget(central)
        
        layout = QVBoxLayout(central)
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
        dialog = InputDialog("New Configuration", "Enter configuration name:", self)
        if dialog.exec() and dialog.get_result():
            name = dialog.get_result()
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
        
        dialog = InputDialog("Rename Configuration", "Enter new name:", self, old_name)
        if dialog.exec() and dialog.get_result():
            new_name = dialog.get_result()
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


class KeyCaptureHelper(QObject):
    def __init__(
        self,
        line_edit,
        key_name,
        keybindings,
        callback,
        display_name="",
        on_focus_in=None,
        on_focus_out=None,
    ):
        super().__init__()
        self.line_edit = line_edit
        self.key_name = key_name
        self.keybindings = keybindings
        self.callback = callback
        self.display_name = display_name or key_name
        self.on_focus_in = on_focus_in
        self.on_focus_out = on_focus_out

    def eventFilter(self, obj, event):
        if event.type() == event.Type.FocusIn:
            if self.on_focus_in:
                self.on_focus_in(self.line_edit, self.key_name, self.display_name)
        elif event.type() == event.Type.FocusOut:
            if self.on_focus_out:
                self.on_focus_out(self.line_edit)
        if event.type() == event.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
                return True
            
            modifiers = event.modifiers()
            key_text = ""
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                key_text += "Shift+"
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                key_text += "Ctrl+"
            if modifiers & Qt.KeyboardModifier.AltModifier:
                key_text += "Alt+"
            
            if event.text() and event.text().isprintable():
                key_text += event.text().upper()
            elif key == Qt.Key.Key_Left:
                key_text += "Left"
            elif key == Qt.Key.Key_Right:
                key_text += "Right"
            elif key == Qt.Key.Key_Up:
                key_text += "Up"
            elif key == Qt.Key.Key_Down:
                key_text += "Down"
            elif key == Qt.Key.Key_Space:
                key_text += "Space"
            elif key == Qt.Key.Key_Backspace:
                key_text += "Backspace"
            elif key == Qt.Key.Key_Delete:
                key_text += "Delete"
            elif Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                key_text += chr(key)
            elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
                key_text += chr(key)
            elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
                key_text += f"F{key - Qt.Key.Key_F1 + 1}"
            
            if key_text:
                self.line_edit.setText(key_text)
                self.keybindings[self.key_name] = key_text
                self.callback()
                return True
        
        return super().eventFilter(obj, event)


class KeyBindingsDialog(QDialog):
    keybindings_changed = pyqtSignal(dict)
    _KEYBIND_ACTIVE_STYLE = "border: 2px solid #4a9eff; background-color: #1a2838;"

    def __init__(self, keybindings: dict, destinations: list, parent=None):
        super().__init__(parent)
        self.keybindings = keybindings.copy()
        self.destinations = destinations
        self.capture_helpers = []
        self.active_lineedit = None
        self.setWindowTitle("Key Bindings")
        self.setMinimumWidth(400)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        self._drag_pos = None
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: #ffffff;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QLineEdit {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #4a9eff;
                font-weight: bold;
            }
            QLineEdit.active {
                border: 2px solid #4a9eff;
                background-color: #1a2838;
            }
            QLineEdit.duplicate {
                border: 2px solid #e74c3c;
                color: #e74c3c;
            }
        """)
        
        self._create_layout()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        if self._drag_pos:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
    
    def _create_layout(self) -> None:
        central = QWidget()
        central.setObjectName("dialog_central")
        central.setStyleSheet("""
            QWidget#dialog_central {
                background-color: #1e1e1e;
                border-radius: 12px;
            }
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.addWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        
        nav_label = QLabel("Navigation Keys")
        nav_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(nav_label)
        
        nav_frame = QFrame()
        nav_layout = QFormLayout(nav_frame)
        nav_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.prev_key = QLineEdit(self.keybindings.get('previous', 'Left'))
        self.prev_key.setReadOnly(True)
        self.prev_key.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self._setup_key_capture(self.prev_key, 'previous', 'Previous')
        nav_layout.addRow("Previous:", self.prev_key)
        
        self.next_key = QLineEdit(self.keybindings.get('next', 'Right'))
        self.next_key.setReadOnly(True)
        self.next_key.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self._setup_key_capture(self.next_key, 'next', 'Next')
        nav_layout.addRow("Next:", self.next_key)
        
        self.undo_key = QLineEdit(self.keybindings.get('undo', 'Z'))
        self.undo_key.setReadOnly(True)
        self.undo_key.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self._setup_key_capture(self.undo_key, 'undo', 'Undo')
        nav_layout.addRow("Undo:", self.undo_key)
        
        layout.addWidget(nav_frame)
        
        if self.destinations:
            dest_label = QLabel("Destination Folders")
            dest_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(dest_label)
            
            self.dest_widgets = {}
            dest_frame = QFrame()
            dest_layout = QFormLayout(dest_frame)
            dest_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            
            for i, dest in enumerate(self.destinations):
                name = dest[0]
                current_key = dest[2] if len(dest) > 2 else ''
                key_edit = QLineEdit(current_key)
                key_edit.setReadOnly(True)
                key_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
                key_name = f"dest_{i}"
                self._setup_key_capture(key_edit, key_name, f'{name}')
                dest_layout.addRow(f"{name}:", key_edit)
                self.dest_widgets[key_name] = key_edit
            
            layout.addWidget(dest_frame)
        
        hint_label = QLabel("Click a field and press a key to assign")
        hint_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(hint_label)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("background-color: #1976d2;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        self.warning_label = QLabel("⚠️ Keybindings are not saved in config")
        self.warning_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.warning_label)
    
    def _setup_key_capture(self, line_edit, key_name, display_name=""):
        def on_keyset():
            self.active_lineedit = line_edit
            self._check_duplicates()

        helper = KeyCaptureHelper(
            line_edit,
            key_name,
            self.keybindings,
            on_keyset,
            display_name=display_name,
            on_focus_in=self._on_capture_focus_in,
            on_focus_out=self._on_capture_focus_out,
        )
        line_edit.installEventFilter(helper)

        self.capture_helpers.append(helper)

    def _on_capture_focus_in(self, line_edit, key_name: str, display_name: str = "") -> None:
        self.active_lineedit = line_edit
        self._check_duplicates()

    def _on_capture_focus_out(self, line_edit) -> None:
        if self.active_lineedit == line_edit:
            self.active_lineedit = None
        self._check_duplicates()

    def _check_duplicates(self):
        duplicates = []
        seen = {}
        for key, value in self.keybindings.items():
            if value and value in seen:
                duplicates.append(key)
                duplicates.append(seen[value])
            elif value:
                seen[value] = key

        for helper in self.capture_helpers:
            helper.line_edit.setStyleSheet("")

        if duplicates:
            self.warning_label.setText(f"⚠️ Duplicate bindings: {list(set([self.keybindings.get(d, d) for d in duplicates]))}")
            self.warning_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
            for key in duplicates:
                for helper in self.capture_helpers:
                    if helper.key_name == key:
                        helper.line_edit.setStyleSheet("border: 2px solid #e74c3c; color: #e74c3c;")
        else:
            self.warning_label.setText("⚠️ Keybindings are not saved in config")
            self.warning_label.setStyleSheet("color: #888888; font-size: 11px;")

        if self.active_lineedit:
            active_key = None
            for h in self.capture_helpers:
                if h.line_edit == self.active_lineedit:
                    active_key = h.key_name
                    break
            if active_key is not None and active_key not in duplicates:
                self.active_lineedit.setStyleSheet(self._KEYBIND_ACTIVE_STYLE)
    
    def _save(self) -> None:
        duplicates = []
        seen = {}
        for key, value in self.keybindings.items():
            if value and value in seen:
                duplicates.append(value)
            elif value:
                seen[value] = key
        
        if duplicates:
            QMessageBox.warning(self, "Duplicate Key Bindings", 
                f"These keys are assigned multiple times: {duplicates}\n\nPlease fix before saving.")
            return
        
        self.keybindings_changed.emit(self.keybindings)
        self.accept()


class SetupPage(QWidget):
    keybindings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_folders: list[Path] = []
        self.dest_folders: list[tuple[str, Path, str]] = []
        self.folder_count = 0
        self.config_manager = ConfigManager()
        self.active_config_name: Optional[str] = None
        self.keybindings: dict = {
            'previous': 'Left',
            'next': 'Right',
            'undo': 'Z'
        }
        
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
        
        keys_btn = QPushButton("⌨️ Keys")
        keys_btn.clicked.connect(self._show_keybindings)
        title_layout.addWidget(keys_btn)
        
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
        
        self.keybindings = {
            'previous': 'Left',
            'next': 'Right',
            'undo': 'Z'
        }
        
        for path_str in config.sources:
            path = Path(path_str)
            if path.exists():
                self.source_folders.append(path)
                self.source_list.addItem(f"📁 {path.name}")
        
        for i, dest in enumerate(config.destinations):
            dest_path = Path(dest.path)
            if dest_path.exists():
                self.folder_count += 1
                key = dest.key if hasattr(dest, 'key') else ''
                self.dest_folders.append((dest.name, dest_path, key))
                if key:
                    self.keybindings[f'dest_{i}'] = key
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
        self.config_manager.save(self.source_folders, self.dest_folders, name, self.keybindings)
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
            
            self.config_manager.export_to_file(self.source_folders, self.dest_folders, export_path, self.keybindings)
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
            
            dialog = InputDialog("Import Configuration", "Enter a name for this configuration:", self)
            if not dialog.exec():
                return
            name = dialog.get_result()
            if not name:
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
                    key = dest.key if hasattr(dest, 'key') else ''
                    self.dest_folders.append((dest.name, dest_path, key))
                    self.dest_list.addItem(f"📂 {dest.name} ({dest_path.name})")
            
            self.config_manager.save(self.source_folders, self.dest_folders, name, self.keybindings)
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
    
    def _show_keybindings(self) -> None:
        dialog = KeyBindingsDialog(self.keybindings, self.dest_folders, self)
        dialog.keybindings_changed.connect(self._on_keybindings_changed)
        dialog.exec()
    
    def _on_keybindings_changed(self, keybindings: dict) -> None:
        self.keybindings = keybindings
        for i in range(len(self.dest_folders)):
            key = keybindings.get(f'dest_{i}', '')
            name, path, _ = self.dest_folders[i]
            self.dest_folders[i] = (name, path, key)
        self.keybindings_changed.emit(self.keybindings)
    
    def _add_destination(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if path:
            path = Path(path)
            name = path.name
            self.dest_folders.append((name, path, ''))
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


class ClickableSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._dragging = False
    
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._update_value_from_pos(ev.position().x())
        super().mousePressEvent(ev)
    
    def mouseMoveEvent(self, ev):
        if self._dragging:
            self._update_value_from_pos(ev.position().x())
        super().mouseMoveEvent(ev)
    
    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(ev)
    
    def _update_value_from_pos(self, x):
        try:
            min_val, max_val = self.minimum(), self.maximum()
            if max_val > min_val:
                ratio = max(0, min(1, x / self.width()))
                value = int(min_val + (max_val - min_val) * ratio)
                self.setValue(value)
                self.sliderMoved.emit(value)
        except Exception:
            pass


class VideoPlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(320, 180)
        self.video_widget.setStyleSheet("border-radius: 8px 8px 0 0;")
        self.video_widget.mousePressEvent = self._on_video_click
        layout.addWidget(self.video_widget, stretch=1)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.9);
                border-radius: 0 0 8px 8px;
            }
            QLabel {
                color: #cccccc;
                font-size: 12px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                padding: 6px 8px;
                border-radius: 4px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            ClickableSlider {
                background: transparent;
                border: none;
                height: 20px;
            }
            ClickableSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #3a3a3a;
                border-radius: 2px;
            }
            ClickableSlider::handle:horizontal {
                background: #4a9eff;
                width: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }
            ClickableSlider::sub-page:horizontal {
                background: #4a9eff;
                border-radius: 2px;
            }
        """)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(12, 6, 12, 6)
        controls_layout.setSpacing(4)
        
        self.progress_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.sliderMoved.connect(self._seek)
        controls_layout.addWidget(self.progress_slider)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.play_btn.clicked.connect(self._toggle_play)
        buttons_layout.addWidget(self.play_btn)
        
        self.position_label = QLabel("00:00 / 00:00")
        buttons_layout.addWidget(self.position_label)
        
        buttons_layout.addStretch()
        
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(8)
        
        self.volume_btn = QPushButton("🔊")
        self.volume_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.volume_btn.clicked.connect(self._toggle_mute)
        volume_layout.addWidget(self.volume_btn)
        
        self.volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.valueChanged.connect(self._set_volume)
        volume_layout.addWidget(self.volume_slider)
        
        buttons_layout.addLayout(volume_layout)
        
        controls_layout.addLayout(buttons_layout)
        layout.addWidget(controls_frame)
        
        self.media_player.positionChanged.connect(self._position_changed)
        self.media_player.durationChanged.connect(self._duration_changed)
        self.media_player.playbackStateChanged.connect(self._playback_state_changed)
    
    def _on_video_click(self, event):
        self._toggle_play()
    
    def load_video(self, path: Path) -> None:
        url = QUrl.fromLocalFile(str(path))
        self.media_player.setSource(url)
        self.media_player.play()
    
    def clear(self) -> None:
        self.media_player.stop()
        self.position_label.setText("00:00 / 00:00")
        self.progress_slider.setValue(0)
    
    def stop(self) -> None:
        self.media_player.stop()
    
    def _toggle_play(self) -> None:
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def _seek(self, position: int) -> None:
        self.media_player.setPosition(position)
    
    def _position_changed(self, position: int) -> None:
        self.progress_slider.setValue(position)
        duration = self.media_player.duration()
        self.position_label.setText(f"{self._format_time(position)} / {self._format_time(duration)}")
    
    def _duration_changed(self, duration: int) -> None:
        self.progress_slider.setRange(0, duration)
    
    def _playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")
    
    def _toggle_mute(self) -> None:
        if self.audio_output.isMuted():
            self.audio_output.setMuted(False)
            self.volume_btn.setText("🔊")
        else:
            self.audio_output.setMuted(True)
            self.volume_btn.setText("🔇")
    
    def _set_volume(self, value: int) -> None:
        self.audio_output.setVolume(value / 100)
        if value == 0:
            self.volume_btn.setText("🔇")
        elif value < 50:
            self.volume_btn.setText("🔉")
        else:
            self.volume_btn.setText("🔊")
    
    def _format_time(self, ms: int) -> str:
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


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
        self.setup_page.keybindings_changed.connect(self._on_keybindings_changed)
        
        self.main_page = QWidget()
        self.pages.addWidget(self.setup_page)
        self.pages.addWidget(self.main_page)
        
        self.keybindings: dict = {
            'previous': 'Left',
            'next': 'Right',
            'undo': 'Z'
        }
        self._dest_buttons: dict[str, QPushButton] = {}
        
    def _on_start_sorting(self) -> None:
        if not self.setup_page.source_folders:
            self.close()
            return
        
        for path in self.setup_page.source_folders:
            self.session.add_source_folder(path)
        
        for name, path, key in self.setup_page.dest_folders:
            self.session.add_destination_folder(path, name)
        
        self.keybindings = self.setup_page.keybindings.copy()
        self._create_main_layout()
        self.pages.setCurrentIndex(1)
        self._update_viewer()
    
    def _on_keybindings_changed(self, keybindings: dict) -> None:
        self.keybindings = keybindings.copy()
    
    def _back_to_setup(self) -> None:
        self.video_player.stop()
        self.session = Session()
        self.pages.setCurrentIndex(0)
    
    def _create_main_layout(self) -> None:
        old_layout = self.main_page.layout()
        if old_layout:
            QWidget().setLayout(old_layout)
        
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
        
        self.viewer_container = QStackedWidget()
        self.image_viewer = ImageViewer()
        self.video_player = VideoPlayerWidget()
        self.viewer_container.addWidget(self.image_viewer)
        self.viewer_container.addWidget(self.video_player)
        self.viewer_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.viewer_container, stretch=1)
        
        self.viewer = self.image_viewer
        
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 10, 0, 10)
        
        nav_frame = QWidget()
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self._previous_file)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self._next_file)
        nav_layout.addWidget(self.next_btn)
        
        controls_layout.addWidget(nav_frame)
        
        controls_layout.addStretch()
        
        self.revert_btn = QPushButton("↩ Undo")
        self.revert_btn.setStyleSheet("background-color: #c0392b;")
        self.revert_btn.clicked.connect(self._revert_last)
        controls_layout.addWidget(self.revert_btn)
        
        controls_layout.addSpacing(20)
        
        self.sort_buttons_frame = QWidget()
        self.sort_buttons_layout = QHBoxLayout(self.sort_buttons_frame)
        self.sort_buttons_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(self.sort_buttons_frame)
        
        layout.addWidget(controls)
    
    def _get_current_file(self) -> tuple[Optional[FolderConfig], Optional[Path]]:
        for source in self.session.source_folders:
            if source.current_file and source.current_file.exists():
                return source, source.current_file
        return None, None
    
    def _update_viewer(self) -> None:
        self.video_player.stop()
        
        for i in reversed(range(self.sort_buttons_layout.count())):
            widget = self.sort_buttons_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        source, current = self._get_current_file()
        
        if current is None:
            self.viewer_container.setCurrentIndex(0)
            self.viewer = self.image_viewer
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
        self._dest_buttons.clear()
        for i, dest in enumerate(self.session.destination_folders):
            key = self.setup_page.keybindings.get(f'dest_{i}', '')
            key_text = f" [{key}]" if key else ""
            btn = QPushButton(f"📂 {dest.name}{key_text}")
            btn.setStyleSheet(f"background-color: {colors[i % len(colors)]}; border-radius: 6px; padding: 10px 15px;")
            btn.clicked.connect(lambda _, d=dest, b=btn: self._sort_file(d, b))
            self.sort_buttons_layout.addWidget(btn)
            if key:
                self._dest_buttons[key] = btn
    
    def _display_file(self, path: Path) -> None:
        ext = path.suffix.lower()
        image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
        
        if ext in image_exts:
            self.viewer_container.setCurrentIndex(0)
            self.viewer = self.image_viewer
            self._display_image(path)
        elif ext == '.pdf' and PYMUPDF_AVAILABLE:
            self.viewer_container.setCurrentIndex(0)
            self.viewer = self.image_viewer
            self._display_pdf(path)
        elif ext in video_exts:
            self.video_player.clear()
            self.viewer_container.setCurrentIndex(1)
            self.video_player.load_video(path)
        else:
            self.viewer_container.setCurrentIndex(0)
            self.viewer = self.image_viewer
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
    
    def _sort_file(self, dest: FolderConfig, btn: QPushButton = None) -> None:
        source, current = self._get_current_file()
        if source is None or current is None:
            return
        
        success = self.session.move_file_to_destination(source, dest)
        
        if success:
            if btn:
                self._flash_button(btn)
            self._update_viewer()
        else:
            MessageDialog("Error", f"Failed to move file: {current.name}", "error", self).exec()
    
    def _flash_button(self, btn: QPushButton) -> None:
        original_style = btn.styleSheet()
        btn.setStyleSheet(original_style + "border: 2px solid #4a9eff;")
        QTimer.singleShot(180, lambda b=btn, s=original_style: b.setStyleSheet(s))
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.pages.currentIndex() != 1:
            super().keyPressEvent(event)
            return
        
        key = event.key()
        modifiers = event.modifiers()
        key_text = ""
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            key_text += "Shift+"
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            key_text += "Ctrl+"
        if modifiers & Qt.KeyboardModifier.AltModifier:
            key_text += "Alt+"
        
        if event.text() and event.text().isprintable():
            key_text += event.text().upper()
        else:
            key_map = {
                Qt.Key_Left: "Left",
                Qt.Key_Right: "Right",
                Qt.Key_Up: "Up",
                Qt.Key_Down: "Down",
                Qt.Key_Space: "Space",
                Qt.Key_Backspace: "Backspace",
                Qt.Key_Delete: "Delete",
            }
            key_text += key_map.get(key, "")
        
        if key_text == self.keybindings.get('previous', 'Left'):
            self._previous_file()
        elif key_text == self.keybindings.get('next', 'Right'):
            self._next_file()
        elif key_text == self.keybindings.get('undo', 'Z'):
            self._revert_last()
        elif key_text in self._dest_buttons:
            btn = self._dest_buttons[key_text]
            for i, dest in enumerate(self.session.destination_folders):
                if self.setup_page.dest_folders[i][0] == dest.name:
                    self._sort_file(dest, btn)
                    break
        else:
            super().keyPressEvent(event)
    
    def _skip_file(self) -> None:
        source, _ = self._get_current_file()
        if source and source.has_next:
            source.advance()
            self._update_viewer()
    
    def _previous_file(self) -> None:
        source, _ = self._get_current_file()
        if source and source.has_previous:
            source.retreat()
            self._flash_button(self.prev_btn)
            self._update_viewer()

    def _next_file(self) -> None:
        source, _ = self._get_current_file()
        if source and source.has_next:
            source.advance()
            self._flash_button(self.next_btn)
            self._update_viewer()
    
    def _revert_last(self) -> None:
        if self.session.revert_last():
            self._flash_button(self.revert_btn)
            self._update_viewer()
        else:
            MessageDialog("Undo", "Nothing to undo", "warning", self).exec()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
