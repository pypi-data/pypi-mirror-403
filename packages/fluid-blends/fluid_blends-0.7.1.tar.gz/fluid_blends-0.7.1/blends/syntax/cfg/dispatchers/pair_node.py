from blends.models import (
    NId,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def build(args: SyntaxCfgArgs) -> NId:
    key_id = args.graph.nodes[args.n_id].get("key_id")
    value_id = args.graph.nodes[args.n_id].get("value_id")
    if key_id and value_id:
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(key_id, args.nxt_id)),
            label_cfg="CFG",
        )
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(value_id, args.nxt_id)),
            label_cfg="CFG",
        )
    return args.n_id
