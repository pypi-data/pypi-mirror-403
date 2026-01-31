from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    args.evaluation[args.n_id] = False
    block_danger = False
    if args.n_id not in args.path:
        block_id = args.graph.nodes[args.n_id]["block_id"]
        block_danger = generic(args.fork_n_id(block_id)).danger

    declaration_danger = False
    if decl_id := args.graph.nodes[args.n_id].get("declaration_id"):
        declaration_danger = generic(args.fork_n_id(decl_id)).danger

    args.evaluation[args.n_id] = block_danger or declaration_danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
