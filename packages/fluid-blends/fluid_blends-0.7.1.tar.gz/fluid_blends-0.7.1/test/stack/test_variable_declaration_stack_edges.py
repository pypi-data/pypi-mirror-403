from unittest.mock import (
    patch,
)

import pytest

from blends.models import (
    Graph,
    Language,
    NId,
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
def test_variable_declaration_pop_edge_created(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_variable_declaration_node(
            mock_args,
            variable_name="x",
            variable_type=None,
            value_id=None,
        )

        assert mock_args.syntax_graph.has_edge("1", "2")
        edge_data = mock_args.syntax_graph["1"]["2"]
        assert edge_data["precedence"] == 0
        assert "label_stack" not in edge_data
        assert "symbol" not in edge_data


@pytest.mark.blends_test_group("stack_unittesting")
def test_variable_declaration_pop_edge_with_variable_type(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_variable_declaration_node(
            mock_args,
            variable_name="count",
            variable_type="int",
            value_id=None,
        )

        assert mock_args.syntax_graph.has_edge("1", "2")
        edge_data = mock_args.syntax_graph["1"]["2"]
        assert edge_data["precedence"] == 0
        assert "label_stack" not in edge_data
        assert "symbol" not in edge_data


@pytest.mark.blends_test_group("stack_unittesting")
def test_variable_declaration_no_edge_when_feature_preview_disabled(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", return_value=False):
        build_variable_declaration_node(
            mock_args,
            variable_name="x",
            variable_type=None,
            value_id=None,
        )

        assert not mock_args.syntax_graph.has_edge("1", "2")


@pytest.mark.blends_test_group("stack_unittesting")
def test_variable_declaration_no_edge_when_scope_stack_empty(
    mock_args: SyntaxGraphArgs,
) -> None:
    mock_args.metadata["scope_stack"] = []
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_variable_declaration_node(
            mock_args,
            variable_name="x",
            variable_type=None,
            value_id=None,
        )

        assert not mock_args.syntax_graph.has_edge("1", "2")


@pytest.mark.blends_test_group("stack_unittesting")
def test_variable_declaration_pop_edge_in_method_scope(
    mock_args: SyntaxGraphArgs,
) -> None:
    mock_args.metadata["scope_stack"] = ["1", "7"]
    mock_args.syntax_graph.add_node("7", label_type="MethodDeclaration", name="foo")
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_variable_declaration_node(
            mock_args,
            variable_name="local_var",
            variable_type=None,
            value_id=None,
        )

        assert mock_args.syntax_graph.has_edge("7", "2")
        edge_data = mock_args.syntax_graph["7"]["2"]
        assert edge_data["precedence"] == 0
        assert "label_stack" not in edge_data
        assert "symbol" not in edge_data
