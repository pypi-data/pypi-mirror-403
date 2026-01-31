from dataclasses import dataclass
from typing import Optional

_OFFSET_MUST_BE_NONNEGATIVE = "offset must be nonnegative"


@dataclass(frozen=True, slots=True)
class SymbolStackVariable:
    var_id: int

    @classmethod
    def new(cls, var_id: int) -> Optional["SymbolStackVariable"]:
        if var_id < 1:
            return None
        return cls(var_id=var_id)

    @classmethod
    def initial(cls) -> "SymbolStackVariable":
        return cls(var_id=1)

    def with_offset(self, offset: int) -> "SymbolStackVariable":
        if offset < 0:
            raise ValueError(_OFFSET_MUST_BE_NONNEGATIVE)
        return SymbolStackVariable(var_id=self.var_id + offset)

    def as_int(self) -> int:
        return self.var_id


@dataclass(frozen=True, slots=True)
class ScopeStackVariable:
    var_id: int

    @classmethod
    def new(cls, var_id: int) -> Optional["ScopeStackVariable"]:
        if var_id < 1:
            return None
        return cls(var_id=var_id)

    @classmethod
    def initial(cls) -> "ScopeStackVariable":
        return cls(var_id=1)

    def with_offset(self, offset: int) -> "ScopeStackVariable":
        if offset < 0:
            raise ValueError(_OFFSET_MUST_BE_NONNEGATIVE)
        return ScopeStackVariable(var_id=self.var_id + offset)

    def as_int(self) -> int:
        return self.var_id
