import re
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from mkdocs_fun_plugin.plugin import DEFAULT_PATTERN, DISABLE_PATTERN, ENABLE_PATTERN, _Executor


class TestBugReproduction(unittest.TestCase):
    def setUp(self) -> None:
        # Create a temporary module file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.module_path = Path(self.temp_dir.name) / "fun.py"

        with self.module_path.open("w") as f:
            f.write(
                dedent("""
                def log(msg):
                    return f"LOG: {msg}"
            """),
            )

        # Create the executor with the default pattern
        self.pattern = re.compile(DEFAULT_PATTERN)
        self.disable_pattern = re.compile(DISABLE_PATTERN)
        self.enable_pattern = re.compile(ENABLE_PATTERN)
        self.executor = _Executor(
            pattern=self.pattern,
            disable_pattern=self.disable_pattern,
            enable_pattern=self.enable_pattern,
            module=self.module_path,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_reproduce_bug(self) -> None:
        """Reproduce the bug where a disabled block still triggers function existence check."""
        markdown = dedent("""
            <!-- fun:disable -->
            ```shell
            #!/bin/bash
            log() {
                echo "hello"
            }
            ```
            <!-- fun:enable -->
        """).strip()

        result = self.executor(markdown)
        self.assertEqual(result, markdown)


if __name__ == "__main__":
    unittest.main()
