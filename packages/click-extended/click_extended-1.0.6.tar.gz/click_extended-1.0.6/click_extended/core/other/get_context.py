"""Function to get the active context."""

# pylint: disable=too-many-branches
# pylint: disable=used-before-assignment

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import click

from click_extended.core.other.context import Context

if TYPE_CHECKING:
    from click_extended.core.decorators.tag import Tag
    from click_extended.core.nodes._root_node import RootNode
    from click_extended.core.nodes.child_node import ChildNode
    from click_extended.core.nodes.node import Node
    from click_extended.core.nodes.parent_node import ParentNode


def get_context() -> Context:
    """
    Get the active context.

    Returns:
        Context:
            The active context.

    Raises:
        RuntimeError:
            If called outside a Click command or before initialization.
    """
    click_context = click.get_current_context(silent=True)
    if click_context is None:
        raise RuntimeError("No active Click context is available.")

    meta_raw = click_context.meta.get("click_extended")
    if not isinstance(meta_raw, dict) or not meta_raw:
        raise RuntimeError(
            "click-extended context has not been initialized yet."
        )

    meta: dict[str, Any] = cast(dict[str, Any], meta_raw)

    root_node = meta.get("root_node")
    if root_node is None:
        raise RuntimeError(
            "click-extended root node is not available in context."
        )

    parents: dict[str, Any] = meta.get("parents", {})
    tags: dict[str, Any] = meta.get("tags", {})
    children: dict[str, Any] = meta.get("children", {})
    globals_nodes: dict[str, Any] = meta.get("globals", {})

    if not isinstance(parents, dict):
        parents = {}
    if not isinstance(tags, dict):
        tags = {}
    if not isinstance(children, dict):
        children = {}
    if not isinstance(globals_nodes, dict):
        globals_nodes = {}

    all_nodes: dict[str, Any] = {}
    if isinstance(parents, dict):
        all_nodes.update(parents)
    if isinstance(tags, dict):
        all_nodes.update(tags)
    if isinstance(children, dict):
        all_nodes.update(children)
    if isinstance(globals_nodes, dict):
        all_nodes.update(globals_nodes)
    if root_node is not None:
        all_nodes[root_node.name] = root_node

    current_scope = meta.get("current_scope", "root")
    if current_scope not in ("root", "parent", "child"):
        current_scope = "root"
    parent_node = meta.get("parent_node")
    child_node = meta.get("child_node")

    current = None
    parent = None
    if current_scope == "root":
        current = root_node
    elif current_scope == "parent":
        current = parent_node
    elif current_scope == "child":
        current = child_node
        parent = parent_node

    return Context(
        root=cast("RootNode", root_node),
        current=cast("Node | None", current),
        parent=cast("ParentNode | Tag | None", parent),
        click_context=click_context,
        nodes=cast("dict[str, Node]", all_nodes),
        parents=cast("dict[str, ParentNode]", parents),
        tags=cast("dict[str, Tag]", tags),
        children=cast("dict[str, ChildNode]", children),
        data=meta.get("data", {}),
        debug=bool(meta.get("debug", False)),
    )
