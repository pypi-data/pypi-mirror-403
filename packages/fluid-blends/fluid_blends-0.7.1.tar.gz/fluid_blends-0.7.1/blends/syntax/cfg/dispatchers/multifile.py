from collections.abc import (
    Iterator,
)

import sympy  # type: ignore[import-untyped]

from blends.models import (
    Graph,
    NId,
)
from blends.query import (
    adj_ast,
    match_ast,
    match_ast_group_d,
    pred_ast,
)
from blends.symbolic_evaluation.context.search import (
    definition_search,
)
from blends.symbolic_evaluation.models import (
    Path,
)
from blends.symbolic_evaluation.utils import (
    get_backward_paths,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def search_value(graph: Graph, n_id: NId, symbol: str) -> str | None:
    for c_id in adj_ast(graph, n_id):
        if str(graph.nodes[c_id].get("case_expression")).strip("\"'") == symbol:
            return c_id
    return None


def guess_char(graph: Graph, path: Path, n_id: NId) -> str | None:
    if val_id := graph.nodes[n_id].get("value_id"):
        return graph.nodes[val_id].get("value")

    if (
        graph.nodes[n_id]["label_type"] == "MethodInvocation"
        and graph.nodes[n_id]["expression"] == "charAt"
        and (obj_id := graph.nodes[n_id].get("object_id"))
        and (obj_symbol := graph.nodes[obj_id].get("symbol")) is not None
        and (val_id := definition_search(graph, path, obj_symbol))
    ):
        args_id = graph.nodes[n_id]["arguments_id"]
        char_pos_id = adj_ast(graph, args_id)[0]
        if (
            (char_pos_str := graph.nodes[char_pos_id].get("value")) is not None
            and (char_pos := int(char_pos_str))
            and (guess_val_id := graph.nodes[val_id].get("value_id"))
            and (guess_value := graph.nodes[guess_val_id].get("value"))
        ):
            return str(guess_value.strip("\"'")[char_pos])
    return None


def get_symbol_assignment(graph: Graph, n_id: NId, symbol: str) -> str | None:
    for path in get_backward_paths(graph, n_id):
        if (
            (var_def_id := definition_search(graph, path, symbol))
            and (val_id := graph.nodes[var_def_id].get("value_id"))
            and (value := guess_char(graph, path, val_id))
        ):
            return value.strip("\"'")
    return None


def get_deterministic_path_id(args: SyntaxCfgArgs) -> NId | None:
    graph = args.graph
    parent_id = pred_ast(graph, args.n_id)[0]
    if (
        (val_id := graph.nodes[parent_id].get("value_id"))
        and (symbol := graph.nodes[val_id].get("symbol"))
        and (var_definition := get_symbol_assignment(graph, parent_id, symbol))
    ):
        return search_value(graph, args.n_id, var_definition)
    return None


def childs_operations(graph: Graph, n_id: str) -> Iterator[str]:
    if value := graph.nodes[n_id].get("value"):
        yield value
    if graph.nodes[n_id]["label_type"] == "BinaryOperation":
        yield from childs_operations(graph, graph.nodes[n_id]["left_id"])
        yield graph.nodes[n_id]["operator"]
        yield from childs_operations(graph, graph.nodes[n_id]["right_id"])


def get_operation_expression(graph: Graph, n_id: str) -> str:
    return "".join(childs_operations(graph, n_id))


def search_symbol_val_id(graph: Graph, n_id: NId) -> NId | None:
    symbol = graph.nodes[n_id]["symbol"]
    for path in get_backward_paths(graph, n_id):
        if (var_def_id := definition_search(graph, path, symbol)) and graph.nodes[var_def_id][
            "label_type"
        ] == "VariableDeclaration":
            return graph.nodes[var_def_id].get("value_id")
    return None


def get_condition_deterministic_result(graph: Graph, cond_id: NId) -> str | None:
    if graph.nodes[cond_id]["label_type"] == "SymbolLookup":
        symbol_ids = [
            cond_id,
        ]
    else:
        symbol_ids = match_ast_group_d(graph, cond_id, "SymbolLookup", depth=-1)

    for var_id in symbol_ids:
        if (
            (val_id := search_symbol_val_id(graph, var_id))
            and graph.nodes[val_id]["label_type"] == "Literal"
            and (var_value := graph.nodes[val_id].get("value"))
        ):
            graph.nodes[var_id]["value"] = var_value
        else:
            return None

    try:
        result = sympy.simplify(get_operation_expression(graph, cond_id))
    except sympy.SympifyError:
        return None

    if isinstance(result, sympy.logic.boolalg.BooleanTrue):
        return "true_id"
    if isinstance(result, sympy.logic.boolalg.BooleanFalse):
        return "false_id"
    return None


def get_element_in_hashmap(graph: Graph, path: Path, var_name: str, access_key: str) -> NId | None:
    for n_id in path:
        n_attrs = graph.nodes[n_id]
        if (
            n_attrs["label_type"] != "MethodInvocation"
            or not n_attrs.get("object_id")
            or n_attrs.get("expression") not in {"put"}
        ):
            continue

        min_args = 2
        if (
            graph.nodes[n_attrs["object_id"]].get("symbol") == var_name
            and (al_id := n_attrs.get("arguments_id"))
            and (arg_ids := adj_ast(graph, al_id))
            and len(arg_ids) >= min_args
            and graph.nodes[arg_ids[0]].get("value") == access_key
        ):
            return arg_ids[1]
    return None


def get_element_in_array(graph: Graph, path: Path, var_name: str, access_val: int) -> NId | None:
    d_nodes: list[NId] = []
    for n_id in reversed(path):
        n_attrs = graph.nodes[n_id]
        if (
            n_attrs["label_type"] == "MethodInvocation"
            and (object_id := n_attrs.get("object_id"))
            and graph.nodes[object_id].get("symbol") == var_name
            and (al_id := n_attrs.get("arguments_id"))
            and (arg_id := match_ast(graph, al_id).get("__0__"))
        ):
            if n_attrs.get("expression") in {"add", "push"}:
                d_nodes.append(arg_id)
            elif n_attrs.get("expression") in {"remove"} and (
                idx := graph.nodes[arg_id].get("value")
            ):
                try:
                    d_nodes.pop(int(idx))
                except ValueError:
                    d_nodes.pop()
    if len(d_nodes) > 0 and len(d_nodes) >= abs(access_val):
        return d_nodes[access_val]
    return None


def search_data_element(graph: Graph, method_id: NId) -> NId | None:
    n_attrs = graph.nodes[method_id]
    obj_id = n_attrs.get("object_id")
    al_id = n_attrs.get("arguments_id")

    if not (obj_id and al_id):
        return None

    args_ids = adj_ast(graph, al_id)
    var_name = graph.nodes[obj_id].get("symbol")
    if not (
        var_name and len(args_ids) == 1 and graph.nodes[args_ids[0]]["label_type"] == "Literal"
    ):
        return None

    access_nid = graph.nodes[args_ids[0]]
    access_val = None
    if access_nid.get("value_type") == "number":
        access_val = int(access_nid["value"])
        for path in get_backward_paths(graph, method_id):
            return get_element_in_array(graph, path, var_name, access_val)
    elif access_nid.get("value_type") == "string":
        access_key = str(access_nid["value"])
        for path in get_backward_paths(graph, method_id):
            return get_element_in_hashmap(graph, path, var_name, access_key)

    return None


def get_node_access_method(graph: Graph, n_id: NId) -> NId | None:
    method_id = n_id
    if graph.nodes[n_id]["label_type"] == "VariableDeclaration" and (
        val_id := graph.nodes[n_id].get("value_id")
    ):
        method_id = val_id

    if (
        graph.nodes[method_id]["label_type"] == "MethodInvocation"
        and graph.nodes[method_id]["expression"] == "get"
    ):
        return method_id

    return None


def adjust_assignment_ast_edges(args: SyntaxCfgArgs) -> None:
    value_id = args.graph.nodes[args.n_id]["value_id"]
    if (
        (args.graph.nodes[value_id]["label_type"] == "TernaryOperation")
        and (cond_id := args.graph.nodes[value_id]["condition_id"])
        and (label := get_condition_deterministic_result(args.graph, cond_id))
        and (c_id := args.graph.nodes[value_id].get(label))
    ):
        args.graph.remove_edge(args.n_id, value_id)
        args.graph.remove_edge(value_id, c_id)
        args.graph.nodes[args.n_id]["value_id"] = c_id
        args.graph.add_edge(args.n_id, c_id, label_ast="AST")

    if (method_id := get_node_access_method(args.graph, value_id)) and (
        c_id := search_data_element(args.graph, method_id)
    ):
        args.graph.remove_edge(args.n_id, value_id)
        args.graph.remove_edge(pred_ast(args.graph, c_id)[0], c_id)
        args.graph.nodes[args.n_id]["value_id"] = c_id
        args.graph.add_edge(args.n_id, c_id, label_ast="AST")


def get_return_literal(graph: Graph, n_id: NId, symbol: str) -> str | None:
    literal_values = set()
    for path in get_backward_paths(graph, n_id):
        if (
            (var_def_id := definition_search(graph, path, symbol))
            and (val_id := graph.nodes[var_def_id].get("value_id"))
            and graph.nodes[val_id]["label_type"] == "Literal"
            and (return_value := graph.nodes[val_id].get("value"))
        ):
            literal_values.add(return_value.strip("\"'"))
        else:
            return None

    if len(literal_values) > 0:
        return str(list(literal_values)[-1])
    return None


def adjust_return_value(args: SyntaxCfgArgs) -> None:
    if (
        (val_id := args.graph.nodes[args.n_id].get("value_id"))
        and (symbol := args.graph.nodes[val_id].get("symbol"))
        and (ret_val := get_return_literal(args.graph, val_id, symbol))
    ):
        args.graph.nodes[val_id].update(
            {
                "label_type": "Literal",
                "value": ret_val,
            },
        )
