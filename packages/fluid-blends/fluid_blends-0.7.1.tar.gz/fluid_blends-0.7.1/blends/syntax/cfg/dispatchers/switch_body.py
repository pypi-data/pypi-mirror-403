from blends.models import (
    NId,
)
from blends.query import (
    adj_ast,
)
from blends.syntax.cfg.dispatchers.multifile import (
    get_deterministic_path_id,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def build(args: SyntaxCfgArgs) -> NId:
    if args.is_multifile and (f_id := get_deterministic_path_id(args)):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(f_id, args.nxt_id)),
            label_cfg="CFG",
        )
    else:
        for c_id in adj_ast(args.graph, args.n_id):
            args.graph.add_edge(
                args.n_id,
                args.generic(args.fork(c_id, args.nxt_id)),
                label_cfg="CFG",
            )
    return args.n_id
