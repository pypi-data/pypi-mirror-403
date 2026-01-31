from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from blends.stack.partial_path.minimal_paths import (
    PartialPathLimits,
    compute_minimal_partial_paths_in_file,
)
from blends.stack.view import StackGraphView

if TYPE_CHECKING:
    from blends.models import Graph
    from blends.stack.partial_path.minimal_paths import PerFilePartialPaths
    from blends.stack.partial_path_database import FileHandle, PartialPathDatabase


@dataclass(frozen=True, slots=True)
class PartialPathIndexRequest:
    file_path: str
    file_handle: FileHandle
    limits: PartialPathLimits | None = None
    record_edges: bool = False


def index_partial_paths_for_file(
    syntax_graph: Graph,
    request: PartialPathIndexRequest,
    database: PartialPathDatabase,
) -> PerFilePartialPaths:
    view = StackGraphView.from_syntax_graph(syntax_graph, path=request.file_path)
    result = compute_minimal_partial_paths_in_file(
        view,
        request.file_path,
        limits=request.limits,
        record_edges=request.record_edges,
    )
    database.put_file(
        file_handle=request.file_handle,
        file_path=request.file_path,
        view=view,
        partial_paths=result,
    )
    return result
