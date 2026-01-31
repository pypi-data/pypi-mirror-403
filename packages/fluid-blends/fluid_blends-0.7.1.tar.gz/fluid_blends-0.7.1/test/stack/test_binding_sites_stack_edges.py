from unittest.mock import (
    patch,
)

import pytest

from blends.models import (
    Graph,
    Language,
    NId,
)
from blends.stack.attributes import (
    STACK_GRAPH_KIND,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.node_kinds import (
    StackGraphNodeKind,
)
from blends.syntax.builders.assignment import (
    build_assignment_node,
)
from blends.syntax.builders.for_each_statement import (
    build_for_each_statement_node,
)
from blends.syntax.builders.for_statement import (
    build_for_statement_node,
)
from blends.syntax.models import (
    SyntaxGraphArgs,
    SyntaxMetadata,
)


def _make_args(
    *, syntax_graph: Graph, ast_graph: Graph, n_id: NId, metadata: SyntaxMetadata
) -> SyntaxGraphArgs:
    def generic(args: SyntaxGraphArgs) -> NId:
        return args.n_id

    return SyntaxGraphArgs(
        generic=generic,
        path="test.py",
        language=Language.PYTHON,
        ast_graph=ast_graph,
        syntax_graph=syntax_graph,
        n_id=n_id,
        metadata=metadata,
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_assignment_emits_pop_symbol_and_scope_edge_for_identifier_target() -> None:
    syntax_graph = Graph()
    ast_graph = Graph()
    metadata: SyntaxMetadata = {"class_path": [], "scope_stack": ["1"]}
    syntax_graph.add_node("1", label_type="File")

    ast_graph.add_node("10", label_type="identifier", label_text="x")
    ast_graph.add_node("11", label_type="integer", label_text="1")

    args = _make_args(syntax_graph=syntax_graph, ast_graph=ast_graph, n_id="2", metadata=metadata)
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_assignment_node(args, var_id="10", val_id="11", operator=None)

    assert syntax_graph.nodes["2"][STACK_GRAPH_KIND] == StackGraphNodeKind.POP_SYMBOL.value
    assert syntax_graph.nodes["2"][STACK_GRAPH_SYMBOL] == "x"
    assert syntax_graph.has_edge("1", "2")


@pytest.mark.blends_test_group("stack_unittesting")
def test_for_each_emits_pop_symbol_and_scope_edge_for_identifier_target() -> None:
    syntax_graph = Graph()
    ast_graph = Graph()
    metadata: SyntaxMetadata = {"class_path": [], "scope_stack": ["1"]}
    syntax_graph.add_node("1", label_type="File")

    ast_graph.add_node("10", label_type="identifier", label_text="x")
    ast_graph.add_node("11", label_type="identifier", label_text="xs")

    args = _make_args(syntax_graph=syntax_graph, ast_graph=ast_graph, n_id="2", metadata=metadata)
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_for_each_statement_node(args, var_node="10", iterable_item="11", block_id=None)

    assert syntax_graph.nodes["2"][STACK_GRAPH_KIND] == StackGraphNodeKind.POP_SYMBOL.value
    assert syntax_graph.nodes["2"][STACK_GRAPH_SYMBOL] == "x"
    assert syntax_graph.has_edge("1", "2")


@pytest.mark.blends_test_group("stack_unittesting")
def test_for_statement_emits_pop_symbol_and_scope_edge_for_identifier_initializer() -> None:
    syntax_graph = Graph()
    ast_graph = Graph()
    metadata: SyntaxMetadata = {"class_path": [], "scope_stack": ["1"]}
    syntax_graph.add_node("1", label_type="File")

    ast_graph.add_node("10", label_type="identifier", label_text="x")
    ast_graph.add_node("11", label_type="identifier", label_text="xs")
    ast_graph.add_node("12", label_type="block", label_text="")

    args = _make_args(syntax_graph=syntax_graph, ast_graph=ast_graph, n_id="2", metadata=metadata)
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_for_statement_node(
            args, initializer_node="10", condition_node="11", update_node=None, body_node="12"
        )

    assert syntax_graph.nodes["2"][STACK_GRAPH_KIND] == StackGraphNodeKind.POP_SYMBOL.value
    assert syntax_graph.nodes["2"][STACK_GRAPH_SYMBOL] == "x"
    assert syntax_graph.has_edge("1", "2")


@pytest.mark.blends_test_group("stack_unittesting")
def test_binding_sites_do_not_emit_stack_graph_when_feature_preview_disabled() -> None:
    syntax_graph = Graph()
    ast_graph = Graph()
    metadata: SyntaxMetadata = {"class_path": [], "scope_stack": ["1"]}
    syntax_graph.add_node("1", label_type="File")

    ast_graph.add_node("10", label_type="identifier", label_text="x")
    ast_graph.add_node("11", label_type="identifier", label_text="xs")
    ast_graph.add_node("12", label_type="block", label_text="")

    with patch("blends.ctx.ctx.has_feature_flag", return_value=False):
        build_assignment_node(
            _make_args(syntax_graph=syntax_graph, ast_graph=ast_graph, n_id="2", metadata=metadata),
            var_id="10",
            val_id="11",
            operator=None,
        )
        build_for_each_statement_node(
            _make_args(syntax_graph=syntax_graph, ast_graph=ast_graph, n_id="3", metadata=metadata),
            var_node="10",
            iterable_item="11",
            block_id=None,
        )
        build_for_statement_node(
            _make_args(syntax_graph=syntax_graph, ast_graph=ast_graph, n_id="4", metadata=metadata),
            initializer_node="10",
            condition_node="11",
            update_node=None,
            body_node="12",
        )

    assert STACK_GRAPH_KIND not in syntax_graph.nodes["2"]
    assert STACK_GRAPH_KIND not in syntax_graph.nodes["3"]
    assert STACK_GRAPH_KIND not in syntax_graph.nodes["4"]
    assert not syntax_graph.has_edge("1", "2")
    assert not syntax_graph.has_edge("1", "3")
    assert not syntax_graph.has_edge("1", "4")
