from blends.query import (
    adj_ast,
    lookup_first_cfg_parent,
)
from blends.symbolic_evaluation.context.search import (
    search_until_def,
)
from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
    SymbolicEvaluation,
)
from blends.symbolic_evaluation.utils import (
    get_lookup_path,
)

OUTSIDEPATH_TYPES = {
    "FieldDeclaration",
    "Import",
    "MethodDeclaration",
    "MethodInvocation",
    "Parameter",
    "VariableDeclaration",
}


def evaluate(args: SymbolicEvalArgs) -> SymbolicEvaluation:
    symbol_id = args.n_id
    args.evaluation[symbol_id] = False
    symbol = args.graph.nodes[args.n_id]["symbol"]

    try:
        path = get_lookup_path(args.graph, args.path, symbol_id)
    except ValueError:
        path = args.path

    refs_search_order = list(search_until_def(args.graph, path, symbol))
    refs_exec_order = reversed(refs_search_order)

    args.evaluation[symbol_id] = False
    arg_ids = adj_ast(args.graph, symbol_id)
    danger = [generic(args.fork_n_id(arg_id)).danger for arg_id in arg_ids]
    refs_dangers = []
    for ref_id in refs_exec_order:
        if args.graph.nodes[ref_id]["label_type"] in OUTSIDEPATH_TYPES:
            generic(args.fork_n_id(ref_id))
        elif ref_id in args.path:
            cfg_id = lookup_first_cfg_parent(args.graph, ref_id)
            generic(args.fork_n_id(cfg_id))

        if ref_id in args.evaluation:
            refs_dangers.append(args.evaluation[ref_id])

    args.evaluation[symbol_id] = any(refs_dangers) or any(danger)

    if args.method_evaluators and (method_evaluator := args.method_evaluators.get("symbol_lookup")):
        args.evaluation[args.n_id] = method_evaluator(args).danger
    return SymbolicEvaluation(args.evaluation[args.n_id], args.triggers)
