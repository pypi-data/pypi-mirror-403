from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    args.evaluation[args.n_id] = False
    if val_id := args.graph.nodes[args.n_id].get("value_id"):
        args.evaluation[args.n_id] = generic(args.fork_n_id(val_id)).danger

    if args.method_evaluators and (method_evaluator := args.method_evaluators.get("parameter")):
        args.evaluation[args.n_id] = method_evaluator(args).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
