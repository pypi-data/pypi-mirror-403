from collections.abc import (
    Iterator,
)

from blends.models import (
    NId,
)
from blends.query import (
    adj_ast,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def iter_with_next(values: list[str], last: str | None) -> Iterator[tuple[str, str | None]]:
    yield from zip(values, [*values[1:], last], strict=False)


def build(args: SyntaxCfgArgs) -> NId:
    if c_ids := adj_ast(args.graph, args.n_id):
        first_child, *_ = c_ids
        args.graph.add_edge(args.n_id, first_child, label_cfg="CFG")

        for c_id, nxt_id in iter_with_next(list(c_ids), args.nxt_id):
            args.generic(args.fork(c_id, nxt_id))

    return args.n_id
