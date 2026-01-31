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
from blends.syntax.builders.import_global import (
    build_import_global_node,
)
from blends.syntax.builders.import_module import (
    build_import_module_node,
)
from blends.syntax.builders.import_statement import (
    build_import_statement_node,
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
def test_import_global_binds_alias_or_last_segment(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_import_global_node(
            mock_args,
            expression="pkg.mod",
            module_nodes=set(),
            alias="m",
        )

        assert (
            mock_args.syntax_graph.nodes["2"]["stack_graph_kind"]
            == StackGraphNodeKind.POP_SYMBOL.value
        )
        assert mock_args.syntax_graph.nodes["2"]["stack_graph_symbol"] == "m"
        assert mock_args.syntax_graph.has_edge("1", "2")
        edge_data = mock_args.syntax_graph["1"]["2"]
        assert edge_data["precedence"] == 0


@pytest.mark.blends_test_group("stack_unittesting")
def test_import_module_binds_alias_or_last_segment(
    mock_args: SyntaxGraphArgs,
) -> None:
    module_args = SyntaxGraphArgs(
        generic=mock_args.generic,
        path=mock_args.path,
        language=mock_args.language,
        ast_graph=mock_args.ast_graph,
        syntax_graph=mock_args.syntax_graph,
        n_id="3",
        metadata=mock_args.metadata,
    )
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_import_module_node(
            module_args,
            expression="pkg.mod",
            alias=None,
        )

        assert (
            mock_args.syntax_graph.nodes["3"]["stack_graph_kind"]
            == StackGraphNodeKind.POP_SYMBOL.value
        )
        assert mock_args.syntax_graph.nodes["3"]["stack_graph_symbol"] == "mod"
        assert mock_args.syntax_graph.has_edge("1", "3")


@pytest.mark.blends_test_group("stack_unittesting")
def test_import_statement_multiple_marks_each_child_as_definition(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_import_statement_node(
            mock_args,
            {"corrected_n_id": "10", "expression": "a.b", "label_alias": "c"},
            {"corrected_n_id": "11", "expression": "x.y", "label_alias": ""},
        )

        assert mock_args.syntax_graph.has_edge("2", "10")
        assert mock_args.syntax_graph.has_edge("2", "11")

        assert (
            mock_args.syntax_graph.nodes["10"]["stack_graph_kind"]
            == StackGraphNodeKind.POP_SYMBOL.value
        )
        assert mock_args.syntax_graph.nodes["10"]["stack_graph_symbol"] == "c"
        assert mock_args.syntax_graph.has_edge("1", "10")

        assert (
            mock_args.syntax_graph.nodes["11"]["stack_graph_kind"]
            == StackGraphNodeKind.POP_SYMBOL.value
        )
        assert mock_args.syntax_graph.nodes["11"]["stack_graph_symbol"] == "y"
        assert mock_args.syntax_graph.has_edge("1", "11")


@pytest.mark.blends_test_group("stack_unittesting")
def test_import_nodes_do_not_emit_stack_graph_when_feature_preview_disabled(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", return_value=False):
        build_import_global_node(
            mock_args,
            expression="pkg.mod",
            module_nodes=set(),
            alias="m",
        )

        assert "stack_graph_kind" not in mock_args.syntax_graph.nodes["2"]
        assert "stack_graph_symbol" not in mock_args.syntax_graph.nodes["2"]
        assert not mock_args.syntax_graph.has_edge("1", "2")
