"""Tests for the CLI module."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from code_to_prompt.cli import run, OUTPUT_DIR


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project structure for testing."""
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "utils.py").write_text("def helper(): pass")
    subdir = tmp_path / "src"
    subdir.mkdir()
    (subdir / "app.py").write_text("class App: pass")
    return tmp_path


class TestCLI:
    """Tests for CLI commands."""

    def test_basic_run(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(run, [str(sample_project)])
        assert result.exit_code == 0
        assert "Created" in result.output
        assert "3 files" in result.output
        output_file = tmp_path / OUTPUT_DIR / f"{sample_project.name}_output.txt"
        assert output_file.exists()

    def test_custom_output_filename(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(run, [str(sample_project), "-o", "custom.txt"])
        assert result.exit_code == 0
        output_file = tmp_path / OUTPUT_DIR / "custom.txt"
        assert output_file.exists()

    def test_lists_files_by_default(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(run, [str(sample_project)])
        assert result.exit_code == 0
        assert "Found 3 files:" in result.output
        assert "main.py" in result.output

    def test_missing_folder_argument(self, runner):
        result = runner.invoke(run, [])
        assert result.exit_code != 0

    def test_nonexistent_folder(self, runner, tmp_path):
        result = runner.invoke(run, [str(tmp_path / "nonexistent")])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_overwrites_existing_output(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        output_dir = tmp_path / OUTPUT_DIR
        output_dir.mkdir()
        output_file = output_dir / "existing.txt"
        output_file.write_text("old content")
        result = runner.invoke(run, [str(sample_project), "-o", "existing.txt"])
        assert result.exit_code == 0
        assert "Created" in result.output
        content = output_file.read_text()
        assert "old content" not in content
        assert "main.py" in content

    def test_skip_single(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(run, [str(sample_project), "-s", "utils.py"])
        assert result.exit_code == 0
        assert "2 files" in result.output
        output_file = tmp_path / OUTPUT_DIR / f"{sample_project.name}_output.txt"
        content = output_file.read_text()
        assert "utils.py" not in content

    def test_skip_multiple_flags(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(run, [str(sample_project), "-s", "utils.py", "-s", "src"])
        assert result.exit_code == 0
        assert "1 files" in result.output
        output_file = tmp_path / OUTPUT_DIR / f"{sample_project.name}_output.txt"
        content = output_file.read_text()
        assert "main.py" in content
        assert "utils.py" not in content
        assert "app.py" not in content

    def test_skip_directory(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(run, [str(sample_project), "-s", "src"])
        assert result.exit_code == 0
        assert "2 files" in result.output
        output_file = tmp_path / OUTPUT_DIR / f"{sample_project.name}_output.txt"
        content = output_file.read_text()
        assert "app.py" not in content

    def test_tokens_flag_no_file_created(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(run, [str(sample_project), "--tokens"])
        assert result.exit_code == 0
        assert "Estimated tokens:" in result.output
        assert not (tmp_path / OUTPUT_DIR).exists()

    def test_tokens_flag_with_skip(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(run, [str(sample_project), "--tokens", "-s", "src"])
        assert result.exit_code == 0
        assert "2 files" in result.output
        assert "Estimated tokens:" in result.output

    def test_invalid_skip_path(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(run, [str(sample_project), "-s", "nonexistent"])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_output_dir_created_automatically(self, runner, sample_project, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert not (tmp_path / OUTPUT_DIR).exists()
        result = runner.invoke(run, [str(sample_project)])
        assert result.exit_code == 0
        assert (tmp_path / OUTPUT_DIR).is_dir()
