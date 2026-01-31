import pytest

from blends.models import (
    Graph,
)
from blends.stack.attributes import (
    STACK_GRAPH_IS_EXPORTED,
    STACK_GRAPH_KIND,
    STACK_GRAPH_SCOPE,
    STACK_GRAPH_SYMBOL,
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
    TransitionError,
    apply_node,
)
from blends.stack.view import (
    StackGraphView,
)


def _view_for_graph(graph: Graph) -> StackGraphView:
    return StackGraphView.from_syntax_graph(graph, path="test.py")


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_push_symbol_pushes_symbol() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    state = StackState(symbol_stack=None, scope_stack=None)

    result = apply_node(view, view.nid_to_index["2"], state)

    assert result.error is None
    assert result.jump_target is None
    assert result.state.symbol_stack is not None
    assert view.symbols.lookup(result.state.symbol_stack.symbol_id) == "x"
    assert result.state.symbol_stack.scopes is None
    assert result.state.symbol_stack.tail is None


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_pop_symbol_pops_only_when_symbol_matches() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    sym_id = view.symbols.intern("x")
    state = StackState(symbol_stack=SymbolStackNode(sym_id, None, None), scope_stack=None)

    result = apply_node(view, view.nid_to_index["2"], state)

    assert result.error is None
    assert result.state.symbol_stack is None


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_pop_symbol_errors_on_empty_symbol_stack() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    state = StackState(symbol_stack=None, scope_stack=None)

    result = apply_node(view, view.nid_to_index["2"], state)

    assert result.error == TransitionError.EMPTY_SYMBOL_STACK


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_pop_symbol_errors_on_symbol_mismatch() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    state = StackState(
        symbol_stack=SymbolStackNode(view.symbols.intern("y"), None, None), scope_stack=None
    )

    result = apply_node(view, view.nid_to_index["2"], state)

    assert result.error == TransitionError.INCORRECT_POPPED_SYMBOL


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_pop_symbol_errors_on_unexpected_attached_scopes() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    attached = ScopeStackNode(scope_index=123, tail=None)
    state = StackState(
        symbol_stack=SymbolStackNode(view.symbols.intern("x"), attached, None),
        scope_stack=None,
    )

    result = apply_node(view, view.nid_to_index["2"], state)

    assert result.error == TransitionError.UNEXPECTED_ATTACHED_SCOPE_LIST


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_drop_scopes_clears_scope_stack() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.DROP_SCOPES.value

    view = _view_for_graph(graph)
    state = StackState(symbol_stack=None, scope_stack=ScopeStackNode(1, None))

    result = apply_node(view, view.nid_to_index["2"], state)

    assert result.error is None
    assert result.state.scope_stack is None


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_jump_to_errors_on_empty_scope_stack() -> None:
    graph = Graph()

    view = _view_for_graph(graph)
    state = StackState(symbol_stack=None, scope_stack=None)

    result = apply_node(view, view.nid_to_index["__stack_graph_jump_to__"], state)

    assert result.error == TransitionError.EMPTY_SCOPE_STACK


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_jump_to_returns_top_scope_and_pops_it() -> None:
    graph = Graph()

    view = _view_for_graph(graph)
    scope_stack = ScopeStackNode(scope_index=10, tail=ScopeStackNode(scope_index=20, tail=None))
    state = StackState(symbol_stack=None, scope_stack=scope_stack)

    result = apply_node(view, view.nid_to_index["__stack_graph_jump_to__"], state)

    assert result.error is None
    assert result.jump_target == 10  # noqa: PLR2004
    assert result.state.scope_stack is not None
    assert result.state.scope_stack.scope_index == 20  # noqa: PLR2004
    assert result.state.scope_stack.tail is None


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_push_scoped_symbol_attaches_scope_and_current_scope_stack() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value
    graph.nodes["2"][STACK_GRAPH_IS_EXPORTED] = True

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SCOPED_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["3"][STACK_GRAPH_SCOPE] = "2"

    view = _view_for_graph(graph)
    existing_scope_stack = ScopeStackNode(scope_index=999, tail=None)
    state = StackState(symbol_stack=None, scope_stack=existing_scope_stack)

    result = apply_node(view, view.nid_to_index["3"], state)

    assert result.error is None
    assert result.state.symbol_stack is not None
    assert result.state.symbol_stack.scopes is not None
    assert result.state.symbol_stack.scopes.scope_index == view.nid_to_index["2"]
    assert result.state.symbol_stack.scopes.tail == existing_scope_stack
    assert result.state.scope_stack == existing_scope_stack


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_pop_scoped_symbol_restores_scope_stack_from_attached_scopes() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SCOPED_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    attached_scopes = ScopeStackNode(scope_index=7, tail=ScopeStackNode(scope_index=8, tail=None))
    top = SymbolStackNode(symbol_id=view.symbols.intern("x"), scopes=attached_scopes, tail=None)
    state = StackState(symbol_stack=top, scope_stack=ScopeStackNode(scope_index=1, tail=None))

    result = apply_node(view, view.nid_to_index["2"], state)

    assert result.error is None
    assert result.state.symbol_stack is None
    assert result.state.scope_stack == attached_scopes


@pytest.mark.blends_test_group("stack_unittesting")
def test_apply_node_ref_to_def_traversal_ends_with_empty_stacks() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    graph.add_node("3")
    graph.nodes["3"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["3"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    state = StackState(symbol_stack=None, scope_stack=None)

    result1 = apply_node(view, view.nid_to_index["2"], state)
    assert result1.error is None
    assert result1.state.symbol_stack is not None

    result2 = apply_node(view, view.nid_to_index["3"], result1.state)
    assert result2.error is None
    assert result2.state.symbol_stack is None
    assert result2.state.scope_stack is None
