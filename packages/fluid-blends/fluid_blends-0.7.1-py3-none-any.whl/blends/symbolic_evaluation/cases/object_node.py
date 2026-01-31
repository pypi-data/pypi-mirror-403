from blends.query import (
    adj_ast,
)
from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    param_ids = adj_ast(args.graph, args.n_id)
    danger = [generic(args.fork_n_id(p_id)).danger for p_id in param_ids]
    args.evaluation[args.n_id] = any(danger)

    if args.method_evaluators and (method_evaluator := args.method_evaluators.get("object_node")):
        args.evaluation[args.n_id] = method_evaluator(args).danger
    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
