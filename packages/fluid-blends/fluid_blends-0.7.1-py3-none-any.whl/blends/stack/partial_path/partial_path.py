from dataclasses import dataclass
from typing import TYPE_CHECKING

from blends.stack.partial_path.bindings import (
    PartialScopeStackBindings,
    PartialSymbolStackBindings,
)
from blends.stack.partial_path.errors import (
    _raise_incorrect_source_node,
    _raise_unbound_scope_stack_variable,
    _raise_unbound_symbol_stack_variable,
)
from blends.stack.partial_path.half_open import (
    halfopen_closed_partial_postcondition,
    halfopen_closed_partial_precondition,
)

if TYPE_CHECKING:
    from blends.stack.partial_path.partial_stacks import PartialScopeStack, PartialSymbolStack
    from blends.stack.partial_path.variables import ScopeStackVariable
    from blends.stack.selection import PartialPathEdge
    from blends.stack.view import StackGraphView


def _scope_vars_from_scope_stack(scope_stack: "PartialScopeStack") -> set["ScopeStackVariable"]:
    if scope_stack.variable is None:
        return set()
    return {scope_stack.variable}


def _scope_vars_from_symbol_stack(symbol_stack: "PartialSymbolStack") -> set["ScopeStackVariable"]:
    vars_from_symbols: set[ScopeStackVariable] = set()
    for symbol in symbol_stack.symbols:
        scopes = symbol.scopes
        if scopes is None or scopes.variable is None:
            continue
        vars_from_symbols.add(scopes.variable)
    return vars_from_symbols


@dataclass(frozen=True, slots=True)
class PartialPath:
    start_node_index: int
    end_node_index: int
    symbol_stack_precondition: "PartialSymbolStack"
    symbol_stack_postcondition: "PartialSymbolStack"
    scope_stack_precondition: "PartialScopeStack"
    scope_stack_postcondition: "PartialScopeStack"
    edges: tuple["PartialPathEdge", ...] = ()

    def largest_symbol_stack_var(self) -> int:
        return max(
            self.symbol_stack_precondition.largest_symbol_stack_var(),
            self.symbol_stack_postcondition.largest_symbol_stack_var(),
        )

    def largest_scope_stack_var(self) -> int:
        return max(
            self.scope_stack_precondition.largest_scope_stack_var(),
            self.scope_stack_postcondition.largest_scope_stack_var(),
            self.symbol_stack_precondition.largest_scope_stack_var(),
            self.symbol_stack_postcondition.largest_scope_stack_var(),
        )

    def ensure_no_overlapping_variables(self, other: "PartialPath") -> "PartialPath":
        symbol_offset = other.largest_symbol_stack_var()
        scope_offset = other.largest_scope_stack_var()
        if symbol_offset == 0 and scope_offset == 0:
            return self
        return PartialPath(
            start_node_index=self.start_node_index,
            end_node_index=self.end_node_index,
            symbol_stack_precondition=self.symbol_stack_precondition.with_offset(
                symbol_offset, scope_offset
            ),
            symbol_stack_postcondition=self.symbol_stack_postcondition.with_offset(
                symbol_offset, scope_offset
            ),
            scope_stack_precondition=self.scope_stack_precondition.with_offset(scope_offset),
            scope_stack_postcondition=self.scope_stack_postcondition.with_offset(scope_offset),
            edges=self.edges,
        )

    def validate_bound_vars(self) -> None:
        pre_symbol_var = self.symbol_stack_precondition.variable
        post_symbol_var = self.symbol_stack_postcondition.variable
        if post_symbol_var is not None and post_symbol_var != pre_symbol_var:
            _raise_unbound_symbol_stack_variable()

        pre_scope_vars = _scope_vars_from_scope_stack(self.scope_stack_precondition)
        pre_scope_vars.update(_scope_vars_from_symbol_stack(self.symbol_stack_precondition))
        post_scope_vars = _scope_vars_from_scope_stack(self.scope_stack_postcondition)
        post_scope_vars.update(_scope_vars_from_symbol_stack(self.symbol_stack_postcondition))
        if not post_scope_vars.issubset(pre_scope_vars):
            _raise_unbound_scope_stack_variable()

    def concatenate(self, view: "StackGraphView", rhs: "PartialPath") -> "PartialPath":
        if self.end_node_index != rhs.start_node_index:
            _raise_incorrect_source_node()
        rhs = rhs.ensure_no_overlapping_variables(self)
        lhs_post = halfopen_closed_partial_postcondition(
            view,
            self.end_node_index,
            self.symbol_stack_postcondition,
            self.scope_stack_postcondition,
        )
        rhs_pre = halfopen_closed_partial_precondition(
            view,
            rhs.start_node_index,
            rhs.symbol_stack_precondition,
            rhs.scope_stack_precondition,
        )
        symbol_bindings = PartialSymbolStackBindings.new()
        scope_bindings = PartialScopeStackBindings.new()
        lhs_post.symbol_stack.unify(rhs_pre.symbol_stack, symbol_bindings, scope_bindings)
        lhs_post.scope_stack.unify(rhs_pre.scope_stack, scope_bindings)
        result = PartialPath(
            start_node_index=self.start_node_index,
            end_node_index=rhs.end_node_index,
            symbol_stack_precondition=self.symbol_stack_precondition.apply_bindings(
                symbol_bindings, scope_bindings
            ),
            symbol_stack_postcondition=rhs.symbol_stack_postcondition.apply_bindings(
                symbol_bindings, scope_bindings
            ),
            scope_stack_precondition=self.scope_stack_precondition.apply_bindings(scope_bindings),
            scope_stack_postcondition=rhs.scope_stack_postcondition.apply_bindings(scope_bindings),
            edges=self.edges + rhs.edges,
        )
        result.validate_bound_vars()
        return result
