"""Utilities for converting Japanese prefecture names and JIS X 0401 codes.

This module loads name↔code mappings from JSON files bundled with the package
and provides two small helpers to translate between prefecture names and their
two-digit JIS X 0401 codes.

Functions:
- name2code(name: str | list[str]) -> str | list[str]
    Return the two-digit JIS X 0401 code (as a zero-padded string) for the
    given prefecture name. If a list is passed, returns a list of codes.
    Raises KeyError if the name is not present in the loaded mapping.

- code2name(code: str | int | list[str | int]) -> str | list[str]
    Return the prefecture name for the given code. If an int is supplied it
    will be converted to a zero-padded two-digit string before lookup.
    If a list is passed, returns a list of names.
    Raises KeyError if the code is not present in the loaded mapping.

Notes:
- Mapping data are read from 'jis_x_0401_name.json' and
  'jis_x_0401_code.json' in the package data directory and are expected to be
  UTF-8 encoded.
- Both functions perform exact-match lookups against the loaded dictionaries
  and return str results.

Examples:
>>> name2code("北海道")   # -> "01"
>>> name2code("東京都")   # -> "13"
>>> code2name(1)         # -> "北海道"
>>> code2name("13")      # -> "東京都"
"""

import json
from importlib import resources
from typing import overload

__all__ = ["code2name", "name2code"]


with resources.files("jp_prefectures_simple.data").joinpath(
    "jis_x_0401_code.json",
).open("r", encoding="utf-8") as f:
    _CODE2NAME = json.load(f)


with resources.files("jp_prefectures_simple.data").joinpath(
    "jis_x_0401_name.json",
).open("r", encoding="utf-8") as f:
    _NAME2CODE = json.load(f)


@overload
def code2name(code: int) -> str: ...
@overload
def code2name(code: str) -> str: ...
@overload
def code2name(code: list[int | str]) -> list[str]: ...


def code2name(code: int | str | list[int | str]) -> str | list[str]:
    """Return the prefecture name for the given JIS X 0401 code.

    Args:
        code: Two-digit JIS X 0401 code (e.g. "01" or 1) or list of codes.

    Returns:
        Prefecture name (e.g. "北海道") or list of names.

    Raises:
        KeyError: If the code is not found.
    """
    ret = None
    if isinstance(code, int):
        filled_code = str(code).zfill(2)
        ret = _CODE2NAME[filled_code]
    elif isinstance(code, str):
        ret = _CODE2NAME[code]
    elif isinstance(code, list):
        ret = [code2name(c) for c in code]
    else:
        msg = f"Unsupported type: {type(code)}"
        raise TypeError(msg)
    return ret


@overload
def name2code(name: str) -> str: ...
@overload
def name2code(name: list[str]) -> list[str]: ...


def name2code(name: str | list[str]) -> str | list[str]:
    """Return the two-digit JIS X 0401 code for the given prefecture name.

    Args:
        name: Prefecture name (e.g. "東京都") or list of names.

    Returns:
        Two-digit JIS X 0401 code (e.g. "13") or list of codes.

    Raises:
        KeyError: If the name is not found.
    """
    ret = None
    if isinstance(name, str):
        ret = _NAME2CODE[name]
    elif isinstance(name, list):
        ret = [name2code(n) for n in name]
    else:
        msg = f"Unsupported type: {type(name)}"
        raise TypeError(msg)
    return ret
