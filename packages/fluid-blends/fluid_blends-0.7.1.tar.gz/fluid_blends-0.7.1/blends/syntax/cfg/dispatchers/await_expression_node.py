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
    if m_id := match_ast_d(args.graph, args.n_id, "MethodInvocation"):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(m_id, args.nxt_id)),
            label_cfg="CFG",
        )

    if args.nxt_id:
        args.graph.add_edge(args.n_id, args.nxt_id, label_cfg="CFG")

    return args.n_id
