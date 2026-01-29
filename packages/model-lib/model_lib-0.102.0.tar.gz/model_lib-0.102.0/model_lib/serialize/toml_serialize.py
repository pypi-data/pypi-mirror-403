from __future__ import annotations

import logging
import re
import sys
from contextlib import suppress
from dataclasses import dataclass
from textwrap import indent
from typing import Any, Callable, Union

logger = logging.getLogger(__name__)


def raise_missing_toml(*_, **__):
    raise Exception("pip install tomli tomli-w tomlkit")


@dataclass
class TomlModule:
    loads: Callable[[Any], Union[dict, list]] = raise_missing_toml
    dumps: Callable[[Any], str] = raise_missing_toml

    @property
    def loads_ready(self) -> bool:
        return self.loads != raise_missing_toml

    @property
    def dumps_ready(self) -> bool:
        return self.dumps != raise_missing_toml


toml = TomlModule()
_, version_minor, *__ = sys.version_info

# For dumping: prefer tomli_w (declared dependency) over tomlkit for consistent output
with suppress(ModuleNotFoundError):
    import tomli_w

    toml.dumps = tomli_w.dumps

if not toml.dumps_ready:
    with suppress(ModuleNotFoundError):
        import tomlkit  # type: ignore

        toml.dumps = tomlkit.dumps

# For loading: try tomlkit first, then tomli, then stdlib tomllib
with suppress(ModuleNotFoundError):
    import tomlkit  # type: ignore

    def loads(value: str) -> Union[dict, list]:
        loaded = tomlkit.loads(value)
        return loaded.value

    toml.loads = loads

if not toml.loads_ready:
    try:
        import tomli  # type: ignore

        toml.loads = tomli.loads
    except ModuleNotFoundError:
        if version_minor >= 11:
            import tomllib

            toml.loads = tomllib.loads

if not toml.loads_ready:
    logger.info("no library for reading toml files: pip install tomlkit | tomli ")
if not toml.dumps_ready:
    logger.info("tomlkit or tomli-w not installed, dumping toml will not work")


_dumps = toml.dumps
# tomli_w.dumps accepts multiline_strings param, tomlkit.dumps does not
_dumps_accepts_multiline_strings = False
with suppress(ModuleNotFoundError):
    import tomli_w as _tomli_w_check

    _dumps_accepts_multiline_strings = _dumps == _tomli_w_check.dumps


def dump_toml_str(data: object, multiline_strings: bool = False, **kwargs) -> str:
    if _dumps_accepts_multiline_strings:
        return _dumps(data, multiline_strings=multiline_strings, **kwargs)  # type: ignore
    return _dumps(data, **kwargs)  # type: ignore


_loads = toml.loads


def parse_toml_str(data: str, **kwargs) -> Union[dict, list]:
    return _loads(data, **kwargs)


_array_pattern = re.compile(r"[^\s]+\s=\s\[(.*)\]$")


def add_line_breaks(updated: str) -> str:
    lines = []
    for line in updated.splitlines():
        if len(line) > 88 and (long_array_match := _array_pattern.match(line)):
            inner_content_old = long_array_match.group(1)
            inner_content_new = inner_content_old.replace(", ", ",\n")
            inner_content_new = indent(inner_content_new, "  ")
            inner_content_new = f"\n{inner_content_new},\n"
            line = line.replace(inner_content_old, inner_content_new)
        lines.append(line)
    return "\n".join(lines)
