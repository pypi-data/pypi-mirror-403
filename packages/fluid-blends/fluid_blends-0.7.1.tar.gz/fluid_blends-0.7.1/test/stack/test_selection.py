import pytest

from blends.models import (
    Graph,
)
from blends.stack.attributes import (
    STACK_GRAPH_IS_DEFINITION,
    STACK_GRAPH_KIND,
    STACK_GRAPH_SYMBOL,
)
from blends.stack.edges import (
    Edge,
    add_edge,
)
from blends.stack.node_kinds import (
    StackGraphNodeKind,
)
from blends.stack.selection import (
    DefinitionCandidate,
    PartialPathEdge,
    edge_list_shadows,
    edge_shadows,
    prune_shadowed_candidates,
    select_definition_candidates_from_scope,
    sort_candidates_deterministically,
)
from blends.stack.view import (
    StackGraphView,
)


def _view_for_graph(graph: Graph) -> StackGraphView:
    return StackGraphView.from_syntax_graph(graph, path="test.py")


def _add_scope_node(graph: Graph, node_id: str) -> None:
    graph.add_node(node_id)
    graph.nodes[node_id][STACK_GRAPH_KIND] = StackGraphNodeKind.SCOPE.value


def _add_pop_symbol_node(
    graph: Graph, node_id: str, symbol: str, *, is_definition: bool = True
) -> None:
    graph.add_node(node_id)
    graph.nodes[node_id][STACK_GRAPH_KIND] = StackGraphNodeKind.POP_SYMBOL.value
    graph.nodes[node_id][STACK_GRAPH_SYMBOL] = symbol
    graph.nodes[node_id][STACK_GRAPH_IS_DEFINITION] = is_definition


@pytest.mark.blends_test_group("stack_unittesting")
@pytest.mark.parametrize(  # type: ignore[misc,attr-defined]
    ("source1", "prec1", "source2", "prec2", "expected"),
    [
        (1, 2, 1, 1, True),
        (1, 1, 1, 1, False),
        (2, 2, 1, 1, False),
    ],
)
def test_edge_shadows(  # type: ignore[misc]
    source1: int,
    prec1: int,
    source2: int,
    prec2: int,
    expected: bool,  # noqa: FBT001
) -> None:
    assert (
        edge_shadows(
            PartialPathEdge(source_node_index=source1, precedence=prec1),
            PartialPathEdge(source_node_index=source2, precedence=prec2),
        )
        == expected
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_edge_list_shadows_is_not_comparable_when_sources_differ() -> None:
    assert not edge_list_shadows(
        (PartialPathEdge(source_node_index=1, precedence=2),),
        (PartialPathEdge(source_node_index=2, precedence=1),),
    )


@pytest.mark.blends_test_group("stack_unittesting")
def test_prune_shadowed_candidates_keeps_ties() -> None:
    candidates = [
        DefinitionCandidate(
            definition_node_index=10,
            edges=(PartialPathEdge(source_node_index=1, precedence=0),),
        ),
        DefinitionCandidate(
            definition_node_index=11,
            edges=(PartialPathEdge(source_node_index=1, precedence=0),),
        ),
    ]

    pruned = prune_shadowed_candidates(candidates)

    assert {c.definition_node_index for c in pruned} == {10, 11}


@pytest.mark.blends_test_group("stack_unittesting")
def test_prune_shadowed_candidates_removes_lower_precedence_for_same_source() -> None:
    candidates = [
        DefinitionCandidate(
            definition_node_index=10,
            edges=(PartialPathEdge(source_node_index=1, precedence=0),),
        ),
        DefinitionCandidate(
            definition_node_index=11,
            edges=(PartialPathEdge(source_node_index=1, precedence=1),),
        ),
    ]

    pruned = prune_shadowed_candidates(candidates)

    assert [c.definition_node_index for c in sort_candidates_deterministically(pruned)] == [11]


@pytest.mark.blends_test_group("stack_unittesting")
def test_sort_candidates_is_deterministic() -> None:
    a = DefinitionCandidate(
        definition_node_index=20,
        edges=(PartialPathEdge(source_node_index=1, precedence=0),),
    )
    b = DefinitionCandidate(
        definition_node_index=10,
        edges=(PartialPathEdge(source_node_index=1, precedence=0),),
    )

    assert sort_candidates_deterministically([a, b]) == [b, a]
    assert sort_candidates_deterministically([b, a]) == [b, a]


@pytest.mark.blends_test_group("stack_unittesting")
def test_select_definition_candidates_from_scope_prunes_by_edge_precedence() -> None:
    graph = Graph()
    _add_scope_node(graph, "2")
    _add_pop_symbol_node(graph, "3", "x")
    _add_pop_symbol_node(graph, "4", "x")

    graph.add_edge("2", "3", precedence=0)
    graph.add_edge("2", "4", precedence=1)

    view = _view_for_graph(graph)
    selected = select_definition_candidates_from_scope(
        view, view.nid_to_index["2"], view.symbols.intern("x")
    )

    assert selected == [view.nid_to_index["4"]]


@pytest.mark.blends_test_group("stack_unittesting")
def test_view_outgoing_is_sorted_by_sink_index() -> None:
    graph = Graph()
    _add_scope_node(graph, "2")
    _add_pop_symbol_node(graph, "3", "x", is_definition=False)
    _add_pop_symbol_node(graph, "4", "x", is_definition=False)

    add_edge(graph, Edge(source="2", sink="4", precedence=0))
    add_edge(graph, Edge(source="2", sink="3", precedence=0))

    view = _view_for_graph(graph)
    assert view.outgoing[view.nid_to_index["2"]] == [
        (view.nid_to_index["3"], 0),
        (view.nid_to_index["4"], 0),
    ]


@pytest.mark.blends_test_group("stack_unittesting")
@pytest.mark.parametrize(  # type: ignore[misc,attr-defined]
    ("first_precedence", "second_precedence", "expected_precedence"),
    [(0, 2, 2), (2, 0, 2)],
)
def test_add_edge_keeps_max_precedence_for_existing_edge(  # type: ignore[misc]
    first_precedence: int, second_precedence: int, expected_precedence: int
) -> None:
    graph = Graph()
    _add_scope_node(graph, "2")
    _add_pop_symbol_node(graph, "3", "x", is_definition=False)

    add_edge(graph, Edge(source="2", sink="3", precedence=first_precedence))
    add_edge(graph, Edge(source="2", sink="3", precedence=second_precedence))

    view = _view_for_graph(graph)
    assert view.outgoing[view.nid_to_index["2"]] == [(view.nid_to_index["3"], expected_precedence)]
