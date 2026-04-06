from pathlib import Path
from typing import Optional

from src.models.folder_config import FolderConfig
from src.logic.file_manager import FileManager


class MoveHistory:
    def __init__(self, file_path: Path, source_path: Path, dest_path: Path):
        self.file_path = file_path
        self.source_path = source_path
        self.dest_path = dest_path


class Session:
    def __init__(self):
        self.source_folders: list[FolderConfig] = []
        self.destination_folders: list[FolderConfig] = []
        self._file_manager = FileManager()
        self._history: list[MoveHistory] = []

    def add_source_folder(self, path: Path, name: str = "") -> FolderConfig:
        folder_name = name or path.name
        config = FolderConfig(name=folder_name, path=path, is_source=True)
        config.load_files()
        self.source_folders.append(config)
        return config

    def add_destination_folder(self, path: Path, name: str = "") -> FolderConfig:
        folder_name = name or path.name
        config = FolderConfig(name=folder_name, path=path, is_source=False)
        self.destination_folders.append(config)
        return config

    def remove_source_folder(self, config: FolderConfig) -> None:
        if config in self.source_folders:
            self.source_folders.remove(config)

    def remove_destination_folder(self, config: FolderConfig) -> None:
        if config in self.destination_folders:
            self.destination_folders.remove(config)

    def move_file_to_destination(self, source_config: FolderConfig, dest_config: FolderConfig) -> bool:
        current_file = source_config.current_file
        if current_file is None:
            return False
        
        success = self._file_manager.move_file(current_file, dest_config.path)
        if success:
            self._history.append(MoveHistory(current_file, source_config.path, dest_config.path))
            source_config.mark_as_moved()
            source_config.load_files()
        return success

    def revert_last(self) -> bool:
        if not self._history:
            return False
        
        move = self._history.pop()
        if not move.file_path.exists():
            dest_file = move.dest_path / move.file_path.name
            if dest_file.exists():
                success = self._file_manager.move_file(dest_file, move.source_path)
                if success:
                    for source in self.source_folders:
                        if source.path == move.source_path:
                            source.load_files()
                            return True
        return False

    def get_total_files(self) -> int:
        return sum(len(f.files) for f in self.source_folders)

    def get_processed_files(self) -> int:
        return sum(f.file_index for f in self.source_folders)

    def get_active_source(self) -> Optional[FolderConfig]:
        for source in self.source_folders:
            if source.current_file is not None:
                return source
        return None
