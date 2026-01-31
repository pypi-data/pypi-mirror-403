from pathlib import Path

from blends.ast.build_graph import get_ast_graph_from_content, get_ast_graph_from_path
from blends.content.content import get_content_by_path, get_language_by_path
from blends.models import GraphPair
from blends.syntax.build_graph import get_syntax_graph, get_syntax_graph_from_path
from blends.tree.parse import get_tree


def get_graphs_from_path(
    path: Path, *, with_cfg: bool = True, with_metadata: bool = False
) -> GraphPair:
    content = get_content_by_path(path)
    if content is None:
        return GraphPair(ast_graph=None, syntax_graph=None)

    ast_graph = get_ast_graph_from_content(content)
    if ast_graph is None:
        return GraphPair(ast_graph=None, syntax_graph=None)

    syntax_graph = get_syntax_graph(
        ast_graph, content, with_cfg=with_cfg, with_metadata=with_metadata
    )
    if syntax_graph is None:
        return GraphPair(ast_graph=ast_graph, syntax_graph=None)

    return GraphPair(ast_graph=ast_graph, syntax_graph=syntax_graph)


__all__ = [
    "get_ast_graph_from_content",
    "get_ast_graph_from_path",
    "get_content_by_path",
    "get_graphs_from_path",
    "get_language_by_path",
    "get_syntax_graph",
    "get_syntax_graph_from_path",
    "get_tree",
]
