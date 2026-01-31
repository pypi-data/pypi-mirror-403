from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    n_attr = args.graph.nodes[args.n_id]
    alt_danger = generic(args.fork_n_id(n_attr["true_id"])).danger
    cons_danger = generic(args.fork_n_id(n_attr["false_id"])).danger

    args.evaluation[args.n_id] = alt_danger or cons_danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
