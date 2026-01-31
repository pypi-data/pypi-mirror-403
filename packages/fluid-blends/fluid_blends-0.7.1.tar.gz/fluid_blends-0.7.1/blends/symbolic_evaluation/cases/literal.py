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
    args.evaluation[args.n_id] = False
    s_ids = adj_ast(args.graph, args.n_id)
    if len(s_ids) > 0:
        danger = [generic(args.fork_n_id(_id)).danger for _id in s_ids]
        args.evaluation[args.n_id] = any(danger)

    if args.method_evaluators and (method_evaluator := args.method_evaluators.get("literal")):
        args.evaluation[args.n_id] = method_evaluator(args).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
