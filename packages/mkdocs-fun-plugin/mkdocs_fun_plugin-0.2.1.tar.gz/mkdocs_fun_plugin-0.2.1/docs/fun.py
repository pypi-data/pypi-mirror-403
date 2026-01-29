import functools
import pathlib
import re
import subprocess


def func_def(file: str, name: str) -> str:
    """
    Reads 'file' and returns the definition of function 'name'
    """

    with (pathlib.Path(__file__).parent / file).open() as f:
        content = f.read()

    # Find function definition including decorators
    pattern = rf"(@.*\n)*def {name}\s*\([^)]*\)[^:]*:"
    match = re.search(pattern, content, re.MULTILINE)
    assert match, f"Function '{name}' not found in '{file}'"

    # Find where function starts and ends
    start_pos = match.start()
    lines = content.splitlines()
    start_line = content[:start_pos].count("\n")

    # Find function body by tracking indentation
    function_lines = [lines[start_line]]
    indent = (
        re.match(r"(\s*)", lines[start_line + 1]).group(1)
        if start_line + 1 < len(lines)
        else ""
    )

    # Collect and return
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        if line.strip() and not line.startswith(indent):
            break
        function_lines.append(line)
    return "\n".join(function_lines).strip()


def hello() -> str:
    return "world"


def ref(key: str) -> str:
    """
    Bookkeeping and standardized format of references in the docs
    """

    r = {
        "mcguffin": ("McGuffin", "/refs/mcguffin.md"),
    }.get(key)
    assert r, f"No ref for '{key}' found"
    return f"[`{r[0]}`]({r[1]})"


def link(key: str) -> str:
    """
    Bookkeeping and standardized format of external links in the docs
    """

    l = {
        "github": (":fontawesome-brands-github: Github", "https://www.github.com"),
    }.get(key)
    assert l, f"No link for '{key}' found"
    return f'[{l[0]}]({l[1]}){{:target="_blank"}}'


@functools.cache
def shell(cmd: str) -> str:
    """
    Run arbitrary commands and return stdout
    """

    return (
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )
