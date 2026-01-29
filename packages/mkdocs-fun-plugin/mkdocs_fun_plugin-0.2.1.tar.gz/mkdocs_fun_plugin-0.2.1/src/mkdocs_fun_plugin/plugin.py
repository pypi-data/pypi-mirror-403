from __future__ import annotations

import ast
import importlib.util
import inspect
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mkdocs.config import config_options as option
from mkdocs.config.base import Config
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

DEFAULT_PATTERN = r"#!(?P<func>[^\(]+)\((?P<params>[^\)]*)\)"
DISABLE_PATTERN = r"<!--\s*fun:disable\s*-->"
ENABLE_PATTERN = r"<!--\s*fun:enable\s*-->"

class FunPluginConfig(Config):
    pattern = option.Type(str, default=DEFAULT_PATTERN)
    disable_pattern = option.Type(str, default=DISABLE_PATTERN)
    enable_pattern = option.Type(str, default=ENABLE_PATTERN)
    module = option.Type(str, default="fun.py")


class FunPlugin(BasePlugin[FunPluginConfig]):
    _executor: _Executor = None  # type: ignore[reportAssignmentType]
    _pattern: re.Pattern = None  # type: ignore[reportAssignmentType]
    _disable_pattern: re.Pattern = None  # type: ignore[reportAssignmentType]
    _enable_pattern: re.Pattern = None  # type: ignore[reportAssignmentType]
    _module: Path = None  # type: ignore[reportAssignmentType]

    def on_config(
        self,
        config: MkDocsConfig,
    ) -> MkDocsConfig | None:
        self._pattern = re.compile(self.config.pattern)
        self._disable_pattern = re.compile(self.config.disable_pattern)
        self._enable_pattern = re.compile(self.config.enable_pattern)
        self._module = Path(config.docs_dir) / self.config.module
        return config

    def on_files(
        self,
        files: Files,
        /,
        *,
        config: MkDocsConfig,  # noqa: ARG002
    ) -> Files | None:
        # Remove fun.py from considered files
        to_remove = None
        for f in files:
            if f.abs_src_path == str(self._module):
                to_remove = f
                break

        if to_remove:
            files.remove(to_remove)

        # Setup module
        try:
            self._executor = _Executor(
                pattern=self._pattern,
                disable_pattern=self._disable_pattern,
                enable_pattern=self._enable_pattern,
                module=self._module,
            )
        except AssertionError as e:
            msg = f"Failed to load module: {e}"
            raise PluginError(msg) from e

        return files

    def on_page_markdown(
        self,
        markdown: str,
        /,
        *,
        page: Page,
        config: MkDocsConfig,  # noqa: ARG002
        files: Files,  # noqa: ARG002
    ) -> str | None:
        if not page.is_page:
            return markdown
        try:
            return self._executor(markdown)
        except Exception as e:
            msg = f"The page '{page.title}' failed rendering: {e}"
            raise PluginError(msg) from e


class _Executor:
    def __init__(
        self,
        *,
        pattern: re.Pattern,
        disable_pattern: re.Pattern,
        enable_pattern: re.Pattern,
        module: Path,
    ) -> None:
        self._pattern = pattern
        self._disable_pattern = disable_pattern
        self._enable_pattern = enable_pattern
        self._map = {}

        assert module.exists(), f"Module '{module}' is not found"
        assert module.is_file(), f"Module '{module}' is not a file"

        # Load module from path find all public functions and add them to _map
        spec = importlib.util.spec_from_file_location("dynamic_module", module)
        if spec and spec.loader:
            dynamic_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dynamic_module)

            # Get all functions from the module (including decorated ones)
            for name, obj in inspect.getmembers(dynamic_module):
                # Only add public functions (not starting with underscore)
                if not name.startswith("_") and (inspect.isfunction(obj) or callable(obj)):
                    self._map[name] = obj

    def __call__(self, markdown: str | None) -> str | None:
        if not markdown:
            return markdown

        result = markdown
        replacements = []

        for match in re.finditer(self._pattern, markdown):
            # Skip if match inside block where fun is disabled
            if not self._is_match_enabled(match.start(), markdown):
                continue

            func_name = match.group("func")
            func = self._map.get(func_name)
            assert func, f"func '{func_name}' not found"

            # Parse args and kwargs from params
            params = match.group("params") if "params" in match.groupdict() else ""
            args, kwargs = self._parse_params(params)

            new = func(*args, **kwargs)

            # Save replacement
            replacements.append((match.span(), str(new)))

        # Apply replacements in reverse order to avoid index shifting
        for (start, end), new_text in reversed(replacements):
            result = result[:start] + new_text + result[end:]

        return result

    def _is_match_enabled(self, match_start: int, markdown: str) -> bool:
        """Check if a function is within an enabled section."""
        # Find all disable/enable markers before the match
        text_before = markdown[:match_start]

        # Process markers in order
        off_pos = [(m.start(), "disable") for m in self._disable_pattern.finditer(text_before)]
        on_pos = [(m.start(), "enable") for m in self._enable_pattern.finditer(text_before)]

        # Combine and sort by position
        all_markers = sorted(off_pos + on_pos)

        enabled = True
        for _, marker_type in all_markers:
            if marker_type == "disable":
                enabled = False
            elif marker_type == "enable":
                enabled = True

        return enabled

    def _parse_params(self, params_str: str) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """Parse a comma-separated string into args and kwargs."""

        if not params_str.strip():
            return (), {}

        # Split by comma, but respect quotes and nested structures
        params_list = []
        current_param = ""
        inside_quotes = False
        quote_char = None
        bracket_count = 0

        for char in params_str:
            if char in ['"', "'"]:
                if not inside_quotes:
                    inside_quotes = True
                    quote_char = char
                elif char == quote_char:
                    inside_quotes = False
                    quote_char = None
                current_param += char
            elif char in ["[", "(", "{"]:
                bracket_count += 1
                current_param += char
            elif char in ["]", ")", "}"]:
                bracket_count -= 1
                current_param += char
            elif char == "," and not inside_quotes and bracket_count == 0:
                params_list.append(current_param.strip())
                current_param = ""
            else:
                current_param += char

        if current_param:
            params_list.append(current_param.strip())

        # Process each param
        args = []
        kwargs = {}
        for param in params_list:
            if "=" in param and not param.startswith(('"', "'")):
                key, value = param.split("=", 1)
                kwargs[key.strip()] = self._parse_value(value.strip())
            else:
                args.append(self._parse_value(param))

        return tuple(args), kwargs

    def _parse_value(self, value_str: str) -> Any:  # noqa: ANN401
        """Parse a string into a Python value."""
        try:
            return ast.literal_eval(value_str)
        except (SyntaxError, ValueError):
            # If literal_eval fails, return the string as is
            return value_str
