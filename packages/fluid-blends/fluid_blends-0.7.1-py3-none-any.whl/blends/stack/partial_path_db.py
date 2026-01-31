from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeAlias

from blends.stack.partial_path_database import (
    FileHandle,
    PartialPathFileRecord,
    StackGraphViewMetadata,
    remap_symbol_id,
)
from blends.stack.view import SymbolInterner

if TYPE_CHECKING:
    from blends.stack.partial_path.partial_path import PartialPath
    from blends.stack.partial_path.partial_stacks import (
        PartialScopedSymbol,
        PartialScopeStack,
        PartialSymbolStack,
    )

PartialPathId: TypeAlias = tuple[FileHandle, int]
SymbolStackKeyEntry: TypeAlias = tuple[int, tuple[int, ...] | None]


@dataclass(frozen=True, slots=True)
class SymbolStackKey:
    symbols: tuple[SymbolStackKeyEntry, ...]
    has_variable: bool


def _scope_key(scopes: PartialScopeStack | None) -> tuple[int, ...] | None:
    if scopes is None:
        return None
    return scopes.scopes


def _symbol_key_entry(symbol: PartialScopedSymbol) -> SymbolStackKeyEntry:
    return (symbol.symbol_id, _scope_key(symbol.scopes))


def _symbol_stack_key(symbol_stack: PartialSymbolStack) -> SymbolStackKey:
    entries = tuple(_symbol_key_entry(symbol) for symbol in symbol_stack.symbols)
    return SymbolStackKey(symbols=entries, has_variable=symbol_stack.variable is not None)


def _symbol_stack_key_prefixes(symbol_stack: PartialSymbolStack) -> tuple[SymbolStackKey, ...]:
    entries = tuple(_symbol_key_entry(symbol) for symbol in symbol_stack.symbols)
    has_variable = symbol_stack.variable is not None
    return tuple(
        SymbolStackKey(symbols=entries[:prefix_len], has_variable=has_variable)
        for prefix_len in range(len(entries), -1, -1)
    )


def _remap_scoped_symbol(
    symbol: PartialScopedSymbol,
    metadata: StackGraphViewMetadata,
    target_symbols: SymbolInterner,
) -> PartialScopedSymbol:
    remapped_symbol_id = remap_symbol_id(symbol.symbol_id, metadata, target_symbols)
    return type(symbol)(symbol_id=remapped_symbol_id, scopes=symbol.scopes)


def _remap_symbol_stack(
    symbol_stack: PartialSymbolStack,
    metadata: StackGraphViewMetadata,
    target_symbols: SymbolInterner,
) -> PartialSymbolStack:
    symbols = tuple(
        _remap_scoped_symbol(symbol, metadata, target_symbols) for symbol in symbol_stack.symbols
    )
    return type(symbol_stack)(symbols=symbols, variable=symbol_stack.variable)


def _remap_partial_path(
    path: PartialPath,
    metadata: StackGraphViewMetadata,
    target_symbols: SymbolInterner,
) -> PartialPath:
    return type(path)(
        start_node_index=path.start_node_index,
        end_node_index=path.end_node_index,
        symbol_stack_precondition=_remap_symbol_stack(
            path.symbol_stack_precondition, metadata, target_symbols
        ),
        symbol_stack_postcondition=_remap_symbol_stack(
            path.symbol_stack_postcondition, metadata, target_symbols
        ),
        scope_stack_precondition=path.scope_stack_precondition,
        scope_stack_postcondition=path.scope_stack_postcondition,
        edges=path.edges,
    )


@dataclass(slots=True)
class PartialPathDb:
    symbols: SymbolInterner = field(
        default_factory=lambda: SymbolInterner(symbol_to_id={}, id_to_symbol=[])
    )
    _paths: list[PartialPath] = field(default_factory=list)
    _path_ids: list[PartialPathId] = field(default_factory=list)
    _by_id: dict[PartialPathId, PartialPath] = field(default_factory=dict)
    start_node_index: dict[tuple[FileHandle, int], list[PartialPathId]] = field(
        default_factory=dict
    )
    root_exact_index: dict[SymbolStackKey, list[PartialPathId]] = field(default_factory=dict)
    root_variable_index: dict[SymbolStackKey, list[PartialPathId]] = field(default_factory=dict)

    def add_file(self, record: PartialPathFileRecord) -> None:
        metadata = record.view_snapshot
        for path_index, path in enumerate(record.paths):
            path_id = (record.file_handle, path_index)
            remapped_path = _remap_partial_path(path, metadata, self.symbols)
            self._paths.append(remapped_path)
            self._path_ids.append(path_id)
            self._by_id[path_id] = remapped_path
            self.start_node_index.setdefault(
                (record.file_handle, remapped_path.start_node_index), []
            ).append(path_id)
            if remapped_path.start_node_index != 0:
                continue
            key = _symbol_stack_key(remapped_path.symbol_stack_precondition)
            if key.has_variable:
                self.root_variable_index.setdefault(key, []).append(path_id)
            else:
                self.root_exact_index.setdefault(key, []).append(path_id)

    def get_candidates(
        self,
        *,
        file_handle: FileHandle,
        end_node_index: int,
        symbol_stack: PartialSymbolStack,
    ) -> tuple[PartialPathId, ...]:
        if end_node_index != 0:
            return tuple(self.start_node_index.get((file_handle, end_node_index), ()))
        return tuple(self._root_candidates(symbol_stack))

    def _root_candidates(self, symbol_stack: PartialSymbolStack) -> list[PartialPathId]:
        entries = tuple(_symbol_key_entry(symbol) for symbol in symbol_stack.symbols)
        has_variable = symbol_stack.variable is not None
        seen: set[PartialPathId] = set()
        candidates: list[PartialPathId] = []

        exact_key = SymbolStackKey(symbols=entries, has_variable=False)
        self._append_from_index(self.root_exact_index, exact_key, seen, candidates)

        if has_variable:
            self._append_longer_candidates(entries, seen, candidates)
            self._append_shorter_variable_candidates(entries, seen, candidates)
        else:
            self._append_prefix_variable_candidates(symbol_stack, seen, candidates)

        variable_equal_key = SymbolStackKey(symbols=entries, has_variable=True)
        self._append_from_index(self.root_variable_index, variable_equal_key, seen, candidates)

        return candidates

    def _append_from_index(
        self,
        index: dict[SymbolStackKey, list[PartialPathId]],
        key: SymbolStackKey,
        seen: set[PartialPathId],
        candidates: list[PartialPathId],
    ) -> None:
        for path_id in index.get(key, ()):
            if path_id in seen:
                continue
            seen.add(path_id)
            candidates.append(path_id)

    def _sort_key(self, key: SymbolStackKey) -> tuple[int, tuple[tuple[int, tuple[int, ...]], ...]]:
        normalized_symbols = tuple(
            (symbol_id, scopes if scopes is not None else ()) for symbol_id, scopes in key.symbols
        )
        return (-len(key.symbols), normalized_symbols)

    def _append_longer_candidates(
        self,
        entries: tuple[SymbolStackKeyEntry, ...],
        seen: set[PartialPathId],
        candidates: list[PartialPathId],
    ) -> None:
        longer_keys = [
            key
            for key in self.root_exact_index
            if len(key.symbols) > len(entries) and key.symbols[: len(entries)] == entries
        ]
        longer_keys.extend(
            key
            for key in self.root_variable_index
            if len(key.symbols) > len(entries) and key.symbols[: len(entries)] == entries
        )
        longer_keys.sort(key=self._sort_key)
        for key in longer_keys:
            if key.has_variable:
                self._append_from_index(self.root_variable_index, key, seen, candidates)
            else:
                self._append_from_index(self.root_exact_index, key, seen, candidates)

    def _append_shorter_variable_candidates(
        self,
        entries: tuple[SymbolStackKeyEntry, ...],
        seen: set[PartialPathId],
        candidates: list[PartialPathId],
    ) -> None:
        shorter_keys = [
            key
            for key in self.root_variable_index
            if len(key.symbols) < len(entries) and key.symbols == entries[: len(key.symbols)]
        ]
        shorter_keys.sort(key=self._sort_key)
        for key in shorter_keys:
            self._append_from_index(self.root_variable_index, key, seen, candidates)

    def _append_prefix_variable_candidates(
        self,
        symbol_stack: PartialSymbolStack,
        seen: set[PartialPathId],
        candidates: list[PartialPathId],
    ) -> None:
        prefixes = _symbol_stack_key_prefixes(symbol_stack)
        for key in prefixes[1:]:
            self._append_from_index(
                self.root_variable_index,
                SymbolStackKey(symbols=key.symbols, has_variable=True),
                seen,
                candidates,
            )

    def get_path(self, path_id: PartialPathId) -> PartialPath | None:
        return self._by_id.get(path_id)

    def list_paths(self) -> tuple[PartialPathId, ...]:
        return tuple(self._path_ids)
