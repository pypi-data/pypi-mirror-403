import pytest

from blends.models import Graph
from blends.stack.attributes import (
    STACK_GRAPH_IS_EXPORTED,
    STACK_GRAPH_KIND,
)
from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.view import (
    JUMP_TO_NID,
    ROOT_NID,
    Degree,
    StackGraphView,
    SymbolInterner,
)


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_ignores_nodes_with_none_kind() -> None:
    graph = Graph()
    graph.add_node("node_with_none_kind")
    graph.nodes["node_with_none_kind"][STACK_GRAPH_KIND] = None

    graph.add_node("node_without_kind")

    graph.add_node("valid_node")
    graph.nodes["valid_node"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    view = StackGraphView.from_syntax_graph(graph)

    assert "valid_node" in view.nid_to_index
    assert "node_with_none_kind" not in view.nid_to_index
    assert "node_without_kind" not in view.nid_to_index


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_singleton_indices_are_fixed() -> None:
    graph = Graph()

    view = StackGraphView.from_syntax_graph(graph)

    assert view.index_to_nid[0] == ROOT_NID
    assert view.index_to_nid[1] == JUMP_TO_NID
    assert view.nid_to_index[ROOT_NID] == 0
    assert view.nid_to_index[JUMP_TO_NID] == 1
    assert view.node_kind[0] == StackGraphNodeKind.ROOT.value
    assert view.node_kind[1] == StackGraphNodeKind.JUMP_TO.value


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_sorts_numeric_node_ids_by_int_value() -> None:
    graph = Graph()

    graph.add_node("10")
    graph.nodes["10"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_node("a")
    graph.nodes["a"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    view = StackGraphView.from_syntax_graph(graph)

    assert view.nid_to_index["2"] < view.nid_to_index["10"]
    assert view.nid_to_index["10"] < view.nid_to_index["a"]


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_includes_edges_only_between_stack_nodes() -> None:
    graph = Graph()

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_node("non_stack")

    graph.add_edge("2", "3", precedence=0)
    graph.add_edge("2", "non_stack", precedence=0)
    graph.add_edge("non_stack", "3", precedence=0)

    view = StackGraphView.from_syntax_graph(graph)

    source_index = view.nid_to_index["2"]
    sink_index = view.nid_to_index["3"]

    assert view.outgoing[source_index] == [(sink_index, 0)]


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_sorts_outgoing_edges_by_sink_index() -> None:
    graph = Graph()

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_node("4")
    graph.nodes["4"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_edge("2", "4", precedence=0)
    graph.add_edge("2", "3", precedence=0)

    view = StackGraphView.from_syntax_graph(graph)

    source_index = view.nid_to_index["2"]
    first_sink_index = view.nid_to_index["3"]
    second_sink_index = view.nid_to_index["4"]

    assert view.outgoing[source_index] == [
        (first_sink_index, 0),
        (second_sink_index, 0),
    ]


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_computes_incoming_degree_summary() -> None:
    graph = Graph()

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_node("4")
    graph.nodes["4"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    graph.add_edge("2", "3", precedence=0)
    graph.add_edge("4", "3", precedence=0)
    graph.add_edge("2", "4", precedence=0)

    view = StackGraphView.from_syntax_graph(graph)

    first_source_index = view.nid_to_index["2"]
    shared_sink_index = view.nid_to_index["3"]
    second_source_index = view.nid_to_index["4"]

    assert view.incoming_degree[first_source_index] == Degree.ZERO
    assert view.incoming_degree[second_source_index] == Degree.ONE
    assert view.incoming_degree[shared_sink_index] == Degree.MULTIPLE


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_collects_exported_scopes() -> None:
    graph = Graph()

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["2"][STACK_GRAPH_IS_EXPORTED] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["3"][STACK_GRAPH_IS_EXPORTED] = False

    view = StackGraphView.from_syntax_graph(graph)

    assert view.nid_to_index["2"] in view.exported_scopes
    assert view.nid_to_index["3"] not in view.exported_scopes


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_uses_path_argument_and_builds_file_maps() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    view = StackGraphView.from_syntax_graph(graph, path="override.py")

    assert view.file_path == "override.py"
    assert "override.py" in view.file_to_nodes
    assert view.nid_to_index["2"] in view.file_to_nodes["override.py"]
    assert view.node_to_file[view.nid_to_index["2"]] == "override.py"
    assert view.node_to_file[view.nid_to_index[ROOT_NID]] == ""
    assert view.node_to_file[view.nid_to_index[JUMP_TO_NID]] == ""


@pytest.mark.blends_test_group("stack_unittesting")
def test_symbol_interner_reuses_cached_symbol_id_zero() -> None:
    interner = SymbolInterner(symbol_to_id={}, id_to_symbol=[])

    first_id = interner.intern("x")
    second_id = interner.intern("x")

    assert first_id == 0
    assert second_id == 0
    assert interner.symbol_to_id["x"] == 0
    assert interner.id_to_symbol == ["x"]


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_resolves_path_from_metadata_node_zero() -> None:
    graph = Graph()
    graph.add_node("0")
    graph.nodes["0"]["path"] = "from_metadata.py"

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value

    view = StackGraphView.from_syntax_graph(graph)

    assert view.file_path == "from_metadata.py"
    assert "from_metadata.py" in view.file_to_nodes
