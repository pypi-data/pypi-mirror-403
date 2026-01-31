from blends.models import Graph
from blends.stack.partial_path import (
    PartialPath,
    PartialScopeStack,
    PartialSymbolStack,
    PerFilePartialPathStats,
    StackGraphViewMetadata,
)
from blends.stack.partial_path_database import PartialPathFileRecord
from blends.stack.view import StackGraphView


def view_for_graph(graph: Graph, *, path: str = "test.py") -> StackGraphView:
    return StackGraphView.from_syntax_graph(graph, path=path)


def empty_path(start: int, end: int) -> PartialPath:
    empty_symbols = PartialSymbolStack.empty()
    empty_scopes = PartialScopeStack.empty()
    return PartialPath(
        start_node_index=start,
        end_node_index=end,
        symbol_stack_precondition=empty_symbols,
        symbol_stack_postcondition=empty_symbols,
        scope_stack_precondition=empty_scopes,
        scope_stack_postcondition=empty_scopes,
    )


def record(
    paths: tuple[PartialPath, ...],
    *,
    file_handle: int = 1,
    file_path: str = "test.py",
    symbol_id_to_string: tuple[str, ...] = ("x",),
) -> PartialPathFileRecord:
    metadata = StackGraphViewMetadata(
        file_handles=(file_path,),
        symbol_id_to_string=symbol_id_to_string,
    )
    return PartialPathFileRecord(
        file_handle=file_handle,
        file_path=file_path,
        view_snapshot=metadata,
        paths=paths,
        stats=PerFilePartialPathStats(),
    )
