from collections.abc import (
    Iterator,
)

from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)


def search(args: SearchArgs) -> Iterator[SearchResult]:
    if args.symbol in args.graph.nodes[args.n_id].get("variable", "").split(","):
        yield True, args.n_id
