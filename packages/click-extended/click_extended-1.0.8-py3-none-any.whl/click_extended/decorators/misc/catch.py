"""
Validation node to catch and handle exceptions from command/group functions.
"""

import asyncio
import inspect
from functools import wraps
from typing import Any, Callable
from weakref import WeakKeyDictionary

from click_extended.core.nodes.validation_node import ValidationNode
from click_extended.core.other._tree import Tree
from click_extended.core.other.context import Context
from click_extended.types import Decorator

_catch_handlers: WeakKeyDictionary[
    Callable[..., Any],
    list[
        tuple[tuple[type[BaseException], ...], Callable[..., Any] | None, bool]
    ],
] = WeakKeyDictionary()


class Catch(ValidationNode):
    """
    Catch and handle exceptions from command/group functions.

    Wraps the decorated function in a try-except block. When an exception
    is caught, an optional handler is invoked. Without a handler, exceptions
    are silently suppressed.

    Handler signatures supported:
    - `handler()` - No arguments, just execute code
    - `handler(exception)` - Receive the exception object
    - `handler(exception, context)` - Receive exception and Context object

    Examples:
        ```py
        # Simple error logging
        @command()
        @catch(ValueError, handler=lambda: print("Invalid value!"))
        def cmd():
            raise ValueError("Bad input")
        ```

        ```py
        # Handle exception with details
        @command()
        @catch(ValueError, handler=lambda e: print(f"Error: {e}"))
        def cmd():
            raise ValueError("Count must be positive")
        ```

        ```py
        # Access context information
        @command()
        @catch(
            ValueError,
            handler=lambda e, ctx: print(f"{ctx.info_name}: {e}"),
        )
        def cmd():
            raise ValueError("Failed!")
        ```
    """

    def __init__(
        self,
        name: str,
        process_args: tuple[Any, ...] | None = None,
        process_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Catch validation node with function to wrap."""
        super().__init__(name, process_args, process_kwargs, **kwargs)
        self.wrapped_func: Callable[..., Any] | None = None

    def on_finalize(self, context: Context, *args: Any, **kwargs: Any) -> None:
        """
        Store exception handler configuration for later use.

        The actual exception catching happens when the function is invoked,
        which is done by wrapping the function in the decorator.

        Args:
            context: The execution context
            *args: Contains exception types tuple at index 0
            **kwargs: Contains handler, reraise parameters
        """


def catch(
    *exception_types: type[BaseException],
    handler: Callable[..., Any] | None = None,
    reraise: bool = False,
) -> Decorator:
    """
    Catch and handle exceptions from command/group functions.

    Wraps the function in a try-except block. When exceptions occur, an optional
    handler is invoked. If no exception types are specified, catches Exception.

    Type: `ValidationNode`

    Args:
        *exception_types: Exception types to catch (defaults to Exception)
        handler: Optional function with signature `()`, `(exception)`, or
            `(exception, context)` to handle caught exceptions
        reraise: If True, re-raise after handling (default: False)

    Returns:
        Decorator function

    Raises:
        TypeError: If exception_types contains non-exception classes

    Examples:
        ```python
        # Simple notification (no arguments)
        @command()
        @catch(ValueError, handler=lambda: print("Error occurred!"))
        def cmd():
            raise ValueError("Invalid input")
        ```

        ```python
        # Log exception details (exception argument)
        @command()
        @catch(ValueError, handler=lambda e: print(f"Error: {e}"))
        def cmd():
            raise ValueError("Count must be positive")
        ```

        ```python
        # Access context (exception + context arguments)
        @command()
        @catch(
            ValueError,
            handler=lambda e, ctx: print(f"{ctx.info_name}: {e}"),
        )
        def cmd():
            raise ValueError("Failed!")
        ```

        ```python
        # Catch multiple exception types
        @command()
        @catch(ValueError, TypeError, handler=lambda e: log_error(e))
        def cmd():
            raise ValueError("Something went wrong")
        ```

        ```python
        # Silent suppression (no handler)
        @command()
        @catch(RuntimeError)
        def cmd():
            raise RuntimeError("Silently suppressed")
        ```

        ```python
        # Log then re-raise
        @command()
        @catch(
            ValueError,
            handler=lambda e: print(f"Logging: {e}"),
            reraise=True,
        )
        def cmd():
            raise ValueError("This will be logged and re-raised")
        ```
    """
    if not exception_types:
        exception_types = (Exception,)

    for exc_type in exception_types:
        if not isinstance(exc_type, type) or not issubclass(
            exc_type, BaseException
        ):
            raise TypeError(
                f"catch() requires exception types, got {exc_type!r}"
            )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """The actual decorator that wraps the function."""

        instance = Catch(
            name="catch",
            process_args=(exception_types,),
            process_kwargs={"handler": handler, "reraise": reraise},
        )

        Tree.queue_validation(instance)

        original_func = func
        while hasattr(original_func, "__wrapped__"):
            original_func = original_func.__wrapped__  # type: ignore

        if original_func not in _catch_handlers:
            _catch_handlers[original_func] = []
        _catch_handlers[original_func].insert(
            0, (exception_types, handler, reraise)
        )

        # Only wrap if this is the first @catch (check handlers dict)
        if len(_catch_handlers[original_func]) > 1:
            return func

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*call_args: Any, **call_kwargs: Any) -> Any:
                """Async wrapper that catches exceptions."""
                try:
                    return await func(*call_args, **call_kwargs)
                except BaseException as exc:
                    for exc_types, hdlr, reraise_flag in _catch_handlers.get(
                        original_func, []
                    ):
                        if isinstance(exc, exc_types):
                            if hdlr is not None:
                                if asyncio.iscoroutinefunction(hdlr):
                                    await _call_handler_async(hdlr, exc)
                                else:
                                    _call_handler_sync(hdlr, exc)

                            if reraise_flag:
                                raise

                            return None
                    raise

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*call_args: Any, **call_kwargs: Any) -> Any:
            """Sync wrapper that catches exceptions."""
            try:
                return func(*call_args, **call_kwargs)
            except BaseException as exc:
                for exc_types, hdlr, reraise_flag in _catch_handlers.get(
                    original_func, []
                ):
                    if isinstance(exc, exc_types):
                        if hdlr is not None:
                            if asyncio.iscoroutinefunction(hdlr):
                                asyncio.run(_call_handler_async(hdlr, exc))
                            else:
                                _call_handler_sync(hdlr, exc)

                        if reraise_flag:
                            raise

                        return None
                raise

        return sync_wrapper

    return decorator


async def _call_handler_async(
    handler: Callable[..., Any], exc: BaseException
) -> Any:
    """Call async handler with appropriate number of arguments."""
    sig = inspect.signature(handler)
    params = list(sig.parameters.values())

    if len(params) == 0:
        return await handler()
    if len(params) == 1:
        return await handler(exc)

    import click

    try:
        ctx = click.get_current_context()
        custom_context = ctx.meta.get("click_extended", {}).get("context")
        return await handler(exc, custom_context)
    except RuntimeError:
        return await handler(exc, None)


def _call_handler_sync(handler: Callable[..., Any], exc: BaseException) -> Any:
    """Call sync handler with appropriate number of arguments."""
    sig = inspect.signature(handler)
    params = list(sig.parameters.values())

    if len(params) == 0:
        return handler()
    if len(params) == 1:
        return handler(exc)

    import click

    try:
        ctx = click.get_current_context()
        custom_context = ctx.meta.get("click_extended", {}).get("context")
        return handler(exc, custom_context)
    except RuntimeError:
        return handler(exc, None)
