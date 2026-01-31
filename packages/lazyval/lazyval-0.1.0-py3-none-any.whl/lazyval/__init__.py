"""
Lazy Evaluation Wrapper for Python
===================================

A lazy evaluation wrapper that works with:
- JSON serialization
- YAML serialization (optional dependency)
- Jinja2 templates
- String formatting (f-strings, format, str)
- Comparisons and arithmetic
- Dictionary and attribute access

Usage:
------
    from lazy import Lazy

    def fetch_from_db():
        return slow_database_query()

    # Wrap the function
    my_var = Lazy(fetch_from_db)

    # Function only executes when you use the value
    if my_var > 10:  # <- Function executes here
        print("Value is large")

    # Works in templates
    template.render(data=my_var)  # <- Function executes here

    # Works in JSON
    import json
    json.dumps({'value': my_var}, default=lazy_json_default)

    # Works in YAML (if pyyaml installed)
    yaml.dump({'value': my_var})

"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Generic, TypeVar

__all__ = [
    "Lazy",
    "lazy",
    "lazy_json_default",
    "lazy_json_encoder",
    "LazyJSONEncoder",
    "loads",
    "dumps",
]

__version__ = "0.1.0"

T = TypeVar("T")


class Lazy(Generic[T]):
    """
    A lazy evaluation wrapper that delays function execution until the value is needed.

    The wrapped function is executed only once, when the value is first accessed.
    Subsequent accesses return the cached value.

    Args:
        func: A callable that returns the value to be lazily evaluated

    Example:
        >>> def expensive_operation():
        ...     print("Computing...")
        ...     return 42
        >>> lazy_val = Lazy(expensive_operation)
        >>> print(lazy_val > 10)  # Prints "Computing..." then True
        >>> print(lazy_val > 10)  # Just prints True (cached)
    """

    __slots__ = ("_func", "_evaluated", "_value")

    def __init__(self, func: Callable[[], T]) -> None:
        if not callable(func):
            raise TypeError(f"Expected callable, got {type(func).__name__}")
        object.__setattr__(self, "_func", func)
        object.__setattr__(self, "_evaluated", False)
        object.__setattr__(self, "_value", None)

    def _get_value(self) -> T:
        """Evaluate the function if not already evaluated and return the cached value."""
        if not self._evaluated:
            object.__setattr__(self, "_value", self._func())
            object.__setattr__(self, "_evaluated", True)
        return self._value  # type: ignore[return-value]

    @property
    def is_evaluated(self) -> bool:
        """Check if the lazy value has been evaluated."""
        return self._evaluated

    def force(self) -> T:
        """Force evaluation and return the value. Alias for _get_value()."""
        return self._get_value()

    # String representation - Critical for YAML and Jinja2
    def __str__(self) -> str:
        return str(self._get_value())

    def __repr__(self) -> str:
        if self._evaluated:
            return repr(self._value)
        func_name = getattr(self._func, "__name__", repr(self._func))
        return f"Lazy(<unevaluated: {func_name}>)"

    def __format__(self, format_spec: str) -> str:
        return format(self._get_value(), format_spec)

    # Comparison operators
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Lazy):
            return self._get_value() == other._get_value()
        return self._get_value() == other

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, Lazy):
            return self._get_value() != other._get_value()
        return self._get_value() != other

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Lazy):
            return self._get_value() < other._get_value()
        return self._get_value() < other

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Lazy):
            return self._get_value() <= other._get_value()
        return self._get_value() <= other

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Lazy):
            return self._get_value() > other._get_value()
        return self._get_value() > other

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, Lazy):
            return self._get_value() >= other._get_value()
        return self._get_value() >= other

    # Arithmetic operators
    def __add__(self, other: Any) -> Any:
        return self._get_value() + (other._get_value() if isinstance(other, Lazy) else other)

    def __sub__(self, other: Any) -> Any:
        return self._get_value() - (other._get_value() if isinstance(other, Lazy) else other)

    def __mul__(self, other: Any) -> Any:
        return self._get_value() * (other._get_value() if isinstance(other, Lazy) else other)

    def __truediv__(self, other: Any) -> Any:
        return self._get_value() / (other._get_value() if isinstance(other, Lazy) else other)

    def __floordiv__(self, other: Any) -> Any:
        return self._get_value() // (other._get_value() if isinstance(other, Lazy) else other)

    def __mod__(self, other: Any) -> Any:
        return self._get_value() % (other._get_value() if isinstance(other, Lazy) else other)

    def __pow__(self, other: Any) -> Any:
        return self._get_value() ** (other._get_value() if isinstance(other, Lazy) else other)

    # Reverse arithmetic operators
    def __radd__(self, other: Any) -> Any:
        return other + self._get_value()

    def __rsub__(self, other: Any) -> Any:
        return other - self._get_value()

    def __rmul__(self, other: Any) -> Any:
        return other * self._get_value()

    def __rtruediv__(self, other: Any) -> Any:
        return other / self._get_value()

    def __rfloordiv__(self, other: Any) -> Any:
        return other // self._get_value()

    def __rmod__(self, other: Any) -> Any:
        return other % self._get_value()

    def __rpow__(self, other: Any) -> Any:
        return other ** self._get_value()

    # Unary operators
    def __neg__(self) -> Any:
        return -self._get_value()  # type: ignore[operator]

    def __pos__(self) -> Any:
        return +self._get_value()  # type: ignore[operator]

    def __abs__(self) -> Any:
        return abs(self._get_value())  # type: ignore[arg-type]

    # Container operations
    def __getitem__(self, key: Any) -> Any:
        """Support for dict/list access: lazy_obj['key'] or lazy_obj[0]"""
        return self._get_value()[key]  # type: ignore[index]

    def __setitem__(self, key: Any, value: Any) -> None:
        """Support for dict/list assignment: lazy_obj['key'] = value"""
        self._get_value()[key] = value  # type: ignore[index]

    def __delitem__(self, key: Any) -> None:
        """Support for dict/list deletion: del lazy_obj['key']"""
        del self._get_value()[key]  # type: ignore[union-attr]

    def __len__(self) -> int:
        return len(self._get_value())  # type: ignore[arg-type]

    def __iter__(self) -> Any:
        """Support for iteration: for item in lazy_obj"""
        return iter(self._get_value())  # type: ignore[call-overload]

    def __contains__(self, item: Any) -> bool:
        """Support for 'in' operator: item in lazy_obj"""
        return item in self._get_value()  # type: ignore[operator]

    # Attribute access
    def __getattr__(self, name: str) -> Any:
        """Support for attribute access: lazy_obj.attribute"""
        # Avoid infinite recursion on internal attributes
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(self._get_value(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Support for attribute assignment: lazy_obj.attribute = value"""
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            setattr(self._get_value(), name, value)

    # Type conversions
    def __bool__(self) -> bool:
        return bool(self._get_value())

    def __int__(self) -> int:
        return int(self._get_value())  # type: ignore[call-overload]

    def __float__(self) -> float:
        return float(self._get_value())  # type: ignore[arg-type]

    def __complex__(self) -> complex:
        return complex(self._get_value())  # type: ignore[arg-type]

    def __hash__(self) -> int:
        return hash(self._get_value())

    # Context manager support (if wrapped value supports it)
    def __enter__(self) -> Any:
        return self._get_value().__enter__()  # type: ignore[union-attr]

    def __exit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> Any:
        return self._get_value().__exit__(exc_type, exc_val, exc_tb)  # type: ignore[union-attr]

    # Callable support (if wrapped value is callable)
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._get_value()(*args, **kwargs)  # type: ignore[operator]


# JSON support
def lazy_json_default(obj: Any) -> Any:
    """
    JSON default function for serializing Lazy objects.

    Usage:
        json.dumps(data, default=lazy_json_default)
    """
    if isinstance(obj, Lazy):
        return obj._get_value()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class LazyJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that handles Lazy objects.

    Usage:
        json.dumps(data, cls=LazyJSONEncoder)
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, Lazy):
            return o._get_value()
        return super().default(o)


def lazy_json_encoder(obj: Any) -> Any:
    """Alias for lazy_json_default for backward compatibility."""
    return lazy_json_default(obj)


def dumps(
    obj: Any,
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = True,
    check_circular: bool = True,
    allow_nan: bool = True,
    indent: int | None = None,
    separators: tuple[str, str] | None = None,
    default: Callable[[Any], Any] | None = None,
    sort_keys: bool = False,
    **kwargs: Any,
) -> str:
    """
    Serialize obj to a JSON formatted string, handling Lazy objects.

    This is a convenience wrapper around json.dumps that automatically
    handles Lazy objects.
    """

    def combined_default(o: Any) -> Any:
        if isinstance(o, Lazy):
            return o._get_value()
        if default is not None:
            return default(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(
        obj,
        skipkeys=skipkeys,
        ensure_ascii=ensure_ascii,
        check_circular=check_circular,
        allow_nan=allow_nan,
        indent=indent,
        separators=separators,
        default=combined_default,
        sort_keys=sort_keys,
        **kwargs,
    )


def loads(s: str | bytes, **kwargs: Any) -> Any:
    """
    Deserialize s to a Python object.

    This is a convenience wrapper around json.loads for API symmetry.
    """
    return json.loads(s, **kwargs)


# YAML support (optional)
def _register_yaml_representer() -> None:
    """Register YAML representer if PyYAML is available."""
    try:
        import yaml

        def _lazy_representer(dumper: yaml.Dumper, data: Lazy[Any]) -> Any:
            """Custom YAML representer for Lazy objects."""
            return dumper.represent_data(data._get_value())

        yaml.add_representer(Lazy, _lazy_representer)
    except ImportError:
        pass


# Register YAML representer on import if available
_register_yaml_representer()


# Convenience function
def lazy(func: Callable[[], T]) -> Lazy[T]:
    """
    Decorator/function to create a lazy value.

    Example:
        >>> @lazy
        ... def expensive_operation():
        ...     return 42
        >>> print(expensive_operation > 10)
        True

        # Or use directly:
        >>> lazy_val = lazy(lambda: 42)
    """
    return Lazy(func)
