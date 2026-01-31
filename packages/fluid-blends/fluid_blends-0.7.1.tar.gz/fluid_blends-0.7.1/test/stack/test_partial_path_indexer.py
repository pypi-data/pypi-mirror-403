import pytest

from blends.models import Graph
from blends.stack.attributes import (
    STACK_GRAPH_IS_DEFINITION,
    STACK_GRAPH_IS_REFERENCE,
    STACK_GRAPH_KIND,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.partial_path_database import PartialPathDatabase
from blends.stack.partial_path_indexer import (
    PartialPathIndexRequest,
    index_partial_paths_for_file,
)


def _build_reference_definition_graph() -> Graph:
    graph = Graph()
    graph.add_node("1")
    graph.nodes["1"][STACK_GRAPH_KIND] = StackGraphNodeKind.PUSH_SYMBOL.value
    graph.nodes["1"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["1"][STACK_GRAPH_IS_REFERENCE] = True

    graph.add_node("2")
    graph.nodes["2"][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes["2"][STACK_GRAPH_SYMBOL] = "x"
    graph.nodes["2"][STACK_GRAPH_IS_DEFINITION] = True

    graph.add_edge("1", "2", precedence=0)
    return graph


@pytest.mark.blends_test_group("stack_unittesting")
def test_index_partial_paths_for_file_stores_results() -> None:
    graph = _build_reference_definition_graph()
    database = PartialPathDatabase()
    request = PartialPathIndexRequest(
        file_path="test.py",
        file_handle=1,
    )

    result = index_partial_paths_for_file(graph, request, database)

    record = database.get_file(1)
    assert record is not None
    assert record.paths == result.paths
