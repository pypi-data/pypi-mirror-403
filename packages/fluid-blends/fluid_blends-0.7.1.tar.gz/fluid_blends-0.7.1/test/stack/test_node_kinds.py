import pytest

from blends.stack.node_kinds import (
    StackGraphNodeKind,
    is_stack_graph_kind,
)


@pytest.mark.blends_test_group("stack_unittesting")
def test_all_node_kinds_defined() -> None:
    expected_kinds = {
        "DropScopesNode",
        "JumpToNode",
        "PopScopedSymbolNode",
        "PopSymbolNode",
        "PushScopedSymbolNode",
        "PushSymbolNode",
        "RootNode",
        "ScopeNode",
    }
    actual_kinds = {kind.value for kind in StackGraphNodeKind}
    assert actual_kinds == expected_kinds


@pytest.mark.blends_test_group("stack_unittesting")
def test_node_kind_string_conversion() -> None:
    assert StackGraphNodeKind.PUSH_SYMBOL.value == "PushSymbolNode"
    assert StackGraphNodeKind.POP_SYMBOL.value == "PopSymbolNode"
    assert StackGraphNodeKind.SCOPE.value == "ScopeNode"
    assert StackGraphNodeKind.ROOT.value == "RootNode"


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_stack_graph_kind_valid_kinds() -> None:
    assert is_stack_graph_kind("PushSymbolNode") is True
    assert is_stack_graph_kind("PopSymbolNode") is True
    assert is_stack_graph_kind("ScopeNode") is True
    assert is_stack_graph_kind("RootNode") is True
    assert is_stack_graph_kind("JumpToNode") is True
    assert is_stack_graph_kind("DropScopesNode") is True
    assert is_stack_graph_kind("PushScopedSymbolNode") is True
    assert is_stack_graph_kind("PopScopedSymbolNode") is True


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_stack_graph_kind_invalid_strings() -> None:
    assert is_stack_graph_kind("InvalidNode") is False
    assert is_stack_graph_kind("push_symbol") is False
    assert is_stack_graph_kind("") is False
    assert is_stack_graph_kind("Scope") is False


@pytest.mark.blends_test_group("stack_unittesting")
def test_is_stack_graph_kind_non_string_types() -> None:
    assert is_stack_graph_kind(123) is False
    assert is_stack_graph_kind(None) is False
    assert is_stack_graph_kind([]) is False
    assert is_stack_graph_kind({}) is False
    assert is_stack_graph_kind(StackGraphNodeKind.PUSH_SYMBOL) is True
