from unittest.mock import (
    patch,
)

import pytest

from blends.models import (
    Graph,
    Language,
    NId,
)
from blends.stack.node_helpers import (
    scope_node_attributes,
)
from blends.stack.node_kinds import (
    StackGraphNodeKind,
)
from blends.stack.view import (
    StackGraphView,
)
from blends.syntax.builders.class_decl import (
    build_class_node,
)
from blends.syntax.builders.method_declaration import (
    build_method_declaration_node,
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


def _make_args(*, syntax_graph: Graph, n_id: NId, metadata: SyntaxMetadata) -> SyntaxGraphArgs:
    ast_graph = Graph()

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
def test_stack_graph_view_extracts_reference_to_definition_edges() -> None:
    syntax_graph = Graph()
    metadata: SyntaxMetadata = {"class_path": [], "scope_stack": ["1"]}
    syntax_graph.add_node("1", label_type="File")
    syntax_graph.update_node("1", scope_node_attributes(is_exported=True))

    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        def_args = _make_args(syntax_graph=syntax_graph, n_id="2", metadata=metadata)
        build_variable_declaration_node(
            def_args,
            variable_name="x",
            variable_type=None,
            value_id=None,
        )

        ref_args = _make_args(syntax_graph=syntax_graph, n_id="3", metadata=metadata)
        build_symbol_lookup_node(ref_args, symbol="x")

    view = StackGraphView.from_syntax_graph(syntax_graph, path="test.py")
    file_index = view.nid_to_index["1"]
    def_index = view.nid_to_index["2"]
    ref_index = view.nid_to_index["3"]

    assert view.node_kind[file_index] == StackGraphNodeKind.SCOPE.value
    assert view.node_kind[def_index] == StackGraphNodeKind.POP_SYMBOL.value
    assert view.node_kind[ref_index] == StackGraphNodeKind.PUSH_SYMBOL.value

    assert (file_index, 0) in view.outgoing[ref_index]
    assert (def_index, 0) in view.outgoing[file_index]


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_extracts_nested_scope_edges() -> None:
    syntax_graph = Graph()
    metadata: SyntaxMetadata = {"class_path": [], "scope_stack": ["1"]}
    syntax_graph.add_node("1", label_type="File")
    syntax_graph.update_node("1", scope_node_attributes(is_exported=True))

    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        class_args = _make_args(syntax_graph=syntax_graph, n_id="10", metadata=metadata)
        build_class_node(
            class_args,
            name="MyClass",
            block_id=None,
            attrl_ids=None,
            inherited_class=None,
            modifiers_id=None,
        )

        method_metadata: SyntaxMetadata = {"class_path": [], "scope_stack": ["1", "10"]}
        method_args = _make_args(syntax_graph=syntax_graph, n_id="20", metadata=method_metadata)
        build_method_declaration_node(
            method_args,
            name="foo",
            block_id=None,
            children={},
        )

    view = StackGraphView.from_syntax_graph(syntax_graph, path="test.py")
    file_index = view.nid_to_index["1"]
    class_index = view.nid_to_index["10"]
    method_index = view.nid_to_index["20"]

    assert view.node_kind[file_index] == StackGraphNodeKind.SCOPE.value
    assert view.node_kind[class_index] == StackGraphNodeKind.SCOPE.value
    assert view.node_kind[method_index] == StackGraphNodeKind.SCOPE.value

    assert (file_index, 0) in view.outgoing[class_index]
    assert (class_index, 0) in view.outgoing[method_index]


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_marks_exported_scopes() -> None:
    syntax_graph = Graph()
    syntax_graph.add_node("1", label_type="File")
    syntax_graph.update_node("1", scope_node_attributes(is_exported=True))
    syntax_graph.add_node("2", label_type="Class")
    syntax_graph.update_node("2", scope_node_attributes(is_exported=False))

    view = StackGraphView.from_syntax_graph(syntax_graph, path="test.py")
    file_index = view.nid_to_index["1"]
    class_index = view.nid_to_index["2"]

    assert file_index in view.exported_scopes
    assert class_index not in view.exported_scopes


@pytest.mark.blends_test_group("stack_unittesting")
def test_stack_graph_view_preserves_edge_precedence_values() -> None:
    syntax_graph = Graph()
    syntax_graph.add_node("1", label_type="File")
    syntax_graph.update_node("1", scope_node_attributes(is_exported=True))

    metadata: SyntaxMetadata = {"class_path": [], "scope_stack": ["1"]}
    with patch("blends.ctx.ctx.has_feature_flag", side_effect=lambda flag: flag == "StackGraph"):
        def_args_a = _make_args(syntax_graph=syntax_graph, n_id="2", metadata=metadata)
        build_variable_declaration_node(
            def_args_a,
            variable_name="a",
            variable_type=None,
            value_id=None,
        )
        def_args_b = _make_args(syntax_graph=syntax_graph, n_id="3", metadata=metadata)
        build_variable_declaration_node(
            def_args_b,
            variable_name="b",
            variable_type=None,
            value_id=None,
        )

    syntax_graph.add_edge("1", "2", precedence=10)
    syntax_graph.add_edge("1", "3", precedence=1)

    view = StackGraphView.from_syntax_graph(syntax_graph, path="test.py")
    file_index = view.nid_to_index["1"]
    def_index_a = view.nid_to_index["2"]
    def_index_b = view.nid_to_index["3"]

    outgoing = set(view.outgoing[file_index])
    assert (def_index_a, 10) in outgoing
    assert (def_index_b, 1) in outgoing
