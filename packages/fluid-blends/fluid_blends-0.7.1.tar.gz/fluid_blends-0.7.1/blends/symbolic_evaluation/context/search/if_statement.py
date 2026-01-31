from collections.abc import (
    Iterator,
)

from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)


def search(args: SearchArgs) -> Iterator[SearchResult]:
    if not args.def_only:
        c_id = args.graph.nodes[args.n_id]["condition_id"]
        c_type = args.graph.nodes[c_id]["label_type"]
        if (c_type == "SymbolLookup" and args.symbol == args.graph.nodes[c_id]["symbol"]) or (
            c_type == "MethodInvocation"
            and (m_expr := args.graph.nodes[c_id].get("expression"))
            and args.symbol == str(m_expr).rsplit(".", 1)[0]
        ):
            yield False, c_id
