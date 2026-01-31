from dataclasses import dataclass
from typing import TYPE_CHECKING

from blends.stack.partial_path.bindings import _SymbolUnifyBindings
from blends.stack.partial_path.errors import (
    _raise_scope_stack_unsatisfied,
    _raise_symbol_stack_unsatisfied,
)

if TYPE_CHECKING:
    from blends.stack.partial_path.bindings import (
        PartialScopeStackBindings,
        PartialSymbolStackBindings,
    )
    from blends.stack.partial_path.variables import (
        ScopeStackVariable,
        SymbolStackVariable,
    )


def _common_prefix_len_scopes(lhs: tuple[int, ...], rhs: tuple[int, ...]) -> int:
    prefix_len = 0
    for lhs_scope, rhs_scope in zip(lhs, rhs, strict=False):
        if lhs_scope != rhs_scope:
            _raise_scope_stack_unsatisfied()
        prefix_len += 1
    return prefix_len


def _unify_scope_suffix_empty(
    lhs: "PartialScopeStack",
    rhs: "PartialScopeStack",
    bindings: "PartialScopeStackBindings",
) -> "PartialScopeStack":
    lhs_var = lhs.variable
    rhs_var = rhs.variable
    if lhs_var is None and rhs_var is None:
        return lhs
    if lhs_var is None and rhs_var is not None:
        bindings.add(rhs_var, PartialScopeStack.empty())
        return rhs
    if lhs_var is not None and rhs_var is None:
        bindings.add(lhs_var, PartialScopeStack.empty())
        return lhs
    if lhs_var is None or rhs_var is None:
        _raise_scope_stack_unsatisfied()
    if lhs_var == rhs_var:
        _raise_scope_stack_unsatisfied()
    bindings.add(rhs_var, PartialScopeStack.from_variable(lhs_var))
    return lhs


def _unify_scope_rhs_is_prefix_of_lhs(
    lhs: "PartialScopeStack",
    rhs: "PartialScopeStack",
    lhs_suffix_scopes: tuple[int, ...],
    bindings: "PartialScopeStackBindings",
) -> "PartialScopeStack":
    rhs_var = rhs.variable
    if rhs_var is None:
        _raise_scope_stack_unsatisfied()
    if lhs.variable is not None and lhs.variable == rhs_var:
        _raise_scope_stack_unsatisfied()
    bindings.add(rhs_var, PartialScopeStack(scopes=lhs_suffix_scopes, variable=lhs.variable))
    return lhs


def _unify_scope_lhs_is_prefix_of_rhs(
    lhs: "PartialScopeStack",
    rhs: "PartialScopeStack",
    rhs_suffix_scopes: tuple[int, ...],
    bindings: "PartialScopeStackBindings",
) -> "PartialScopeStack":
    lhs_var = lhs.variable
    if lhs_var is None:
        _raise_scope_stack_unsatisfied()
    if rhs.variable is not None and rhs.variable == lhs_var:
        _raise_scope_stack_unsatisfied()
    bindings.add(lhs_var, PartialScopeStack(scopes=rhs_suffix_scopes, variable=rhs.variable))
    return rhs


def _unify_symbol_suffix_empty(
    prefix: tuple["PartialScopedSymbol", ...],
    lhs: "PartialSymbolStack",
    rhs: "PartialSymbolStack",
    symbol_bindings: "PartialSymbolStackBindings",
    scope_bindings: "PartialScopeStackBindings",
) -> "PartialSymbolStack":
    lhs_var = lhs.variable
    rhs_var = rhs.variable
    if lhs_var is None and rhs_var is None:
        return PartialSymbolStack(symbols=prefix, variable=None)
    if lhs_var is None and rhs_var is not None:
        symbol_bindings.add(rhs_var, PartialSymbolStack.empty(), scope_bindings)
        return PartialSymbolStack(symbols=prefix, variable=rhs_var)
    if lhs_var is not None and rhs_var is None:
        symbol_bindings.add(lhs_var, PartialSymbolStack.empty(), scope_bindings)
        return PartialSymbolStack(symbols=prefix, variable=lhs_var)
    if lhs_var is None or rhs_var is None:
        _raise_symbol_stack_unsatisfied()
    if lhs_var == rhs_var:
        _raise_symbol_stack_unsatisfied()
    symbol_bindings.add(rhs_var, PartialSymbolStack.from_variable(lhs_var), scope_bindings)
    return PartialSymbolStack(symbols=prefix, variable=lhs_var)


def _unify_symbol_rhs_is_prefix_of_lhs(
    prefix: tuple["PartialScopedSymbol", ...],
    lhs: "PartialSymbolStack",
    rhs: "PartialSymbolStack",
    lhs_suffix_symbols: tuple["PartialScopedSymbol", ...],
    bindings: _SymbolUnifyBindings,
) -> "PartialSymbolStack":
    rhs_var = rhs.variable
    if rhs_var is None:
        _raise_symbol_stack_unsatisfied()
    if lhs.variable is not None and lhs.variable == rhs_var:
        _raise_symbol_stack_unsatisfied()
    bindings.symbol_bindings.add(
        rhs_var,
        PartialSymbolStack(symbols=lhs_suffix_symbols, variable=lhs.variable),
        bindings.scope_bindings,
    )
    return PartialSymbolStack(symbols=prefix + lhs_suffix_symbols, variable=lhs.variable)


def _unify_symbol_lhs_is_prefix_of_rhs(
    prefix: tuple["PartialScopedSymbol", ...],
    lhs: "PartialSymbolStack",
    rhs: "PartialSymbolStack",
    rhs_suffix_symbols: tuple["PartialScopedSymbol", ...],
    bindings: _SymbolUnifyBindings,
) -> "PartialSymbolStack":
    lhs_var = lhs.variable
    if lhs_var is None:
        _raise_symbol_stack_unsatisfied()
    if rhs.variable is not None and rhs.variable == lhs_var:
        _raise_symbol_stack_unsatisfied()
    bindings.symbol_bindings.add(
        lhs_var,
        PartialSymbolStack(symbols=rhs_suffix_symbols, variable=rhs.variable),
        bindings.scope_bindings,
    )
    return PartialSymbolStack(symbols=prefix + rhs_suffix_symbols, variable=rhs.variable)


@dataclass(frozen=True, slots=True)
class PartialScopeStack:
    scopes: tuple[int, ...]
    variable: "ScopeStackVariable | None"

    @classmethod
    def empty(cls) -> "PartialScopeStack":
        return cls(scopes=(), variable=None)

    @classmethod
    def from_variable(cls, variable: "ScopeStackVariable") -> "PartialScopeStack":
        return cls(scopes=(), variable=variable)

    def has_variable(self) -> bool:
        return self.variable is not None

    def can_match_empty(self) -> bool:
        return len(self.scopes) == 0

    def can_only_match_empty(self) -> bool:
        return len(self.scopes) == 0 and self.variable is None

    def contains_scopes(self) -> bool:
        return len(self.scopes) > 0

    def with_offset(self, scope_offset: int) -> "PartialScopeStack":
        if self.variable is None or scope_offset == 0:
            return self
        return PartialScopeStack(
            scopes=self.scopes,
            variable=self.variable.with_offset(scope_offset),
        )

    def largest_scope_stack_var(self) -> int:
        if self.variable is None:
            return 0
        return self.variable.as_int()

    def apply_bindings(self, bindings: "PartialScopeStackBindings") -> "PartialScopeStack":
        if self.variable is None:
            return self
        bound = bindings.get(self.variable)
        if bound is None:
            return self
        return PartialScopeStack(
            scopes=self.scopes + bound.scopes,
            variable=bound.variable,
        )

    def unify(
        self, rhs: "PartialScopeStack", bindings: "PartialScopeStackBindings"
    ) -> "PartialScopeStack":
        prefix_len = _common_prefix_len_scopes(self.scopes, rhs.scopes)
        lhs_suffix_scopes = self.scopes[prefix_len:]
        rhs_suffix_scopes = rhs.scopes[prefix_len:]

        if len(lhs_suffix_scopes) == 0 and len(rhs_suffix_scopes) == 0:
            return _unify_scope_suffix_empty(self, rhs, bindings)
        if len(rhs_suffix_scopes) == 0:
            return _unify_scope_rhs_is_prefix_of_lhs(self, rhs, lhs_suffix_scopes, bindings)
        if len(lhs_suffix_scopes) == 0:
            return _unify_scope_lhs_is_prefix_of_rhs(self, rhs, rhs_suffix_scopes, bindings)
        _raise_scope_stack_unsatisfied()
        raise AssertionError  # unreachable


@dataclass(frozen=True, slots=True)
class PartialScopedSymbol:
    symbol_id: int
    scopes: "PartialScopeStack | None"

    def unify(
        self, rhs: "PartialScopedSymbol", bindings: "PartialScopeStackBindings"
    ) -> "PartialScopedSymbol":
        if self.symbol_id != rhs.symbol_id:
            _raise_symbol_stack_unsatisfied()
        if (self.scopes is None) != (rhs.scopes is None):
            _raise_symbol_stack_unsatisfied()
        if self.scopes is None or rhs.scopes is None:
            return self
        unified_scopes = self.scopes.unify(rhs.scopes, bindings)
        return PartialScopedSymbol(symbol_id=self.symbol_id, scopes=unified_scopes)

    def with_offset(self, scope_offset: int) -> "PartialScopedSymbol":
        if self.scopes is None:
            return self
        return PartialScopedSymbol(
            symbol_id=self.symbol_id,
            scopes=self.scopes.with_offset(scope_offset),
        )

    def largest_scope_stack_var(self) -> int:
        if self.scopes is None:
            return 0
        return self.scopes.largest_scope_stack_var()

    def apply_bindings(self, bindings: "PartialScopeStackBindings") -> "PartialScopedSymbol":
        if self.scopes is None:
            return self
        return PartialScopedSymbol(
            symbol_id=self.symbol_id,
            scopes=self.scopes.apply_bindings(bindings),
        )


@dataclass(frozen=True, slots=True)
class PartialSymbolStack:
    symbols: tuple["PartialScopedSymbol", ...]
    variable: "SymbolStackVariable | None"

    @classmethod
    def empty(cls) -> "PartialSymbolStack":
        return cls(symbols=(), variable=None)

    @classmethod
    def from_variable(cls, variable: "SymbolStackVariable") -> "PartialSymbolStack":
        return cls(symbols=(), variable=variable)

    def has_variable(self) -> bool:
        return self.variable is not None

    def can_match_empty(self) -> bool:
        return len(self.symbols) == 0

    def can_only_match_empty(self) -> bool:
        return len(self.symbols) == 0 and self.variable is None

    def contains_symbols(self) -> bool:
        return len(self.symbols) > 0

    def with_offset(self, symbol_offset: int, scope_offset: int) -> "PartialSymbolStack":
        if symbol_offset == 0 and scope_offset == 0:
            return self
        if self.variable is None:
            variable = None
        elif symbol_offset == 0:
            variable = self.variable
        else:
            variable = self.variable.with_offset(symbol_offset)
        symbols = tuple(symbol.with_offset(scope_offset) for symbol in self.symbols)
        return PartialSymbolStack(symbols=symbols, variable=variable)

    def largest_symbol_stack_var(self) -> int:
        if self.variable is None:
            return 0
        return self.variable.as_int()

    def largest_scope_stack_var(self) -> int:
        max_var = 0
        for symbol in self.symbols:
            max_var = max(max_var, symbol.largest_scope_stack_var())
        return max_var

    def apply_bindings(
        self,
        symbol_bindings: "PartialSymbolStackBindings",
        scope_bindings: "PartialScopeStackBindings",
    ) -> "PartialSymbolStack":
        bound_stack = None
        if self.variable is not None:
            bound_stack = symbol_bindings.get(self.variable)
        base_symbols: tuple[PartialScopedSymbol, ...] = ()
        base_variable = self.variable
        if bound_stack is not None:
            base_symbols = tuple(
                symbol.apply_bindings(scope_bindings) for symbol in bound_stack.symbols
            )
            base_variable = bound_stack.variable
        prefix_symbols = tuple(symbol.apply_bindings(scope_bindings) for symbol in self.symbols)
        return PartialSymbolStack(
            symbols=prefix_symbols + base_symbols,
            variable=base_variable,
        )

    def unify(
        self,
        rhs: "PartialSymbolStack",
        symbol_bindings: "PartialSymbolStackBindings",
        scope_bindings: "PartialScopeStackBindings",
    ) -> "PartialSymbolStack":
        common_len = min(len(self.symbols), len(rhs.symbols))
        prefix = tuple(
            self.symbols[index].unify(rhs.symbols[index], scope_bindings)
            for index in range(common_len)
        )

        lhs_suffix_symbols = self.symbols[common_len:]
        rhs_suffix_symbols = rhs.symbols[common_len:]

        if len(lhs_suffix_symbols) == 0 and len(rhs_suffix_symbols) == 0:
            return _unify_symbol_suffix_empty(prefix, self, rhs, symbol_bindings, scope_bindings)
        if len(rhs_suffix_symbols) == 0:
            bindings = _SymbolUnifyBindings(
                symbol_bindings=symbol_bindings,
                scope_bindings=scope_bindings,
            )
            return _unify_symbol_rhs_is_prefix_of_lhs(
                prefix, self, rhs, lhs_suffix_symbols, bindings
            )
        if len(lhs_suffix_symbols) == 0:
            bindings = _SymbolUnifyBindings(
                symbol_bindings=symbol_bindings,
                scope_bindings=scope_bindings,
            )
            return _unify_symbol_lhs_is_prefix_of_rhs(
                prefix, self, rhs, rhs_suffix_symbols, bindings
            )
        _raise_symbol_stack_unsatisfied()
        raise AssertionError  # unreachable
