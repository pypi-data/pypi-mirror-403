from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from blends.stack.criteria import (
    is_complete_definition_path,
    is_reference_endpoint,
)
from blends.stack.partial_path.errors import PartialPathResolutionError
from blends.stack.partial_path.stack_conditions import create_seed_path

if TYPE_CHECKING:
    from collections.abc import Callable

    from blends.stack.partial_path import (
        FileHandle,
        PartialPath,
        PartialScopeStack,
        PartialSymbolStack,
    )
    from blends.stack.partial_path_db import PartialPathDb
    from blends.stack.view import StackGraphView

from blends.stack.stacks import (
    ScopeStackNode,
    StackState,
    SymbolStackNode,
)


@dataclass(frozen=True, slots=True)
class ForwardStitcherConfig:
    max_work_per_phase: int | None = None
    max_phases: int | None = None
    enable_dedupe: bool = True
    enable_cycle_guard: bool = True
    is_cancelled: Callable[[], bool] | None = None
    deadline: float | None = None


@dataclass(slots=True)
class ForwardStitcherStats:
    phases_executed: int = 0
    candidates_considered: int = 0
    concatenations_succeeded: int = 0
    complete_paths_found: int = 0
    cancelled: bool = False


@dataclass(frozen=True, slots=True)
class ForwardStitcherStatsSnapshot:
    phases_executed: int
    candidates_considered: int
    concatenations_succeeded: int
    complete_paths_found: int
    cancelled: bool


@dataclass(frozen=True, slots=True)
class ForwardStitcherLoadRequests:
    node_requests: tuple[tuple[FileHandle, int], ...] = ()
    root_requests: tuple[tuple[FileHandle, PartialSymbolStack], ...] = ()


@dataclass(frozen=True, slots=True)
class ForwardStitcherPhaseResult:
    complete_paths: tuple[PartialPath, ...]
    load_requests: ForwardStitcherLoadRequests
    stats: ForwardStitcherStatsSnapshot


@dataclass(slots=True)
class ForwardStitcher:
    view: StackGraphView
    file_handle: FileHandle
    db: PartialPathDb
    config: ForwardStitcherConfig = field(default_factory=ForwardStitcherConfig)

    _current_queue: list[PartialPath] = field(default_factory=list)
    _next_queue: list[PartialPath] = field(default_factory=list)
    _previous_phase_paths: tuple[PartialPath, ...] = ()
    _stats: ForwardStitcherStats = field(default_factory=ForwardStitcherStats)
    _is_complete: bool = False

    @classmethod
    def from_references(
        cls,
        *,
        view: StackGraphView,
        file_handle: FileHandle,
        db: PartialPathDb,
        reference_nodes: tuple[int, ...],
        config: ForwardStitcherConfig | None = None,
    ) -> ForwardStitcher:
        seed_paths: list[PartialPath] = []
        for node_index in sorted(reference_nodes):
            if not is_reference_endpoint(view, node_index):
                continue
            seed_paths.append(create_seed_path(view, node_index))

        stitcher = cls(
            view=view,
            file_handle=file_handle,
            db=db,
            config=config or ForwardStitcherConfig(),
        )
        stitcher._current_queue = seed_paths
        stitcher._is_complete = len(seed_paths) == 0
        return stitcher

    def process_next_phase(self) -> ForwardStitcherPhaseResult:
        if self._is_complete or self._phase_limit_reached():
            self._is_complete = True
            return self._build_phase_result(ForwardStitcherLoadRequests(), ())

        self._stats.phases_executed += 1
        self._previous_phase_paths = tuple(self._current_queue)

        complete_paths: list[PartialPath] = []
        self._current_queue = self._expand_phase(self._current_queue, complete_paths)
        if len(self._current_queue) == 0:
            self._is_complete = True

        load_requests = _collect_load_requests(self.file_handle, self._current_queue)
        if self._phase_limit_reached():
            self._is_complete = True

        return self._build_phase_result(load_requests, tuple(complete_paths))

    def previous_phase_paths(self) -> tuple[PartialPath, ...]:
        return self._previous_phase_paths

    def is_complete(self) -> bool:
        return self._is_complete

    def current_load_requests(self) -> ForwardStitcherLoadRequests:
        return _collect_load_requests(self.file_handle, self._current_queue)

    def _phase_limit_reached(self) -> bool:
        return (
            self.config.max_phases is not None
            and self._stats.phases_executed >= self.config.max_phases
        )

    def _build_phase_result(
        self,
        load_requests: ForwardStitcherLoadRequests,
        complete_paths: tuple[PartialPath, ...],
    ) -> ForwardStitcherPhaseResult:
        return ForwardStitcherPhaseResult(
            complete_paths=complete_paths,
            load_requests=load_requests,
            stats=_snapshot_stats(self._stats),
        )

    def _expand_phase(
        self,
        current_queue: list[PartialPath],
        complete_paths: list[PartialPath],
    ) -> list[PartialPath]:
        next_queue: list[PartialPath] = []
        work_performed = 0

        for index, current_path in enumerate(current_queue):
            if _should_cancel(self.config):
                self._stats.cancelled = True
                self._is_complete = True
                return []
            if (
                self.config.max_work_per_phase is not None
                and work_performed >= self.config.max_work_per_phase
            ):
                next_queue.extend(current_queue[index:])
                return next_queue

            work_performed += self._extend_with_candidates(current_path, next_queue, complete_paths)

        return next_queue

    def _extend_with_candidates(
        self,
        current_path: PartialPath,
        next_queue: list[PartialPath],
        complete_paths: list[PartialPath],
    ) -> int:
        candidates = self.db.get_candidates(
            file_handle=self.file_handle,
            end_node_index=current_path.end_node_index,
            symbol_stack=current_path.symbol_stack_postcondition,
        )
        self._stats.candidates_considered += len(candidates)

        for candidate_id in candidates:
            candidate_path = self.db.get_path(candidate_id)
            if candidate_path is None:
                continue
            try:
                extended = current_path.concatenate(self.view, candidate_path)
            except PartialPathResolutionError:
                continue
            next_queue.append(extended)
            self._stats.concatenations_succeeded += 1
            if _is_complete_path(self.view, extended):
                complete_paths.append(extended)
                self._stats.complete_paths_found += 1

        return len(candidates)


def _snapshot_stats(stats: ForwardStitcherStats) -> ForwardStitcherStatsSnapshot:
    return ForwardStitcherStatsSnapshot(
        phases_executed=stats.phases_executed,
        candidates_considered=stats.candidates_considered,
        concatenations_succeeded=stats.concatenations_succeeded,
        complete_paths_found=stats.complete_paths_found,
        cancelled=stats.cancelled,
    )


def _should_cancel(config: ForwardStitcherConfig) -> bool:
    if config.is_cancelled is not None and config.is_cancelled():
        return True
    return _deadline_exceeded(config)


def _deadline_exceeded(config: ForwardStitcherConfig) -> bool:
    if config.deadline is None:
        return False
    return time.monotonic() >= config.deadline


def _collect_load_requests(
    file_handle: FileHandle,
    paths: list[PartialPath],
) -> ForwardStitcherLoadRequests:
    node_requests: list[tuple[FileHandle, int]] = []
    root_requests: list[tuple[FileHandle, PartialSymbolStack]] = []
    seen_nodes: set[tuple[FileHandle, int]] = set()
    seen_roots: set[tuple[FileHandle, PartialSymbolStack]] = set()

    for path in paths:
        if path.end_node_index == 0:
            root_key = (file_handle, path.symbol_stack_postcondition)
            if root_key in seen_roots:
                continue
            seen_roots.add(root_key)
            root_requests.append(root_key)
        else:
            node_key = (file_handle, path.end_node_index)
            if node_key in seen_nodes:
                continue
            seen_nodes.add(node_key)
            node_requests.append(node_key)

    return ForwardStitcherLoadRequests(
        node_requests=tuple(node_requests),
        root_requests=tuple(root_requests),
    )


def _stack_state_from_partial(
    symbol_stack: PartialSymbolStack, scope_stack: PartialScopeStack
) -> StackState:
    symbol_node = None
    scope_node = None
    if not symbol_stack.can_match_empty():
        symbol_node = SymbolStackNode(symbol_id=0, scopes=None, tail=None)
    if not scope_stack.can_match_empty():
        scope_node = ScopeStackNode(scope_index=0, tail=None)
    return StackState(symbol_stack=symbol_node, scope_stack=scope_node)


def _is_complete_path(view: StackGraphView, path: PartialPath) -> bool:
    start_state = _stack_state_from_partial(
        path.symbol_stack_precondition, path.scope_stack_precondition
    )
    end_state = _stack_state_from_partial(
        path.symbol_stack_postcondition, path.scope_stack_postcondition
    )
    return is_complete_definition_path(
        view,
        start_node_index=path.start_node_index,
        end_node_index=path.end_node_index,
        start_state=start_state,
        end_state=end_state,
    )
