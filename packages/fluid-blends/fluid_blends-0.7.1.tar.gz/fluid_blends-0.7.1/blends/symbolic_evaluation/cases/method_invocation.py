from blends.models import (
    SUPPORTED_MULTIFILE,
    NId,
    decide_language,
)
from blends.query import (
    adj_ast,
)
from blends.symbolic_evaluation.context.method import (
    solve_invocation,
)
from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)
from blends.symbolic_evaluation.multifile.method_invocation import (
    evaluate_method_invocation,
)

MODIFYING_METHODS: set[str] = {"add", "push", "put", "get"}


def evaluate_method_expression(
    args: SymbolicEvalArgs,
    expr_id: NId,
) -> bool:
    if args.graph.nodes[expr_id].get("symbol") in MODIFYING_METHODS:
        return False

    if md_id := solve_invocation(args.graph, args.path, expr_id):
        # Avoid infinite propagation in recursive method invocations
        if expr_id in adj_ast(args.graph, md_id, depth=-1):
            return False
        fork_id = args.graph.nodes[md_id].get("block_id") or md_id
        d_expression = generic(args.fork_n_id(fork_id)).danger
    else:
        d_expression = generic(args.fork_n_id(expr_id)).danger

    return d_expression


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    args.evaluation[args.n_id] = False
    n_attrs = args.graph.nodes[args.n_id]

    d_method = False
    propagate_danger = True
    if (
        (metadata_node := args.graph.nodes.get("0"))
        and (lang := decide_language(path=metadata_node["path"]))
        and lang in SUPPORTED_MULTIFILE
    ):
        d_method, propagate_danger = evaluate_method_invocation(args, lang)

    propagation_result = False
    if propagate_danger:
        d_expression = False
        if expr_id := n_attrs.get("expression_id"):
            d_expression = evaluate_method_expression(args, expr_id)

        d_arguments = False
        if al_id := args.graph.nodes[args.n_id].get("arguments_id"):
            d_arguments = generic(args.fork_n_id(al_id)).danger

        d_object = False
        if obj_id := args.graph.nodes[args.n_id].get("object_id"):
            d_object = generic(args.fork_n_id(obj_id)).danger

        propagation_result = d_expression or d_arguments or d_object

    args.evaluation[args.n_id] = propagation_result or d_method
    if args.method_evaluators and (
        method_evaluator := args.method_evaluators.get("method_invocation")
    ):
        args.evaluation[args.n_id] = method_evaluator(args).danger

    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
