from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    op_attr = args.graph.nodes[args.n_id]
    d_l_expr = generic(args.fork_n_id(op_attr["left_id"])).danger
    d_r_expr = generic(args.fork_n_id(op_attr["right_id"])).danger

    args.evaluation[args.n_id] = d_l_expr or d_r_expr

    if args.method_evaluators and (
        method_evaluator := args.method_evaluators.get("binary_operation")
    ):
        args.evaluation[args.n_id] = method_evaluator(args).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
