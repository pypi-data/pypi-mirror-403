from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from blends.stack.partial_path.partial_stacks import (
        PartialScopeStack,
        PartialSymbolStack,
    )
    from blends.stack.partial_path.variables import (
        ScopeStackVariable,
        SymbolStackVariable,
    )


@dataclass(frozen=True, slots=True)
class _SymbolUnifyBindings:
    symbol_bindings: "PartialSymbolStackBindings"
    scope_bindings: "PartialScopeStackBindings"


@dataclass(slots=True)
class PartialScopeStackBindings:
    bindings: dict["ScopeStackVariable", "PartialScopeStack"]

    @classmethod
    def new(cls) -> "PartialScopeStackBindings":
        return cls(bindings={})

    def get(self, variable: "ScopeStackVariable") -> "PartialScopeStack | None":
        return self.bindings.get(variable)

    def add(self, variable: "ScopeStackVariable", scopes: "PartialScopeStack") -> None:
        old = self.bindings.get(variable)
        if old is None:
            self.bindings[variable] = scopes
            return
        unified = scopes.unify(old, self)
        self.bindings[variable] = unified


@dataclass(slots=True)
class PartialSymbolStackBindings:
    bindings: dict["SymbolStackVariable", "PartialSymbolStack"]

    @classmethod
    def new(cls) -> "PartialSymbolStackBindings":
        return cls(bindings={})

    def get(self, variable: "SymbolStackVariable") -> "PartialSymbolStack | None":
        return self.bindings.get(variable)

    def add(
        self,
        variable: "SymbolStackVariable",
        symbols: "PartialSymbolStack",
        scope_bindings: "PartialScopeStackBindings",
    ) -> None:
        old = self.bindings.get(variable)
        if old is None:
            self.bindings[variable] = symbols
            return
        unified = symbols.unify(old, self, scope_bindings)
        self.bindings[variable] = unified
