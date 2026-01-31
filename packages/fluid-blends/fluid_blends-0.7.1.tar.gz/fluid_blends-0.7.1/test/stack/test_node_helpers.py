import pytest

from blends.models import (
    Graph,
)
from blends.stack.attributes import (
    STACK_GRAPH_IS_EXPORTED,
    STACK_GRAPH_KIND,
    STACK_GRAPH_PRECEDENCE,
    STACK_GRAPH_SCOPE,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.node_helpers import (
    drop_scopes_node_attributes,
    jump_to_node_attributes,
    pop_scoped_symbol_node_attributes,
    pop_symbol_node_attributes,
    push_scoped_symbol_node_attributes,
    push_symbol_node_attributes,
    root_node_attributes,
    scope_node_attributes,
)
from blends.stack.node_kinds import (
    StackGraphNodeKind,
)


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_push_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1", label_type="SymbolLookup")

    graph.update_node("node_1", push_symbol_node_attributes(symbol="foo", precedence=5))

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.PUSH_SYMBOL.value
    assert node_data[STACK_GRAPH_SYMBOL] == "foo"
    assert node_data[STACK_GRAPH_SCOPE] is None
    assert node_data[STACK_GRAPH_PRECEDENCE] == 5  # noqa: PLR2004
    assert node_data[STACK_GRAPH_IS_EXPORTED] is False
    assert node_data["label_type"] == "SymbolLookup"


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_push_symbol_node_default_precedence() -> None:
    graph = Graph()
    graph.add_node("node_1")

    graph.update_node("node_1", push_symbol_node_attributes(symbol="bar"))

    assert graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] == 0


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_push_scoped_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.add_node("scope_1")

    graph.update_node(
        "node_1",
        push_scoped_symbol_node_attributes(symbol="foo", scope="scope_1", precedence=3),
    )

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.PUSH_SCOPED_SYMBOL.value
    assert node_data[STACK_GRAPH_SYMBOL] == "foo"
    assert node_data[STACK_GRAPH_SCOPE] == "scope_1"
    assert node_data[STACK_GRAPH_PRECEDENCE] == 3  # noqa: PLR2004
    assert node_data[STACK_GRAPH_IS_EXPORTED] is False


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_pop_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1", label_type="VariableDeclaration")

    graph.update_node("node_1", pop_symbol_node_attributes(symbol="x", precedence=10))

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.POP_SYMBOL.value
    assert node_data[STACK_GRAPH_SYMBOL] == "x"
    assert node_data[STACK_GRAPH_SCOPE] is None
    assert node_data[STACK_GRAPH_PRECEDENCE] == 10  # noqa: PLR2004
    assert node_data[STACK_GRAPH_IS_EXPORTED] is False
    assert node_data["label_type"] == "VariableDeclaration"


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_pop_scoped_symbol_node() -> None:
    graph = Graph()
    graph.add_node("node_1")

    graph.update_node("node_1", pop_scoped_symbol_node_attributes(symbol="y"))

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.POP_SCOPED_SYMBOL.value
    assert node_data[STACK_GRAPH_SYMBOL] == "y"
    assert node_data[STACK_GRAPH_SCOPE] is None
    assert node_data[STACK_GRAPH_PRECEDENCE] == 0
    assert node_data[STACK_GRAPH_IS_EXPORTED] is False


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_scope_node_exported() -> None:
    graph = Graph()
    graph.add_node("node_1", label_type="File")

    graph.update_node("node_1", scope_node_attributes(is_exported=True))

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.SCOPE.value
    assert node_data[STACK_GRAPH_SYMBOL] is None
    assert node_data[STACK_GRAPH_SCOPE] is None
    assert node_data[STACK_GRAPH_PRECEDENCE] == 0
    assert node_data[STACK_GRAPH_IS_EXPORTED] is True
    assert node_data["label_type"] == "File"


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_scope_node_not_exported() -> None:
    graph = Graph()
    graph.add_node("node_1", label_type="Class")

    graph.update_node("node_1", scope_node_attributes(is_exported=False))

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.SCOPE.value
    assert node_data[STACK_GRAPH_IS_EXPORTED] is False
    assert node_data["label_type"] == "Class"


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_root_node() -> None:
    graph = Graph()
    graph.add_node("node_1")

    graph.update_node("node_1", root_node_attributes())

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.ROOT.value
    assert node_data[STACK_GRAPH_SYMBOL] is None
    assert node_data[STACK_GRAPH_SCOPE] is None
    assert node_data[STACK_GRAPH_PRECEDENCE] == 0
    assert node_data[STACK_GRAPH_IS_EXPORTED] is False


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_jump_to_node() -> None:
    graph = Graph()
    graph.add_node("node_1")

    graph.update_node("node_1", jump_to_node_attributes())

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.JUMP_TO.value
    assert node_data[STACK_GRAPH_SYMBOL] is None
    assert node_data[STACK_GRAPH_SCOPE] is None
    assert node_data[STACK_GRAPH_PRECEDENCE] == 0
    assert node_data[STACK_GRAPH_IS_EXPORTED] is False


@pytest.mark.blends_test_group("stack_unittesting")
def test_mark_as_drop_scopes_node() -> None:
    graph = Graph()
    graph.add_node("node_1")

    graph.update_node("node_1", drop_scopes_node_attributes())

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.DROP_SCOPES.value
    assert node_data[STACK_GRAPH_SYMBOL] is None
    assert node_data[STACK_GRAPH_SCOPE] is None
    assert node_data[STACK_GRAPH_PRECEDENCE] == 0
    assert node_data[STACK_GRAPH_IS_EXPORTED] is False


@pytest.mark.blends_test_group("stack_unittesting")
def test_helper_preserves_existing_attributes() -> None:
    graph = Graph()
    graph.add_node(
        "node_1",
        label_type="SymbolLookup",
        symbol="x",
        custom_attr="preserved",
    )

    graph.update_node("node_1", push_symbol_node_attributes(symbol="y"))

    node_data = graph.nodes["node_1"]
    assert node_data["label_type"] == "SymbolLookup"
    assert node_data["custom_attr"] == "preserved"
    assert node_data[STACK_GRAPH_SYMBOL] == "y"


@pytest.mark.blends_test_group("stack_unittesting")
def test_helper_overwrites_existing_stack_graph_attributes() -> None:
    graph = Graph()
    graph.add_node("node_1")
    graph.nodes["node_1"][STACK_GRAPH_KIND] = "OldKind"
    graph.nodes["node_1"][STACK_GRAPH_PRECEDENCE] = 99

    graph.update_node("node_1", push_symbol_node_attributes(symbol="foo", precedence=5))

    node_data = graph.nodes["node_1"]
    assert node_data[STACK_GRAPH_KIND] == StackGraphNodeKind.PUSH_SYMBOL.value
    assert node_data[STACK_GRAPH_PRECEDENCE] == 5  # noqa: PLR2004
