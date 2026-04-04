import shutil
from pathlib import Path


class FileManager:
    @staticmethod
    def move_file(source: Path, destination_folder: Path) -> bool:
        try:
            destination_folder.mkdir(parents=True, exist_ok=True)
            dest_path = destination_folder / source.name
            
            if dest_path.exists():
                return False
            
            shutil.move(str(source), str(dest_path))
            return True
        except Exception:
            return False

    @staticmethod
    def file_exists(path: Path) -> bool:
        return path.exists()

    @staticmethod
    def get_file_size(path: Path) -> str:
        size = path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
