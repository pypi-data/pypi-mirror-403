from blends.models import (
    NId,
)
from blends.syntax.cfg.dispatchers.multifile import (
    get_condition_deterministic_result,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def build(args: SyntaxCfgArgs) -> NId:
    if (
        args.is_multifile
        and (cond_id := args.graph.nodes[args.n_id]["condition_id"])
        and (label := get_condition_deterministic_result(args.graph, cond_id))
        and (f_id := args.graph.nodes[args.n_id].get(label))
    ):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(f_id, args.nxt_id)),
            label_cfg="CFG",
        )
        return args.n_id

    if true_id := args.graph.nodes[args.n_id].get("true_id"):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(true_id, args.nxt_id)),
            label_cfg="CFG",
        )

    if false_id := args.graph.nodes[args.n_id].get("false_id"):
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(false_id, args.nxt_id)),
            label_cfg="CFG",
        )

    if args.nxt_id:
        args.graph.add_edge(args.n_id, args.nxt_id, label_cfg="CFG")

    return args.n_id
