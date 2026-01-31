from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    danger_cond = False
    danger_true = False
    danger_false = False
    node = args.graph.nodes[args.n_id]
    if _id := node.get("condition_id"):
        danger_cond = generic(args.fork_n_id(_id)).danger
    if args.n_id not in args.path:
        if _id := node.get("true_id"):
            danger_true = generic(args.fork_n_id(_id)).danger
        if _id := node.get("false_id"):
            danger_false = generic(args.fork_n_id(_id)).danger

    args.evaluation[args.n_id] = danger_cond or danger_true or danger_false

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
