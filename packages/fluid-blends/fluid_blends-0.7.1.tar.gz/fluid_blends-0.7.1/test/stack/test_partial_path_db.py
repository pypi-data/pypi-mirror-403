import pytest

from blends.models import Graph
from blends.stack.attributes import STACK_GRAPH_KIND
from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.partial_path import (
    PartialPath,
    PartialPathDb,
    PartialPathResolutionError,
    PartialScopedSymbol,
    PartialScopeStack,
    PartialSymbolStack,
    PerFilePartialPathStats,
    StackGraphViewMetadata,
    SymbolStackVariable,
)
from blends.stack.partial_path_database import PartialPathFileRecord
from blends.stack.view import StackGraphView


def _path(
    *,
    start: int,
    end: int,
    symbol_ids: tuple[int, ...],
    has_variable: bool = False,
) -> PartialPath:
    symbols = tuple(
        PartialScopedSymbol(symbol_id=symbol_id, scopes=None) for symbol_id in symbol_ids
    )
    variable = SymbolStackVariable.initial() if has_variable else None
    symbol_stack = PartialSymbolStack(symbols=symbols, variable=variable)
    return PartialPath(
        start_node_index=start,
        end_node_index=end,
        symbol_stack_precondition=symbol_stack,
        symbol_stack_postcondition=symbol_stack,
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )


def _record(file_handle: int, paths: tuple[PartialPath, ...]) -> PartialPathFileRecord:
    metadata = StackGraphViewMetadata(
        file_handles=("test.py",),
        symbol_id_to_string=("a", "b", "c", "d"),
    )
    return PartialPathFileRecord(
        file_handle=file_handle,
        file_path="test.py",
        view_snapshot=metadata,
        paths=paths,
        stats=PerFilePartialPathStats(),
    )


def _view_with_node(node_id: str, kind: str) -> StackGraphView:
    graph = Graph()
    graph.add_node(node_id)
    graph.nodes[node_id][STACK_GRAPH_KIND] = kind
    return StackGraphView.from_syntax_graph(graph, path="test.py")


@pytest.mark.blends_test_group("stack_unittesting")
def test_start_node_index_returns_paths_for_node() -> None:
    db = PartialPathDb()
    paths = (
        _path(start=2, end=3, symbol_ids=(0,)),
        _path(start=2, end=4, symbol_ids=(1,)),
        _path(start=5, end=6, symbol_ids=(2,)),
    )
    db.add_file(_record(1, paths))

    candidates = db.get_candidates(
        file_handle=1,
        end_node_index=2,
        symbol_stack=PartialSymbolStack.empty(),
    )

    assert candidates == ((1, 0), (1, 1))


@pytest.mark.blends_test_group("stack_unittesting")
def test_root_exact_match_returns_expected_paths() -> None:
    db = PartialPathDb()
    paths = (
        _path(start=0, end=7, symbol_ids=(0,)),
        _path(start=0, end=8, symbol_ids=(1,)),
    )
    db.add_file(_record(1, paths))

    candidates = db.get_candidates(
        file_handle=1,
        end_node_index=0,
        symbol_stack=PartialSymbolStack(
            symbols=(PartialScopedSymbol(symbol_id=0, scopes=None),),
            variable=None,
        ),
    )

    assert candidates == ((1, 0),)


@pytest.mark.blends_test_group("stack_unittesting")
def test_root_variable_query_includes_longer_and_shorter_variable_prefixes() -> None:
    db = PartialPathDb()
    paths = (
        _path(start=0, end=10, symbol_ids=(0,), has_variable=False),
        _path(start=0, end=11, symbol_ids=(0, 1), has_variable=False),
        _path(start=0, end=12, symbol_ids=(0, 1), has_variable=True),
        _path(start=0, end=13, symbol_ids=(), has_variable=True),
    )
    db.add_file(_record(1, paths))

    query_stack = PartialSymbolStack(
        symbols=(PartialScopedSymbol(symbol_id=0, scopes=None),),
        variable=SymbolStackVariable.initial(),
    )
    candidates = db.get_candidates(
        file_handle=1,
        end_node_index=0,
        symbol_stack=query_stack,
    )

    assert (1, 0) in candidates
    assert (1, 1) in candidates
    assert (1, 2) in candidates
    assert (1, 3) in candidates


@pytest.mark.blends_test_group("stack_unittesting")
def test_root_incompatible_stack_returns_empty() -> None:
    db = PartialPathDb()
    paths = (_path(start=0, end=20, symbol_ids=(0,)),)
    db.add_file(_record(1, paths))

    candidates = db.get_candidates(
        file_handle=1,
        end_node_index=0,
        symbol_stack=PartialSymbolStack(
            symbols=(PartialScopedSymbol(symbol_id=1, scopes=None),),
            variable=None,
        ),
    )

    assert candidates == ()


@pytest.mark.blends_test_group("stack_unittesting")
def test_root_candidates_are_deterministic() -> None:
    paths = (
        _path(start=0, end=30, symbol_ids=(0,), has_variable=False),
        _path(start=0, end=31, symbol_ids=(0,), has_variable=True),
    )
    record = _record(1, paths)

    db_one = PartialPathDb()
    db_one.add_file(record)
    db_two = PartialPathDb()
    db_two.add_file(record)

    query_stack = PartialSymbolStack(
        symbols=(PartialScopedSymbol(symbol_id=0, scopes=None),),
        variable=None,
    )
    candidates_one = db_one.get_candidates(
        file_handle=1,
        end_node_index=0,
        symbol_stack=query_stack,
    )
    candidates_two = db_two.get_candidates(
        file_handle=1,
        end_node_index=0,
        symbol_stack=query_stack,
    )

    assert candidates_one == candidates_two


@pytest.mark.blends_test_group("stack_unittesting")
def test_integration_non_root_candidates_concatenate() -> None:
    db = PartialPathDb()
    expected_end_index = 3
    left = _path(start=1, end=2, symbol_ids=())
    right = _path(start=2, end=expected_end_index, symbol_ids=())
    db.add_file(_record(1, (left, right)))

    candidates = db.get_candidates(
        file_handle=1,
        end_node_index=2,
        symbol_stack=PartialSymbolStack.empty(),
    )

    assert candidates == ((1, 1),)

    view = _view_with_node("2", StackGraphNodeKind.SCOPE.value)
    candidate = db.get_path(candidates[0])
    assert candidate is not None
    concatenated = left.concatenate(view, candidate)

    assert concatenated.start_node_index == 1
    assert concatenated.end_node_index == expected_end_index


@pytest.mark.blends_test_group("stack_unittesting")
def test_integration_root_candidates_concatenate_success_and_failure() -> None:
    db = PartialPathDb()
    expected_end_index = 4
    expected_bad_end_index = 5
    symbol = PartialScopedSymbol(symbol_id=0, scopes=None)
    left = PartialPath(
        start_node_index=0,
        end_node_index=0,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack(
            symbols=(symbol,),
            variable=SymbolStackVariable.initial(),
        ),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )
    right_ok = PartialPath(
        start_node_index=0,
        end_node_index=expected_end_index,
        symbol_stack_precondition=PartialSymbolStack(symbols=(symbol,), variable=None),
        symbol_stack_postcondition=PartialSymbolStack(symbols=(), variable=None),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )
    right_bad = PartialPath(
        start_node_index=0,
        end_node_index=expected_bad_end_index,
        symbol_stack_precondition=PartialSymbolStack(symbols=(symbol,), variable=None),
        symbol_stack_postcondition=PartialSymbolStack(symbols=(), variable=None),
        scope_stack_precondition=PartialScopeStack(scopes=(1,), variable=None),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )
    db.add_file(_record(1, (left, right_ok, right_bad)))

    candidates = db.get_candidates(
        file_handle=1,
        end_node_index=0,
        symbol_stack=left.symbol_stack_postcondition,
    )

    assert (1, 1) in candidates
    assert (1, 2) in candidates

    view = StackGraphView.from_syntax_graph(Graph(), path="test.py")
    candidate_paths = [db.get_path(candidate) for candidate in candidates]
    assert all(path is not None for path in candidate_paths)
    resolved_candidates = [path for path in candidate_paths if path is not None]
    ok_candidate = next(
        path for path in resolved_candidates if path.end_node_index == expected_end_index
    )
    assert left.concatenate(view, ok_candidate).end_node_index == expected_end_index
    bad_candidate = next(
        path for path in resolved_candidates if path.end_node_index == expected_bad_end_index
    )
    with pytest.raises(PartialPathResolutionError):
        left.concatenate(view, bad_candidate)
