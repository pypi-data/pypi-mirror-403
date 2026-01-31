from collections.abc import (
    Iterator,
)

from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)


def search(args: SearchArgs) -> Iterator[SearchResult]:
    variable_id = args.graph.nodes[args.n_id]["variable_id"]
    if args.symbol == args.graph.nodes[variable_id].get("symbol"):
        yield False, args.n_id
