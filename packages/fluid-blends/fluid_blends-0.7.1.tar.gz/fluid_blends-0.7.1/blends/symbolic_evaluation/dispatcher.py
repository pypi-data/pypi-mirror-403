from blends.symbolic_evaluation.models import (
    Evaluator,
    MissingSymbolicEvalError,
    SymbolicEvalArgs,
    SymbolicEvaluation,
)

EVALUATORS: dict[str, Evaluator] = {}


def register_evaluators(evaluators: dict[str, Evaluator]) -> None:
    EVALUATORS.update(evaluators)


def generic(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    node_type = args.graph.nodes[args.n_id]["label_type"]
    evaluator = EVALUATORS.get(node_type)
    if not evaluator:
        exc_log = f"Missing symbolic evaluator {node_type}"
        raise MissingSymbolicEvalError(exc_log)

    if args.n_id in args.evaluation:
        return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)

    return evaluator(args)
