from unittest.mock import (
    patch,
)

import pytest

from blends.models import (
    Graph,
    Language,
    NId,
)
from blends.syntax.builders.symbol_lookup import (
    build_symbol_lookup_node,
)
from blends.syntax.builders.variable_declaration import (
    build_variable_declaration_node,
)
from blends.syntax.models import (
    SyntaxGraphArgs,
    SyntaxMetadata,
)


@pytest.fixture  # type: ignore[misc,attr-defined]
def mock_args() -> SyntaxGraphArgs:  # type: ignore[misc]
    syntax_graph = Graph()
    ast_graph = Graph()
    metadata: SyntaxMetadata = {
        "class_path": [],
        "scope_stack": ["1"],
    }
    syntax_graph.add_node("1", label_type="File")

    def generic(args: SyntaxGraphArgs) -> NId:
        return args.n_id

    return SyntaxGraphArgs(
        generic=generic,
        path="test.py",
        language=Language.PYTHON,
        ast_graph=ast_graph,
        syntax_graph=syntax_graph,
        n_id="2",
        metadata=metadata,
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_symbol_lookup_push_edge_created(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_symbol_lookup_node(mock_args, symbol="x")

        assert mock_args.syntax_graph.has_edge("2", "1")
        edge_data = mock_args.syntax_graph["2"]["1"]
        assert edge_data["precedence"] == 0


@pytest.mark.blends_test_group("stack_unittesting")
def test_symbol_lookup_no_edge_when_feature_preview_disabled(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", return_value=False):
        build_symbol_lookup_node(mock_args, symbol="x")

        assert not mock_args.syntax_graph.has_edge("2", "1")


@pytest.mark.blends_test_group("stack_unittesting")
def test_symbol_lookup_no_edge_when_scope_stack_empty(
    mock_args: SyntaxGraphArgs,
) -> None:
    mock_args.metadata["scope_stack"] = []
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_symbol_lookup_node(mock_args, symbol="x")

        assert not mock_args.syntax_graph.has_edge("2", "1")


@pytest.mark.blends_test_group("stack_unittesting")
def test_symbol_lookup_push_edge_in_method_scope(
    mock_args: SyntaxGraphArgs,
) -> None:
    mock_args.metadata["scope_stack"] = ["1", "7"]
    mock_args.syntax_graph.add_node("7", label_type="MethodDeclaration", name="foo")
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_symbol_lookup_node(mock_args, symbol="local_var")

        assert mock_args.syntax_graph.has_edge("2", "7")
        edge_data = mock_args.syntax_graph["2"]["7"]
        assert edge_data["precedence"] == 0


@pytest.mark.blends_test_group("stack_unittesting")
def test_symbol_lookup_to_variable_declaration_complete_path(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        variable_args = SyntaxGraphArgs(
            generic=mock_args.generic,
            path=mock_args.path,
            language=mock_args.language,
            ast_graph=mock_args.ast_graph,
            syntax_graph=mock_args.syntax_graph,
            n_id="2",
            metadata=mock_args.metadata,
        )
        build_variable_declaration_node(
            variable_args,
            variable_name="x",
            variable_type=None,
            value_id=None,
        )

        lookup_args = SyntaxGraphArgs(
            generic=mock_args.generic,
            path=mock_args.path,
            language=mock_args.language,
            ast_graph=mock_args.ast_graph,
            syntax_graph=mock_args.syntax_graph,
            n_id="3",
            metadata=mock_args.metadata,
        )
        build_symbol_lookup_node(lookup_args, symbol="x")

        assert mock_args.syntax_graph.has_edge("3", "1")
        push_edge_data = mock_args.syntax_graph["3"]["1"]
        assert push_edge_data["precedence"] == 0

        assert mock_args.syntax_graph.has_edge("1", "2")
        pop_edge_data = mock_args.syntax_graph["1"]["2"]
        assert pop_edge_data["precedence"] == 0
