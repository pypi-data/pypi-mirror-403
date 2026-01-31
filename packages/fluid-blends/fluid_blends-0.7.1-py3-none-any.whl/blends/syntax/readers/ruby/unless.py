from blends.models import (
    NId,
)
from blends.syntax.builders.if_statement import (
    build_if_node,
)
from blends.syntax.builders.literal import build_literal_node
from blends.syntax.models import (
    SyntaxGraphArgs,
)


def reader(args: SyntaxGraphArgs) -> NId:
    graph = args.ast_graph
    n_attrs = graph.nodes[args.n_id]

    condition_id = n_attrs.get("label_field_condition")
    if not condition_id:
        return build_literal_node(args, "unless", "unless")

    false_id = n_attrs.get("label_field_body")

    return build_if_node(args, condition_id, None, false_id)
