from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from blends.stack.criteria import (
    is_definition_endpoint,
    is_reference_endpoint,
)
from blends.stack.forward_stitcher import (
    ForwardStitcher,
    ForwardStitcherConfig,
)
from blends.stack.partial_path_db import PartialPathDb
from blends.stack.selection import (
    DefinitionCandidate,
    prune_shadowed_candidates,
    sort_candidates_deterministically,
)

if TYPE_CHECKING:
    from blends.stack.partial_path import (
        FileHandle,
        PartialPath,
        PartialPathFileRecord,
    )
    from blends.stack.view import StackGraphView


@dataclass(frozen=True, slots=True)
class SingleFileResolutionStats:
    phases_executed: int
    candidates_considered: int
    concatenations_succeeded: int
    complete_paths_found: int
    cancelled: bool


@dataclass(frozen=True, slots=True)
class SingleFileResolutionRequest:
    file_handle: FileHandle
    record: PartialPathFileRecord
    ref_node_index: int
    config: ForwardStitcherConfig | None = None
    include_stats: bool = False


def resolve_definitions_single_file(
    view: StackGraphView,
    *,
    request: SingleFileResolutionRequest,
) -> list[int] | tuple[list[int], SingleFileResolutionStats]:
    if not is_reference_endpoint(view, request.ref_node_index):
        return _empty_result(include_stats=request.include_stats)
    if not _record_matches_view(view, request):
        return _empty_result(include_stats=request.include_stats)

    db = PartialPathDb(symbols=view.symbols)
    db.add_file(request.record)

    stitcher = ForwardStitcher.from_references(
        view=view,
        file_handle=request.file_handle,
        db=db,
        reference_nodes=(request.ref_node_index,),
        config=request.config,
    )

    definition_nodes, latest_stats = _run_resolution(view, stitcher)
    return _finalize_result(
        definition_nodes,
        latest_stats,
        include_stats=request.include_stats,
    )


def _empty_result(
    *,
    include_stats: bool,
) -> list[int] | tuple[list[int], SingleFileResolutionStats]:
    if include_stats:
        return [], SingleFileResolutionStats(
            phases_executed=0,
            candidates_considered=0,
            concatenations_succeeded=0,
            complete_paths_found=0,
            cancelled=False,
        )
    return []


def _run_resolution(
    view: StackGraphView,
    stitcher: ForwardStitcher,
) -> tuple[list[int], SingleFileResolutionStats | None]:
    candidates: list[DefinitionCandidate] = []
    latest_stats: SingleFileResolutionStats | None = None

    while not stitcher.is_complete():
        result = stitcher.process_next_phase()
        latest_stats = SingleFileResolutionStats(
            phases_executed=result.stats.phases_executed,
            candidates_considered=result.stats.candidates_considered,
            concatenations_succeeded=result.stats.concatenations_succeeded,
            complete_paths_found=result.stats.complete_paths_found,
            cancelled=result.stats.cancelled,
        )
        _collect_candidates(view, result.complete_paths, candidates)

    definition_nodes = _select_definitions_from_candidates(candidates)
    return definition_nodes, latest_stats


def _collect_candidates(
    view: StackGraphView,
    complete_paths: tuple[PartialPath, ...],
    candidates: list[DefinitionCandidate],
) -> None:
    for path in complete_paths:
        if not is_definition_endpoint(view, path.end_node_index):
            continue
        candidates.append(
            DefinitionCandidate(
                definition_node_index=path.end_node_index,
                edges=path.edges,
            )
        )


def _select_definitions_from_candidates(
    candidates: list[DefinitionCandidate],
) -> list[int]:
    if not candidates:
        return []
    pruned = prune_shadowed_candidates(candidates)
    ordered = sort_candidates_deterministically(pruned)
    seen_definitions: set[int] = set()
    definition_nodes: list[int] = []
    for candidate in ordered:
        if candidate.definition_node_index in seen_definitions:
            continue
        seen_definitions.add(candidate.definition_node_index)
        definition_nodes.append(candidate.definition_node_index)
    return definition_nodes


def _finalize_result(
    definition_nodes: list[int],
    latest_stats: SingleFileResolutionStats | None,
    *,
    include_stats: bool,
) -> list[int] | tuple[list[int], SingleFileResolutionStats]:
    if include_stats:
        if latest_stats is None:
            latest_stats = SingleFileResolutionStats(
                phases_executed=0,
                candidates_considered=0,
                concatenations_succeeded=0,
                complete_paths_found=0,
                cancelled=False,
            )
        return definition_nodes, latest_stats
    return definition_nodes


def _record_matches_view(view: StackGraphView, request: SingleFileResolutionRequest) -> bool:
    if request.record.file_handle != request.file_handle:
        return False
    if request.record.file_path and view.file_path:
        return request.record.file_path == view.file_path
    return True
