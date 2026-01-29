"""Check if a value matches a regex pattern."""

import re
from typing import Any, Union

from click_extended.core.nodes.child_node import ChildNode
from click_extended.core.other.context import Context
from click_extended.types import Decorator


class Regex(ChildNode):
    """Check if a value matches a regex pattern."""

    def handle_str(
        self,
        value: str,
        context: Context,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        patterns: tuple[Union[str, re.Pattern[str]], ...] = kwargs["patterns"]
        flags: int = kwargs.get("flags", 0)

        for pattern in patterns:
            compiled_pattern: re.Pattern[str]
            if isinstance(pattern, re.Pattern):
                compiled_pattern = pattern
            else:
                compiled_pattern = re.compile(pattern, flags)

            if compiled_pattern.fullmatch(value):
                return value

        pattern_strs: list[str] = [
            p.pattern if isinstance(p, re.Pattern) else p for p in patterns
        ]
        raise ValueError(
            f"Value '{value}' does not match any "
            + f"of the patterns: {pattern_strs}"
        )


def regex(*patterns: Union[str, re.Pattern[str]], flags: int = 0) -> Decorator:
    """
    Check if a value matches a regex pattern.

    Type: `ChildNode`

    Supports: `str`

    Args:
        *patterns (Union[str, Pattern[str]]):
            The regex patterns to check against. Can be strings or compiled
            Pattern objects. If strings are provided, they will be compiled
            with the specified flags.
        flags (int):
            Regex flags to use when compiling string patterns (e.g.,
            re.IGNORECASE, re.MULTILINE). Ignored for pre-compiled patterns.
            Default is 0 (no flags).

    Returns:
        Decorator:
            The decorated function.
    """
    return Regex.as_decorator(patterns=patterns, flags=flags)
