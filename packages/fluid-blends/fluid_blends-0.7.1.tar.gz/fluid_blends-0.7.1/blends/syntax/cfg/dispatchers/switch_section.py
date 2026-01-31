from blends.models import (
    NId,
)
from blends.query import (
    adj_ast,
    pred_ast,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def build(args: SyntaxCfgArgs) -> NId:
    childs = adj_ast(args.graph, args.n_id)
    if len(childs) == 0:
        parent_id = pred_ast(args.graph, args.n_id)[0]
        siblings = adj_ast(args.graph, parent_id)
        next_sibling = next(
            (_id for _id in siblings if len(adj_ast(args.graph, _id)) > 0 and _id > args.n_id),
            siblings[-1],
        )
        childs = adj_ast(args.graph, next_sibling)
    for c_id in childs:
        args.graph.add_edge(
            args.n_id,
            args.generic(args.fork(c_id, args.nxt_id)),
            label_cfg="CFG",
        )
    return args.n_id
