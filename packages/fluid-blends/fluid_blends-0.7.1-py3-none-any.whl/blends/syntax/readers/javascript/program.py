from blends.models import (
    Graph,
    NId,
)
from blends.query import (
    adj_ast,
)
from blends.syntax.builders.file import (
    build_file_node,
)
from blends.syntax.models import (
    SyntaxGraphArgs,
)


def get_filtered_node(ast_graph: Graph, c_id: NId) -> NId:
    if ast_graph.nodes[c_id]["label_type"] == "expression_statement":
        return adj_ast(ast_graph, c_id)[0]
    return c_id


def reader(args: SyntaxGraphArgs) -> NId:
    c_ids = [
        c_id
        for n_id in adj_ast(args.ast_graph, args.n_id)
        if args.ast_graph.nodes[n_id].get("label_type") != "empty_statement"
        and (c_id := get_filtered_node(args.ast_graph, n_id))
    ]

    return build_file_node(args, c_ids)
