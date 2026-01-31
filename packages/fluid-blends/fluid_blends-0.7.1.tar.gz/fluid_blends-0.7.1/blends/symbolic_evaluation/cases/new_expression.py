from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    n_attrs = args.graph.nodes[args.n_id]
    c_danger = generic(args.fork_n_id(n_attrs["constructor_id"])).danger
    if al_id := n_attrs.get("arguments_id"):
        al_danger = generic(args.fork_n_id(al_id)).danger
    else:
        al_danger = False

    args.evaluation[args.n_id] = c_danger or al_danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
