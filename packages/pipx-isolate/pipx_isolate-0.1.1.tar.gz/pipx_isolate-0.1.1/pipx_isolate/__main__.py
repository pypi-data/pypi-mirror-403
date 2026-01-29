import os
import sys
import shlex
import shutil
from urllib.parse import urlsplit
from typing import Sequence
import subprocess

import click

local_share = os.environ.get(
    "XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share")
)
app_dir = os.environ.get("PIPX_ISOLATE_DIR", os.path.join(local_share, "pipx_isolate"))

bin_dir = os.path.join(app_dir, "bin")
http_cache = os.path.join(app_dir, "remote")


@click.group()
def main() -> None:
    pass


def which(cmd: str, prompt_to_install: bool = False) -> str:
    if found := shutil.which(cmd):
        return found
    click.secho(f"Could not find {cmd} in your $PATH", err=True, fg="red")
    if prompt_to_install:
        install_cmd = [sys.executable, "-m", "pip", "install", "uv"]
        if click.confirm(f"Run {' '.join(install_cmd)} to install?"):
            subprocess.Popen(install_cmd).wait()
            installed_path = shutil.which(cmd)
            assert installed_path is not None
            return installed_path
    raise click.Abort()


def resolve_local_path(path: str) -> str:
    search_dirs: str | None = None
    search_in = os.environ.get("PATH")

    # remove pipx_isolate bin dir from search path so we don't self-loop
    # and call the wrapper script itself
    if search_in is not None:
        filtered_dirs = [p for p in search_in.split(":") if p != bin_dir]
        search_dirs = ":".join(filtered_dirs)

    if not os.path.exists(path):
        if installed := shutil.which(path, path=search_dirs):
            path = installed
    if not os.path.exists(path):
        click.echo(f"Could not find {path} locally or in your $PATH", err=True)
        raise click.Abort()
    return os.path.abspath(path)


@main.command(short_help="add inline metadata to a script")
@click.argument("PATH")
def add_metadata(path: str) -> None:
    # TODO: use ast module to parse possible remote packages
    path = resolve_local_path(path)
    with open(path, "r") as f:
        lines = f.readlines()
    colored_lines = []
    for line in lines:
        words = line.split(" ")
        if "import" in words:
            cl = []
            for w in words:
                if w == "import":
                    cl.append(click.style(w, "green"))
                else:
                    cl.append(w)
            colored_lines.append(" ".join(cl))
    click.echo("".join(colored_lines))

    packages = click.prompt(
        f"{os.path.basename(path)}: enter packages to add to metadata"
    ).strip()
    cmd = [
        which("uv", prompt_to_install=True),
        "add",
        "--script",
        path,
        *packages.split(),
    ]
    if packages:
        click.echo(f"Running {' '.join(cmd)}", err=True)
        subprocess.Popen(cmd).wait()


@main.command(
    short_help="install script", context_settings=dict(ignore_unknown_options=True)
)
@click.option(
    "--run", default=False, is_flag=True, help="run the script during install"
)
@click.argument("PATH")
@click.argument("PIPX_RUN_ARGUMENTS", required=False, nargs=-1)
def install(path: str, pipx_run_arguments: Sequence[str], run: bool) -> None:
    maybe_url = urlsplit(path)
    name: str | None = None
    if maybe_url.scheme == "https":
        import requests

        click.echo(f"Fetching URL {shlex.quote(path)}", err=True)
        resp = requests.get(path)
        resp.raise_for_status()
        name = os.path.basename(maybe_url.path)
        if not name.strip():
            raise click.Abort(f"Could not determine a filename from {maybe_url.path}")
        os.makedirs(http_cache, exist_ok=True)
        path = os.path.join(http_cache, name)
        with open(path, "w") as fp:
            fp.write(resp.text)

    if name is None:
        name = os.path.basename(path)

    path = resolve_local_path(path)

    assert bin_dir not in path, f"found pipx_isolate/bin dir in script path: {path}"

    os.makedirs(bin_dir, exist_ok=True)

    pipx_path = which("pipx")
    if run:
        args = [pipx_path, "run", *list(pipx_run_arguments), path, "--help"]
        click.echo(f"Running {' '.join(args)}", err=True)
        proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        # send something to stdin and close, so this terminates if its waiting
        # for something through STDIN
        proc.communicate()
        proc.wait()

    parts = [
        "exec",
        shlex.quote(pipx_path),
        "run",
        *[shlex.quote(p) for p in pipx_run_arguments],
        "--path",
        shlex.quote(path),
        '"$@"',
    ]

    wrapper = f"""#!/bin/sh
{' '.join(parts)}
"""

    target = os.path.join(bin_dir, name)
    with open(target, "w") as w:
        w.write(wrapper)
    os.chmod(target, 0o755)

    click.echo(f"Installed {shlex.quote(path)} to {shlex.quote(target)}")


if __name__ == "__main__":
    main(prog_name="pipx_isolate")
