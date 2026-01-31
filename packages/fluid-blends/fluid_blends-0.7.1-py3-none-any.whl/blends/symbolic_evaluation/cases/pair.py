from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    n_attr = args.graph.nodes[args.n_id]
    key_danger = generic(args.fork_n_id(n_attr["key_id"])).danger
    val_danger = generic(args.fork_n_id(n_attr["value_id"])).danger

    args.evaluation[args.n_id] = key_danger or val_danger

    if args.method_evaluators and (method_evaluator := args.method_evaluators.get("pair")):
        args.evaluation[args.n_id] = method_evaluator(args).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
