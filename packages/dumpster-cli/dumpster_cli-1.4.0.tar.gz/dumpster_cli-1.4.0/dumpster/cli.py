import typer
from pathlib import Path
from typing import List, Optional

from dumpster.api import dump, tree

app = typer.Typer()

DEFAULT_DUMP_YAML = """# Dumpster configuration
dumps:
  - name: example1
#    extensions:
#      - .py
#      - .md
#      - .json
#      - .toml
    contents:
      - **/*.py
      - tests
      - README.md
      - pyproject.toml
"""


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    contents: Optional[List[str]] = typer.Option(
        None,
        "--contents",
        "-c",
        help="Override dump.yaml contents entries (repeatable).",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Select dump profile by name (regex/fuzzy). Only applies when dump.yaml has `dumps:`.",
    ),
):
    """
    Calling without command starts the dump.
    """
    if ctx.invoked_subcommand is None:
        dump(contents=contents, name=name)


@app.command(help="Run dumpster")
def run(
    contents: Optional[List[str]] = typer.Option(
        None,
        "--contents",
        "-c",
        help="Override dump.yaml contents entries (repeatable).",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Select dump profile by name (regex/fuzzy). Only applies when dump.yaml has `dumps:`.",
    ),
):
    """Default command to dump code based on dump.yaml settings"""
    dump(contents=contents, name=name)


@app.command(help="Generate a dumpster configuration")
def init(
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path"
    )
):
    """Create/update dump.yaml and .gitignore"""
    dump_yaml_path = Path("dump.yaml")
    if not dump_yaml_path.exists():
        dump_yaml_path.write_text(DEFAULT_DUMP_YAML, encoding="utf-8")
        typer.echo(f"Created {dump_yaml_path}")
    else:
        typer.echo(f"File {dump_yaml_path} already exists, skipping creation")

    gitignore_path = Path(".gitignore")
    output_file = output or ".dumpster"

    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        if output_file not in content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(f"\n# Dumpster output\n{output_file}\n")
            typer.echo(f"Updated {gitignore_path} with {output_file}")
        else:
            typer.echo(
                f"Reference of {output_file} is already in {gitignore_path}, skipping"
            )
    else:
        gitignore_path.write_text(
            f"# Dumpster output\n{output_file}\n", encoding="utf-8"
        )
        typer.echo(f"Created {gitignore_path} with {output_file}")


@app.command(
    help="Show the list of files that would be included in the dump (tree view)",
    name="tree",
)
def tree_cmd(
    contents: Optional[List[str]] = typer.Option(
        None,
        "--contents",
        "-c",
        help="Override dump.yaml contents entries (repeatable).",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Select dump profile by name (regex/fuzzy). Only applies when dump.yaml has `dumps:`.",
    ),
):
    typer.echo(tree(contents=contents, name=name), nl=False)


def cli():
    app()
