"""Utility functions."""

from collections.abc import Mapping
from typing import Any


def merge_dict_nested(
    dic_user: Mapping[str, Any], dic_default: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge two dictionaries.

    Keep elements from `dic_user` if it exists, with a fallback on elements in
    `dic_default`. All nested dictionaries are also treated like this.

    Parameters
    ----------
    dic_user : dict-like
        Dict being merged, its values have priority over `dic_default`.
    dic_default : dict-like
        Dict being merged, its values are used if they are not in `dic_user`.

    Returns
    -------
    dic : dict
        Merged dict.
    """
    dic_copy = dic_default.copy()
    for key, value in dic_user.items():
        if key in dic_default:
            if isinstance(value, Mapping):
                dic_copy[key] = merge_dict_nested(value, dic_default[key])
            else:
                if key in dic_user:
                    dic_copy[key] = dic_user[key]

        else:
            dic_copy[key] = dic_user[key]

    return dic_copy


def cast_type_dict(
    dic: dict[str, Any], in_type: type, out_type: type
) -> dict[str, Any]:
    """
    Convert `in_type` value to `out_type` values in a dictionary.

    Nested dictionaries are supported, so the casted types can't be `dict`.

    Parameters
    ----------
    dic : dict
        Dict in which values are casted.
    in_type, out_type : type
        `in_type` types are casted to `out_type`. Can't be `dict`.
    """
    dic_copy = dic.copy()
    for key, value in dic.items():
        if isinstance(value, dict):
            dic_copy[key] = cast_type_dict(value, in_type, out_type)
        else:
            if isinstance(dic_copy[key], in_type):
                dic_copy[key] = out_type(dic[key])

    return dic_copy


def strip_none_dict(dic: dict) -> dict:
    """
    Strip elements that are None from `dic`.

    Parameters
    ----------
    dic : dict
        Dict in which None values are removed.
    """
    dic_copy = dic.copy()
    for key, value in dic.items():
        if isinstance(value, dict):
            dic_copy[key] = strip_none_dict(value)
        elif value is None:
            dic_copy.pop(key)

    return dic_copy
