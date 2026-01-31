from collections.abc import (
    Callable,
)
from typing import (
    NamedTuple,
)

from blends.models import (
    Graph,
    NId,
)
from blends.symbolic_evaluation.context.search import (
    definition_search,
)
from blends.symbolic_evaluation.models import (
    Path,
)
from blends.symbolic_evaluation.utils import (
    get_lookup_path,
)


class SolverArgs(NamedTuple):
    generic: Callable[["SolverArgs"], NId | None]
    graph: Graph
    path: Path
    n_id: NId

    def fork_n_id(self, n_id: NId) -> "SolverArgs":
        return SolverArgs(
            generic=self.generic,
            graph=self.graph,
            path=self.path,
            n_id=n_id,
        )


def solve_symbol_lookup(args: SolverArgs) -> NId | None:
    symbol = args.graph.nodes[args.n_id]["symbol"]
    try:
        search_path = get_lookup_path(args.graph, args.path, args.n_id)
    except ValueError:
        return None

    return definition_search(args.graph, search_path, symbol)


SOLVERS: dict[str, Callable[[SolverArgs], NId | None]] = {
    "SymbolLookup": solve_symbol_lookup,
}


def generic(args: SolverArgs) -> NId | None:
    if args.n_id not in args.graph.nodes:
        return None
    node_type = args.graph.nodes[args.n_id]["label_type"]
    if solver := SOLVERS.get(node_type):
        return solver(args)
    return None


def solve_invocation(graph: Graph, path: Path, n_id: NId) -> NId | None:
    return generic(SolverArgs(generic, graph, path, n_id))
