from enum import Enum
from typing import NoReturn


class PartialPathResolutionErrorCode(str, Enum):
    INCORRECT_SOURCE_NODE = "IncorrectSourceNode"
    SCOPE_STACK_UNSATISFIED = "ScopeStackUnsatisfied"
    SYMBOL_STACK_UNSATISFIED = "SymbolStackUnsatisfied"
    INCORRECT_POPPED_SYMBOL = "IncorrectPoppedSymbol"
    EMPTY_SCOPE_STACK = "EmptyScopeStack"
    EMPTY_SYMBOL_STACK = "EmptySymbolStack"
    MISSING_ATTACHED_SCOPE_LIST = "MissingAttachedScopeList"
    UNEXPECTED_ATTACHED_SCOPE_LIST = "UnexpectedAttachedScopeList"
    UNKNOWN_ATTACHED_SCOPE = "UnknownAttachedScope"
    UNBOUND_SYMBOL_STACK_VARIABLE = "UnboundSymbolStackVariable"
    UNBOUND_SCOPE_STACK_VARIABLE = "UnboundScopeStackVariable"


class PartialPathResolutionError(Exception):
    @property
    def code(self) -> "PartialPathResolutionErrorCode":
        first_arg = (
            self.args[0] if self.args else PartialPathResolutionErrorCode.SYMBOL_STACK_UNSATISFIED
        )
        return (
            first_arg
            if isinstance(first_arg, PartialPathResolutionErrorCode)
            else PartialPathResolutionErrorCode.SYMBOL_STACK_UNSATISFIED
        )


def _raise_scope_stack_unsatisfied() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.SCOPE_STACK_UNSATISFIED)


def _raise_symbol_stack_unsatisfied() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.SYMBOL_STACK_UNSATISFIED)


def _raise_incorrect_source_node() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.INCORRECT_SOURCE_NODE)


def _raise_incorrect_popped_symbol() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.INCORRECT_POPPED_SYMBOL)


def _raise_empty_scope_stack() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.EMPTY_SCOPE_STACK)


def _raise_empty_symbol_stack() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.EMPTY_SYMBOL_STACK)


def _raise_missing_attached_scope_list() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.MISSING_ATTACHED_SCOPE_LIST)


def _raise_unexpected_attached_scope_list() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.UNEXPECTED_ATTACHED_SCOPE_LIST)


def _raise_unknown_attached_scope() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.UNKNOWN_ATTACHED_SCOPE)


def _raise_unbound_symbol_stack_variable() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.UNBOUND_SYMBOL_STACK_VARIABLE)


def _raise_unbound_scope_stack_variable() -> NoReturn:
    raise PartialPathResolutionError(PartialPathResolutionErrorCode.UNBOUND_SCOPE_STACK_VARIABLE)
