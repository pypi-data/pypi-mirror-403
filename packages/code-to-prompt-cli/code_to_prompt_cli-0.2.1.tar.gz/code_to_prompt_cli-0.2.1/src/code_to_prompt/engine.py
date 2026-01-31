"""
Core engine for code-to-prompt.

This module contains pure logic with no user interaction or console I/O.
All filesystem operations are explicit and return values rather than printing.

Public API:
    - convert_folder(): One-shot conversion
    - collect_files(): File collection without writing
    - format_output(): Format collected files as prompt text
"""

import os
from pathlib import Path

INCLUDE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.html', '.css', '.scss', '.sass', '.less',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.md', '.rst', '.txt',
    '.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd',
    '.java', '.kt', '.scala', '.go', '.rs', '.rb', '.php',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.m',
    '.sql', '.graphql', '.proto',
}

# Dotfiles where the entire filename looks like an extension
INCLUDE_DOTFILES = {'.env', '.gitignore', '.dockerignore'}

# Extensionless files to include
INCLUDE_NAMES = {'Dockerfile', 'Makefile', 'Procfile', 'Gemfile'}

SKIP_DIRS = {
    '__pycache__', '.git', '.svn', '.hg', 'node_modules',
    '.venv', 'venv', '.tox', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', 'dist', 'build',
    '.eggs', '.idea', '.vscode', '.vs', '.code-to-prompt',
}

SKIP_FILES = {'.DS_Store', 'Thumbs.db', '.gitkeep'}

SKIP_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
    '.exe', '.bin', '.class', '.jar',
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.mp3', '.mp4', '.wav', '.avi', '.mov',
    '.woff', '.woff2', '.ttf', '.eot',
    '.lock', '.log', '.db', '.sqlite', '.sqlite3',
}


def validate_skip_paths(
    folder: Path,
    skip_paths: list[str],
) -> tuple[list[Path], list[str]]:
    """
    Validate and resolve skip paths against the input folder.
    
    Args:
        folder: Canonical absolute path to input folder
        skip_paths: Raw skip path strings from CLI
    
    Returns:
        Tuple of (valid_canonical_paths, error_messages)
    """
    valid: list[Path] = []
    errors: list[str] = []
    seen: set[str] = set()
    
    for skip in skip_paths:
        if skip in seen:
            continue
        seen.add(skip)
        
        if Path(skip).is_absolute():
            errors.append(f"Skip path must be relative to input folder: {skip}")
            continue
        
        candidate = (folder / skip).resolve()
        
        try:
            candidate.relative_to(folder)
        except ValueError:
            errors.append(f"Skip path escapes input folder: {skip}")
            continue
        
        if not candidate.exists():
            errors.append(f"Skip path does not exist: {skip}")
            continue
        
        valid.append(candidate)
    
    return valid, errors


def _should_include_file(path: Path) -> bool:
    """Determine if a file should be included based on extension/name rules."""
    if path.name in SKIP_FILES:
        return False
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return False
    if path.suffix.lower() in INCLUDE_EXTENSIONS:
        return True
    if path.name.lower() in INCLUDE_DOTFILES:
        return True
    if path.name in INCLUDE_NAMES:
        return True
    return False


def _is_path_under_any(path: Path, skip_paths: set[Path]) -> bool:
    """Check if path is equal to or a descendant of any skip path."""
    for skip_path in skip_paths:
        if path == skip_path:
            return True
        try:
            path.relative_to(skip_path)
            return True
        except ValueError:
            continue
    return False


def collect_files(
    folder: Path,
    skip_paths: set[Path] | None = None,
) -> list[Path]:
    """
    Collect all includable files from a folder.
    
    Args:
        folder: Canonical absolute path to input folder
        skip_paths: Set of canonical absolute paths to skip
    
    Returns:
        Sorted list of file paths to include
    """
    files = []
    skip_paths = skip_paths or set()
    
    for root, dirs, filenames in os.walk(folder, followlinks=False):
        root_path = Path(root).resolve()
        
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not _is_path_under_any((root_path / d).resolve(), skip_paths)
        ]
        
        for name in filenames:
            path = (root_path / name).resolve()
            
            if _is_path_under_any(path, skip_paths):
                continue
            
            if _should_include_file(path):
                files.append(path)
    
    return sorted(files)


def format_output(files: list[Path], base_folder: Path) -> str:
    """
    Format collected files as LLM-ready prompt text.
    
    Args:
        files: List of file paths to include
        base_folder: Base folder for relative path computation
    
    Returns:
        Formatted string with all file contents
    """
    cwd = Path.cwd()
    entries = []
    
    for path in files:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        
        try:
            rel_path = path.relative_to(cwd)
        except ValueError:
            rel_path = path.relative_to(base_folder)
        
        entries.append(f"{rel_path}\n```\n{content.rstrip()}\n```")
    
    return "\n\n".join(entries) + "\n\n" if entries else ""


def convert_folder(
    folder_path: str,
    output_path: str | None = None,
    skip: list[str] | None = None,
) -> tuple[Path, list[Path]]:
    """
    Convenience function to convert a folder to a single LLM-ready text file.
    
    This is a one-shot wrapper around collect_files() + format_output() for
    callers who want simple file-to-file conversion without composing the
    primitives directly.
    
    Args:
        folder_path: Path to the source folder
        output_path: Output file path (defaults to <folder_name>_output.txt)
        skip: List of file or folder paths (relative to folder) to skip
    
    Returns:
        Tuple of (output_path, included_files)
    
    Raises:
        ValueError: If folder doesn't exist, skip paths are invalid, or no files found
    """
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise ValueError(f"Not a directory: {folder}")

    output = Path(output_path) if output_path else Path(f"{folder.name}_output.txt")
    
    skip_paths: set[Path] | None = None
    if skip:
        valid_paths, errors = validate_skip_paths(folder, skip)
        if errors:
            error_message = "Invalid skip paths:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_message)
        skip_paths = set(valid_paths)

    files = collect_files(folder, skip_paths)
    if not files:
        raise ValueError("No files found")

    content = format_output(files, folder)
    output.write_text(content, encoding="utf-8")
    
    return output, files
