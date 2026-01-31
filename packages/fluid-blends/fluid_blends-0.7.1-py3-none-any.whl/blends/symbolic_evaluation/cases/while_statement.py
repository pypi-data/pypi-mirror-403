from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    args.evaluation[args.n_id] = False
    block_id = args.graph.nodes[args.n_id]["block_id"]
    args.evaluation[args.n_id] = generic(args.fork_n_id(block_id)).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
