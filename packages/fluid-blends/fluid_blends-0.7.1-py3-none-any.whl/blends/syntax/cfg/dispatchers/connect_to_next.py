from blends.models import (
    NId,
)
from blends.syntax.cfg.dispatchers.multifile import (
    adjust_assignment_ast_edges,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def build(args: SyntaxCfgArgs) -> NId:
    if args.is_multifile and args.graph.nodes[args.n_id]["label_type"] == "Assignment":
        adjust_assignment_ast_edges(args)

    if args.nxt_id:
        args.graph.add_edge(args.n_id, args.nxt_id, label_cfg="CFG")
    elif (
        args.graph.nodes[args.n_id]["label_type"] == "Assignment"
        and (var_value_id := args.graph.nodes[args.n_id].get("value_id"))
        and args.graph.nodes[var_value_id]["label_type"] in {"MethodDeclaration", "Object"}
    ):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(var_value_id, args.nxt_id)),
            label_cfg="CFG",
        )
    return args.n_id
