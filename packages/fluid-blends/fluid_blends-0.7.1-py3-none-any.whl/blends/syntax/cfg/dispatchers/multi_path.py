from blends.models import (
    NId,
)
from blends.query import (
    adj_ast,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def build(args: SyntaxCfgArgs) -> NId:
    for c_id in adj_ast(args.graph, args.n_id):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(c_id, args.nxt_id)),
            label_cfg="CFG",
        )
    return args.n_id
