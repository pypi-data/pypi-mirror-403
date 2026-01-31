from collections.abc import (
    Callable,
    Iterator,
)
from typing import (
    NamedTuple,
)

from blends.models import (
    Graph,
    NId,
)

# Bool value indicates whether the founded node is a definition or not
SearchResult = tuple[bool, NId]


class SearchArgs(NamedTuple):
    graph: Graph
    n_id: NId
    symbol: str
    def_only: bool


Searcher = Callable[[SearchArgs], Iterator[SearchResult]]
