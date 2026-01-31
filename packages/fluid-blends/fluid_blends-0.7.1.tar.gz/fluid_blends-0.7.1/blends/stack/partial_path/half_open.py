from dataclasses import dataclass

from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.partial_path.errors import (
    _raise_empty_symbol_stack,
    _raise_incorrect_popped_symbol,
    _raise_missing_attached_scope_list,
    _raise_unexpected_attached_scope_list,
)
from blends.stack.partial_path.partial_stacks import (
    PartialScopedSymbol,
    PartialScopeStack,
    PartialSymbolStack,
)
from blends.stack.view import StackGraphView


@dataclass(frozen=True, slots=True)
class HalfOpenResult:
    symbol_stack: PartialSymbolStack
    scope_stack: PartialScopeStack


def _pop_symbol(symbol_stack: PartialSymbolStack) -> tuple[PartialScopedSymbol, PartialSymbolStack]:
    if not symbol_stack.symbols:
        _raise_empty_symbol_stack()
    head = symbol_stack.symbols[0]
    tail = PartialSymbolStack(symbols=symbol_stack.symbols[1:], variable=symbol_stack.variable)
    return head, tail


def halfopen_closed_partial_precondition(
    view: StackGraphView,
    join_node_index: int,
    symbol_stack_precondition: PartialSymbolStack,
    scope_stack_precondition: PartialScopeStack,
) -> HalfOpenResult:
    kind = view.kind_at(join_node_index)
    if kind not in {
        StackGraphNodeKind.POP_SYMBOL.value,
        StackGraphNodeKind.POP_SCOPED_SYMBOL.value,
    }:
        return HalfOpenResult(
            symbol_stack=symbol_stack_precondition,
            scope_stack=scope_stack_precondition,
        )
    popped_symbol, updated_symbol_stack = _pop_symbol(symbol_stack_precondition)
    expected_symbol_id = view.symbol_id_at(join_node_index)
    if expected_symbol_id is None or popped_symbol.symbol_id != expected_symbol_id:
        _raise_incorrect_popped_symbol()
    if kind == StackGraphNodeKind.POP_SYMBOL.value:
        if popped_symbol.scopes is not None:
            _raise_unexpected_attached_scope_list()
        return HalfOpenResult(
            symbol_stack=updated_symbol_stack,
            scope_stack=scope_stack_precondition,
        )
    if popped_symbol.scopes is None:
        _raise_missing_attached_scope_list()
    return HalfOpenResult(
        symbol_stack=updated_symbol_stack,
        scope_stack=popped_symbol.scopes,
    )


def halfopen_closed_partial_postcondition(
    view: StackGraphView,
    join_node_index: int,
    symbol_stack_postcondition: PartialSymbolStack,
    scope_stack_postcondition: PartialScopeStack,
) -> HalfOpenResult:
    kind = view.kind_at(join_node_index)
    if kind not in {
        StackGraphNodeKind.PUSH_SYMBOL.value,
        StackGraphNodeKind.PUSH_SCOPED_SYMBOL.value,
    }:
        return HalfOpenResult(
            symbol_stack=symbol_stack_postcondition,
            scope_stack=scope_stack_postcondition,
        )
    popped_symbol, updated_symbol_stack = _pop_symbol(symbol_stack_postcondition)
    expected_symbol_id = view.symbol_id_at(join_node_index)
    if expected_symbol_id is None or popped_symbol.symbol_id != expected_symbol_id:
        _raise_incorrect_popped_symbol()
    if kind == StackGraphNodeKind.PUSH_SYMBOL.value:
        if popped_symbol.scopes is not None:
            _raise_unexpected_attached_scope_list()
        return HalfOpenResult(
            symbol_stack=updated_symbol_stack,
            scope_stack=scope_stack_postcondition,
        )
    if popped_symbol.scopes is None:
        _raise_missing_attached_scope_list()
    return HalfOpenResult(
        symbol_stack=updated_symbol_stack,
        scope_stack=scope_stack_postcondition,
    )
