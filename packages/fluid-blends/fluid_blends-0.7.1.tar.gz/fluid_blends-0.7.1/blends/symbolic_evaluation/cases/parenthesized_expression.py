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
    c_id = adj_ast(args.graph, args.n_id)[0]
    args.evaluation[args.n_id] = generic(args.fork_n_id(c_id)).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
