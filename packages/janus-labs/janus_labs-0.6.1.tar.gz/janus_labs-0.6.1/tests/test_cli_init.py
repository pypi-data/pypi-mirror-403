"""Tests for janus-labs init command."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from cli.main import cmd_init
import argparse


class TestCmdInit:
    """Tests for the init command."""

    def test_init_creates_workspace(self):
        """Test successful workspace initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "janus-task"
            args = argparse.Namespace(
                suite="refactor-storm",
                behavior="BHV-002-refactor-complexity",
                output=str(output)
            )
            result = cmd_init(args)
            assert result == 0
            assert output.exists()
            assert (output / ".janus-task.json").exists()

    def test_init_unknown_suite(self, capsys):
        """Test error on unknown suite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                suite="nonexistent-suite",
                behavior="BHV-002",
                output=str(Path(tmpdir) / "janus-task")
            )
            result = cmd_init(args)
            assert result == 1
            captured = capsys.readouterr()
            assert "Unknown suite" in captured.err
            assert "Try:" in captured.err

    def test_init_unknown_behavior(self, capsys):
        """Test error on unknown behavior with suggestions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                suite="refactor-storm",
                behavior="BHV-999-nonexistent",
                output=str(Path(tmpdir) / "janus-task")
            )
            result = cmd_init(args)
            assert result == 1
            captured = capsys.readouterr()
            assert "Unknown behavior" in captured.err
            assert "Available behaviors" in captured.err
            assert "Try:" in captured.err

    def test_init_prefix_matching(self, capsys):
        """Test behavior prefix matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "janus-task"
            args = argparse.Namespace(
                suite="refactor-storm",
                behavior="BHV-002",  # Prefix only
                output=str(output)
            )
            result = cmd_init(args)
            assert result == 0
            captured = capsys.readouterr()
            assert "Matched:" in captured.out

    def test_init_directory_not_empty(self, capsys):
        """Test error when directory is not empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "janus-task"
            output.mkdir()
            (output / "existing-file.txt").write_text("content")

            args = argparse.Namespace(
                suite="refactor-storm",
                behavior="BHV-002-refactor-complexity",
                output=str(output)
            )
            result = cmd_init(args)
            assert result == 1
            captured = capsys.readouterr()
            assert "not empty" in captured.err
            assert "Try:" in captured.err


class TestInteractiveInit:
    """Tests for interactive init mode."""

    def test_init_interactive_by_number(self):
        """Test interactive selection by number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "janus-task"
            args = argparse.Namespace(
                suite="refactor-storm",
                behavior=None,  # Triggers interactive
                output=str(output)
            )
            with patch('builtins.input', return_value='1'):
                result = cmd_init(args)
            assert result == 0
            assert output.exists()

    def test_init_interactive_by_id(self):
        """Test interactive selection by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "janus-task"
            args = argparse.Namespace(
                suite="refactor-storm",
                behavior=None,
                output=str(output)
            )
            with patch('builtins.input', return_value='BHV-002'):
                result = cmd_init(args)
            assert result == 0

    def test_init_interactive_abort(self, capsys):
        """Test Ctrl+C aborts gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(
                suite="refactor-storm",
                behavior=None,
                output=str(Path(tmpdir) / "janus-task")
            )
            with patch('builtins.input', side_effect=KeyboardInterrupt):
                result = cmd_init(args)
            assert result == 1
            captured = capsys.readouterr()
            assert "Aborted" in captured.err
