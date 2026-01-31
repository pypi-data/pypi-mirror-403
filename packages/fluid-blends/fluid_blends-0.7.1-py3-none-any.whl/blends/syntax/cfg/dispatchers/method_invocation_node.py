from blends.models import (
    NId,
)
from blends.query import (
    match_ast_d,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def build(args: SyntaxCfgArgs) -> NId:
    al_id = args.graph.nodes[args.n_id].get("arguments_id")
    if al_id and match_ast_d(args.graph, al_id, "MethodDeclaration"):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(al_id, args.nxt_id)),
            label_cfg="CFG",
        )
    el_id = args.graph.nodes[args.n_id].get("expression_id")
    if (
        el_id
        and args.graph.nodes[el_id]["label_type"] == "MemberAccess"
        and (mi_id := match_ast_d(args.graph, el_id, "MethodInvocation", 1))
    ):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(mi_id, args.nxt_id)),
            label_cfg="CFG",
        )
    if bl_id := args.graph.nodes[args.n_id].get("block_id") or match_ast_d(
        args.graph, args.n_id, "ExecutionBlock"
    ):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(bl_id, args.nxt_id)),
            label_cfg="CFG",
        )
    if args.nxt_id:
        args.graph.add_edge(args.n_id, args.nxt_id, label_cfg="CFG")

    return args.n_id
