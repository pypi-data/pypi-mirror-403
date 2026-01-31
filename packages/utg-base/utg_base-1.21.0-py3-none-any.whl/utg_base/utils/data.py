from collections.abc import Iterable
from copy import deepcopy

from django.db.models import QuerySet


def deep_map(data: dict | list, func_cond, func_map, in_place=True):
    if not in_place:
        data = deepcopy(data)

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (list, dict, QuerySet)):
                deep_map(value, func_cond, func_map, True)
            elif func_cond(value):
                data[key] = func_map(value)
    elif isinstance(data, (list, QuerySet)):
        for index, value in enumerate(data):
            if isinstance(value, (list, dict, QuerySet)):
                deep_map(value, func_cond, func_map, True)
            elif func_cond(value):
                data[index] = func_map(value)

    return data


def deep_round(data: dict | list, ndigits: int, in_place=True):
    return deep_map(data, lambda value: isinstance(value, float), lambda value: round(value, ndigits), in_place)


def to_numeric_or_none(*args):
    _is_iterable = isinstance(args[0], Iterable) and not isinstance(args[0], str)
    if _is_iterable:
        args = args[0]
    result = []

    for x in args:
        if isinstance(x, (int, float, complex, bool)):
            result.append(x)
        else:
            result.append(None)
    if not _is_iterable and len(result) == 1 and len(args) == 1:
        return result[0]
    return result


def safe_sum(*args, allow_null=True):
    args = to_numeric_or_none(*args)

    if all(arg is None for arg in args):
        return None
    if not allow_null and any(arg is None for arg in args):
        return None

    _sum = 0
    for arg in args:
        _sum += arg or 0
    return _sum


def safe_subtract(*args, allow_null=False):
    args = to_numeric_or_none(*args)

    if all(arg is None for arg in args):
        return None
    if not allow_null and any(arg is None for arg in args):
        return None

    _sum = args[0] or 0
    for arg in args[1:]:
        _sum -= arg or 0
    return _sum


def safe_multiply(*args, allow_null=False):
    args = to_numeric_or_none(*args)

    if all(arg is None for arg in args):
        return None
    if not allow_null and any(arg is None for arg in args):
        return None

    result = 1
    for arg in args:
        value = 0 if allow_null and arg is None else arg
        result *= value
    return result


def safe_divide(*args, allow_null=False):
    args = to_numeric_or_none(*args)

    if all(arg is None for arg in args):
        return None
    if not allow_null and any(arg is None for arg in args):
        return None

    result = 0 if allow_null and args[0] is None else args[0]

    for arg in args[1:]:
        value = 0 if allow_null and arg is None else arg
        if value == 0:
            return None
        result /= value

    return result


def safe_get(obj, dotted_path: str, default=None):
    """
    Universal safe getter: supports dicts, objects, lists, and mixes of them.

    Args:
        obj: Any object, dict, list, etc.
        dotted_path (str): Path like 'a.b.c' or 'items.0.name'.
        default: Returned if path does not exist.

    Returns:
        Any: The resolved value or default.
    """
    parts = dotted_path.split('.')

    for part in parts:
        if obj is None:
            return default

        # --- Handle LIST index ---
        if isinstance(obj, (list, tuple)) and part.isdigit():
            idx = int(part)
            if 0 <= idx < len(obj):
                obj = obj[idx]
            else:
                return default

        # --- Handle DICT ---
        elif isinstance(obj, dict):
            if part in obj:
                obj = obj.get(part)
            else:
                return default

        # --- Handle OBJECT attribute ---
        else:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return default

    return obj


def compute_change_percent(current, previous, ndigits=2):
    if not current or previous in (None, 0):
        return None
    return round(((current - previous) / previous) * 100, ndigits)
