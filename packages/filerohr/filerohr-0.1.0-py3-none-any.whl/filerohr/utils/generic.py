from collections.abc import Callable, Iterable
import functools
from html import unescape
from typing import Any


def get_qualified_cls_name(obj) -> str:
    cls = obj if isinstance(obj, type) else type(obj)
    cls_name = cls.__qualname__
    module = cls.__module__
    if not module or module == "builtins":
        return cls_name
    if module == "types":
        return str(obj)
    return f"{module}.{cls_name}"


def once[**Params, Result](func: Callable[Params, Result]):
    sentinel = object()
    result = sentinel

    @functools.wraps(func)
    def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Result:
        nonlocal result
        if result is sentinel:
            result = func(*args, **kwargs)
        return result

    return wrapper


def omit_falsy(iterable: Iterable[Any], *, is_truthy: Callable[[Any], bool] | None = None):
    is_truthy = is_truthy or bool
    for item in iterable:
        if is_truthy(item):
            yield item


def normalize_str(value) -> str:
    if value is None:
        return ""
    return unescape(str(value)).strip()
