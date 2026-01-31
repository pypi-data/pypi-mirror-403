from collections.abc import (
    Iterator,
)

from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)


def search(args: SearchArgs) -> Iterator[SearchResult]:
    if (c_id := args.graph.nodes[args.n_id].get("catch_declaration")) and args.graph.nodes[
        c_id
    ].get("variable") == args.symbol:
        yield True, c_id
