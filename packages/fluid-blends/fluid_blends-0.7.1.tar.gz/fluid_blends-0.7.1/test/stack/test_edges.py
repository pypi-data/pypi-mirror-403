import pytest

from blends.models import (
    Graph,
)
from blends.stack.edges import (
    Edge,
    add_edge,
)


@pytest.mark.blends_test_group("stack_unittesting")
def test_add_edge_from_reference_to_scope() -> None:
    graph = Graph()
    graph.add_node("ref_1", label_type="SymbolLookup", symbol="x")
    graph.add_node("scope_1", label_type="File")

    add_edge(graph, Edge(source="ref_1", sink="scope_1", precedence=0))

    assert graph.has_edge("ref_1", "scope_1")
    edge_data = graph["ref_1"]["scope_1"]
    assert edge_data["precedence"] == 0
    assert "label_stack" not in edge_data
    assert "symbol" not in edge_data


@pytest.mark.blends_test_group("stack_unittesting")
def test_add_edge_from_scope_to_definition() -> None:
    graph = Graph()
    graph.add_node("scope_1", label_type="File")
    graph.add_node("def_1", label_type="VariableDeclaration", variable="x")

    add_edge(graph, Edge(source="scope_1", sink="def_1", precedence=0))

    assert graph.has_edge("scope_1", "def_1")
    edge_data = graph["scope_1"]["def_1"]
    assert edge_data["precedence"] == 0
    assert "label_stack" not in edge_data
    assert "symbol" not in edge_data


@pytest.mark.blends_test_group("stack_unittesting")
def test_add_lookup_edge() -> None:
    graph = Graph()
    graph.add_node("child_scope", label_type="MethodDeclaration")
    graph.add_node("parent_scope", label_type="File")

    add_edge(graph, Edge(source="child_scope", sink="parent_scope", precedence=0))

    assert graph.has_edge("child_scope", "parent_scope")
    edge_data = graph["child_scope"]["parent_scope"]
    assert edge_data["precedence"] == 0
    assert "label_stack" not in edge_data
    assert "symbol" not in edge_data


@pytest.mark.blends_test_group("stack_unittesting")
def test_add_edge_from_reference_to_scope_with_precedence() -> None:
    graph = Graph()
    graph.add_node("ref_1", label_type="SymbolLookup", symbol="x")
    graph.add_node("scope_1", label_type="File")

    add_edge(graph, Edge(source="ref_1", sink="scope_1", precedence=5))

    edge_data = graph["ref_1"]["scope_1"]
    assert edge_data["precedence"] == 5  # noqa: PLR2004


@pytest.mark.blends_test_group("stack_unittesting")
def test_add_edge_from_scope_to_definition_with_precedence() -> None:
    graph = Graph()
    graph.add_node("scope_1", label_type="MethodDeclaration")
    graph.add_node("def_1", label_type="VariableDeclaration", variable="x")

    add_edge(graph, Edge(source="scope_1", sink="def_1", precedence=10))

    edge_data = graph["scope_1"]["def_1"]
    assert edge_data["precedence"] == 10  # noqa: PLR2004


@pytest.mark.blends_test_group("stack_unittesting")
def test_multiple_edges_from_scope_to_definitions() -> None:
    graph = Graph()
    graph.add_node("scope_1", label_type="File")
    graph.add_node("def_1", label_type="VariableDeclaration", variable="x")
    graph.add_node("def_2", label_type="VariableDeclaration", variable="y")

    add_edge(graph, Edge(source="scope_1", sink="def_1", precedence=0))
    add_edge(graph, Edge(source="scope_1", sink="def_2", precedence=0))

    assert graph.has_edge("scope_1", "def_1")
    assert graph.has_edge("scope_1", "def_2")
    assert graph["scope_1"]["def_1"]["precedence"] == 0
    assert graph["scope_1"]["def_2"]["precedence"] == 0


@pytest.mark.blends_test_group("stack_unittesting")
def test_scope_hierarchy_with_lookup_edges() -> None:
    graph = Graph()
    graph.add_node("file_scope", label_type="File")
    graph.add_node("class_scope", label_type="Class")
    graph.add_node("method_scope", label_type="MethodDeclaration")

    add_edge(graph, Edge(source="class_scope", sink="file_scope", precedence=0))
    add_edge(graph, Edge(source="method_scope", sink="class_scope", precedence=0))

    assert graph.has_edge("class_scope", "file_scope")
    assert graph.has_edge("method_scope", "class_scope")
    assert graph["class_scope"]["file_scope"]["precedence"] == 0
    assert graph["method_scope"]["class_scope"]["precedence"] == 0
