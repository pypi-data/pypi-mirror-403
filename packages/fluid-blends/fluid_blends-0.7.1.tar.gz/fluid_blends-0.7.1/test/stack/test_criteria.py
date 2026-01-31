import pytest

from blends.models import (
    Graph,
)
from blends.stack.attributes import (
    STACK_GRAPH_IS_DEFINITION,
    STACK_GRAPH_IS_EXPORTED,
    STACK_GRAPH_IS_REFERENCE,
    STACK_GRAPH_KIND,
    STACK_GRAPH_SCOPE,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.criteria import (
    is_complete_definition_path,
    is_definition_endpoint,
    is_endpoint,
    is_exported_scope_endpoint,
    is_jump_to_boundary,
    is_reference_endpoint,
    is_root_endpoint,
)
from blends.stack.node_kinds import (
    StackGraphNodeKind,
)
from blends.stack.stacks import (
    ScopeStackNode,
    StackState,
    SymbolStackNode,
)
from blends.stack.transitions import (
    apply_node,
)
from test.stack.test_helpers import view_for_graph


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_reference_endpoint_push_with_flag_true() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_REFERENCE] = True

    view = view_for_graph(graph)
    node_index = view.nid_to_index["2"]

    assert is_reference_endpoint(view, node_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_reference_endpoint_push_with_flag_false() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_REFERENCE] = False

    view = view_for_graph(graph)
    node_index = view.nid_to_index["2"]

    assert not is_reference_endpoint(view, node_index)
    assert not is_endpoint(view, node_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_reference_endpoint_push_scoped_symbol() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["2"][STACK_GRAPH_IS_EXPORTED] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SCOPED_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_SCOPE] = "2"
    graph.nodes["3"][STACK_GRAPH_IS_REFERENCE] = True

    view = view_for_graph(graph)
    node_index = view.nid_to_index["3"]

    assert is_reference_endpoint(view, node_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_definition_endpoint_pop_with_flag_true() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_DEFINITION] = True

    view = view_for_graph(graph)
    node_index = view.nid_to_index["2"]

    assert is_definition_endpoint(view, node_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_definition_endpoint_pop_with_flag_false() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_DEFINITION] = False

    view = view_for_graph(graph)
    node_index = view.nid_to_index["2"]

    assert not is_definition_endpoint(view, node_index)
    assert not is_endpoint(view, node_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_exported_scope_endpoint_exported_scope() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["2"][STACK_GRAPH_IS_EXPORTED] = True

    view = view_for_graph(graph)
    node_index = view.nid_to_index["2"]

    assert is_exported_scope_endpoint(view, node_index)
    assert is_endpoint(view, node_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_exported_scope_endpoint_non_exported_scope() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["2"][STACK_GRAPH_IS_EXPORTED] = False

    view = view_for_graph(graph)
    node_index = view.nid_to_index["2"]

    assert not is_exported_scope_endpoint(view, node_index)
    assert not is_endpoint(view, node_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_root_endpoint() -> None:
    graph = Graph()

    view = view_for_graph(graph)
    root_index = 0

    assert is_root_endpoint(view, root_index)
    assert is_endpoint(view, root_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_jump_to_boundary() -> None:
    graph = Graph()

    view = view_for_graph(graph)
    jump_to_index = 1

    assert is_jump_to_boundary(view, jump_to_index)
    assert not is_endpoint(view, jump_to_index)


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_complete_definition_path_valid_ref_to_def() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_IS_DEFINITION] = True

    view = view_for_graph(graph)
    start_index = view.nid_to_index["2"]
    end_index = view.nid_to_index["3"]

    start_state = StackState(symbol_stack=None, scope_stack=None)
    result = apply_node(view, start_index, start_state)
    end_state = apply_node(view, end_index, result.state).state

    assert is_complete_definition_path(
        view,
        start_node_index=start_index,
        end_node_index=end_index,
        start_state=start_state,
        end_state=end_state,
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_complete_definition_path_false_if_start_not_reference_endpoint() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_REFERENCE] = False

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_IS_DEFINITION] = True

    view = view_for_graph(graph)
    start_index = view.nid_to_index["2"]
    end_index = view.nid_to_index["3"]

    start_state = StackState(symbol_stack=None, scope_stack=None)
    end_state = StackState(symbol_stack=None, scope_stack=None)

    assert not is_complete_definition_path(
        view,
        start_node_index=start_index,
        end_node_index=end_index,
        start_state=start_state,
        end_state=end_state,
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_complete_definition_path_false_if_end_not_definition_endpoint() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_IS_DEFINITION] = False

    view = view_for_graph(graph)
    start_index = view.nid_to_index["2"]
    end_index = view.nid_to_index["3"]

    start_state = StackState(symbol_stack=None, scope_stack=None)
    end_state = StackState(symbol_stack=None, scope_stack=None)

    assert not is_complete_definition_path(
        view,
        start_node_index=start_index,
        end_node_index=end_index,
        start_state=start_state,
        end_state=end_state,
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_complete_definition_path_false_if_start_symbol_stack_non_empty() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_IS_DEFINITION] = True

    view = view_for_graph(graph)
    start_index = view.nid_to_index["2"]
    end_index = view.nid_to_index["3"]

    sym_id = view.symbols.intern("y")
    start_state = StackState(
        symbol_stack=SymbolStackNode(symbol_id=sym_id, scopes=None, tail=None),
        scope_stack=None,
    )
    end_state = StackState(symbol_stack=None, scope_stack=None)

    assert not is_complete_definition_path(
        view,
        start_node_index=start_index,
        end_node_index=end_index,
        start_state=start_state,
        end_state=end_state,
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_complete_definition_path_false_if_start_scope_stack_non_empty() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_IS_DEFINITION] = True

    view = view_for_graph(graph)
    start_index = view.nid_to_index["2"]
    end_index = view.nid_to_index["3"]

    start_state = StackState(
        symbol_stack=None,
        scope_stack=ScopeStackNode(scope_index=10, tail=None),
    )
    end_state = StackState(symbol_stack=None, scope_stack=None)

    assert not is_complete_definition_path(
        view,
        start_node_index=start_index,
        end_node_index=end_index,
        start_state=start_state,
        end_state=end_state,
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_complete_definition_path_false_if_end_symbol_stack_non_empty() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_IS_DEFINITION] = True

    view = view_for_graph(graph)
    start_index = view.nid_to_index["2"]
    end_index = view.nid_to_index["3"]

    start_state = StackState(symbol_stack=None, scope_stack=None)
    sym_id = view.symbols.intern("y")
    end_state = StackState(
        symbol_stack=SymbolStackNode(symbol_id=sym_id, scopes=None, tail=None),
        scope_stack=None,
    )

    assert not is_complete_definition_path(
        view,
        start_node_index=start_index,
        end_node_index=end_index,
        start_state=start_state,
        end_state=end_state,
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_complete_definition_path_false_if_end_scope_stack_non_empty() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_IS_DEFINITION] = True

    view = view_for_graph(graph)
    start_index = view.nid_to_index["2"]
    end_index = view.nid_to_index["3"]

    start_state = StackState(symbol_stack=None, scope_stack=None)
    result = apply_node(view, start_index, start_state)
    end_result = apply_node(view, end_index, result.state)
    end_state = end_result.state

    end_state_with_scope = StackState(
        symbol_stack=end_state.symbol_stack,
        scope_stack=ScopeStackNode(scope_index=10, tail=None),
    )

    assert not is_complete_definition_path(
        view,
        start_node_index=start_index,
        end_node_index=end_index,
        start_state=start_state,
        end_state=end_state_with_scope,
    )
