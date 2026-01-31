from collections.abc import (
    Callable,
)
from typing import (
    NamedTuple,
    TypedDict,
    Unpack,
)

from blends.models import (
    Graph,
    GraphDB,
    NId,
)

Path = list[NId]


class SymbolicEvaluation(NamedTuple):
    danger: bool
    triggers: set[str]


class SymbolicEvalArgs(NamedTuple):
    evaluation: dict[NId, bool]
    graph: Graph
    path: Path
    n_id: NId
    triggers: set[str]
    graph_db: GraphDB | None
    method_evaluators: dict[str, Callable[["SymbolicEvalArgs"], SymbolicEvaluation]] | None = None

    def fork_n_id(
        self,
        n_id: NId,
        path: Path | None = None,
        graph: Graph | None = None,
    ) -> "SymbolicEvalArgs":
        if not path:
            path = self.path
        if not graph:
            graph = self.graph
        return SymbolicEvalArgs(
            evaluation=self.evaluation,
            triggers=self.triggers,
            graph=graph,
            path=path,
            n_id=n_id,
            graph_db=self.graph_db,
            method_evaluators=self.method_evaluators,
        )

    def fork(self, **attrs: Unpack["SymbolicEvalParams"]) -> "SymbolicEvalArgs":
        params = self._asdict()
        params.update(attrs)
        return SymbolicEvalArgs(**params)


Evaluator = Callable[[SymbolicEvalArgs], SymbolicEvaluation]


class SymbolicEvalParams(TypedDict, total=False):
    evaluation: dict[NId, bool]
    graph: Graph
    path: Path
    n_id: NId
    triggers: set[str]
    graph_db: GraphDB | None
    method_evaluators: dict[str, Callable[["SymbolicEvalArgs"], SymbolicEvaluation]] | None


class MissingSymbolicEvalError(Exception):
    pass
