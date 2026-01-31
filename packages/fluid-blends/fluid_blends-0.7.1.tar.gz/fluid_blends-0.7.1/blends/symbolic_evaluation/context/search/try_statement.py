from collections.abc import (
    Iterator,
)

from blends.query import adj_ast
from blends.symbolic_evaluation.context.search.model import (
    SearchArgs,
    SearchResult,
)


def search(args: SearchArgs) -> Iterator[SearchResult]:
    graph = args.graph
    n_id = args.n_id
    if (resources_n_id := graph.nodes[n_id].get("resources_id")) and (
        resource_vars_ids := adj_ast(graph, resources_n_id)
    ):
        for resource_id in resource_vars_ids:
            if graph.nodes[resource_id].get("variable", "") == args.symbol:
                yield True, resource_id
