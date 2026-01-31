from blends.models import (
    NId,
)
from blends.query import pred_ast
from blends.syntax.builders.parameter import (
    build_parameter_node,
)
from blends.syntax.builders.symbol_lookup import (
    build_symbol_lookup_node,
)
from blends.syntax.models import (
    SyntaxGraphArgs,
)
from blends.utilities.text_nodes import (
    node_to_str,
)


def reader(args: SyntaxGraphArgs) -> NId:
    symbol = node_to_str(args.ast_graph, args.n_id)
    parent_id = pred_ast(args.ast_graph, args.n_id)[0]
    if args.ast_graph.nodes[parent_id]["label_type"] == "inferred_parameters":
        return build_parameter_node(args=args, variable=symbol, variable_type=None, value_id=None)
    return build_symbol_lookup_node(args, symbol)
