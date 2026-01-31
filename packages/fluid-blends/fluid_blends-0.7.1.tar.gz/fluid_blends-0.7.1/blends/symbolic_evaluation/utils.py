from collections.abc import (
    Iterator,
)

from blends.ctx import ctx
from blends.models import (
    Graph,
    NId,
)
from blends.query import (
    adj_cfg,
    lookup_first_cfg_parent,
    matching_nodes,
    pred_ast,
    pred_cfg,
    search_pred_until_type,
)
from blends.symbolic_evaluation.models import (
    Path,
)


def iter_backward_paths(graph: Graph, cfg_n_id: NId) -> Iterator[Path]:
    path = [cfg_n_id]
    parents = pred_cfg(graph, cfg_n_id)

    if not parents:
        yield path

    for parent in parents:
        for sub_path in iter_backward_paths(graph, parent):
            yield path + sub_path


def get_backward_paths(graph: Graph, n_id: NId) -> Iterator[Path]:
    cfg_id = lookup_first_cfg_parent(graph, n_id)
    paths_gen = iter_backward_paths(graph, cfg_id)
    if limit := ctx.recursion_limit:
        it_count = 1
        while it_count < limit:
            try:
                yield next(paths_gen)
                it_count += 1
            except StopIteration:
                return
    else:
        yield from paths_gen


def iter_forward_paths(graph: Graph, cfg_id: NId) -> Iterator[Path]:
    path = [cfg_id]
    childs = adj_cfg(graph, cfg_id)

    if not childs:
        yield path

    for child in childs:
        for sub_path in iter_forward_paths(graph, child):
            yield path + sub_path


def get_forward_paths(graph: Graph, n_id: NId) -> Iterator[Path]:
    cfg_id = lookup_first_cfg_parent(graph, n_id)
    yield from iter_forward_paths(graph, cfg_id)


def get_lookup_path(graph: Graph, path: Path, symbol_id: NId) -> Path:
    cfg_parent = lookup_first_cfg_parent(graph, symbol_id)
    cfg_parent_idx = path.index(cfg_parent)  # current instruction idx
    return path[cfg_parent_idx + 1 :]  # from previous instruction idx


def get_object_identifiers(graph: Graph, obj_names: set[str]) -> list[str]:
    return [
        var_name
        for n_id in matching_nodes(graph, label_type="ObjectCreation")
        if graph.nodes[n_id].get("name") in obj_names
        and (pred := pred_ast(graph, n_id)[0])
        and graph.nodes[pred].get("label_type") == "VariableDeclaration"
        and (var_name := graph.nodes[pred].get("variable"))
    ]


def get_current_class(graph: Graph, n_id: str) -> NId:
    return class_nids[0] if (class_nids := search_pred_until_type(graph, n_id, {"Class"})) else n_id
