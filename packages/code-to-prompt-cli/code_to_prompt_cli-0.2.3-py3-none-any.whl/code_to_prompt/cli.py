"""
CLI interface for code-to-prompt.

This module handles argument parsing and user interaction.
Core logic is delegated to the engine module.
"""

from pathlib import Path

import click
from rich.console import Console

from .engine import collect_files, format_output, validate_skip_paths


OUTPUT_DIR = ".code-to-prompt"


def _estimate_tokens(text: str) -> int | None:
    """Estimate token count using tiktoken with cl100k_base encoding."""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return None


console = Console()


@click.command()
@click.argument("folder", required=True)
@click.option(
    "--output", "-o",
    default=None,
    help=f"Output filename (created in {OUTPUT_DIR}/ directory)",
)
@click.option(
    "--tokens",
    is_flag=True,
    help="Estimate token count only (no file created)",
)
@click.option(
    "--skip", "-s",
    multiple=True,
    help="Skip files or folders (relative to input folder)",
)
def run(
    folder: str,
    output: str | None,
    tokens: bool,
    skip: tuple[str, ...],
) -> None:
    """Convert a code folder into a single LLM-ready text file.
    
    Output is written to .code-to-prompt/ directory in current working directory.
    
    Examples:
    
    \b
      code-to-prompt .
      code-to-prompt . -s src -s tests
      code-to-prompt . --tokens -s src
      code-to-prompt . -o custom.txt
    """
    folder_path = Path(folder).resolve()
    
    if not folder_path.is_dir():
        console.print(f"[red]Error:[/red] Not a directory: {folder_path}")
        raise SystemExit(1)

    # Validate skip paths
    skip_list = list(skip)
    skip_paths_set: set[Path] | None = None
    if skip_list:
        valid_paths, errors = validate_skip_paths(folder_path, skip_list)
        if errors:
            console.print("[red]Error:[/red] Invalid skip paths:")
            for e in errors:
                console.print(f"  - {e}")
            raise SystemExit(1)
        skip_paths_set = set(valid_paths)

    # Collect files
    files = collect_files(folder_path, skip_paths_set)
    if not files:
        console.print("[red]Error:[/red] No files found")
        raise SystemExit(1)

    # List files
    console.print(f"\nFound {len(files)} files:")
    cwd = Path.cwd()
    for file_path in files:
        try:
            rel_path = file_path.relative_to(cwd)
        except ValueError:
            rel_path = file_path.relative_to(folder_path)
        console.print(f"  {rel_path}")

    # Format output
    content = format_output(files, folder_path)

    # Token estimation mode
    if tokens:
        token_count = _estimate_tokens(content)
        if token_count is not None:
            console.print(f"\nEstimated tokens: ~{token_count:,}")
        else:
            console.print("\n[yellow]Warning:[/yellow] Could not estimate token count (tiktoken not installed?)")
        return

    # Write output
    output_dir = Path.cwd() / OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    
    filename = output or f"{folder_path.name}_output.txt"
    output_file = output_dir / filename
    output_file.write_text(content, encoding="utf-8")
    
    console.print(f"\nCreated {output_file}")


def main() -> None:
    """Entry point for the CLI."""
    run()


if __name__ == "__main__":
    main()
