"""Tests for the engine module."""

import pytest
from pathlib import Path

from code_to_prompt.engine import (
    convert_folder,
    collect_files,
    format_output,
    validate_skip_paths,
    _should_include_file,
    _is_path_under_any,
)


class TestShouldIncludeFile:
    """Tests for file inclusion logic."""

    def test_includes_python_files(self, tmp_path):
        f = tmp_path / "test.py"
        f.touch()
        assert _should_include_file(f) is True

    def test_includes_javascript_files(self, tmp_path):
        f = tmp_path / "app.js"
        f.touch()
        assert _should_include_file(f) is True

    def test_excludes_binary_files(self, tmp_path):
        f = tmp_path / "image.png"
        f.touch()
        assert _should_include_file(f) is False

    def test_excludes_lock_files(self, tmp_path):
        f = tmp_path / "package.lock"
        f.touch()
        assert _should_include_file(f) is False

    def test_excludes_ds_store(self, tmp_path):
        f = tmp_path / ".DS_Store"
        f.touch()
        assert _should_include_file(f) is False

    def test_includes_dockerfile(self, tmp_path):
        f = tmp_path / "Dockerfile"
        f.touch()
        assert _should_include_file(f) is True

    def test_includes_makefile(self, tmp_path):
        f = tmp_path / "Makefile"
        f.touch()
        assert _should_include_file(f) is True


class TestValidateSkipPaths:
    """Tests for skip path validation."""

    def test_valid_skip_path(self, tmp_path):
        subdir = tmp_path / "src"
        subdir.mkdir()
        valid, errors = validate_skip_paths(tmp_path, ["src"])
        assert len(valid) == 1
        assert valid[0] == subdir.resolve()
        assert errors == []

    def test_nonexistent_skip_path(self, tmp_path):
        valid, errors = validate_skip_paths(tmp_path, ["nonexistent"])
        assert valid == []
        assert len(errors) == 1
        assert "does not exist" in errors[0]

    def test_escape_via_dotdot(self, tmp_path):
        valid, errors = validate_skip_paths(tmp_path, ["../outside"])
        assert valid == []
        assert len(errors) == 1
        assert "escapes input folder" in errors[0]

    def test_absolute_path_rejected(self, tmp_path):
        import os
        if os.name == 'nt':
            abs_path = "C:\\absolute\\path"
        else:
            abs_path = "/absolute/path"
        valid, errors = validate_skip_paths(tmp_path, [abs_path])
        assert valid == []
        assert len(errors) == 1
        assert "must be relative" in errors[0]

    def test_duplicate_skip_paths_deduplicated(self, tmp_path):
        subdir = tmp_path / "src"
        subdir.mkdir()
        valid, errors = validate_skip_paths(tmp_path, ["src", "src", "src"])
        assert len(valid) == 1
        assert errors == []

    def test_multiple_errors_collected(self, tmp_path):
        valid, errors = validate_skip_paths(tmp_path, ["nonexistent1", "nonexistent2"])
        assert valid == []
        assert len(errors) == 2


class TestIsPathUnderAny:
    """Tests for path containment check."""

    def test_exact_match(self, tmp_path):
        skip = {tmp_path / "src"}
        assert _is_path_under_any(tmp_path / "src", skip) is True

    def test_descendant_match(self, tmp_path):
        skip = {tmp_path / "src"}
        assert _is_path_under_any(tmp_path / "src" / "file.py", skip) is True

    def test_no_match(self, tmp_path):
        skip = {tmp_path / "src"}
        assert _is_path_under_any(tmp_path / "tests", skip) is False


class TestCollectFiles:
    """Tests for file collection."""

    def test_collects_python_files(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("def helper(): pass")
        files = collect_files(tmp_path)
        assert len(files) == 2
        assert all(f.suffix == ".py" for f in files)

    def test_skips_pycache(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')")
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "main.cpython-312.pyc").write_bytes(b"bytecode")
        files = collect_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "main.py"

    def test_skips_node_modules(self, tmp_path):
        (tmp_path / "index.js").write_text("console.log('hi')")
        nm = tmp_path / "node_modules"
        nm.mkdir()
        (nm / "dep.js").write_text("module.exports = {}")
        files = collect_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "index.js"

    def test_respects_skip_paths(self, tmp_path):
        (tmp_path / "keep.py").write_text("keep")
        skip_dir = tmp_path / "skip_me"
        skip_dir.mkdir()
        (skip_dir / "skipped.py").write_text("skip")
        files = collect_files(tmp_path, {skip_dir.resolve()})
        assert len(files) == 1
        assert files[0].name == "keep.py"

    def test_returns_sorted_files(self, tmp_path):
        (tmp_path / "z.py").write_text("")
        (tmp_path / "a.py").write_text("")
        (tmp_path / "m.py").write_text("")
        files = collect_files(tmp_path)
        names = [f.name for f in files]
        assert names == sorted(names)


class TestFormatOutput:
    """Tests for output formatting."""

    def test_formats_single_file(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("print('hello')")
        output = format_output([f], tmp_path)
        assert "test.py" in output
        assert "print('hello')" in output
        assert "```" in output

    def test_formats_multiple_files(self, tmp_path):
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("a")
        f2.write_text("b")
        output = format_output([f1, f2], tmp_path)
        assert "a.py" in output
        assert "b.py" in output


class TestConvertFolder:
    """Tests for the main convert_folder function."""

    def test_basic_conversion(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')")
        output = tmp_path / "output.txt"
        result_path, files = convert_folder(str(tmp_path), str(output))
        assert result_path == output
        assert len(files) == 1
        assert output.exists()
        content = output.read_text()
        assert "main.py" in content
        assert "print('hello')" in content

    def test_raises_on_nonexistent_folder(self, tmp_path):
        with pytest.raises(ValueError, match="Not a directory"):
            convert_folder(str(tmp_path / "nonexistent"), str(tmp_path / "out.txt"))

    def test_raises_on_no_files(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(ValueError, match="No files found"):
            convert_folder(str(empty), str(tmp_path / "out.txt"))

    def test_raises_on_invalid_skip(self, tmp_path):
        (tmp_path / "main.py").write_text("code")
        with pytest.raises(ValueError, match="Invalid skip paths"):
            convert_folder(str(tmp_path), str(tmp_path / "out.txt"), skip=["nonexistent"])

    def test_skip_file(self, tmp_path):
        (tmp_path / "keep.py").write_text("keep")
        (tmp_path / "skip.py").write_text("skip")
        output = tmp_path / "output.txt"
        _, files = convert_folder(str(tmp_path), str(output), skip=["skip.py"])
        assert len(files) == 1
        content = output.read_text()
        assert "keep.py" in content
        assert "skip.py" not in content

    def test_skip_directory(self, tmp_path):
        (tmp_path / "main.py").write_text("main")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "sub.py").write_text("sub")
        output = tmp_path / "output.txt"
        _, files = convert_folder(str(tmp_path), str(output), skip=["subdir"])
        assert len(files) == 1
        content = output.read_text()
        assert "main.py" in content
        assert "sub.py" not in content
