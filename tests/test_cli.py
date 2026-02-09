"""Tests for CLI commands."""

import json
import os

from click.testing import CliRunner

from lkr.cli import cli


def test_init(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    result = runner.invoke(cli, ["init", "My KB"])
    assert result.exit_code == 0
    assert (tmp_path / ".knowledge" / "config.yaml").exists()
    assert (tmp_path / "entries").is_dir()


def test_new_entry(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "Test KB"])
    result = runner.invoke(cli, ["new", "note", "Test Note", "-t", "test"])
    assert result.exit_code == 0
    assert "Created" in result.output


def test_new_entry_with_author(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "Test KB"])
    result = runner.invoke(cli, ["new", "guide", "My Guide", "-t", "dev", "-a", "alice"])
    assert result.exit_code == 0


def test_validate_clean(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "Test KB"])
    runner.invoke(cli, ["new", "note", "A Note", "-t", "test"])
    result = runner.invoke(cli, ["validate"])
    assert result.exit_code == 0


def test_cat_entry(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "Test KB"])
    new_result = runner.invoke(cli, ["new", "note", "Cat Test", "-t", "test"])

    # Extract the entry ID from output
    # Output is like "Created ab123456 at ..."
    entry_id = new_result.output.split()[1]

    result = runner.invoke(cli, ["cat", entry_id])
    assert result.exit_code == 0
    assert "Cat Test" in result.output


def test_get_entry(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "Test KB"])
    new_result = runner.invoke(cli, ["new", "note", "Get Test", "-t", "test"])
    entry_id = new_result.output.split()[1]

    result = runner.invoke(cli, ["get", entry_id])
    assert result.exit_code == 0
    assert "Get Test" in result.output


def test_index(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "Test KB"])
    runner.invoke(cli, ["new", "note", "Index Test", "-t", "test"])

    result = runner.invoke(cli, ["index"])
    assert result.exit_code == 0
    assert "1 entries" in result.output

    index_path = tmp_path / ".knowledge" / "index.json"
    assert index_path.exists()
    data = json.loads(index_path.read_text())
    assert data["entry_count"] == 1


def test_search(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "Test KB"])
    runner.invoke(cli, ["new", "note", "Searchable Note", "-t", "test"])

    result = runner.invoke(cli, ["search", "Searchable"])
    assert result.exit_code == 0
    assert "Searchable Note" in result.output


def test_search_no_results(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "Test KB"])

    result = runner.invoke(cli, ["search", "nonexistent"])
    assert result.exit_code == 0
    assert "No results" in result.output


def test_cat_nonexistent(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "Test KB"])

    result = runner.invoke(cli, ["cat", "zzzzzzzz"])
    assert result.exit_code == 1


def test_init_already_exists(tmp_path):
    runner = CliRunner()
    os.chdir(tmp_path)
    runner.invoke(cli, ["init", "First"])
    result = runner.invoke(cli, ["init", "Second"])
    # Should succeed (idempotent) but not overwrite config
    assert result.exit_code == 0
