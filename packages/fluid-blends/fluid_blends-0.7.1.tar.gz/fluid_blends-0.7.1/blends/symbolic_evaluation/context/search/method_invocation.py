from collections.abc import (
    Iterator,
)

from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)


def method_modifies_symbol(args: SearchArgs) -> bool:
    n_attr = args.graph.nodes[args.n_id]
    expr_split = n_attr["expression"].split(".")
    obj_id = n_attr.get("object_id")
    return (obj_id and args.symbol == args.graph.nodes[obj_id].get("symbol")) or (
        len(expr_split) > 1 and args.symbol == expr_split[0]
    )


def search(args: SearchArgs) -> Iterator[SearchResult]:
    if not args.def_only and method_modifies_symbol(args):
        yield False, args.n_id
