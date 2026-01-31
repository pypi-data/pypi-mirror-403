import pytest

from blends.models import Graph
from blends.stack.attributes import (
    STACK_GRAPH_IS_DEFINITION,
    STACK_GRAPH_IS_REFERENCE,
    STACK_GRAPH_KIND,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.partial_path import (
    PartialPathLimits,
    compute_minimal_partial_paths_in_file,
)
from blends.stack.partial_path_database import (
    PartialPathDatabase,
    StackGraphViewMetadata,
    remap_symbol_id,
)
from blends.stack.view import StackGraphView, SymbolInterner


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
def test_partial_path_database_roundtrip_and_copies_stats() -> None:
    graph = _build_reference_definition_graph()
    view = StackGraphView.from_syntax_graph(graph, path="test.py")
    per_file = compute_minimal_partial_paths_in_file(
        view,
        "test.py",
        limits=PartialPathLimits(),
    )

    database = PartialPathDatabase()
    database.put_file(file_handle=1, file_path="test.py", view=view, partial_paths=per_file)

    record = database.get_file(1)
    assert record is not None
    assert record.file_handle == 1
    assert record.file_path == "test.py"
    assert record.view_snapshot.symbol_id_to_string == ("x",)
    assert record.paths == per_file.paths

    record.stats.mark_limit_hit("external")
    changed_record = database.get_file(1)
    assert changed_record is not None
    assert "external" not in changed_record.stats.limit_hits

    assert database.list_files() == (1,)
    database.drop_file(1)
    assert database.get_file(1) is None


@pytest.mark.blends_test_group("stack_unittesting")
def test_remap_symbol_id_interns_into_target_interner() -> None:
    metadata = StackGraphViewMetadata(file_handles=("test.py",), symbol_id_to_string=("x",))
    target = SymbolInterner(symbol_to_id={}, id_to_symbol=[])

    symbol_id = remap_symbol_id(0, metadata, target)

    assert symbol_id == 0
    assert target.lookup(symbol_id) == "x"
