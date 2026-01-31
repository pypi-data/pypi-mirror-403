from unittest.mock import (
    patch,
)

import pytest

from blends.models import (
    Graph,
    Language,
    NId,
)
from blends.stack.node_kinds import (
    StackGraphNodeKind,
)
from blends.syntax.builders.parameter import (
    build_parameter_node,
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
def test_parameter_emits_pop_symbol_and_scope_edge(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_parameter_node(
            args=mock_args,
            variable="x",
            variable_type=None,
            value_id=None,
        )

        assert (
            mock_args.syntax_graph.nodes["2"]["stack_graph_kind"]
            == StackGraphNodeKind.POP_SYMBOL.value
        )
        assert mock_args.syntax_graph.nodes["2"]["stack_graph_symbol"] == "x"

        assert mock_args.syntax_graph.has_edge("1", "2")
        edge_data = mock_args.syntax_graph["1"]["2"]
        assert edge_data["precedence"] == 0


@pytest.mark.blends_test_group("stack_unittesting")
def test_parameter_no_stack_graph_emission_when_feature_preview_disabled(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", return_value=False):
        build_parameter_node(
            args=mock_args,
            variable="x",
            variable_type=None,
            value_id=None,
        )

        assert "stack_graph_kind" not in mock_args.syntax_graph.nodes["2"]
        assert "stack_graph_symbol" not in mock_args.syntax_graph.nodes["2"]
        assert not mock_args.syntax_graph.has_edge("1", "2")


@pytest.mark.blends_test_group("stack_unittesting")
def test_parameter_no_scope_edge_when_scope_stack_empty(
    mock_args: SyntaxGraphArgs,
) -> None:
    mock_args.metadata["scope_stack"] = []
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_parameter_node(
            args=mock_args,
            variable="x",
            variable_type=None,
            value_id=None,
        )

        assert (
            mock_args.syntax_graph.nodes["2"]["stack_graph_kind"]
            == StackGraphNodeKind.POP_SYMBOL.value
        )
        assert mock_args.syntax_graph.nodes["2"]["stack_graph_symbol"] == "x"
        assert not mock_args.syntax_graph.has_edge("1", "2")
