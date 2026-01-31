import os
from collections.abc import Iterator
from pathlib import Path

CPU_CORES = os.cpu_count() or 1
STATE_FOLDER: str = str(Path("~/.blends").expanduser())
STATE_FOLDER_DEBUG = Path(STATE_FOLDER) / "debug"


Path(STATE_FOLDER).mkdir(mode=0o700, exist_ok=True, parents=True)
Path(STATE_FOLDER_DEBUG).mkdir(mode=0o700, exist_ok=True, parents=True)


class _Context:
    def __init__(self) -> None:
        self._feature_flags: set[str] = set[str]()
        self._multi_path: set[Path] = set[Path]()

        self.recursion_limit: int | None = None
        self.working_dir: Path | None = None

    def set_feature_flag(self, feature_flag: str) -> None:
        self._feature_flags.add(feature_flag)

    def has_feature_flag(self, feature_flag: str) -> bool:
        return feature_flag in self._feature_flags

    def add_multi_path(self, path: Path) -> None:
        self._multi_path.add(path)

    def iterate_multi_paths(self) -> Iterator[Path]:
        return iter(self._multi_path)


ctx = _Context()
