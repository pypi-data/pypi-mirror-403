from collections.abc import (
    Iterator,
)

from blends.query import (
    adj_cfg,
)
from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)

VAR_MAPPINGS = {
    "VariableDeclaration": "variable",
    "MethodDeclaration": "name",
    "Import": "expression",
    "ModuleImport": "expression",
}


def search(args: SearchArgs) -> Iterator[SearchResult]:
    for c_id in adj_cfg(args.graph, args.n_id):
        n_attrs = args.graph.nodes[c_id]
        if n_attrs["label_type"] in VAR_MAPPINGS and (
            n_attrs.get(VAR_MAPPINGS[n_attrs["label_type"]]) == args.symbol
            or n_attrs.get("label_alias") == args.symbol
        ):
            yield True, c_id
            break
