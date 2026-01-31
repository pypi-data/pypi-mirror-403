from collections.abc import (
    Iterator,
)

from blends.query import adj_ast
from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)


def search(args: SearchArgs) -> Iterator[SearchResult]:
    assign_id = args.graph.nodes[args.n_id]["variable_id"]

    if args.symbol == args.graph.nodes[assign_id].get("symbol"):
        if args.graph.nodes[args.n_id].get("operator") in {"+=", "*=", "/="}:
            if not args.def_only:
                yield False, args.n_id
        else:
            yield True, args.n_id
    elif args.graph.nodes[assign_id].get("label_type") == "ArgumentList":
        graph = args.graph
        for n_id in adj_ast(graph, assign_id, 1, label_type="SymbolLookup"):
            if args.symbol == graph.nodes[n_id].get("symbol"):
                yield True, args.n_id
    elif (
        not args.def_only
        and (expr := args.graph.nodes[assign_id].get("expression"))
        and args.symbol in expr
    ):
        yield False, args.n_id
