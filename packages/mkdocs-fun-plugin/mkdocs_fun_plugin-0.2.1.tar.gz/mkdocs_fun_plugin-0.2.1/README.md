<h1>
  <p align="center">
    <a href="https://github.com/gbbirkisson/mkdocs-fun-plugin">
      <img src="https://raw.githubusercontent.com/gbbirkisson/mkdocs-fun-plugin/main/logo.png" alt="Logo" height="128">
    </a>
    <br>mkdocs-fun-plugin
  </p>
</h1>

<p align="center">
  Dead simple custom python <b>fun</b>ctions with <b>mkdocs</b>
</p>

<!-- vim-markdown-toc GFM -->

* [Usage 📖](#usage-)
* [Configuration 🎛](#configuration-)
* [Examples 💡](#examples-)
  * [References and links](#references-and-links)
  * [Shell](#shell)
  * [File contents](#file-contents)
  * [Disable plugin for a section](#disable-plugin-for-a-section)

<!-- vim-markdown-toc -->

## Usage 📖

Install the plugin in your project ...

```bash
pip install mkdocs-fun-plugin
```

... and add it to your `mkdocs.yaml` configuration ...

```yaml
# mkdocs.yaml
plugins:
  - fun
```

... create a `docs/fun.py` file ...

```python
# docs/fun.py
def hello() -> str:
    return "world"
```

... and start using your functions in your docs ...

```markdown
<!-- docs/docs.md -->
This #!hello() comes from my function!
```

... becomes ...

```markdown
This world comes from my function!
```

## Configuration 🎛

You can customize the plugin behaviour with configuration:

```yaml
# mkdocs.yaml
plugins:
  - fun:
      pattern: "#!(?P<func>[^\(]+)\((?P<params>[^\)]*)\)"  # Regex to match functions
      module: fun.py  # Python file that defines your functions
      disable_pattern: "<!--\s*fun:disable\s*-->"
      enable_pattern: "<!--\s*fun:enable\s*-->"
```

## Examples 💡

### References and links

```python
# docs/fun.py
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
```

```markdown
<!-- docs/docs.md -->
Look at our internal #!ref(mcguffin) docs for more info. Also open up #!link(github).
```

... becomes ...

```markdown
Look at our internal [`McGuffin`](/refs/mcguffin.md) docs for more info. Also open up [:fontawesome-brands-github: Github](https://www.github.com){:target="_blank"}.
```

### Shell

```python
# docs/fun.py
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
```

```markdown
<!-- docs/docs.md -->
#!shell("echo hello | cowsay")
```

... becomes ...

```markdown
_______
< hello >
 -------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
```

### File contents

```python
# docs/fun.py
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
```

```markdown
<!-- docs/docs.md -->
#!func_def(fun.py, hello)
```

... becomes ...

```markdown
def hello() -> str:
    return "world"
```

### Disable plugin for a section

```markdown
<!-- docs/docs.md -->
#!shell("echo hello | cowsay")
<!-- fun:disable -->
#!shell("echo there | cowsay")
<!-- fun:enable -->
#!shell("echo friend | cowsay")
```

... becomes ...

```markdown
_______
< hello >
 -------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
<!-- fun:disable -->
#!shell("echo there | cowsay")
<!-- fun:enable -->
________
< friend >
 --------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
```
