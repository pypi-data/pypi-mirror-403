import pytest

from blends.models import Graph
from blends.stack.attributes import (
    STACK_GRAPH_IS_DEFINITION,
    STACK_GRAPH_IS_REFERENCE,
    STACK_GRAPH_KIND,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.partial_path import (
    PartialPathLimits,
    compute_minimal_partial_paths_in_file,
)
from blends.stack.view import StackGraphView


def _view_for_graph(graph: Graph) -> StackGraphView:
    return StackGraphView.from_syntax_graph(graph, path="test.py")


@pytest.mark.blends_test_group("stack_unittesting")
def test_minimal_paths_seed_count_includes_root_and_jump() -> None:
    graph = Graph()
    graph.add_node("1")
    graph.nodes["1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["1"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["1"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_DEFINITION] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.JUMP_TO.value

    view = _view_for_graph(graph)
    result = compute_minimal_partial_paths_in_file(view, "test.py", limits=PartialPathLimits())
    expected_seed_count = 4

    assert result.stats.seed_count == expected_seed_count


@pytest.mark.blends_test_group("stack_unittesting")
def test_minimal_paths_accept_reference_to_definition() -> None:
    graph = Graph()
    graph.add_node("1")
    graph.nodes["1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["1"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["1"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_DEFINITION] = True

    graph.add_edge("1", "2", precedence=0)

    view = _view_for_graph(graph)
    result = compute_minimal_partial_paths_in_file(view, "test.py", limits=PartialPathLimits())

    push_index = view.nid_to_index["1"]
    pop_index = view.nid_to_index["2"]
    accepted_pairs = {(path.start_node_index, path.end_node_index) for path in result.paths}

    assert (push_index, pop_index) in accepted_pairs


@pytest.mark.blends_test_group("stack_unittesting")
def test_minimal_paths_accept_jump_boundary() -> None:
    graph = Graph()
    graph.add_node("1")
    graph.nodes["1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["1"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["1"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.JUMP_TO.value

    graph.add_edge("1", "3", precedence=0)

    view = _view_for_graph(graph)
    result = compute_minimal_partial_paths_in_file(view, "test.py", limits=PartialPathLimits())

    jump_index = view.nid_to_index["3"]
    assert any(path.end_node_index == jump_index for path in result.paths)


@pytest.mark.blends_test_group("stack_unittesting")
def test_minimal_paths_forward_expands_past_non_endpoint() -> None:
    graph = Graph()
    graph.add_node("1")
    graph.nodes["1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["1"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["1"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_IS_DEFINITION] = True

    graph.add_edge("1", "2", precedence=0)
    graph.add_edge("2", "3", precedence=0)

    view = _view_for_graph(graph)
    result = compute_minimal_partial_paths_in_file(view, "test.py", limits=PartialPathLimits())

    push_index = view.nid_to_index["1"]
    pop_index = view.nid_to_index["3"]
    accepted_pairs = {(path.start_node_index, path.end_node_index) for path in result.paths}

    assert (push_index, pop_index) in accepted_pairs
    assert result.stats.length_histogram.get(2) == 1
