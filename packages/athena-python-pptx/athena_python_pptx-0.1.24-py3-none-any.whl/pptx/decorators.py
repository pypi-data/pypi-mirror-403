"""
Decorators for the Athena Python PPTX SDK.

These decorators are used to mark functions and methods that are specific
to Athena Python PPTX and not part of the standard python-pptx library.
"""

from __future__ import annotations
from functools import wraps
from typing import Any, Callable, TypeVar, Union

F = TypeVar("F", bound=Callable[..., Any])

# Registry of all Athena-specific functions
_athena_registry: list[dict[str, Any]] = []


def athena_only(
    description: str = "",
    since: str = "0.1.0",
) -> Callable[[F], F]:
    """
    Decorator to mark functions/methods as Athena Python PPTX specific.

    These functions are NOT part of the standard python-pptx library and are
    exclusive to Athena Python PPTX. Use this decorator to flag functions
    for separate documentation generation.

    Args:
        description: Brief description of what this function does
        since: Version when this function was introduced

    Example:
        @athena_only(description="Delete multiple slides at once")
        def delete_slides(self, indices: list[int]) -> None:
            ...

    The decorator preserves the original function and adds metadata:
        - func._athena_only = True
        - func._athena_description = description
        - func._athena_since = since
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        # Add metadata to the wrapper
        wrapper._athena_only = True  # type: ignore[attr-defined]
        wrapper._athena_description = description  # type: ignore[attr-defined]
        wrapper._athena_since = since  # type: ignore[attr-defined]

        # Register the function
        _athena_registry.append({
            "name": func.__name__,
            "qualname": func.__qualname__,
            "module": func.__module__,
            "description": description,
            "since": since,
            "doc": func.__doc__,
        })

        return wrapper  # type: ignore[return-value]

    return decorator


def get_athena_functions() -> list[dict[str, Any]]:
    """
    Get a list of all registered Athena-specific functions.

    Returns:
        List of dictionaries with function metadata:
            - name: Function name
            - qualname: Qualified name (e.g., "Slides.delete_slides")
            - module: Module where the function is defined
            - description: Brief description
            - since: Version when introduced
            - doc: Full docstring
    """
    return _athena_registry.copy()


def is_athena_only(func: Callable[..., Any]) -> bool:
    """
    Check if a function is marked as Athena-specific.

    Args:
        func: Function to check

    Returns:
        True if the function has the @athena_only decorator
    """
    return getattr(func, "_athena_only", False)
