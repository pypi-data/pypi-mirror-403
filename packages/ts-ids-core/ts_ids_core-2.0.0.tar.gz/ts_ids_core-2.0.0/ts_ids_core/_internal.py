import functools
import typing
from typing import Any, Tuple

import typing_extensions


# Use an unbounded cache for this function, for optimal performance
@functools.lru_cache(maxsize=None)
def get_typing_objects_by_name_of(name: str) -> Tuple[Any, ...]:
    """
    Get all typing objects by their name from both `typing` and `typing_extensions`.

    This function is taken from `typing_extensions` as part of a solution to runtime
    type checking which is compatible with both `typing` and `typing_extensions`
    interchangeably.
    """
    result = tuple(
        getattr(module, name)
        for module in (typing, typing_extensions)
        if hasattr(module, name)
    )
    if not result:
        raise ValueError(
            f"Neither typing nor typing_extensions has an object called {name!r}"
        )
    return result


# Use a cache here as well, but make it a bounded cache
# (the default cache size is 128)
@functools.lru_cache()
def is_typing_name(type_: Any, name: str) -> bool:
    """
    Check if a type `type_` *is* the type defined by importing `name` from either
    `typing` or `typing_extensions`.

    For example, whether you import `Literal` from `typing` or `typing_extensions`,
    `is_typing_name(Literal, "Literal")` is True.

    Note `is_typing_name(Literal["a"], "Literal")` is False because this function only
    checks for an exact match. In this case you could use `typing.get_origin`:
    `is_typing_name(get_origin(Literal["a"]), "Literal")` is True.

    This function is taken from `typing_extensions` as part of a solution to runtime
    type checking which is compatible with both `typing` and `typing_extensions`
    interchangeably.
    """
    return any(type_ is thing for thing in get_typing_objects_by_name_of(name))


def is_literal(type_: Any) -> bool:
    """
    Return `True` if `type_` is either `typing.Literal` or `typing_extensions.Literal`.
    """
    return is_typing_name(type_=type_, name="Literal")
