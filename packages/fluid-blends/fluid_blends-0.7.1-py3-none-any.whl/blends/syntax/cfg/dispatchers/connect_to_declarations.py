from blends.models import (
    NId,
)
from blends.query import (
    adj_ast,
)
from blends.syntax.cfg.dispatchers.multifile import (
    adjust_return_value,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)

DEC_TYPES = {
    "Class",
    "MethodDeclaration",
    "VariableDeclaration",
}


def build(args: SyntaxCfgArgs) -> NId:
    if (
        args.is_multifile
        and args.graph.nodes[args.n_id]["label_type"] == "Return"
        and args.graph.nodes[args.n_id].get("value_id")
    ):
        adjust_return_value(args)

    for _id in adj_ast(args.graph, args.n_id):
        if args.graph.nodes[_id]["label_type"] not in DEC_TYPES:
            continue

        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(_id, args.nxt_id)),
            label_cfg="CFG",
        )

    return args.n_id
