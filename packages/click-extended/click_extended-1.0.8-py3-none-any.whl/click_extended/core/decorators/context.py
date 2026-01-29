"""`ParentNode` to inject the context into the function."""

# pylint: disable=redefined-builtin
# pylint: disable=redefined-outer-name

from typing import Any

from click_extended.core.nodes.parent_node import ParentNode
from click_extended.core.other.context import Context as Ctx
from click_extended.types import Decorator


class Context(ParentNode):
    """`ParentNode` to inject the context into the function."""

    def load(self, context: Ctx, *args: Any, **kwargs: Any) -> Ctx:
        return context


def context(
    name: str = "ctx",
    param: str | None = None,
    help: str | None = None,
    tags: str | list[str] | None = None,
    **kwargs: Any,
) -> Decorator:
    """
    A `ParentNode` to inject the context into the function.

    Type: `ParentNode`

    Args:
        name (str, optional):
            Internal node name (must be snake_case). Defaults
            to "ctx".
        param (str, optional):
            The parameter name to inject into the function.
            If not provided, uses `name` (or derived name).
        help (str, optional):
            Help text for this parameter.
        tags (str | list[str], optional):
            Tag(s) to associate with this parameter for grouping.
        **kwargs (Any):
            Additional keyword arguments.

    Returns:
        Callable:
            A decorator function that registers the context parent node.
    """
    return Context.as_decorator(
        name=name,
        param=param,
        help=help,
        tags=tags,
        **kwargs,
    )
