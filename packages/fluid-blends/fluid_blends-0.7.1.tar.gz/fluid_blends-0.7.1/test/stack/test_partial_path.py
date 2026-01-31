import pytest

from blends.models import (
    Graph,
)
from blends.stack.attributes import (
    STACK_GRAPH_KIND,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.node_kinds import (
    StackGraphNodeKind,
)
from blends.stack.partial_path import (
    PartialPath,
    PartialPathResolutionError,
    PartialPathResolutionErrorCode,
    PartialScopedSymbol,
    PartialScopeStack,
    PartialScopeStackBindings,
    PartialSymbolStack,
    PartialSymbolStackBindings,
    ScopeStackVariable,
    SymbolStackVariable,
)
from blends.stack.view import (
    StackGraphView,
)


def _view_for_graph(graph: Graph) -> StackGraphView:
    return StackGraphView.from_syntax_graph(graph, path="test.py")


@pytest.mark.blends_test_group("stack_unittesting")
def test_symbol_stack_variable_with_offset() -> None:
    initial_var_id = 1
    offset_amount = 2
    expected_offset_id = 3
    variable = SymbolStackVariable.initial()
    offset = variable.with_offset(offset_amount)
    assert variable.as_int() == initial_var_id
    assert offset.as_int() == expected_offset_id


@pytest.mark.blends_test_group("stack_unittesting")
def test_scope_stack_variable_with_offset() -> None:
    initial_var_id = 1
    offset_amount = 2
    expected_offset_id = 3
    variable = ScopeStackVariable.initial()
    offset = variable.with_offset(offset_amount)
    assert variable.as_int() == initial_var_id
    assert offset.as_int() == expected_offset_id


@pytest.mark.blends_test_group("stack_unittesting")
def test_partial_scope_stack_unify_binds_suffix() -> None:
    bindings = PartialScopeStackBindings.new()
    var = ScopeStackVariable.initial()
    lhs = PartialScopeStack(scopes=(1, 2), variable=None)
    rhs = PartialScopeStack(scopes=(1,), variable=var)

    result = lhs.unify(rhs, bindings)

    assert result == lhs
    assert bindings.get(var) == PartialScopeStack(scopes=(2,), variable=None)


@pytest.mark.blends_test_group("stack_unittesting")
def test_partial_scope_stack_unify_mismatch_raises() -> None:
    bindings = PartialScopeStackBindings.new()
    lhs = PartialScopeStack(scopes=(1,), variable=None)
    rhs = PartialScopeStack(scopes=(2,), variable=None)

    with pytest.raises(PartialPathResolutionError) as excinfo:
        lhs.unify(rhs, bindings)

    exception = excinfo.value  # type: ignore[attr-defined]
    assert exception.code == PartialPathResolutionErrorCode.SCOPE_STACK_UNSATISFIED


@pytest.mark.blends_test_group("stack_unittesting")
def test_partial_symbol_stack_unify_with_attached_scopes() -> None:
    scope_bindings = PartialScopeStackBindings.new()
    symbol_bindings = PartialSymbolStackBindings.new()
    scopes = PartialScopeStack(scopes=(5,), variable=None)
    symbol = PartialScopedSymbol(symbol_id=1, scopes=scopes)
    lhs = PartialSymbolStack(symbols=(symbol,), variable=None)
    rhs = PartialSymbolStack(symbols=(symbol,), variable=None)

    result = lhs.unify(rhs, symbol_bindings, scope_bindings)

    assert result.symbols[0].symbol_id == 1
    assert result.symbols[0].scopes == scopes
    assert symbol_bindings.bindings == {}
    assert scope_bindings.bindings == {}


@pytest.mark.blends_test_group("stack_unittesting")
def test_partial_symbol_stack_unify_symbol_mismatch_raises() -> None:
    scope_bindings = PartialScopeStackBindings.new()
    symbol_bindings = PartialSymbolStackBindings.new()
    lhs = PartialSymbolStack(
        symbols=(PartialScopedSymbol(symbol_id=1, scopes=None),),
        variable=None,
    )
    rhs = PartialSymbolStack(
        symbols=(PartialScopedSymbol(symbol_id=2, scopes=None),),
        variable=None,
    )

    with pytest.raises(PartialPathResolutionError) as excinfo:
        lhs.unify(rhs, symbol_bindings, scope_bindings)

    exception = excinfo.value  # type: ignore[attr-defined]
    assert exception.code == PartialPathResolutionErrorCode.SYMBOL_STACK_UNSATISFIED


@pytest.mark.blends_test_group("stack_unittesting")
def test_concatenate_undoes_join_push_symbol() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    join = view.nid_to_index["2"]
    symbol_id = view.symbols.intern("x")

    left = PartialPath(
        start_node_index=0,
        end_node_index=join,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack(
            symbols=(PartialScopedSymbol(symbol_id=symbol_id, scopes=None),),
            variable=None,
        ),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )
    right = PartialPath(
        start_node_index=join,
        end_node_index=join,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack.empty(),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )

    result = left.concatenate(view, right)

    assert result.symbol_stack_precondition == PartialSymbolStack.empty()
    assert result.symbol_stack_postcondition == PartialSymbolStack.empty()


@pytest.mark.blends_test_group("stack_unittesting")
def test_concatenate_undoes_join_pop_symbol() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    join = view.nid_to_index["2"]
    symbol_id = view.symbols.intern("x")

    left = PartialPath(
        start_node_index=0,
        end_node_index=join,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack.empty(),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )
    right = PartialPath(
        start_node_index=join,
        end_node_index=join,
        symbol_stack_precondition=PartialSymbolStack(
            symbols=(PartialScopedSymbol(symbol_id=symbol_id, scopes=None),),
            variable=None,
        ),
        symbol_stack_postcondition=PartialSymbolStack.empty(),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )

    result = left.concatenate(view, right)

    assert result.symbol_stack_precondition == PartialSymbolStack.empty()
    assert result.symbol_stack_postcondition == PartialSymbolStack.empty()


@pytest.mark.blends_test_group("stack_unittesting")
def test_concatenate_incorrect_source_node_raises() -> None:
    graph = Graph()
    view = _view_for_graph(graph)
    left = PartialPath(
        start_node_index=0,
        end_node_index=0,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack.empty(),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )
    right = PartialPath(
        start_node_index=1,
        end_node_index=1,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack.empty(),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )

    with pytest.raises(PartialPathResolutionError) as excinfo:
        left.concatenate(view, right)

    exception = excinfo.value  # type: ignore[attr-defined]
    assert exception.code == PartialPathResolutionErrorCode.INCORRECT_SOURCE_NODE


@pytest.mark.blends_test_group("stack_unittesting")
def test_concatenate_unbound_symbol_stack_var_raises() -> None:
    graph = Graph()
    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"

    view = _view_for_graph(graph)
    join = view.nid_to_index["2"]
    symbol_id = view.symbols.intern("x")
    var = SymbolStackVariable.initial()

    left = PartialPath(
        start_node_index=0,
        end_node_index=join,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack(
            symbols=(PartialScopedSymbol(symbol_id=symbol_id, scopes=None),),
            variable=None,
        ),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )
    right = PartialPath(
        start_node_index=join,
        end_node_index=join,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack.from_variable(var),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )

    with pytest.raises(PartialPathResolutionError) as excinfo:
        left.concatenate(view, right)

    exception = excinfo.value  # type: ignore[attr-defined]
    assert exception.code == PartialPathResolutionErrorCode.UNBOUND_SYMBOL_STACK_VARIABLE


@pytest.mark.blends_test_group("stack_unittesting")
def test_concatenate_unbound_scope_stack_var_raises() -> None:
    graph = Graph()
    view = _view_for_graph(graph)
    var = ScopeStackVariable.initial()

    left = PartialPath(
        start_node_index=0,
        end_node_index=0,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack.empty(),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )
    right = PartialPath(
        start_node_index=0,
        end_node_index=0,
        symbol_stack_precondition=PartialSymbolStack.empty(),
        symbol_stack_postcondition=PartialSymbolStack.empty(),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.from_variable(var),
    )

    with pytest.raises(PartialPathResolutionError) as excinfo:
        left.concatenate(view, right)

    exception = excinfo.value  # type: ignore[attr-defined]
    assert exception.code == PartialPathResolutionErrorCode.UNBOUND_SCOPE_STACK_VARIABLE


@pytest.mark.blends_test_group("stack_unittesting")
def test_ensure_no_overlapping_variables_offsets_rhs() -> None:
    expected_var_id = 2
    var = SymbolStackVariable.initial()
    lhs = PartialPath(
        start_node_index=0,
        end_node_index=0,
        symbol_stack_precondition=PartialSymbolStack.from_variable(var),
        symbol_stack_postcondition=PartialSymbolStack.empty(),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )
    rhs = PartialPath(
        start_node_index=0,
        end_node_index=0,
        symbol_stack_precondition=PartialSymbolStack.from_variable(var),
        symbol_stack_postcondition=PartialSymbolStack.empty(),
        scope_stack_precondition=PartialScopeStack.empty(),
        scope_stack_postcondition=PartialScopeStack.empty(),
    )

    updated_rhs = rhs.ensure_no_overlapping_variables(lhs)

    assert updated_rhs.symbol_stack_precondition.variable is not None
    assert updated_rhs.symbol_stack_precondition.variable.as_int() == expected_var_id
