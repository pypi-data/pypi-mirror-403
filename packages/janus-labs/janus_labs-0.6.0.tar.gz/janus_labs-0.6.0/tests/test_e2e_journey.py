"""End-to-end journey test: init -> score -> submit."""
import pytest
import tempfile
import subprocess
import json
from pathlib import Path


class TestE2EJourney:
    """Full user journey tests."""

    def test_init_score_flow(self):
        """Test the complete init -> modify -> score flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "janus-task"
            cwd = Path(__file__).parent.parent

            # Step 1: Init
            result = subprocess.run(
                ["python", "-m", "janus_labs", "init",
                 "--behavior", "BHV-002-refactor-complexity",
                 "--output", str(workspace)],
                capture_output=True, text=True,
                cwd=cwd
            )
            assert result.returncode == 0, f"Init failed: {result.stderr}"
            assert workspace.exists()
            assert (workspace / ".janus-task.json").exists()

            # Step 2: Initialize git repo (required for scoring)
            subprocess.run(["git", "init"], cwd=workspace, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=workspace, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=workspace, capture_output=True)

            # Step 3: Make a change and commit
            solution_file = workspace / "solution.py"
            solution_file.write_text("# Refactored solution\ndef calculate():\n    return 42\n")
            subprocess.run(["git", "add", "."], cwd=workspace, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Add solution"], cwd=workspace, capture_output=True)

            # Step 4: Score
            result = subprocess.run(
                ["python", "-m", "janus_labs", "score",
                 "--workspace", str(workspace)],
                capture_output=True, text=True,
                cwd=cwd
            )
            # Score may pass or fail based on solution quality, but should not error
            # The command returns 0 for PASS, 1 for FAIL - both are valid outcomes
            assert result.returncode in [0, 1], f"Score errored: {result.stderr}"

    def test_init_with_prefix(self):
        """Test init with behavior prefix matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "janus-task"
            cwd = Path(__file__).parent.parent

            result = subprocess.run(
                ["python", "-m", "janus_labs", "init",
                 "--behavior", "BHV-002",  # Prefix only
                 "--output", str(workspace)],
                capture_output=True, text=True,
                cwd=cwd
            )
            assert result.returncode == 0, f"Init failed: {result.stderr}"
            assert "Matched:" in result.stdout

    def test_status_command(self):
        """Test status command in workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "janus-task"
            cwd = Path(__file__).parent.parent

            # Init first
            subprocess.run(
                ["python", "-m", "janus_labs", "init",
                 "--behavior", "BHV-002-refactor-complexity",
                 "--output", str(workspace)],
                capture_output=True,
                cwd=cwd
            )

            # Then status
            result = subprocess.run(
                ["python", "-m", "janus_labs", "status",
                 "--workspace", str(workspace)],
                capture_output=True, text=True,
                cwd=cwd
            )
            assert result.returncode == 0, f"Status failed: {result.stderr}"
            assert "BHV-002" in result.stdout
            assert "refactor-storm" in result.stdout

    def test_status_not_in_workspace(self):
        """Test status command outside workspace shows helpful error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(__file__).parent.parent

            result = subprocess.run(
                ["python", "-m", "janus_labs", "status",
                 "--workspace", tmpdir],
                capture_output=True, text=True,
                cwd=cwd
            )
            assert result.returncode == 1
            assert "Not in a Janus workspace" in result.stderr
            assert "Try:" in result.stderr

    def test_init_unknown_behavior_shows_help(self):
        """Test that init with unknown behavior shows actionable help."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "janus-task"
            cwd = Path(__file__).parent.parent

            result = subprocess.run(
                ["python", "-m", "janus_labs", "init",
                 "--behavior", "INVALID-BEHAVIOR",
                 "--output", str(workspace)],
                capture_output=True, text=True,
                cwd=cwd
            )
            assert result.returncode == 1
            assert "Unknown behavior" in result.stderr
            assert "Try:" in result.stderr
            assert "Available behaviors" in result.stderr
