import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict, field


@dataclass
class FolderConfigData:
    name: str
    path: str
    key: str = ""


@dataclass
class KeyBindings:
    previous: str = "Left"
    next: str = "Right"
    undo: str = "Z"
    destinations: dict[str, str] = field(default_factory=dict)


@dataclass
class AppConfig:
    version: str = "1.0"
    sources: list = None
    destinations: list = None
    keybindings: KeyBindings = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.destinations is None:
            self.destinations = []
        if self.keybindings is None:
            self.keybindings = KeyBindings()


class ConfigManager:
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".sortmymedia"
        self.config_dir = config_dir
        self.configs_dir = self.config_dir / "configs"
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        self.default_config_path = self.config_dir / "config.yaml"
        self.last_config_file = self.config_dir / ".last_config"

    def _get_config_path(self, name: str) -> Path:
        safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in name)
        return self.configs_dir / f"{safe_name}.yaml"

    def save(self, sources: list[Path], destinations: list[tuple[str, Path]], 
             name: str, keybindings: Optional[KeyBindings] = None) -> Path:
        path = self._get_config_path(name)

        config = AppConfig(
            sources=[str(s) for s in sources],
            destinations=[
                FolderConfigData(name=dest_name, path=str(dest_path), key=key or "")
                for dest_name, dest_path, key in destinations
            ],
            keybindings=keybindings or KeyBindings()
        )

        with open(path, 'w') as f:
            yaml.dump(asdict(config), f, default_flow_style=False, sort_keys=False)

        with open(self.last_config_file, 'w') as f:
            f.write(name)

        return path

    def load(self, name: str) -> Optional[AppConfig]:
        path = self._get_config_path(name)
        return self._load_from_path(path)

    def _load_from_path(self, path: Path) -> Optional[AppConfig]:
        if not path.exists():
            return None

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        kb_data = data.get('keybindings', {})
        keybindings = KeyBindings(
            previous=kb_data.get('previous', 'Left'),
            next=kb_data.get('next', 'Right'),
            undo=kb_data.get('undo', 'Z'),
            destinations=kb_data.get('destinations', {})
        )

        return AppConfig(
            version=data.get('version', '1.0'),
            sources=data.get('sources', []),
            destinations=[
                FolderConfigData(
                    name=d['name'], 
                    path=d['path'],
                    key=d.get('key', '')
                )
                for d in data.get('destinations', [])
            ],
            keybindings=keybindings
        )

    def delete(self, name: str) -> bool:
        path = self._get_config_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def rename(self, old_name: str, new_name: str) -> Optional[Path]:
        old_path = self._get_config_path(old_name)
        new_path = self._get_config_path(new_name)
        
        if not old_path.exists():
            return None
        
        if new_path.exists():
            return None
        
        old_path.rename(new_path)
        return new_path

    def list_configs(self) -> list[dict]:
        configs = []
        
        for config_file in sorted(self.configs_dir.glob("*.yaml")):
            config = self._load_from_path(config_file)
            if config:
                source_count = len(config.sources)
                dest_count = len(config.destinations)
                configs.append({
                    'name': config_file.stem,
                    'path': config_file,
                    'sources': source_count,
                    'destinations': dest_count,
                    'modified': config_file.stat().st_mtime
                })
        
        return configs

    def get_last_config_name(self) -> Optional[str]:
        if self.last_config_file.exists():
            return self.last_config_file.read_text().strip()
        return None

    def export_to_file(self, sources: list[Path], destinations: list[tuple[str, Path]],
                       path: Path, keybindings: Optional[KeyBindings] = None) -> Path:
        config = AppConfig(
            sources=[str(s) for s in sources],
            destinations=[
                FolderConfigData(name=dest_name, path=str(dest_path), key=key or "")
                for dest_name, dest_path, key in destinations
            ],
            keybindings=keybindings or KeyBindings()
        )

        with open(path, 'w') as f:
            yaml.dump(asdict(config), f, default_flow_style=False, sort_keys=False)

        return path

    def import_from_file(self, path: Path) -> Optional[AppConfig]:
        return self._load_from_path(path)
