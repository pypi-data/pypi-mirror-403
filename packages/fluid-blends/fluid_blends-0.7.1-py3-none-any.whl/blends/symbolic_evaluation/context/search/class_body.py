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


def search(args: SearchArgs) -> Iterator[SearchResult]:
    for c_id in adj_cfg(args.graph, args.n_id):
        if (
            args.graph.nodes[c_id]["label_type"] == "VariableDeclaration"
            and args.graph.nodes[c_id]["variable"] == args.symbol
        ):
            yield True, c_id
            break
