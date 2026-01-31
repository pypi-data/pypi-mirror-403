from blends.models import (
    Graph,
    NId,
)
from blends.query import (
    adj_ast,
    match_ast_d,
    match_ast_group_d,
    pred,
)
from blends.syntax.builders.method_invocation import (
    build_method_invocation_node,
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

SELECTORS_FOR_THREE_PART_INVOCATION = 3
SELECTORS_FOR_TWO_PART_INVOCATION = 2


def _try_build_chained_method_invocation(
    args: SyntaxGraphArgs,
    symbol: str,
    selectors_ids: list[NId],
) -> NId | None:
    graph = args.ast_graph
    child_s1 = None
    child_s2 = None

    if (
        len(selectors_ids) == SELECTORS_FOR_THREE_PART_INVOCATION
        and (child_s0 := match_ast_d(graph, selectors_ids[0], "argument_part"))
        and (args_id := match_ast_d(graph, child_s0, "arguments"))
    ):
        if not match_ast_d(graph, args_id, "(") and not match_ast_d(graph, args_id, ")"):
            return build_symbol_lookup_node(args, symbol)
        child_s1 = match_ast_d(graph, selectors_ids[1], "unconditional_assignable_selector")
        child_s2 = match_ast_d(graph, selectors_ids[2], "argument_part")

    if len(selectors_ids) == SELECTORS_FOR_TWO_PART_INVOCATION:
        child_s1 = match_ast_d(graph, selectors_ids[0], "unconditional_assignable_selector")
        child_s2 = match_ast_d(graph, selectors_ids[1], "argument_part")

    if child_s1 and child_s2 and (expr_id := adj_ast(graph, child_s1)) and len(expr_id) > 1:
        expr = symbol + "." + node_to_str(graph, expr_id[1])
        args_id = match_ast_d(graph, child_s2, "arguments")
        return build_method_invocation_node(args, expr, expr_id[1], args_id, None)

    return None


def _try_build_single_selector_invocation(
    args: SyntaxGraphArgs,
    graph: Graph,
    symbol: str,
    selectors_ids: list[NId],
) -> NId | None:
    if len(selectors_ids) != 1:
        return None

    child_args = match_ast_d(graph, selectors_ids[0], "argument_part")
    if child_args:
        args_id = match_ast_d(graph, child_args, "arguments")
        return build_method_invocation_node(args, symbol, None, args_id, None)

    return None


def reader(args: SyntaxGraphArgs) -> NId:
    graph = args.ast_graph
    symbol = graph.nodes[args.n_id]["label_text"]
    pred_nid = pred(graph, args.n_id)[0]
    label_type = graph.nodes[pred_nid]["label_type"]

    selectors_ids = match_ast_group_d(graph, pred_nid, "selector")
    if not selectors_ids:
        return build_symbol_lookup_node(args, symbol)

    if label_type in {"initialized_variable_definition", "assignment_expression"} and (
        result := _try_build_chained_method_invocation(args, symbol, selectors_ids)
    ):
        return result

    if label_type in {"static_final_declaration", "initialized_variable_definition"} and (
        result := _try_build_single_selector_invocation(args, graph, symbol, selectors_ids)
    ):
        return result

    return build_symbol_lookup_node(args, symbol)
