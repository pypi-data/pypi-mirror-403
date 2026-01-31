import logging

from blends.models import (
    Graph,
    NId,
)
from blends.syntax.cfg.dispatchers import (
    DISPATCHERS,
)
from blends.syntax.models import (
    MissingCfgBuilderError,
    SyntaxCfgArgs,
)

LOGGER = logging.getLogger(__name__)


def generic(args: SyntaxCfgArgs) -> NId:
    node_type = args.graph.nodes[args.n_id]["label_type"]

    if dispatcher := DISPATCHERS.get(node_type):
        return dispatcher(args)

    exc_log = f"Missing cfg builder for {node_type}"
    raise MissingCfgBuilderError(exc_log)


def add_syntax_cfg(graph: Graph, *, is_multifile: bool = False) -> Graph:
    try:
        generic(
            args=SyntaxCfgArgs(
                generic,
                graph,
                n_id="1",
                nxt_id=None,
                is_multifile=is_multifile,
            ),
        )
    except MissingCfgBuilderError:
        LOGGER.exception("Missing cfg builder")
    return graph
