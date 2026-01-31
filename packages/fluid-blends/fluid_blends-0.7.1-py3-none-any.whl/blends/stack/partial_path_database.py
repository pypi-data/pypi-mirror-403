from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from blends.stack.partial_path.minimal_paths import (
    PerFilePartialPaths,
    PerFilePartialPathStats,
)

if TYPE_CHECKING:
    from blends.stack.partial_path.partial_path import PartialPath
    from blends.stack.view import StackGraphView, SymbolInterner

FileHandle = int


@dataclass(frozen=True, slots=True)
class StackGraphViewMetadata:
    file_handles: tuple[str, ...]
    symbol_id_to_string: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PartialPathFileRecord:
    file_handle: FileHandle
    file_path: str
    view_snapshot: StackGraphViewMetadata
    paths: tuple[PartialPath, ...]
    stats: PerFilePartialPathStats


def _clone_stats(stats: PerFilePartialPathStats) -> PerFilePartialPathStats:
    return PerFilePartialPathStats(
        seed_count=stats.seed_count,
        explored_count=stats.explored_count,
        accepted_count=stats.accepted_count,
        deduped_count=stats.deduped_count,
        discarded_count=stats.discarded_count,
        max_queue_size=stats.max_queue_size,
        limit_hits=dict(stats.limit_hits),
        length_histogram=dict(stats.length_histogram),
    )


def remap_symbol_id(
    symbol_id: int, metadata: StackGraphViewMetadata, target_symbols: SymbolInterner
) -> int:
    return target_symbols.intern(metadata.symbol_id_to_string[symbol_id])


@dataclass(slots=True)
class PartialPathDatabase:
    _records: dict[FileHandle, PartialPathFileRecord] = field(default_factory=dict)

    def put_file(
        self,
        file_handle: FileHandle,
        file_path: str,
        view: StackGraphView,
        partial_paths: PerFilePartialPaths,
    ) -> None:
        view_snapshot = StackGraphViewMetadata(
            file_handles=(file_path,),
            symbol_id_to_string=tuple(view.symbols.id_to_symbol),
        )
        self._records[file_handle] = PartialPathFileRecord(
            file_handle=file_handle,
            file_path=file_path,
            view_snapshot=view_snapshot,
            paths=partial_paths.paths,
            stats=_clone_stats(partial_paths.stats),
        )

    def get_file(self, file_handle: FileHandle) -> PartialPathFileRecord | None:
        record = self._records.get(file_handle)
        if record is None:
            return None
        return replace(record, stats=_clone_stats(record.stats))

    def drop_file(self, file_handle: FileHandle) -> None:
        self._records.pop(file_handle, None)

    def list_files(self) -> tuple[FileHandle, ...]:
        return tuple(sorted(self._records))
