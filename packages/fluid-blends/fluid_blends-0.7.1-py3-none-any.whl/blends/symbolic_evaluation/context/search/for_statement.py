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
    init_id = args.graph.nodes[args.n_id].get("initializer_node")
    if init_id:
        init_node = args.graph.nodes[init_id]
        if init_node.get("label_type") == "SymbolLookup" and args.symbol == init_node.get("symbol"):
            yield True, args.n_id
        else:
            symbols_ids = adj_ast(args.graph, init_id, label_type="SymbolLookup")
            for c_id in symbols_ids:
                if args.symbol == args.graph.nodes[c_id].get("symbol"):
                    yield True, args.n_id
                    break
