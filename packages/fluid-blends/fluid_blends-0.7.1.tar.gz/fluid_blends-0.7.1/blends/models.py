from collections.abc import Callable
from enum import (
    Enum,
)
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from networkx import DiGraph


class Language(Enum):
    CSHARP = "c_sharp"
    DART = "dart"
    GO = "go"
    HCL = "hcl"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    JSON = "json"
    KOTLIN = "kotlin"
    NOT_SUPPORTED = "not_supported"
    PHP = "php"
    PYTHON = "python"
    RUBY = "ruby"
    SCALA = "scala"
    SWIFT = "swift"
    TYPESCRIPT = "tsx"
    YAML = "yaml"


LANGUAGE_TO_EXTENSIONS: dict[Language, tuple[str, ...]] = {
    Language.CSHARP: (".cs",),
    Language.DART: (".dart",),
    Language.GO: (".go",),
    Language.HCL: (".hcl", ".tf"),
    Language.JAVA: (".java",),
    Language.JAVASCRIPT: (".js", ".jsx"),
    Language.JSON: (".json",),
    Language.KOTLIN: (".kt", ".ktm", ".kts"),
    Language.PHP: (".php",),
    Language.PYTHON: (".py",),
    Language.RUBY: (".rb",),
    Language.SCALA: (".scala",),
    Language.SWIFT: (".swift",),
    Language.TYPESCRIPT: (".ts", ".tsx"),
    Language.YAML: (".yaml", ".yml"),
}

EXTENSION_TO_LANGUAGE: dict[str, Language] = {
    ext: lang for lang, exts in LANGUAGE_TO_EXTENSIONS.items() for ext in exts
}


def decide_language(path: str) -> Language:
    file_extension = "." + path.split(".")[-1]
    return EXTENSION_TO_LANGUAGE.get(file_extension, Language.NOT_SUPPORTED)


SUPPORTED_MULTIFILE = {
    Language.JAVA,
}


class Content(NamedTuple):
    content_bytes: bytes
    content_str: str
    language: Language
    path: Path


class CustomParser(NamedTuple):
    validator: Callable[[Content], bool]
    parser: Callable[[Content], Content | None]


NId = str

if TYPE_CHECKING:

    class BaseGraph(DiGraph[NId]): ...
else:

    class BaseGraph(DiGraph): ...


class Graph(BaseGraph):
    def update_node(self, node_id: NId, attributes: dict[str, object]) -> None:
        self.nodes[node_id].update(attributes)


class GraphPair(NamedTuple):
    ast_graph: Graph | None
    syntax_graph: Graph | None


class GraphShard(NamedTuple):
    path: str
    graph: Graph
    syntax_graph: Graph
    content_as_str: str
    file_size: int


class GraphDB(NamedTuple):
    context: dict[Language, dict[str, dict]]  # type: ignore[type-arg]
    shards: dict[str, GraphShard]
    properties: dict[str, dict[str, str]] = {}  # noqa: RUF012

    def get_path_shard(self, path: str) -> GraphShard | None:
        return self.shards.get(path)
