from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.partial_path.partial_path import PartialPath
from blends.stack.partial_path.partial_stacks import (
    PartialScopedSymbol,
    PartialScopeStack,
    PartialSymbolStack,
)
from blends.stack.partial_path.variables import (
    ScopeStackVariable,
    SymbolStackVariable,
)

if TYPE_CHECKING:
    from blends.stack.view import StackGraphView


@dataclass(slots=True)
class StackConditions:
    symbol_pre: PartialSymbolStack
    symbol_post: PartialSymbolStack
    scope_pre: PartialScopeStack
    scope_post: PartialScopeStack


def default_stacks() -> tuple[
    PartialSymbolStack, PartialSymbolStack, PartialScopeStack, PartialScopeStack
]:
    symbol_var = PartialSymbolStack.from_variable(SymbolStackVariable.initial())
    scope_var = PartialScopeStack.from_variable(ScopeStackVariable.initial())
    return symbol_var, symbol_var, scope_var, scope_var


def apply_node_semantics(view: StackGraphView, node_index: int) -> StackConditions:
    symbol_pre, symbol_post, scope_pre, scope_post = default_stacks()
    stacks = StackConditions(
        symbol_pre=symbol_pre,
        symbol_post=symbol_post,
        scope_pre=scope_pre,
        scope_post=scope_post,
    )
    handler = _HANDLERS.get(view.kind_at(node_index))
    if handler is not None:
        stacks = handler(view, node_index, stacks)
    return stacks


def create_seed_path(view: StackGraphView, seed_node_index: int) -> PartialPath:
    stacks = apply_node_semantics(view, seed_node_index)
    return PartialPath(
        start_node_index=seed_node_index,
        end_node_index=seed_node_index,
        symbol_stack_precondition=stacks.symbol_pre,
        symbol_stack_postcondition=stacks.symbol_post,
        scope_stack_precondition=stacks.scope_pre,
        scope_stack_postcondition=stacks.scope_post,
        edges=(),
    )


def _handle_push_symbol(
    view: StackGraphView,
    sink_node_index: int,
    stacks: StackConditions,
) -> StackConditions:
    symbol_id = view.symbol_id_at(sink_node_index)
    if symbol_id is None:
        return stacks
    stacks.symbol_post = PartialSymbolStack(
        symbols=(PartialScopedSymbol(symbol_id=symbol_id, scopes=None),),
        variable=SymbolStackVariable.initial(),
    )
    return stacks


def _handle_pop_symbol(
    view: StackGraphView,
    sink_node_index: int,
    stacks: StackConditions,
) -> StackConditions:
    symbol_id = view.symbol_id_at(sink_node_index)
    if symbol_id is None:
        return stacks
    stacks.symbol_pre = PartialSymbolStack(
        symbols=(PartialScopedSymbol(symbol_id=symbol_id, scopes=None),),
        variable=SymbolStackVariable.initial(),
    )
    stacks.symbol_post = PartialSymbolStack.from_variable(SymbolStackVariable.initial())
    return stacks


def _handle_push_scoped_symbol(
    view: StackGraphView,
    sink_node_index: int,
    stacks: StackConditions,
) -> StackConditions:
    symbol_id = view.symbol_id_at(sink_node_index)
    scope_index = view.scope_index_at(sink_node_index)
    if symbol_id is None or scope_index is None:
        return stacks
    attached_scopes = PartialScopeStack(
        scopes=(scope_index,), variable=ScopeStackVariable.initial()
    )
    stacks.symbol_post = PartialSymbolStack(
        symbols=(PartialScopedSymbol(symbol_id=symbol_id, scopes=attached_scopes),),
        variable=SymbolStackVariable.initial(),
    )
    return stacks


def _handle_pop_scoped_symbol(
    view: StackGraphView,
    sink_node_index: int,
    stacks: StackConditions,
) -> StackConditions:
    symbol_id = view.symbol_id_at(sink_node_index)
    if symbol_id is None:
        return stacks
    attached_scopes = PartialScopeStack(scopes=(), variable=ScopeStackVariable.initial())
    stacks.symbol_pre = PartialSymbolStack(
        symbols=(PartialScopedSymbol(symbol_id=symbol_id, scopes=attached_scopes),),
        variable=SymbolStackVariable.initial(),
    )
    stacks.symbol_post = PartialSymbolStack.from_variable(SymbolStackVariable.initial())
    stacks.scope_post = attached_scopes
    return stacks


def _handle_drop_scopes(
    _view: StackGraphView,
    _sink_node_index: int,
    stacks: StackConditions,
) -> StackConditions:
    stacks.scope_pre = PartialScopeStack.from_variable(ScopeStackVariable.initial())
    stacks.scope_post = PartialScopeStack.empty()
    return stacks


def _handle_jump_to(
    _view: StackGraphView,
    _sink_node_index: int,
    stacks: StackConditions,
) -> StackConditions:
    stacks.scope_pre = PartialScopeStack.from_variable(ScopeStackVariable.initial())
    stacks.scope_post = PartialScopeStack.from_variable(ScopeStackVariable.initial())
    return stacks


_HANDLERS = {
    StackGraphNodeKind.PUSH_SYMBOL.value: _handle_push_symbol,
    StackGraphNodeKind.POP_SYMBOL.value: _handle_pop_symbol,
    StackGraphNodeKind.PUSH_SCOPED_SYMBOL.value: _handle_push_scoped_symbol,
    StackGraphNodeKind.POP_SCOPED_SYMBOL.value: _handle_pop_scoped_symbol,
    StackGraphNodeKind.DROP_SCOPES.value: _handle_drop_scopes,
    StackGraphNodeKind.JUMP_TO.value: _handle_jump_to,
}
