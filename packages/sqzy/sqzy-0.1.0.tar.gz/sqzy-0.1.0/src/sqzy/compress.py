from __future__ import annotations

from collections.abc import Callable
from functools import wraps
import inspect
from typing import Any, Iterable

_REMOVE = object()


def _should_drop_str(value: str, drop_empty_str: bool, drop_whitespace_only: bool) -> bool:
    if drop_empty_str and value == "":
        return True
    if drop_whitespace_only and value.strip() == "":
        return True
    return False


def _compress_value(
    value: Any,
    *,
    drop_null: bool,
    drop_empty_str: bool,
    drop_whitespace_only: bool,
    drop_empty_list: bool,
    drop_empty_dict: bool,
    preserve_keys: set[str] | None,
    current_key: str | None = None,
) -> Any:
    if preserve_keys and current_key in preserve_keys:
        return value

    if value is None:
        return _REMOVE if drop_null else value

    if isinstance(value, str):
        return _REMOVE if _should_drop_str(value, drop_empty_str, drop_whitespace_only) else value

    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            child = _compress_value(
                item,
                drop_null=drop_null,
                drop_empty_str=drop_empty_str,
                drop_whitespace_only=drop_whitespace_only,
                drop_empty_list=drop_empty_list,
                drop_empty_dict=drop_empty_dict,
                preserve_keys=preserve_keys,
                current_key=str(key),
            )
            if child is not _REMOVE:
                cleaned[key] = child
        if drop_empty_dict and not cleaned:
            return _REMOVE
        return cleaned

    if isinstance(value, list):
        cleaned_list = []
        for item in value:
            child = _compress_value(
                item,
                drop_null=drop_null,
                drop_empty_str=drop_empty_str,
                drop_whitespace_only=drop_whitespace_only,
                drop_empty_list=drop_empty_list,
                drop_empty_dict=drop_empty_dict,
                preserve_keys=preserve_keys,
            )
            if child is not _REMOVE:
                cleaned_list.append(child)
        if drop_empty_list and not cleaned_list:
            return _REMOVE
        return cleaned_list

    return value


def compress_json(
    data: Any,
    *,
    drop_null: bool = True,
    drop_empty_str: bool = True,
    drop_whitespace_only: bool = True,
    drop_empty_list: bool = True,
    drop_empty_dict: bool = True,
    preserve_keys: Iterable[str] | None = None,
) -> Any:
    """
    Recursively remove null/blank/empty values from JSON-like structures.

    Returns the cleaned structure, or None when the entire input is removed.
    """
    preserve_set = set(preserve_keys) if preserve_keys else None
    cleaned = _compress_value(
        data,
        drop_null=drop_null,
        drop_empty_str=drop_empty_str,
        drop_whitespace_only=drop_whitespace_only,
        drop_empty_list=drop_empty_list,
        drop_empty_dict=drop_empty_dict,
        preserve_keys=preserve_set,
    )
    return None if cleaned is _REMOVE else cleaned


def compress_response(**options: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that compresses the return value of a function using compress_json.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                result = await func(*args, **kwargs)
                return compress_json(result, **options)

            return async_wrapper

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            return compress_json(result, **options)

        return wrapper

    return decorator
