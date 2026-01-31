import logging
from collections.abc import Callable

from blends.models import (
    Graph,
    GraphDB,
    NId,
)
from blends.symbolic_evaluation.cases import (
    argument,
    argument_list,
    assignment,
    binary_operation,
    element_access,
    else_clause,
    execution_block,
    for_each_statement,
    for_statement,
    general_evaluator,
    if_statement,
    import_statement,
    literal,
    member_access,
    method_declaration,
    method_invocation,
    named_argument,
    new_expression,
    not_dangerous,
    object_creation,
    object_node,
    pair,
    parameter,
    parenthesized_expression,
    return_node,
    spread_element,
    symbol_lookup,
    ternary_operation,
    try_statement,
    unary_expression,
    using_statement,
    variable_declaration,
    while_statement,
)
from blends.symbolic_evaluation.dispatcher import (
    generic,
    register_evaluators,
)
from blends.symbolic_evaluation.models import (
    MissingSymbolicEvalError,
    Path,
    SymbolicEvalArgs,
    SymbolicEvaluation,
)
from blends.symbolic_evaluation.utils import get_backward_paths

LOGGER = logging.getLogger(__name__)

register_evaluators(
    {
        "Annotation": not_dangerous.evaluate,
        "Argument": argument.evaluate,
        "ArgumentList": argument_list.evaluate,
        "ArrayInitializer": general_evaluator.evaluate,
        "Assignment": assignment.evaluate,
        "Attribute": not_dangerous.evaluate,
        "AwaitExpression": general_evaluator.evaluate,
        "BinaryOperation": binary_operation.evaluate,
        "Break": not_dangerous.evaluate,
        "CatchClause": not_dangerous.evaluate,
        "CatchDeclaration": not_dangerous.evaluate,
        "Comment": not_dangerous.evaluate,
        "Continue": not_dangerous.evaluate,
        "Class": not_dangerous.evaluate,
        "ClassBody": not_dangerous.evaluate,
        "Debugger": not_dangerous.evaluate,
        "DeclarationBlock": not_dangerous.evaluate,
        "DoStatement": not_dangerous.evaluate,
        "ElementAccess": element_access.evaluate,
        "ElseClause": else_clause.evaluate,
        "ExecutionBlock": execution_block.evaluate,
        "Export": not_dangerous.evaluate,
        "ExpressionStatement": general_evaluator.evaluate,
        "File": not_dangerous.evaluate,
        "FinallyClause": not_dangerous.evaluate,
        "ForEachStatement": for_each_statement.evaluate,
        "ForStatement": for_statement.evaluate,
        "If": if_statement.evaluate,
        "Import": import_statement.evaluate,
        "JsxElement": not_dangerous.evaluate,
        "Literal": literal.evaluate,
        "MemberAccess": member_access.evaluate,
        "MethodDeclaration": method_declaration.evaluate,
        "MethodInvocation": method_invocation.evaluate,
        "MissingNode": not_dangerous.evaluate,
        "Modifiers": general_evaluator.evaluate,
        "ModuleImport": not_dangerous.evaluate,
        "NamedArgument": named_argument.evaluate,
        "Namespace": not_dangerous.evaluate,
        "NewExpression": new_expression.evaluate,
        "Object": object_node.evaluate,
        "ObjectCreation": object_creation.evaluate,
        "Pair": pair.evaluate,
        "Parameter": parameter.evaluate,
        "ParameterList": general_evaluator.evaluate,
        "ParenthesizedExpression": parenthesized_expression.evaluate,
        "ReservedWord": not_dangerous.evaluate,
        "RestPattern": not_dangerous.evaluate,
        "Return": return_node.evaluate,
        "Selector": not_dangerous.evaluate,
        "SpreadElement": spread_element.evaluate,
        "SwitchBody": general_evaluator.evaluate,
        "SwitchSection": general_evaluator.evaluate,
        "SwitchStatement": general_evaluator.evaluate,
        "SymbolLookup": symbol_lookup.evaluate,
        "TernaryOperation": ternary_operation.evaluate,
        "TryStatement": try_statement.evaluate,
        "This": not_dangerous.evaluate,
        "ThrowStatement": general_evaluator.evaluate,
        "TypeOf": not_dangerous.evaluate,
        "UnaryExpression": unary_expression.evaluate,
        "UsingStatement": using_statement.evaluate,
        "VariableDeclaration": variable_declaration.evaluate,
        "WhileStatement": while_statement.evaluate,
        "Yield": not_dangerous.evaluate,
    }
)


def evaluate(
    graph: Graph,
    path: Path,
    n_id: NId,
    graph_db: GraphDB | None = None,
    method_evaluators: dict[str, Callable[[SymbolicEvalArgs], SymbolicEvaluation]] | None = None,
) -> SymbolicEvaluation | None:
    try:
        evaluation: dict[NId, bool] = {}
        return generic(
            SymbolicEvalArgs(
                evaluation,
                graph,
                path,
                n_id,
                set(),
                graph_db,
                method_evaluators,
            ),
        )
    except MissingSymbolicEvalError:
        LOGGER.exception("Missing symbolic evaluator in %s", path)
        return None


def get_node_evaluation_results(  # noqa: PLR0913
    graph: Graph,
    n_id: NId,
    triggers_goal: set[str],
    *,
    danger_goal: bool = True,
    graph_db: GraphDB | None = None,
    method_evaluators: dict[str, Callable[[SymbolicEvalArgs], SymbolicEvaluation]] | None = None,
) -> bool:
    for path in get_backward_paths(graph, n_id):
        evaluation = evaluate(graph, path, n_id, graph_db, method_evaluators)
        if evaluation and evaluation.danger == danger_goal and evaluation.triggers == triggers_goal:
            return True
    return False
