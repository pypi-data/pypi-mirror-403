from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    args.evaluation[args.n_id] = False
    danger_params = False
    if pl_id := args.graph.nodes[args.n_id].get("parameters_id"):
        danger_params = generic(args.fork_n_id(pl_id)).danger
    danger_block = False
    if block_id := args.graph.nodes[args.n_id].get("block_id"):
        danger_block = generic(args.fork_n_id(block_id)).danger

    args.evaluation[args.n_id] = danger_params or danger_block
    if args.method_evaluators and (
        method_evaluator := args.method_evaluators.get("method_declaration")
    ):
        args.evaluation[args.n_id] = method_evaluator(args).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
