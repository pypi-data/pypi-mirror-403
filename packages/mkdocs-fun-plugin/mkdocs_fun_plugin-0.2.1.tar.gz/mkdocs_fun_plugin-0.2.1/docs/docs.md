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
{{func_def(fun.py, hello)}}
```

... and start using your functions in your docs ...

```markdown
<!-- docs/docs.md -->
This #!hello() comes from my function!
```

... becomes ...

```markdown
This {{hello()}} comes from my function!
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
{{func_def(fun.py, ref)}}

{{func_def(fun.py, link)}}
```

```markdown
<!-- docs/docs.md -->
Look at our internal #!ref(mcguffin) docs for more info. Also open up #!link(github).
```

... becomes ...

```markdown
Look at our internal {{ref(mcguffin)}} docs for more info. Also open up {{link(github)}}.
```

### Shell

```python
# docs/fun.py
{{func_def(fun.py, shell)}}
```

```markdown
<!-- docs/docs.md -->
#!shell("echo hello | cowsay")
```

... becomes ...

```markdown
{{shell("echo hello | cowsay")}}
```

### File contents

```python
# docs/fun.py
{{func_def(fun.py, func_def)}}
```

```markdown
<!-- docs/docs.md -->
#!func_def(fun.py, hello)
```

... becomes ...

```markdown
{{func_def(fun.py, hello)}}
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
{{shell("echo hello | cowsay")}}
<!-- fun:disable -->
#!shell("echo there | cowsay")
<!-- fun:enable -->
{{shell("echo friend | cowsay")}}
```
