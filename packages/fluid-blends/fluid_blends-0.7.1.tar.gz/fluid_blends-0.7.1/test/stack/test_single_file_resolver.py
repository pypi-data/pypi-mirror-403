import time

import pytest

from blends.models import Graph
from blends.stack.attributes import (
    STACK_GRAPH_IS_DEFINITION,
    STACK_GRAPH_IS_REFERENCE,
    STACK_GRAPH_KIND,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.forward_stitcher import ForwardStitcherConfig
from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.partial_path import (
    PartialPath,
    PartialScopeStack,
    PartialSymbolStack,
)
from blends.stack.selection import PartialPathEdge
from blends.stack.single_file_resolver import (
    SingleFileResolutionRequest,
    SingleFileResolutionStats,
    resolve_definitions_single_file,
)
from blends.stack.view import StackGraphView
from test.stack.test_helpers import empty_path, view_for_graph
from test.stack.test_helpers import record as make_record


def _path_with_edge(start: int, end: int, *, precedence: int) -> PartialPath:
    empty_symbols = PartialSymbolStack.empty()
    empty_scopes = PartialScopeStack.empty()
    return PartialPath(
        start_node_index=start,
        end_node_index=end,
        symbol_stack_precondition=empty_symbols,
        symbol_stack_postcondition=empty_symbols,
        scope_stack_precondition=empty_scopes,
        scope_stack_postcondition=empty_scopes,
        edges=(PartialPathEdge(source_node_index=start, precedence=precedence),),
    )


def _resolve_with_stats(
    view: StackGraphView, request: SingleFileResolutionRequest
) -> tuple[list[int], SingleFileResolutionStats]:
    result = resolve_definitions_single_file(view, request=request)
    assert isinstance(result, tuple)
    return result


def _build_view_with_defs() -> StackGraphView:
    graph = Graph()
    graph.add_node("ref")
    graph.nodes["ref"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["ref"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["ref"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("def1")
    graph.nodes["def1"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["def1"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["def1"][STACK_GRAPH_IS_DEFINITION] = True

    graph.add_node("def2")
    graph.nodes["def2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["def2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["def2"][STACK_GRAPH_IS_DEFINITION] = True

    return view_for_graph(graph)


@pytest.mark.blends_test_group("stack_unittesting")
def test_single_file_resolver_returns_empty_for_non_reference() -> None:
    graph = Graph()
    graph.add_node("scope")
    graph.nodes["scope"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    view = view_for_graph(graph)
    scope_index = view.nid_to_index["scope"]

    request = SingleFileResolutionRequest(
        file_handle=1,
        record=make_record(()),
        ref_node_index=scope_index,
        include_stats=True,
    )
    result, stats = _resolve_with_stats(view, request)

    assert result == []
    assert stats.complete_paths_found == 0


@pytest.mark.blends_test_group("stack_unittesting")
def test_single_file_resolver_respects_work_budget() -> None:
    view = _build_view_with_defs()
    ref_index = view.nid_to_index["ref"]
    def_index = view.nid_to_index["def1"]

    record = make_record((empty_path(ref_index, def_index),))
    request = SingleFileResolutionRequest(
        file_handle=1,
        record=record,
        ref_node_index=ref_index,
        include_stats=True,
        config=ForwardStitcherConfig(max_work_per_phase=0, max_phases=1),
    )

    result, stats = _resolve_with_stats(view, request)

    assert result == []
    assert stats.phases_executed == 1
    assert stats.candidates_considered == 0


@pytest.mark.blends_test_group("stack_unittesting")
def test_single_file_resolver_respects_deadline() -> None:
    view = _build_view_with_defs()
    ref_index = view.nid_to_index["ref"]
    def_index = view.nid_to_index["def1"]

    record = make_record((empty_path(ref_index, def_index),))
    request = SingleFileResolutionRequest(
        file_handle=1,
        record=record,
        ref_node_index=ref_index,
        include_stats=True,
        config=ForwardStitcherConfig(deadline=time.monotonic() - 1),
    )

    result, stats = _resolve_with_stats(view, request)

    assert result == []
    assert stats.cancelled


@pytest.mark.blends_test_group("stack_unittesting")
def test_single_file_resolver_stitches_across_two_paths() -> None:
    graph = Graph()
    graph.add_node("ref")
    graph.nodes["ref"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["ref"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["ref"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("join")
    graph.nodes["join"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value

    graph.add_node("def")
    graph.nodes["def"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["def"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["def"][STACK_GRAPH_IS_DEFINITION] = True

    view = view_for_graph(graph)
    ref_index = view.nid_to_index["ref"]
    join_index = view.nid_to_index["join"]
    def_index = view.nid_to_index["def"]

    record = make_record((empty_path(ref_index, join_index), empty_path(join_index, def_index)))
    request = SingleFileResolutionRequest(
        file_handle=1,
        record=record,
        ref_node_index=ref_index,
    )

    result = resolve_definitions_single_file(view, request=request)

    assert result == [def_index]


@pytest.mark.blends_test_group("stack_unittesting")
def test_single_file_resolver_prunes_shadowed_candidates() -> None:
    view = _build_view_with_defs()
    ref_index = view.nid_to_index["ref"]
    def1_index = view.nid_to_index["def1"]
    def2_index = view.nid_to_index["def2"]

    record = make_record(
        (
            _path_with_edge(ref_index, def1_index, precedence=0),
            _path_with_edge(ref_index, def2_index, precedence=1),
        )
    )
    request = SingleFileResolutionRequest(
        file_handle=1,
        record=record,
        ref_node_index=ref_index,
    )

    result = resolve_definitions_single_file(view, request=request)

    assert result == [def2_index]
