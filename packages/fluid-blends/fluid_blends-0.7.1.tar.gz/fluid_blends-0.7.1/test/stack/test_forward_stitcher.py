import pytest

from blends.models import Graph
from blends.stack.attributes import (
    STACK_GRAPH_IS_DEFINITION,
    STACK_GRAPH_IS_REFERENCE,
    STACK_GRAPH_KIND,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.criteria import is_definition_endpoint
from blends.stack.forward_stitcher import (
    ForwardStitcher,
    ForwardStitcherConfig,
)
from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.partial_path import PartialPathDb
from blends.stack.view import StackGraphView
from test.stack.test_helpers import empty_path, view_for_graph
from test.stack.test_helpers import record as make_record


def _view_with_reference_join_definition() -> StackGraphView:
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

    return view_for_graph(graph)


@pytest.mark.blends_test_group("stack_unittesting")
def test_forward_stitcher_respects_phase_work_limit() -> None:
    view = _view_with_reference_join_definition()
    ref_index = view.nid_to_index["ref"]
    def_index = view.nid_to_index["def"]

    db = PartialPathDb()
    db.add_file(make_record((empty_path(ref_index, def_index),)))

    stitcher = ForwardStitcher.from_references(
        view=view,
        file_handle=1,
        db=db,
        reference_nodes=(ref_index,),
        config=ForwardStitcherConfig(max_work_per_phase=0),
    )

    result = stitcher.process_next_phase()

    assert result.complete_paths == ()
    assert result.stats.candidates_considered == 0
    assert stitcher.previous_phase_paths() != ()
    assert not stitcher.is_complete()


@pytest.mark.blends_test_group("stack_unittesting")
def test_forward_stitcher_finds_complete_path_single_phase() -> None:
    view = _view_with_reference_join_definition()
    ref_index = view.nid_to_index["ref"]
    def_index = view.nid_to_index["def"]

    db = PartialPathDb()
    db.add_file(make_record((empty_path(ref_index, def_index),)))

    stitcher = ForwardStitcher.from_references(
        view=view,
        file_handle=1,
        db=db,
        reference_nodes=(ref_index,),
        config=ForwardStitcherConfig(),
    )

    result = stitcher.process_next_phase()

    assert len(result.complete_paths) == 1
    assert is_definition_endpoint(view, result.complete_paths[0].end_node_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_forward_stitcher_stitches_across_two_paths() -> None:
    view = _view_with_reference_join_definition()
    ref_index = view.nid_to_index["ref"]
    join_index = view.nid_to_index["join"]
    def_index = view.nid_to_index["def"]

    db = PartialPathDb()
    db.add_file(make_record((empty_path(ref_index, join_index), empty_path(join_index, def_index))))

    stitcher = ForwardStitcher.from_references(
        view=view,
        file_handle=1,
        db=db,
        reference_nodes=(ref_index,),
        config=ForwardStitcherConfig(),
    )

    first = stitcher.process_next_phase()
    assert first.complete_paths == ()

    second = stitcher.process_next_phase()
    assert len(second.complete_paths) == 1
    assert is_definition_endpoint(view, second.complete_paths[0].end_node_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_forward_stitcher_stitches_via_root() -> None:
    view = _view_with_reference_join_definition()
    ref_index = view.nid_to_index["ref"]
    def_index = view.nid_to_index["def"]

    db = PartialPathDb()
    db.add_file(make_record((empty_path(ref_index, 0), empty_path(0, def_index))))

    stitcher = ForwardStitcher.from_references(
        view=view,
        file_handle=1,
        db=db,
        reference_nodes=(ref_index,),
        config=ForwardStitcherConfig(),
    )

    stitcher.process_next_phase()
    result = stitcher.process_next_phase()

    assert len(result.complete_paths) == 1
    assert is_definition_endpoint(view, result.complete_paths[0].end_node_index)
