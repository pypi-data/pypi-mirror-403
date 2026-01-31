from unittest.mock import (
    patch,
)

import pytest

from blends.models import (
    Graph,
    Language,
    NId,
)
from blends.syntax.builders.class_decl import (
    build_class_node,
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
def test_class_adds_edge_to_parent_scope(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_class_node(
            mock_args,
            name="MyClass",
            block_id=None,
            attrl_ids=None,
            inherited_class=None,
            modifiers_id=None,
        )

        assert mock_args.syntax_graph.has_edge("1", "2__sg_def")
        def_edge_data = mock_args.syntax_graph["1"]["2__sg_def"]
        assert def_edge_data["precedence"] == 0

        assert mock_args.syntax_graph.has_edge("2__sg_def", "2")
        link_edge_data = mock_args.syntax_graph["2__sg_def"]["2"]
        assert link_edge_data["precedence"] == 0

        assert mock_args.syntax_graph.has_edge("2", "1")
        assert not mock_args.syntax_graph.has_edge("1", "2")
        edge_data = mock_args.syntax_graph["2"]["1"]
        assert edge_data["precedence"] == 0


@pytest.mark.blends_test_group("stack_unittesting")
def test_class_no_edge_when_flag_false(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", return_value=False):
        build_class_node(
            mock_args,
            name="MyClass",
            block_id=None,
            attrl_ids=None,
            inherited_class=None,
            modifiers_id=None,
        )

        assert not mock_args.syntax_graph.has_edge("1", "2__sg_def")
        assert not mock_args.syntax_graph.has_edge("2__sg_def", "2")
        assert not mock_args.syntax_graph.has_edge("1", "2")
        assert not mock_args.syntax_graph.has_edge("2", "1")


@pytest.mark.blends_test_group("stack_unittesting")
def test_class_not_edge_when_scope_stack_empty(
    mock_args: SyntaxGraphArgs,
) -> None:
    mock_args.metadata["scope_stack"] = []
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_class_node(
            mock_args,
            name="MyClass",
            block_id=None,
            attrl_ids=None,
            inherited_class=None,
            modifiers_id=None,
        )

        assert not mock_args.syntax_graph.has_edge("1", "2__sg_def")
        assert not mock_args.syntax_graph.has_edge("2__sg_def", "2")
        assert "2__sg_def" not in mock_args.syntax_graph.nodes
        assert not mock_args.syntax_graph.has_edge("1", "2")
        assert not mock_args.syntax_graph.has_edge("2", "1")


@pytest.mark.blends_test_group("stack_unittesting")
def test_build_class_node_preserves_scope_stack(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        initial_stack = mock_args.metadata["scope_stack"].copy()
        build_class_node(
            mock_args,
            name="MyClass",
            block_id=None,
            attrl_ids=None,
            inherited_class=None,
            modifiers_id=None,
        )

        assert mock_args.metadata["scope_stack"] == initial_stack
        assert mock_args.metadata["scope_stack"] == ["1"]
        assert mock_args.syntax_graph.has_edge("2", "1")


@pytest.mark.blends_test_group("stack_unittesting")
def test_class_scope_connects_to_field_definition(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        build_class_node(
            mock_args,
            name="MyClass",
            block_id=None,
            attrl_ids=None,
            inherited_class=None,
            modifiers_id=None,
        )

        mock_args.metadata["scope_stack"].append("2")

        field_args = SyntaxGraphArgs(
            generic=mock_args.generic,
            path=mock_args.path,
            language=mock_args.language,
            ast_graph=mock_args.ast_graph,
            syntax_graph=mock_args.syntax_graph,
            n_id="3",
            metadata=mock_args.metadata,
        )
        build_variable_declaration_node(
            field_args,
            variable_name="class_var",
            variable_type=None,
            value_id=None,
        )

        assert mock_args.syntax_graph.has_edge("2", "3")
        edge_data = mock_args.syntax_graph["2"]["3"]
        assert edge_data["precedence"] == 0

        assert not mock_args.syntax_graph.has_edge("1", "3")


@pytest.mark.blends_test_group("stack_unittesting")
def test_reference_in_class_can_reach_parent_scope_definition(
    mock_args: SyntaxGraphArgs,
) -> None:
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        parent_variable_args = SyntaxGraphArgs(
            generic=mock_args.generic,
            path=mock_args.path,
            language=mock_args.language,
            ast_graph=mock_args.ast_graph,
            syntax_graph=mock_args.syntax_graph,
            n_id="3",
            metadata=mock_args.metadata,
        )
        build_variable_declaration_node(
            parent_variable_args,
            variable_name="module_var",
            variable_type=None,
            value_id=None,
        )

        class_args = SyntaxGraphArgs(
            generic=mock_args.generic,
            path=mock_args.path,
            language=mock_args.language,
            ast_graph=mock_args.ast_graph,
            syntax_graph=mock_args.syntax_graph,
            n_id="4",
            metadata=mock_args.metadata,
        )
        build_class_node(
            class_args,
            name="MyClass",
            block_id=None,
            attrl_ids=None,
            inherited_class=None,
            modifiers_id=None,
        )

        mock_args.metadata["scope_stack"].append("4")

        lookup_args = SyntaxGraphArgs(
            generic=mock_args.generic,
            path=mock_args.path,
            language=mock_args.language,
            ast_graph=mock_args.ast_graph,
            syntax_graph=mock_args.syntax_graph,
            n_id="5",
            metadata=mock_args.metadata,
        )
        build_symbol_lookup_node(lookup_args, symbol="module_var")

        assert mock_args.syntax_graph.has_edge("5", "4")
        push_edge_data = mock_args.syntax_graph["5"]["4"]
        assert push_edge_data["precedence"] == 0

        assert mock_args.syntax_graph.has_edge("4", "1")
        lookup_edge_data = mock_args.syntax_graph["4"]["1"]
        assert lookup_edge_data["precedence"] == 0

        assert mock_args.syntax_graph.has_edge("1", "3")
        pop_edge_data = mock_args.syntax_graph["1"]["3"]
        assert pop_edge_data["precedence"] == 0
