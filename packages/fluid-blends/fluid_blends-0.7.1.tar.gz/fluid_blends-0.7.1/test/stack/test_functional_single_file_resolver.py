from pathlib import Path
from unittest.mock import patch

import pytest

from blends import get_graphs_from_path
from blends.stack.forward_stitcher import ForwardStitcherConfig
from blends.stack.partial_path import (
    PartialPathDatabase,
    PartialPathFileRecord,
    PartialPathIndexRequest,
    PartialPathLimits,
    index_partial_paths_for_file,
)
from blends.stack.single_file_resolver import (
    SingleFileResolutionRequest,
    resolve_definitions_single_file,
)
from blends.stack.view import StackGraphView

INDEX_MAX_WORK = 50_000
QUERY_MAX_PHASES = 100
QUERY_MAX_WORK = 10_000


def _find_symbol_nodes(view: StackGraphView, *, symbol_id: int, is_definition: bool) -> list[int]:
    matches: list[int] = []
    flags = view.node_is_definition if is_definition else view.node_is_reference
    for node_index, flag in enumerate(flags):
        if not flag:
            continue
        if view.node_symbol_id[node_index] == symbol_id:
            matches.append(node_index)
    return matches


def _resolve_symbol(
    view: StackGraphView,
    *,
    record: PartialPathFileRecord,
    symbol: str,
) -> None:
    symbol_id = view.symbols.symbol_to_id.get(symbol)
    assert symbol_id is not None

    ref_nodes = _find_symbol_nodes(view, symbol_id=symbol_id, is_definition=False)
    def_nodes = _find_symbol_nodes(view, symbol_id=symbol_id, is_definition=True)

    assert len(ref_nodes) == 1
    assert len(def_nodes) == 1

    request = SingleFileResolutionRequest(
        file_handle=1,
        record=record,
        ref_node_index=ref_nodes[0],
        config=ForwardStitcherConfig(
            max_phases=QUERY_MAX_PHASES,
            max_work_per_phase=QUERY_MAX_WORK,
        ),
    )
    result = resolve_definitions_single_file(view, request=request)
    assert result == [def_nodes[0]]


@pytest.mark.blends_test_group("functional")
def test_single_file_resolver_end_to_end_python() -> None:
    test_data_dir = Path(__file__).parent.parent / "data"
    test_file_path = test_data_dir / "test_files" / "stack_graph_single_file.py"
    file_path = "test/data/test_files/stack_graph_single_file.py"

    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        graphs = get_graphs_from_path(test_file_path)

    assert graphs.ast_graph is not None
    assert graphs.syntax_graph is not None

    view = StackGraphView.from_syntax_graph(graphs.syntax_graph, path=file_path)

    database = PartialPathDatabase()
    per_file = index_partial_paths_for_file(
        graphs.syntax_graph,
        request=PartialPathIndexRequest(
            file_path=file_path,
            file_handle=1,
            limits=PartialPathLimits(max_work_per_phase=INDEX_MAX_WORK),
        ),
        database=database,
    )
    assert per_file.paths, "Expected at least one partial path from the test file."

    record = database.get_file(1)
    assert record is not None

    symbol_id = view.symbols.symbol_to_id.get("x")
    assert symbol_id is not None

    ref_nodes = _find_symbol_nodes(view, symbol_id=symbol_id, is_definition=False)
    def_nodes = _find_symbol_nodes(view, symbol_id=symbol_id, is_definition=True)

    assert len(ref_nodes) == 1
    assert len(def_nodes) == 1

    ref_node = ref_nodes[0]
    def_node = def_nodes[0]

    request = SingleFileResolutionRequest(
        file_handle=1,
        record=record,
        ref_node_index=ref_node,
        config=ForwardStitcherConfig(
            max_phases=QUERY_MAX_PHASES,
            max_work_per_phase=QUERY_MAX_WORK,
        ),
    )
    result = resolve_definitions_single_file(view, request=request)

    assert result == [def_node]


@pytest.mark.blends_test_group("functional")
def test_single_file_resolver_end_to_end_python_scopes() -> None:
    test_data_dir = Path(__file__).parent.parent / "data"
    test_file_path = test_data_dir / "test_files" / "stack_graph_single_file_scopes.py"
    file_path = "test/data/test_files/stack_graph_single_file_scopes.py"

    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        graphs = get_graphs_from_path(test_file_path, with_cfg=False)

    assert graphs.syntax_graph is not None
    view = StackGraphView.from_syntax_graph(graphs.syntax_graph, path=file_path)

    database = PartialPathDatabase()
    per_file = index_partial_paths_for_file(
        graphs.syntax_graph,
        request=PartialPathIndexRequest(
            file_path=file_path,
            file_handle=1,
            limits=PartialPathLimits(max_work_per_phase=INDEX_MAX_WORK),
        ),
        database=database,
    )
    assert per_file.paths

    record = database.get_file(1)
    assert record is not None

    _resolve_symbol(view, record=record, symbol="x")
    _resolve_symbol(view, record=record, symbol="y")
