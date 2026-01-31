import re
from collections import (
    ChainMap,
)

from blends.ctx import ctx
from blends.models import (
    Graph,
    GraphDB,
    Language,
    NId,
)
from blends.query import (
    adj_ast,
    match_ast_group_d,
)
from blends.symbolic_evaluation.context.search import (
    definition_search,
)
from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
)
from blends.symbolic_evaluation.utils import (
    get_backward_paths,
    get_current_class,
)


def is_symbol_literal(graph: Graph, n_id: NId) -> bool:
    searched_symbol = graph.nodes[n_id].get("symbol")

    if not searched_symbol:
        return False

    var_values = set()
    for path in get_backward_paths(graph, n_id):
        if not (
            (var_def_id := definition_search(graph, path, searched_symbol))
            and (val_id := graph.nodes[var_def_id].get("value_id"))
        ):
            return False

        if graph.nodes[val_id]["label_type"] == "Literal":
            var_values.add(val_id)
        elif (
            graph.nodes[val_id]["label_type"] == "MethodInvocation"
            and (al_id := graph.nodes[val_id].get("arguments_id"))
            and (args_ids := adj_ast(graph, al_id))
            and is_symbol_literal(graph, args_ids[0])
        ):
            var_values.add(args_ids[0])
        else:
            return False

    return len(var_values) == 1


def method_returns_literals(graph: Graph, method_id: NId) -> bool:
    return_nodes = match_ast_group_d(graph, method_id, "Return", -1)
    if all(
        (val_id := graph.nodes[_id].get("value_id"))
        and graph.nodes[val_id]["label_type"] == "Literal"
        for _id in return_nodes
    ):
        return True

    if (  # noqa: SIM103
        len(return_nodes) == 1
        and (val_id := graph.nodes[return_nodes[0]].get("value_id"))
        and is_symbol_literal(graph, val_id)
    ):
        return True

    return False


def evaluate_file(
    args: SymbolicEvalArgs,
    obj_construct: str,
    file: str,
    struct: dict,  # type: ignore [type-arg]
) -> tuple[bool, bool]:
    danger = False
    n_attrs = args.graph.nodes[args.n_id]
    if args.graph_db and obj_construct in struct:
        graph = shard.syntax_graph if (shard := args.graph_db.get_path_shard(file)) else None
        if not graph:
            return (danger, True)
        class_data = struct[obj_construct]["data"]
        method_id = class_data[n_attrs["expression"]]["node"]
        if return_nodes := match_ast_group_d(graph, method_id, "Return", -1):
            danger = any(
                generic(args.fork_n_id(node, path, graph)).danger
                for node in return_nodes
                for path in get_backward_paths(graph, node)
            )

        if method_returns_literals(graph, method_id):
            return (danger, False)
    return (danger, True)


def evaluate_method_extern_file(
    args: SymbolicEvalArgs,
    lang: Language,
    obj_instance: dict,  # type: ignore [type-arg]
    graph_db: GraphDB,
) -> tuple[bool, bool]:
    lang_context = graph_db.context[lang]
    obj_source = obj_instance["source"]

    working_dir = f"{ctx.working_dir}/"
    if obj_source.startswith(working_dir):
        obj_source = re.sub(working_dir, "", obj_source)

    if obj_instance["source_type"] == "package" and (
        source_context := lang_context.get(obj_source)
    ):
        for file, struct in source_context.items():
            return evaluate_file(
                args,
                obj_instance["object"],
                file,
                struct,
            )
    else:
        file_structures = dict(ChainMap(*lang_context.values()))
        if struct := file_structures.get(obj_source):
            return evaluate_file(
                args,
                obj_instance["object"],
                obj_source,
                struct,
            )
    return (False, True)


def evaluate_method_invocation(
    args: SymbolicEvalArgs,
    lang: Language,
) -> tuple[bool, bool]:
    graph = args.graph
    n_attrs = graph.nodes[args.n_id]
    metadata_node = graph.nodes["0"]
    current_class = graph.nodes[get_current_class(graph, args.n_id)]["name"]
    if not args.graph_db:
        return (False, True)

    if not (obj_id := n_attrs.get("object_id")):
        if (
            (expr_method := n_attrs.get("expression"))
            and (class_methods := metadata_node["structure"].get(current_class, {}).get("data"))
            and (invocation_id := class_methods.get(expr_method, {}).get("node"))
        ):
            danger = any(
                generic(args.fork_n_id(node, path, graph)).danger
                for node in match_ast_group_d(graph, invocation_id, "Return", -1)
                for path in get_backward_paths(graph, node)
            )
            return (danger, not method_returns_literals(graph, invocation_id))
        return (False, True)

    if (
        (class_name := graph.nodes[obj_id].get("name"))
        and (
            class_methods := metadata_node["structure"]
            .get(current_class, {})
            .get("data", {})
            .get(class_name, {})
            .get("data")
        )
        and (expr_method := n_attrs.get("expression"))
        and (invocation_id := class_methods.get(expr_method, {}).get("node"))
    ):
        danger = any(
            generic(args.fork_n_id(node, path, graph)).danger
            for node in match_ast_group_d(graph, invocation_id, "Return", -1)
            for path in get_backward_paths(graph, node)
        )
        return (danger, not method_returns_literals(graph, invocation_id))

    if (
        (object_method := graph.nodes[obj_id].get("symbol"))
        and (class_instances := metadata_node["instances"].get(current_class))
        and (obj_instance := class_instances.get(object_method))
    ):
        return evaluate_method_extern_file(args, lang, obj_instance, args.graph_db)

    return (False, True)
