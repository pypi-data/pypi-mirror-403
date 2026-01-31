from collections.abc import (
    Iterator,
)

from blends.models import (
    Graph,
    NId,
)
from blends.symbolic_evaluation.context.search import (
    assignment,
    catch_clause,
    class_body,
    declaration_block,
    file_node,
    for_each,
    for_statement,
    if_statement,
    method_declaration,
    method_invocation,
    try_statement,
    using_statement,
    variable_declaration,
)
from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    Searcher,
    SearchResult,
)
from blends.symbolic_evaluation.models import (
    Path,
)

SEARCHERS: dict[str, Searcher] = {
    "Assignment": assignment.search,
    "CatchClause": catch_clause.search,
    "ClassBody": class_body.search,
    "DeclarationBlock": declaration_block.search,
    "File": file_node.search,
    "ForEachStatement": for_each.search,
    "ForStatement": for_statement.search,
    "If": if_statement.search,
    "MethodDeclaration": method_declaration.search,
    "MethodInvocation": method_invocation.search,
    "UsingStatement": using_statement.search,
    "VariableDeclaration": variable_declaration.search,
    "TryStatement": try_statement.search,
}


def search(graph: Graph, path: Path, symbol: str, *, def_only: bool) -> Iterator[SearchResult]:
    for n_id in path:
        if searcher := SEARCHERS.get(graph.nodes[n_id]["label_type"]):
            yield from searcher(SearchArgs(graph, n_id, symbol, def_only))


def search_until_def(graph: Graph, path: Path, symbol: str) -> Iterator[NId]:
    for is_def, ref_id in search(graph, path, symbol, def_only=False):
        yield ref_id
        if is_def:
            break


def definition_search(graph: Graph, path: Path, symbol: str) -> NId | None:
    for _, ref_id in search(graph, path, symbol, def_only=True):
        return ref_id
    return None
