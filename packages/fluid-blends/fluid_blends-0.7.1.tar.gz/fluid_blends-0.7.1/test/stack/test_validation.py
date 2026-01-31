import pytest

from blends.models import (
    Graph,
)
from blends.stack.attributes import (
    STACK_GRAPH_IS_DEFINITION,
    STACK_GRAPH_IS_EXPORTED,
    STACK_GRAPH_IS_REFERENCE,
    STACK_GRAPH_KIND,
    STACK_GRAPH_PRECEDENCE,
    STACK_GRAPH_SCOPE,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.node_kinds import (
    StackGraphNodeKind,
)
from blends.stack.validation import (
    validate_stack_graph_graph,
    validate_stack_graph_node,
)


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_valid_push_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "foo"
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = None
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 0
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = False
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_valid_pop_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "bar"
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = None
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 5
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = False
    graph.nodes["node_1"][STACK_GRAPH_IS_DEFINITION] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_valid_push_scoped_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.add_node("scope_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SCOPED_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "baz"
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = "scope_1"
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 0
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = False
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_valid_scope_node_exported() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = None
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = None
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 0
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_valid_scope_node_not_exported() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = None
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = None
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 0
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = False

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_valid_root_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.ROOT.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = None
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = None
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 0
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = False

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_valid_drop_scopes_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.DROP_SCOPES.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = None
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = None
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 0
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = False

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_valid_jump_to_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.JUMP_TO.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = None
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = None
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 0
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = False

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_valid_pop_scoped_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SCOPED_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "qux"
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = None
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 0
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = False
    graph.nodes["node_1"][STACK_GRAPH_IS_DEFINITION] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_missing_symbol_on_push_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = None
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Missing symbol" in errors[0]
    assert "node_1" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_empty_symbol_on_push_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = ""
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Missing symbol" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_missing_scope_on_push_scoped_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SCOPED_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "foo"
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = None
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Missing scope" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_missing_is_exported_on_scope_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = None

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Missing is_exported" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_symbol_on_scope_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "unexpected"
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = False

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected symbol" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_scope_on_push_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "foo"
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = "scope_1"
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected scope" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_is_exported_on_push_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "foo"
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = True
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected is_exported" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_missing_symbol_on_pop_scoped_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SCOPED_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = None
    graph.nodes["node_1"][STACK_GRAPH_IS_DEFINITION] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Missing symbol" in errors[0]
    assert "node_1" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_symbol_on_drop_scopes_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.DROP_SCOPES.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "unexpected"

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected symbol" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_symbol_on_jump_to_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.JUMP_TO.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "unexpected"

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected symbol" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_scope_on_drop_scopes_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.DROP_SCOPES.value
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = "scope_1"

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected scope" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_scope_on_jump_to_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.JUMP_TO.value
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = "scope_1"

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected scope" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_is_exported_on_drop_scopes_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.DROP_SCOPES.value
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected is_exported" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_is_exported_on_jump_to_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.JUMP_TO.value
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected is_exported" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unexpected_is_exported_on_pop_scoped_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SCOPED_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "foo"
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = True
    graph.nodes["node_1"][STACK_GRAPH_IS_DEFINITION] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unexpected is_exported" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_invalid_precedence() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "foo"
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = "not_an_int"
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Invalid precedence" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_unknown_kind() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = "UnknownNodeKind"

    errors = validate_stack_graph_node(graph, "node_1")

    assert len(errors) == 1
    assert "Unknown stack graph kind" in errors[0]
    assert "UnknownNodeKind" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_returns_error_list() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = None
    graph.nodes["node_1"][STACK_GRAPH_SCOPE] = "unexpected"
    graph.nodes["node_1"][STACK_GRAPH_IS_EXPORTED] = True
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_node(graph, "node_1")

    assert isinstance(errors, list)
    assert len(errors) == 3  # noqa: PLR2004
    assert all(isinstance(error, str) for error in errors)


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_ignores_nodes_without_kind() -> None:
    graph = Graph()
    graph.add_node("node_1", label_type="SomeNode")

    errors = validate_stack_graph_node(graph, "node_1")

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_stack_graph_graph_all_nodes() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "foo"
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True
    graph.add_node("node_2")
    graph.nodes["node_2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["node_2"][STACK_GRAPH_SYMBOL] = None
    graph.nodes["node_2"][STACK_GRAPH_IS_DEFINITION] = True
    graph.add_node("node_3")

    errors = validate_stack_graph_graph(graph)

    assert len(errors) == 1
    assert "Missing symbol" in errors[0]
    assert "node_2" in errors[0]


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_stack_graph_graph_specific_nodes() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["node_1"][STACK_GRAPH_SYMBOL] = "foo"
    graph.nodes["node_1"][STACK_GRAPH_IS_REFERENCE] = True
    graph.add_node("node_2")
    graph.nodes["node_2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["node_2"][STACK_GRAPH_SYMBOL] = None

    errors = validate_stack_graph_graph(graph, node_ids=["node_1"])

    assert errors == []


@pytest.mark.blends_test_group("stack_unittesting")
def test_validate_stack_graph_graph_with_new_node_kinds() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = StackGraphNodeKind.DROP_SCOPES.value
    graph.add_node("node_2")
    graph.nodes["node_2"][STACK_GRAPH_KIND] = StackGraphNodeKind.JUMP_TO.value
    graph.add_node("node_3")
    graph.nodes["node_3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SCOPED_SYMBOL.value
    graph.nodes["node_3"][STACK_GRAPH_SYMBOL] = "bar"
    graph.nodes["node_3"][STACK_GRAPH_IS_DEFINITION] = True
    graph.add_node("node_4")
    graph.add_node("scope_1")
    graph.nodes["node_4"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SCOPED_SYMBOL.value
    graph.nodes["node_4"][STACK_GRAPH_SYMBOL] = "baz"
    graph.nodes["node_4"][STACK_GRAPH_SCOPE] = "scope_1"
    graph.nodes["node_4"][STACK_GRAPH_IS_REFERENCE] = True

    errors = validate_stack_graph_graph(graph)

    assert errors == []
