import pytest

from blends.models import Graph
from blends.query import (
    adj,
    adj_ast,
    adj_lazy,
    filter_nodes,
    get_node_by_path,
    get_nodes_by_path,
    has_labels,
    match_ast_d,
    match_ast_group,
    match_ast_group_d,
    matching_nodes,
    nodes_by_type,
    pred,
    pred_lazy,
    predicate_has_labels,
)


@pytest.mark.blends_test_group("query_unittesting")
def test_has_labels() -> None:
    n_attrs = {"label_type": "function", "label_name": "test", "label_ast": "AST"}
    assert has_labels(n_attrs, label_type="function")
    assert has_labels(n_attrs, label_type="function", label_name="test")
    assert has_labels(n_attrs, label_type="function", label_name="test", label_ast="AST")
    assert not has_labels(n_attrs, label_type="class")
    assert not has_labels(n_attrs, label_type="function", label_name="other")
    assert has_labels({}, label_type="function") is False
    assert has_labels(n_attrs) is True


@pytest.mark.blends_test_group("query_unittesting")
def test_predicate_has_labels() -> None:
    predicate = predicate_has_labels(label_type="function", label_name="test")
    assert predicate({"label_type": "function", "label_name": "test"})
    assert not predicate({"label_type": "class", "label_name": "test"})
    assert not predicate({"label_type": "function", "label_name": "other"})
    assert not predicate({})


@pytest.mark.blends_test_group("query_unittesting")
def test_filter_nodes() -> None:
    graph = Graph()
    graph.add_node("1", label_type="function")
    graph.add_node("2", label_type="class")
    graph.add_node("3", label_type="function")
    graph.add_node("4", label_type="variable")

    predicate = predicate_has_labels(label_type="function")
    result = filter_nodes(graph, ["1", "2", "3", "4"], predicate)
    assert result == ("1", "3")

    predicate2 = predicate_has_labels(label_type="class")
    result2 = filter_nodes(graph, ["1", "2", "3", "4"], predicate2)
    assert result2 == ("2",)

    result3 = filter_nodes(graph, [], predicate)
    assert result3 == ()


@pytest.mark.blends_test_group("query_unittesting")
def test_matching_nodes() -> None:
    graph = Graph()
    graph.add_node("1", label_type="function", label_name="test")
    graph.add_node("2", label_type="class", label_name="Test")
    graph.add_node("3", label_type="function", label_name="other")
    graph.add_node("4", label_type="function", label_name="test")

    result = matching_nodes(graph, label_type="function")
    assert set(result) == {"1", "3", "4"}

    result2 = matching_nodes(graph, label_type="function", label_name="test")
    assert set(result2) == {"1", "4"}

    result3 = matching_nodes(graph, label_type="class")
    assert result3 == ("2",)

    result4 = matching_nodes(graph, label_type="nonexistent")
    assert result4 == ()


@pytest.mark.blends_test_group("query_unittesting")
def test_adj_and_pred_comprehensive() -> None:  # noqa: PLR0915
    graph = Graph()
    graph.add_node("1")
    graph.add_node("2")
    graph.add_node("3")
    graph.add_node("4")
    graph.add_node("5")
    graph.add_node("6")
    graph.add_edge("1", "2", attr_0="b")
    graph.add_edge("1", "3", attr_0="a")
    graph.add_edge("2", "6", attr_0="b")
    graph.add_edge("3", "4", attr_0="b")
    graph.add_edge("4", "5", attr_1="a")

    assert adj(graph, "1", depth=-1) == ("2", "3", "6", "4", "5")
    assert adj(graph, "1", depth=-1, attr_0="a") == ("3",)
    assert adj(graph, "1", depth=-1, attr_0="b") == ("2", "6")
    assert not adj(graph, "1", depth=0)
    assert adj(graph, "1", depth=1) == ("2", "3")
    assert adj(graph, "1", depth=1, attr_0="a") == ("3",)
    assert adj(graph, "1", depth=1, attr_0="b") == ("2",)
    assert not adj(graph, "1", depth=1, attr_1="b")

    assert pred(graph, "5", depth=-1) == ("4", "3", "1")
    assert not pred(graph, "5", depth=-1, attr_0="a")
    assert pred(graph, "5", depth=-1, attr_1="a") == ("4",)
    assert not pred(graph, "5", depth=-1, attr_0="b")
    assert not pred(graph, "5", depth=0)
    assert pred(graph, "5", depth=1) == ("4",)
    assert not pred(graph, "5", depth=1, attr_0="a")
    assert pred(graph, "5", depth=1, attr_1="a") == ("4",)
    assert not pred(graph, "5", depth=1, attr_0="b")
    assert pred(graph, "5", depth=2) == ("4", "3")


@pytest.mark.blends_test_group("query_unittesting")
def test_adj_cycles() -> None:
    graph = Graph()
    graph.add_node("1")
    graph.add_node("2")
    graph.add_edge("1", "2")
    graph.add_edge("2", "1")

    assert adj(graph, "1", depth=-1) == ("2", "1")
    assert adj(graph, "2", depth=-1) == ("1", "2")
    assert adj(graph, "1", depth=1) == ("2",)
    assert adj(graph, "2", depth=1) == ("1",)


@pytest.mark.blends_test_group("query_unittesting")
def test_adj_ast() -> None:
    graph = Graph()
    graph.add_node("1", label_type="root")
    graph.add_node("2", label_type="function")
    graph.add_node("3", label_type="class")
    graph.add_node("4", label_type="statement")
    graph.add_node("5", label_type="expression")
    graph.add_node("6", label_type="block")

    graph.add_edge("1", "2", label_ast="AST", label_index="0")
    graph.add_edge("1", "3", label_ast="AST", label_index="1")
    graph.add_edge("2", "3", label_ast="AST", label_index="0")

    assert adj_ast(graph, "1") == ("2", "3")
    assert adj_ast(graph, "1", strict=True) == ("2", "3")
    assert adj_ast(graph, "1", label_type="function") == ("2",)
    assert adj_ast(graph, "1", label_type="class") == ("3",)


@pytest.mark.blends_test_group("query_unittesting")
def test_adj_lazy() -> None:
    graph = Graph()
    graph.add_node("1")
    graph.add_node("2")
    graph.add_node("3")
    graph.add_edge("1", "2", attr="a")
    graph.add_edge("1", "3", attr="b")
    graph.add_edge("2", "3", attr="a")

    result = list(adj_lazy(graph, "1", depth=1))
    assert result == ["2", "3"]

    result2 = list(adj_lazy(graph, "1", depth=-1))
    assert result2 == ["2", "3", "3"]

    result3 = list(adj_lazy(graph, "1", depth=1, attr="a"))
    assert result3 == ["2"]

    result4 = list(adj_lazy(graph, "1", depth=0))
    assert result4 == []


@pytest.mark.blends_test_group("query_unittesting")
def test_pred_lazy() -> None:
    graph = Graph()
    graph.add_node("1")
    graph.add_node("2")
    graph.add_node("3")
    graph.add_edge("1", "2", attr="a")
    graph.add_edge("2", "3", attr="b")
    graph.add_edge("1", "3", attr="a")

    result = list(pred_lazy(graph, "3", depth=1))
    assert set(result) == {"1", "2"}

    result2 = list(pred_lazy(graph, "3", depth=-1))
    assert set(result2) == {"1", "2"}

    result3 = list(pred_lazy(graph, "3", depth=1, attr="a"))
    assert result3 == ["1"]

    result4 = list(pred_lazy(graph, "3", depth=0))
    assert result4 == []


@pytest.mark.blends_test_group("query_unittesting")
def test_match_ast_d() -> None:
    graph = Graph()
    graph.add_node("1", label_type="root")
    graph.add_node("2", label_type="function")
    graph.add_node("3", label_type="class")

    graph.add_edge("1", "2", label_ast="AST")
    graph.add_edge("1", "3", label_ast="AST")

    assert match_ast_d(graph, "1", "function", depth=1) == "2"
    assert match_ast_d(graph, "1", "class", depth=1) == "3"
    assert match_ast_d(graph, "1", "nonexistent", depth=1) is None
    assert match_ast_d(graph, "1", "function", depth=2) == "2"


@pytest.mark.blends_test_group("query_unittesting")
def test_match_ast_group() -> None:
    graph = Graph()
    graph.add_node("1", label_type="root")
    graph.add_node("2", label_type="function")
    graph.add_node("3", label_type="function")
    graph.add_node("4", label_type="class")
    graph.add_node("5", label_type="variable")

    graph.add_edge("1", "2", label_ast="AST")
    graph.add_edge("1", "3", label_ast="AST")
    graph.add_edge("1", "4", label_ast="AST")
    graph.add_edge("1", "5", label_ast="AST")

    result = match_ast_group(graph, "1", "function", "class", depth=1)
    assert set(result["function"]) == {"2", "3"}
    assert result["class"] == ["4"]
    assert result["__0__"] == ["5"]

    result2 = match_ast_group(graph, "1", "function", depth=1)
    assert set(result2["function"]) == {"2", "3"}

    result3 = match_ast_group(graph, "1", "nonexistent", depth=1)
    assert result3["nonexistent"] == []


@pytest.mark.blends_test_group("query_unittesting")
def test_match_ast_group_d() -> None:
    graph = Graph()
    graph.add_node("1", label_type="root")
    graph.add_node("2", label_type="function")
    graph.add_node("3", label_type="function")

    graph.add_edge("1", "2", label_ast="AST")
    graph.add_edge("1", "3", label_ast="AST")

    result = match_ast_group_d(graph, "1", "function", depth=1)
    assert set(result) == {"2", "3"}

    result2 = match_ast_group_d(graph, "1", "nonexistent", depth=1)
    assert result2 == []


@pytest.mark.blends_test_group("query_unittesting")
def test_get_nodes_by_path() -> None:
    graph = Graph()
    graph.add_node("1", label_type="root")
    graph.add_node("2", label_type="function")
    graph.add_node("3", label_type="class")
    graph.add_node("4", label_type="method")
    graph.add_node("5", label_type="method")

    graph.add_edge("1", "2", label_ast="AST")
    graph.add_edge("2", "3", label_ast="AST")
    graph.add_edge("3", "4", label_ast="AST")
    graph.add_edge("3", "5", label_ast="AST")

    result = get_nodes_by_path(graph, "1", "function", "class", "method")
    assert set(result) == {"4", "5"}

    result2 = get_nodes_by_path(graph, "1", "function")
    assert result2 == {"2"}

    result3 = get_nodes_by_path(graph, "1", "nonexistent")
    assert result3 == set()

    result4 = get_nodes_by_path(graph, "1")
    assert result4 == set()


@pytest.mark.blends_test_group("query_unittesting")
def test_get_node_by_path() -> None:
    graph = Graph()
    graph.add_node("1", label_type="root")
    graph.add_node("2", label_type="function")
    graph.add_node("3", label_type="class")
    graph.add_node("4", label_type="method")

    graph.add_edge("1", "2", label_ast="AST")
    graph.add_edge("2", "3", label_ast="AST")
    graph.add_edge("3", "4", label_ast="AST")

    assert get_node_by_path(graph, "1", "function", "class", "method") == "4"
    assert get_node_by_path(graph, "1", "function") == "2"
    assert get_node_by_path(graph, "1", "nonexistent") is None
    assert get_node_by_path(graph, "1") is None


@pytest.mark.blends_test_group("query_unittesting")
def test_nodes_by_type() -> None:
    graph = Graph()
    graph.add_node("1", label_type="function")
    graph.add_node("2", label_type="class")
    graph.add_node("3", label_type="function")
    graph.add_node("4", label_type="variable")

    result = nodes_by_type(graph)
    assert set(result["function"]) == {"1", "3"}
    assert result["class"] == ["2"]
    assert result["variable"] == ["4"]

    graph2 = Graph()
    graph2.add_node("1")
    result2 = nodes_by_type(graph2)
    assert result2 == {}
