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
    arg_ids = adj_ast(args.graph, args.n_id)
    danger = [generic(args.fork_n_id(arg_id)).danger for arg_id in arg_ids]
    args.evaluation[args.n_id] = any(danger)

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
