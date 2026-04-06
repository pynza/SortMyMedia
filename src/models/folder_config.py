from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FolderConfig:
    name: str
    path: Path
    is_source: bool
    file_index: int = 0
    files: list[Path] = field(default_factory=list)

    def load_files(self) -> None:
        if not self.path.exists():
            self.files = []
            return
        self.files = sorted([
            f for f in self.path.iterdir()
            if f.is_file() and not f.name.startswith('.')
        ])
        self.file_index = 0

    @property
    def current_file(self) -> Optional[Path]:
        if 0 <= self.file_index < len(self.files):
            return self.files[self.file_index]
        return None

    @property
    def has_next(self) -> bool:
        return len(self.files) > 0

    @property
    def has_previous(self) -> bool:
        return len(self.files) > 0

    def advance(self) -> None:
        if len(self.files) > 0:
            self.file_index = (self.file_index + 1) % len(self.files)

    def retreat(self) -> None:
        if len(self.files) > 0:
            self.file_index = (self.file_index - 1) % len(self.files)

    def mark_as_moved(self) -> None:
        self.advance()
