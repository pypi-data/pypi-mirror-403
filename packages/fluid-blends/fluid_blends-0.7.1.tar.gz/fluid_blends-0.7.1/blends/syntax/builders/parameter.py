from collections.abc import (
    Iterator,
)

from blends.ctx import ctx
from blends.models import (
    NId,
)
from blends.stack.edges import (
    Edge,
    add_edge,
)
from blends.stack.node_helpers import (
    pop_symbol_node_attributes,
)
from blends.syntax.models import (
    SyntaxGraphArgs,
)


def _setup_stack_graph_parameter(args: SyntaxGraphArgs, node_id: NId, variable: str) -> None:
    if node_id not in args.syntax_graph.nodes:
        return

    args.syntax_graph.update_node(
        node_id,
        pop_symbol_node_attributes(symbol=variable, precedence=0),
    )
    scope_stack = args.metadata.setdefault("scope_stack", [])
    if scope_stack and (parent_scope := scope_stack[-1]):
        add_edge(
            args.syntax_graph,
            Edge(source=parent_scope, sink=node_id, precedence=0),
        )


def build_parameter_node(  # noqa: PLR0913
    *,
    args: SyntaxGraphArgs,
    variable: str | None,
    variable_type: str | None,
    value_id: NId | None,
    c_ids: Iterator[NId] | list[str] | None = None,
    variable_id: NId | None = None,
    modifier: NId | None = None,
) -> NId:
    _id = variable_id if variable_id else args.n_id
    args.syntax_graph.add_node(
        _id,
        label_type="Parameter",
    )

    if variable:
        args.syntax_graph.nodes[_id]["variable"] = variable

    if variable_type:
        args.syntax_graph.nodes[_id]["variable_type"] = variable_type

    if value_id:
        args.syntax_graph.nodes[_id]["value_id"] = value_id
        args.syntax_graph.add_edge(
            _id,
            args.generic(args.fork_n_id(value_id)),
            label_ast="AST",
        )

    if c_ids:
        for c_id in c_ids:
            args.syntax_graph.add_edge(
                _id,
                args.generic(args.fork_n_id(c_id)),
                label_ast="AST",
            )

    if modifier:
        args.syntax_graph.nodes[_id]["parameter_mode"] = modifier

    if ctx.has_feature_flag("StackGraph") and variable:
        _setup_stack_graph_parameter(args, _id, variable)

    return _id
