from blends.models import (
    Graph,
    NId,
)
from blends.query import (
    match_ast_group_d,
    pred_ast,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
)
from blends.symbolic_evaluation.utils import (
    get_lookup_path,
)


def is_not_valid_expression(args: SymbolicEvalArgs, graph: Graph, n_attrs: dict[str, str]) -> bool:
    return "." in n_attrs["expression"] or graph.nodes[pred_ast(graph, args.n_id)[0]][
        "label_type"
    ] not in {"Assignment", "VariableDeclaration"}


def solve(args: SymbolicEvalArgs) -> NId | None:
    graph = args.graph
    n_attrs = graph.nodes[args.n_id]
    if is_not_valid_expression(args, graph, n_attrs):
        return None

    try:
        search_path = get_lookup_path(graph, args.path, args.n_id)
    except ValueError:
        return None

    search_expr = n_attrs["expression"]
    search_member = n_attrs["member"]
    for n_id in search_path:
        if graph.nodes[n_id]["label_type"] == "Assignment" and search_in_assignment(
            graph,
            n_id,
            search_expr,
            search_member,
        ):
            return n_id
        if graph.nodes[n_id]["label_type"] == "VariableDeclaration" and (
            val_id := search_in_declaration(graph, n_id, search_expr, search_member)
        ):
            return val_id
    return None


def search_in_assignment(graph: Graph, n_id: NId, search_expr: str, search_member: str) -> bool:
    var_id = graph.nodes[n_id]["variable_id"]
    return (
        graph.nodes[var_id]["label_type"] == "ElementAccess"
        and (v_attrs := graph.nodes[var_id]) is not None
        and graph.nodes[v_attrs["expression_id"]].get("symbol") == search_expr
        and graph.nodes[v_attrs["arguments_id"]].get("value") == search_member
    )


def search_in_objects(graph: Graph, val_id: str, search_member: str) -> NId | None:
    childs = match_ast_group_d(graph, val_id, "Pair")
    if pair_id := next(
        (
            _id
            for _id in childs
            if graph.nodes[graph.nodes[_id]["key_id"]].get("symbol") == search_member
        ),
        None,
    ):
        return str(graph.nodes[pair_id]["value_id"])
    return None


def search_in_declaration(
    graph: Graph,
    n_id: NId,
    search_expr: str,
    search_member: str,
) -> NId | None:
    if (
        graph.nodes[n_id]["variable"] == search_expr
        and (val_id := graph.nodes[n_id].get("value_id"))
        and graph.nodes[val_id]["label_type"] == "Object"
    ):
        return search_in_objects(graph, val_id, search_member)
    return None
