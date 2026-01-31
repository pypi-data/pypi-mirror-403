from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    iterable_id = args.graph.nodes[args.n_id]["iterable_item_id"]
    args.evaluation[args.n_id] = generic(args.fork_n_id(iterable_id)).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
