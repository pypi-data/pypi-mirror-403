# pipx_isolate

a [`pipx`](https://pipx.pypa.io/latest/installation/) script installer supporting [inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/) for python scripts

The purpose for this is to be able to isolate the dependencies for small scripts into a virtual environment.

Inline Script Metadata looks like this:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "beautifulsoup4",
#     "click>=8.3.1",
# ]
# ///

import os
import sys
import contextlib
from typing import Sequence, NamedTuple
import click
from bs4 import BeautifulSoup, Doctype
```

You could either manually add that to your script, or use [`uv`](https://docs.astral.sh/uv/) like: `uv add --script <PATH> click beautifulsoup4`. `pipx_isolate add-metadata <PATH>` shows you all the import statements and wraps `uv add --script`.

Once you have a script that has metadata, you can use `pipx run --path /path/to/script`, which parses the metadata at the top, installs anything that is needed into a venv into `~/.cache/pipx`, and then runs the script in that environment.

Running `pipx_isolate install <name>` looks up the name of the script in your `$PATH`, and creates a wrapper script that looks like this:

```
#!/bin/sh
exec /home/username/.local/bin/pipx run --path /full/path/to/name "$@"
```

Note: to install this calls `pipx run` which _does_ mean it runs the script, it does so like `script-name --help`.

This way, if you ever update the metadata at the top, `pipx` picks up the new changes, and runs it with the correct dependencies in a virtual environment.

`pipx_isolate install` by default creates a `bin` directory at `~/.local/share/pipx_isolate/bin/` so in order to call the wrapper scripts instead of the original, you should update your `$PATH` to put that directory near the front of your `$PATH`:

```bash
export PATH="$HOME/.local/share/pipx_isolate/bin:$PATH"
```

## Installation

Requires `python3.10+`

To install with pip, run:

```
pip install git+https://github.com/purarue/pipx_isolate
```

## Usage

```
pipx_isolate --help
```

### Tests

```bash
git clone 'https://github.com/purarue/pipx_isolate'
cd ./pipx_isolate
pip install '.[testing]'
flake8 ./pipx_isolate
mypy ./pipx_isolate
```
