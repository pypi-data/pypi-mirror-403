from blends.models import (
    NId,
)
from blends.query import (
    adj_ast,
)
from blends.syntax.builders.for_statement import (
    build_for_statement_node,
)
from blends.syntax.models import (
    SyntaxGraphArgs,
)


def reader(args: SyntaxGraphArgs) -> NId:
    graph = args.ast_graph
    n_attrs = graph.nodes[args.n_id]
    body_id = n_attrs["label_field_body"]
    children = adj_ast(graph, args.n_id)
    var_node: NId | None = None
    condition_node: NId | None = None
    for child in children:
        if graph.nodes[child]["label_type"] == "range_clause":
            var_node = graph.nodes[child].get("label_field_left")
            condition_node = graph.nodes[child].get("label_field_right")

    return build_for_statement_node(args, var_node, condition_node, None, body_id)
