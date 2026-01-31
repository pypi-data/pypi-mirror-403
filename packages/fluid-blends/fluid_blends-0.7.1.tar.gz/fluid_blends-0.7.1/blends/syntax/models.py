from collections.abc import Callable
from typing import NamedTuple, TypedDict

from blends.models import (
    Graph,
    Language,
    NId,
)


class SyntaxMetadata(TypedDict):
    class_path: list[str]
    scope_stack: list[NId]


class SyntaxGraphArgs(NamedTuple):
    generic: Callable[["SyntaxGraphArgs"], NId]
    path: str
    language: Language
    ast_graph: Graph
    syntax_graph: Graph
    n_id: NId
    metadata: SyntaxMetadata

    def fork_n_id(self, n_id: NId) -> "SyntaxGraphArgs":
        return SyntaxGraphArgs(
            generic=self.generic,
            path=self.path,
            language=self.language,
            ast_graph=self.ast_graph,
            syntax_graph=self.syntax_graph,
            n_id=n_id,
            metadata=self.metadata,
        )


SyntaxReader = Callable[[SyntaxGraphArgs], NId]
Dispatcher = dict[str, SyntaxReader]


class FileStructData(TypedDict):
    node: NId
    type: str
    data: dict[str, str] | str


class FileInstanceData(TypedDict):
    object: str
    source: str
    source_type: str


class ReaderLogicError(Exception):
    pass


class SyntaxCfgArgs(NamedTuple):
    generic: Callable[["SyntaxCfgArgs"], NId]
    graph: Graph
    n_id: NId
    nxt_id: NId | None
    is_multifile: bool = False

    def fork(self, n_id: NId, nxt_id: NId | None) -> "SyntaxCfgArgs":
        return SyntaxCfgArgs(
            generic=self.generic,
            graph=self.graph,
            n_id=n_id,
            nxt_id=nxt_id,
            is_multifile=self.is_multifile,
        )


class MissingCfgBuilderError(Exception):
    pass
