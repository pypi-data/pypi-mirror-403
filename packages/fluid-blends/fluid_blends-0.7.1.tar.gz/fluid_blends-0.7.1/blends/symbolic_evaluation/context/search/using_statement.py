from collections.abc import (
    Iterator,
)

from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)


def search(args: SearchArgs) -> Iterator[SearchResult]:
    if (
        var_id := args.graph.nodes[args.n_id].get("declaration_id")
    ) and args.symbol == args.graph.nodes[var_id].get("variable"):
        yield True, args.n_id

    if (
        var_id
        and args.graph.nodes[var_id]["label_type"] == "Assignment"
        and (val_id := args.graph.nodes[var_id]["variable_id"])
        and args.graph.nodes[val_id].get("symbol") == args.symbol
    ):
        yield True, args.n_id
