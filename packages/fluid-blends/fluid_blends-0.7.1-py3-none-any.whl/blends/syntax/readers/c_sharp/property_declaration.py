from blends.models import (
    NId,
)
from blends.query import (
    adj_ast,
)
from blends.syntax.builders.object import (
    build_object_node,
)
from blends.syntax.models import (
    SyntaxGraphArgs,
)


def reader(args: SyntaxGraphArgs) -> NId:
    graph = args.ast_graph
    match_identifier = graph.nodes[args.n_id]["label_field_name"]
    property_name = graph.nodes[match_identifier].get("label_text")

    accessors = adj_ast(graph, args.n_id, label_type="accessor_declaration", depth=2)

    return build_object_node(args, iter(accessors), property_name)
