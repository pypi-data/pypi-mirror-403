# pydoc_mintlify/cli.py

import subprocess
from pathlib import Path
from watchfiles import watch
from typing import Any, Optional, List
import typer
import yaml
import pydoc_markdown.main as pm
import logging
from .mintlify_renderer import MintlifyRenderer

app = typer.Typer(
    help="pydoc-mintlify: generate & serve docs with Mintlify + pydoc-markdown"
)

ROOT = Path.cwd()

DEFAULT_CONFIG = "pydoc-markdown.yaml"

logger = logging.getLogger(__name__)


def _get_config(config_path: str) -> pm.PydocMarkdown:
    rs = pm.RenderSession(config_path)
    return rs.load()


def _get_python_loader(config: pm.PydocMarkdown) -> pm.PythonLoader:
    python_loaders = list(
        filter(lambda x: isinstance(x, pm.PythonLoader), config.loaders)
    )
    if len(python_loaders) == 0:
        raise ValueError(
            """No Python loader found. Please add one to use pydoc-mintlify cli.
            Example:
            loaders:
              - type: python
                search_path: ["src"] # or ["."]
                packages: ["<your package name>"]
            """
        )
    python_loader = python_loaders[0]
    if not python_loader.search_path:
        raise ValueError(
            """No search path found. Please add one to use pydoc-mintlify cli. Example:
            loaders:
              - type: python
                search_path: ["src"] # or ["."]
                packages: ["<your package name>"]
            """
        )
    return python_loaders[0]


def pydoc_markdown(cmd: list[str]):
    """
    Execute pydoc-markdown with the given command.
    """
    logger.debug(f"Executing pydoc-markdown: {cmd}")
    try:
        pm.cli.main(cmd)
    except SystemExit:
        return


def _render_modules(modules: list[str], config_path: str) -> None:
    """
    Render a single module.
    """
    session = pm.RenderSession(
        config=config_path,
    )

    config = session.load()

    # Update the config to only render specific modules
    python_loader = _get_python_loader(config)
    python_loader.modules = modules
    python_loader.packages = []

    # Weird but necearry hack to get the loader to use the correct search path to find the modules
    python_loader.search_path = python_loader.get_effective_search_path()

    session.render(config)


def _docs_build_impl(config_path: str) -> int:
    """
    Perform a full docs render.
    """
    pydoc_markdown([config_path])


def _docs_watch_impl(config_path: str) -> None:
    config = _get_config(config_path)
    python_loader = _get_python_loader(config)
    search_paths = python_loader.get_effective_search_path()
    logger.info(f"Watching {search_paths + [config_path]}")
    typer.echo(f"Watching {search_paths + [config_path]}")

    def derive_module_name_from_file(file_path: Path) -> Optional[str]:
        """
        Turn a changed file path under src/ into a Python module name.
        E.g., src/pkg/sub/mod.py -> pkg.sub.mod ; __init__.py -> pkg.sub
        """
        for path in search_paths:
            try:
                relative_path = file_path.relative_to(path)
            except ValueError:
                pass
            else:
                relative_no_ext = relative_path.with_suffix("")
                parts = list(relative_no_ext.parts)
                if not parts:
                    continue
                if parts[-1] == "__init__":
                    parts.pop()
                return ".".join(parts)
        return None

    # Initial build
    _docs_build_impl(config_path)
    config_path_obj = Path(config_path)

    for changes in watch(config_path_obj, *search_paths):
        # Determine which files changed
        changed_paths = [Path(p) for _, p in changes]
        cfg_changed = any(
            p.resolve() == config_path_obj.resolve() for p in changed_paths
        )
        py_changes = [p for p in changed_paths if p.suffix == ".py" and p.is_file()]

        if cfg_changed:
            logger.info("pydoc-markdown config changed. Regenerating all docs...")
            typer.echo("pydoc-markdown config changed. Regenerating all docs...")
            _docs_build_impl(config_path)
            continue

        # Rebuild only the modules that changed
        modules = [derive_module_name_from_file(p) for p in py_changes if p]
        if modules:
            logger.info(f"Rebuilding modules: {modules}")
            typer.echo(f"Rebuilding modules: {modules}")
            _render_modules(modules, config_path)


# ---------- Typer commands (only call helpers) ----------


@app.command("build")
def build(
    config: str = typer.Option(
        DEFAULT_CONFIG, "--config", "-c", help="Path to pydoc-markdown config file."
    ),
):
    """
    One-shot docs generation. Builds all autogrenerated .mdx files for your .py files.
    """
    code = _docs_build_impl(config)
    raise typer.Exit(code)


@app.command("docs-watch")
def docs_watch(
    config: str = typer.Option(DEFAULT_CONFIG, "--config", "-c"),
):
    """
    Watch Python sources & pydoc config and regenerate .mdx files.
    """
    _docs_watch_impl(config)


@app.command("dev")
def dev(
    config: str = typer.Option(DEFAULT_CONFIG, "--config", "-c"),
):
    """
    Equivalent of your `npm run dev`:
      1. docs-watch, which watches your .py files and rebuilds the .mdx files when they change
      2. mint dev, which runs the mintlify dev server and serves your .mdx files
    """
    # Initial full build; abort dev if it fails
    _docs_build_impl(config)

    config_obj = _get_config(config)
    renderer = config_obj.renderer
    if not isinstance(renderer, MintlifyRenderer):
        typer.echo(
            "Please configure the renderer to be a pydoc_mintlify.MintlifyRenderer in your pydoc-markdown.yaml file"
        )
        raise typer.Exit(1)

    docs_base_path = renderer.docs_base_path
    try:
        proc = subprocess.Popen(["mint", "dev"], cwd=ROOT / docs_base_path)
    except FileNotFoundError:
        typer.echo(
            "mint command not found. Please install it: https://www.mintlify.com/docs/installation"
        )
        raise typer.Exit(1)

    try:
        docs_watch(config)
    except KeyboardInterrupt:
        pass
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
