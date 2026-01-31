from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import NoReturn

from blends.stack.criteria import (
    is_endpoint,
    is_jump_to_boundary,
)
from blends.stack.node_kinds import StackGraphNodeKind
from blends.stack.partial_path.errors import (
    PartialPathResolutionError,
    _raise_incorrect_popped_symbol,
    _raise_missing_attached_scope_list,
    _raise_symbol_stack_unsatisfied,
    _raise_unexpected_attached_scope_list,
    _raise_unknown_attached_scope,
)
from blends.stack.partial_path.partial_path import PartialPath
from blends.stack.partial_path.partial_stacks import (
    PartialScopedSymbol,
    PartialScopeStack,
    PartialSymbolStack,
)
from blends.stack.partial_path.stack_conditions import (
    StackConditions,
    create_seed_path,
)
from blends.stack.partial_path.variables import ScopeStackVariable
from blends.stack.selection import PartialPathEdge
from blends.stack.stacks import (
    ScopeStackNode,
    StackState,
    SymbolStackNode,
)
from blends.stack.transitions import apply_node
from blends.stack.view import StackGraphView


@dataclass(frozen=True, slots=True)
class PartialPathLimits:
    max_work_per_phase: int | None = None
    enable_dedupe: bool = True
    enable_cycle_guard: bool = True


@dataclass(slots=True)
class PerFilePartialPathStats:
    seed_count: int = 0
    explored_count: int = 0
    accepted_count: int = 0
    deduped_count: int = 0
    discarded_count: int = 0
    max_queue_size: int = 0
    limit_hits: dict[str, int] = field(default_factory=dict)
    length_histogram: dict[int, int] = field(default_factory=dict)

    def record_length(self, length: int) -> None:
        self.length_histogram[length] = self.length_histogram.get(length, 0) + 1

    def mark_limit_hit(self, name: str) -> None:
        self.limit_hits[name] = self.limit_hits.get(name, 0) + 1


@dataclass(slots=True)
class PerFilePartialPaths:
    paths: tuple[PartialPath, ...]
    stats: PerFilePartialPathStats


def _collect_seed_nodes(view: StackGraphView, file_path: str) -> list[int]:
    file_nodes = view.file_to_nodes.get(file_path, frozenset())
    seeds = [
        node_index
        for node_index in file_nodes
        if is_endpoint(view, node_index) or is_jump_to_boundary(view, node_index)
    ]
    if 0 not in seeds:
        seeds.append(0)
    return sorted(seeds)


def _build_scope_stack(scopes: tuple[int, ...]) -> ScopeStackNode | None:
    tail: ScopeStackNode | None = None
    for scope_index in reversed(scopes):
        tail = ScopeStackNode(scope_index=scope_index, tail=tail)
    return tail


def _build_symbol_stack(
    symbols: tuple[PartialScopedSymbol, ...],
) -> tuple[SymbolStackNode | None, bool]:
    tail: SymbolStackNode | None = None
    for symbol in reversed(symbols):
        scopes = symbol.scopes
        if scopes is None:
            scopes_node = None
        else:
            if scopes.variable is not None:
                return None, False
            scopes_node = _build_scope_stack(scopes.scopes)
        tail = SymbolStackNode(symbol_id=symbol.symbol_id, scopes=scopes_node, tail=tail)
    return tail, True


def _build_concrete_state(
    symbol_stack: PartialSymbolStack, scope_stack: PartialScopeStack
) -> StackState | None:
    if symbol_stack.variable is not None or scope_stack.variable is not None:
        return None
    symbol_node, symbol_is_concrete = _build_symbol_stack(symbol_stack.symbols)
    if not symbol_is_concrete:
        return None
    scope_node = _build_scope_stack(scope_stack.scopes)
    return StackState(symbol_stack=symbol_node, scope_stack=scope_node)


def _can_apply_transition(
    view: StackGraphView,
    node_index: int,
    symbol_stack: PartialSymbolStack,
    scope_stack: PartialScopeStack,
) -> bool:
    state = _build_concrete_state(symbol_stack, scope_stack)
    if state is None:
        return True
    result = apply_node(view, node_index, state)
    return result.error is None


def _pop_symbol_stack(
    symbol_stack: PartialSymbolStack,
) -> tuple[PartialScopedSymbol | None, PartialSymbolStack]:
    if not symbol_stack.symbols:
        return None, symbol_stack
    head = symbol_stack.symbols[0]
    tail = PartialSymbolStack(symbols=symbol_stack.symbols[1:], variable=symbol_stack.variable)
    return head, tail


def _push_symbol_front(
    symbol_stack: PartialSymbolStack,
    symbol: PartialScopedSymbol,
) -> PartialSymbolStack:
    return PartialSymbolStack(
        symbols=(symbol, *symbol_stack.symbols), variable=symbol_stack.variable
    )


def _push_symbol_back(
    symbol_stack: PartialSymbolStack,
    symbol: PartialScopedSymbol,
) -> PartialSymbolStack:
    return PartialSymbolStack(
        symbols=(*symbol_stack.symbols, symbol), variable=symbol_stack.variable
    )


def _push_scope_front(scope_stack: PartialScopeStack, scope_index: int) -> PartialScopeStack:
    return PartialScopeStack(
        scopes=(scope_index, *scope_stack.scopes), variable=scope_stack.variable
    )


def _fresh_scope_stack_variable(stacks: StackConditions) -> ScopeStackVariable:
    max_var = max(
        stacks.symbol_pre.largest_scope_stack_var(),
        stacks.symbol_post.largest_scope_stack_var(),
        stacks.scope_pre.largest_scope_stack_var(),
        stacks.scope_post.largest_scope_stack_var(),
    )
    return ScopeStackVariable(var_id=max_var + 1)


def _symbol_stack_unsatisfied() -> NoReturn:
    _raise_symbol_stack_unsatisfied()


def _append_drop_scopes(
    _view: StackGraphView, _node_index: int, stacks: StackConditions
) -> StackConditions:
    return StackConditions(
        symbol_pre=stacks.symbol_pre,
        symbol_post=stacks.symbol_post,
        scope_pre=stacks.scope_pre,
        scope_post=PartialScopeStack.empty(),
    )


def _append_pop_scoped_symbol(
    view: StackGraphView, node_index: int, stacks: StackConditions
) -> StackConditions:
    symbol_id = view.symbol_id_at(node_index)
    if symbol_id is None:
        _raise_incorrect_popped_symbol()
    popped, symbol_post = _pop_symbol_stack(stacks.symbol_post)
    if popped is not None:
        if popped.symbol_id != symbol_id:
            _raise_incorrect_popped_symbol()
        if popped.scopes is None:
            _raise_missing_attached_scope_list()
        return StackConditions(
            symbol_pre=stacks.symbol_pre,
            symbol_post=symbol_post,
            scope_pre=stacks.scope_pre,
            scope_post=popped.scopes,
        )
    if stacks.symbol_post.has_variable():
        scope_var = _fresh_scope_stack_variable(stacks)
        attached_scopes = PartialScopeStack.from_variable(scope_var)
        symbol_pre = _push_symbol_back(
            stacks.symbol_pre,
            PartialScopedSymbol(symbol_id=symbol_id, scopes=attached_scopes),
        )
        return StackConditions(
            symbol_pre=symbol_pre,
            symbol_post=symbol_post,
            scope_pre=stacks.scope_pre,
            scope_post=PartialScopeStack.from_variable(scope_var),
        )
    return _symbol_stack_unsatisfied()


def _append_pop_symbol(
    view: StackGraphView, node_index: int, stacks: StackConditions
) -> StackConditions:
    symbol_id = view.symbol_id_at(node_index)
    if symbol_id is None:
        _raise_incorrect_popped_symbol()
    popped, symbol_post = _pop_symbol_stack(stacks.symbol_post)
    if popped is not None:
        if popped.symbol_id != symbol_id:
            _raise_incorrect_popped_symbol()
        if popped.scopes is not None:
            _raise_unexpected_attached_scope_list()
        return StackConditions(
            symbol_pre=stacks.symbol_pre,
            symbol_post=symbol_post,
            scope_pre=stacks.scope_pre,
            scope_post=stacks.scope_post,
        )
    if stacks.symbol_post.has_variable():
        symbol_pre = _push_symbol_back(
            stacks.symbol_pre, PartialScopedSymbol(symbol_id=symbol_id, scopes=None)
        )
        return StackConditions(
            symbol_pre=symbol_pre,
            symbol_post=symbol_post,
            scope_pre=stacks.scope_pre,
            scope_post=stacks.scope_post,
        )
    return _symbol_stack_unsatisfied()


def _append_push_scoped_symbol(
    view: StackGraphView, node_index: int, stacks: StackConditions
) -> StackConditions:
    symbol_id = view.symbol_id_at(node_index)
    scope_index = view.scope_index_at(node_index)
    if symbol_id is None:
        _raise_incorrect_popped_symbol()
    if scope_index is None:
        _raise_unknown_attached_scope()
    attached_scopes = _push_scope_front(stacks.scope_post, scope_index)
    symbol_post = _push_symbol_front(
        stacks.symbol_post,
        PartialScopedSymbol(symbol_id=symbol_id, scopes=attached_scopes),
    )
    return StackConditions(
        symbol_pre=stacks.symbol_pre,
        symbol_post=symbol_post,
        scope_pre=stacks.scope_pre,
        scope_post=stacks.scope_post,
    )


def _append_push_symbol(
    view: StackGraphView, node_index: int, stacks: StackConditions
) -> StackConditions:
    symbol_id = view.symbol_id_at(node_index)
    if symbol_id is None:
        _raise_incorrect_popped_symbol()
    symbol_post = _push_symbol_front(
        stacks.symbol_post,
        PartialScopedSymbol(symbol_id=symbol_id, scopes=None),
    )
    return StackConditions(
        symbol_pre=stacks.symbol_pre,
        symbol_post=symbol_post,
        scope_pre=stacks.scope_pre,
        scope_post=stacks.scope_post,
    )


_APPEND_BY_KIND: dict[str, Callable[[StackGraphView, int, StackConditions], StackConditions]] = {
    StackGraphNodeKind.DROP_SCOPES.value: _append_drop_scopes,
    StackGraphNodeKind.POP_SCOPED_SYMBOL.value: _append_pop_scoped_symbol,
    StackGraphNodeKind.POP_SYMBOL.value: _append_pop_symbol,
    StackGraphNodeKind.PUSH_SCOPED_SYMBOL.value: _append_push_scoped_symbol,
    StackGraphNodeKind.PUSH_SYMBOL.value: _append_push_symbol,
}


def _append_node_to_partial_stacks(
    view: StackGraphView, node_index: int, stacks: StackConditions
) -> StackConditions:
    kind = view.kind_at(node_index)
    handler = _APPEND_BY_KIND.get(kind)
    if handler is None:
        return stacks
    return handler(view, node_index, stacks)


def _extend_path_with_edge(
    view: StackGraphView,
    current_path: PartialPath,
    sink_node_index: int,
    precedence: int,
    *,
    record_edges: bool,
) -> PartialPath:
    stacks = _append_node_to_partial_stacks(
        view,
        sink_node_index,
        StackConditions(
            symbol_pre=current_path.symbol_stack_precondition,
            symbol_post=current_path.symbol_stack_postcondition,
            scope_pre=current_path.scope_stack_precondition,
            scope_post=current_path.scope_stack_postcondition,
        ),
    )
    if record_edges:
        edges = (
            *current_path.edges,
            PartialPathEdge(source_node_index=current_path.end_node_index, precedence=precedence),
        )
    else:
        edges = current_path.edges
    return PartialPath(
        start_node_index=current_path.start_node_index,
        end_node_index=sink_node_index,
        symbol_stack_precondition=stacks.symbol_pre,
        symbol_stack_postcondition=stacks.symbol_post,
        scope_stack_precondition=stacks.scope_pre,
        scope_stack_postcondition=stacks.scope_post,
        edges=edges,
    )


def _should_accept_path(view: StackGraphView, path: PartialPath, file_path: str) -> bool:
    if not (
        is_endpoint(view, path.start_node_index) or is_jump_to_boundary(view, path.start_node_index)
    ):
        return False
    file_nodes = view.file_to_nodes.get(file_path, frozenset())
    return (
        path.end_node_index in file_nodes and is_endpoint(view, path.end_node_index)
    ) or is_jump_to_boundary(view, path.end_node_index)


@dataclass(slots=True)
class _ExpansionContext:
    view: StackGraphView
    file_path: str
    limits: PartialPathLimits
    stats: PerFilePartialPathStats
    accepted_paths: list[PartialPath]
    seen_paths: set[
        tuple[
            int,
            int,
            PartialSymbolStack,
            PartialSymbolStack,
            PartialScopeStack,
            PartialScopeStack,
        ]
    ]
    seen_states: set[tuple[int, int, PartialSymbolStack, PartialScopeStack]]
    queue: deque[tuple[PartialPath, int]]
    record_edges: bool


def _process_current_path(
    context: _ExpansionContext, current_path: PartialPath, current_length: int
) -> int:
    if current_length > 0 and _should_accept_path(context.view, current_path, context.file_path):
        path_key = (
            current_path.start_node_index,
            current_path.end_node_index,
            current_path.symbol_stack_precondition,
            current_path.symbol_stack_postcondition,
            current_path.scope_stack_precondition,
            current_path.scope_stack_postcondition,
        )
        if context.limits.enable_dedupe and path_key in context.seen_paths:
            context.stats.deduped_count += 1
            return 0
        context.seen_paths.add(path_key)
        context.accepted_paths.append(current_path)
        context.stats.accepted_count += 1
        context.stats.record_length(current_length)
        return 0

    if context.limits.enable_cycle_guard:
        state_key = (
            current_path.start_node_index,
            current_path.end_node_index,
            current_path.symbol_stack_postcondition,
            current_path.scope_stack_postcondition,
        )
        if state_key in context.seen_states:
            context.stats.discarded_count += 1
            return 0
        context.seen_states.add(state_key)

    outgoing_edges = context.view.outgoing[current_path.end_node_index]
    for sink_node_index, precedence in outgoing_edges:
        if not _can_apply_transition(
            context.view,
            sink_node_index,
            current_path.symbol_stack_postcondition,
            current_path.scope_stack_postcondition,
        ):
            context.stats.discarded_count += 1
            continue
        try:
            extended_path = _extend_path_with_edge(
                context.view,
                current_path,
                sink_node_index,
                precedence,
                record_edges=context.record_edges,
            )
            context.queue.append((extended_path, current_length + 1))
        except PartialPathResolutionError:
            context.stats.discarded_count += 1
            continue

    return len(outgoing_edges)


def compute_minimal_partial_paths_in_file(
    view: StackGraphView,
    file_path: str,
    *,
    limits: PartialPathLimits | None = None,
    record_edges: bool = False,
) -> PerFilePartialPaths:
    if limits is None:
        limits = PartialPathLimits()
    stats = PerFilePartialPathStats()
    accepted_paths: list[PartialPath] = []
    seen_paths: set[
        tuple[
            int,
            int,
            PartialSymbolStack,
            PartialSymbolStack,
            PartialScopeStack,
            PartialScopeStack,
        ]
    ] = set()
    seen_states: set[tuple[int, int, PartialSymbolStack, PartialScopeStack]] = set()

    seed_nodes = _collect_seed_nodes(view, file_path)
    stats.seed_count = len(seed_nodes)

    queue: deque[tuple[PartialPath, int]] = deque()
    for seed_node_index in seed_nodes:
        seed_path = create_seed_path(view, seed_node_index)
        queue.append((seed_path, 0))

    context = _ExpansionContext(
        view=view,
        file_path=file_path,
        limits=limits,
        stats=stats,
        accepted_paths=accepted_paths,
        seen_paths=seen_paths,
        seen_states=seen_states,
        queue=queue,
        record_edges=record_edges,
    )

    work_performed = 0
    while queue:
        stats.max_queue_size = max(stats.max_queue_size, len(queue))

        if limits.max_work_per_phase is not None and work_performed >= limits.max_work_per_phase:
            stats.mark_limit_hit("max_work_per_phase")
            break

        current_path, current_length = queue.popleft()
        stats.explored_count += 1
        candidate_count = _process_current_path(context, current_path, current_length)
        work_performed += candidate_count

    return PerFilePartialPaths(paths=tuple(accepted_paths), stats=stats)
