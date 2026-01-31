from collections.abc import (
    Iterator,
)

from blends.query import (
    adj_ast,
)
from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)


def search(args: SearchArgs) -> Iterator[SearchResult]:
    if args.graph.nodes[args.n_id].get("name") == args.symbol:
        yield True, args.n_id
    else:
        pl_id = args.graph.nodes[args.n_id].get("parameters_id") or args.n_id
        params_ids = adj_ast(args.graph, pl_id, label_type="Parameter")
        for c_id in params_ids:
            if args.symbol == args.graph.nodes[c_id].get("variable"):
                yield True, c_id
                break
