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
    if args.n_id in args.path:
        deps_ids = tuple(args.path[: args.path.index(args.n_id)])
    else:
        deps_ids = adj_ast(args.graph, args.n_id)

    danger = [generic(args.fork_n_id(_id)).danger for _id in deps_ids]
    args.evaluation[args.n_id] = any(danger)

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
