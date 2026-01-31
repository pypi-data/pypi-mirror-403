from blends.symbolic_evaluation.context.member import (
    solve as solve_member_access,
)
from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    expr_id = solve_member_access(args) or args.graph.nodes[args.n_id]["expression_id"]
    args.evaluation[args.n_id] = generic(args.fork_n_id(expr_id)).danger

    if args.method_evaluators and (method_evaluator := args.method_evaluators.get("member_access")):
        args.evaluation[args.n_id] = method_evaluator(args).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
