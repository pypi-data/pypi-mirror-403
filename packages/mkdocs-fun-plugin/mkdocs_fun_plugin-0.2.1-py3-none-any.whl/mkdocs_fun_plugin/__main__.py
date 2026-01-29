import argparse
import re
import sys
from pathlib import Path

from mkdocs_fun_plugin.plugin import (
    DEFAULT_PATTERN,
    DISABLE_PATTERN,
    ENABLE_PATTERN,
    _Executor,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("module")
    parser.add_argument("pattern", default=DEFAULT_PATTERN)
    parser.add_argument("disable_pattern", default=DISABLE_PATTERN)
    parser.add_argument("enable_pattern", default=ENABLE_PATTERN)
    args = parser.parse_args()
    e = _Executor(module=Path(args.module),
                  pattern=re.compile(args.pattern),
                  disable_pattern=re.compile(args.disable_pattern),
                  enable_pattern=re.compile(args.enable_pattern))
    for line in sys.stdin:
        print(e(line), end="")  # noqa: T201
