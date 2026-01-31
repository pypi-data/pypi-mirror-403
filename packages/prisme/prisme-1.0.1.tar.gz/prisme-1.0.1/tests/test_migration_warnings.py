"""Tests for migration warning messages after generation (issues #55 and #57)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prism.cli import _show_migration_warnings
from prism.generators.base import GeneratorResult


@pytest.fixture
def mock_stack_spec() -> MagicMock:
    spec = MagicMock()
    spec.name = "TestProject"
    spec.generator.backend_output = "backend"
    return spec


class TestMigrationWarnings:
    """Tests for _show_migration_warnings."""

    def test_no_migrations_shows_initial_warning(
        self, tmp_path: Path, mock_stack_spec: MagicMock
    ) -> None:
        """Issue #57: When no migration files exist, show initial migration warning."""
        # Create alembic/versions directory with no .py files
        versions_dir = tmp_path / "backend" / "test_project" / "alembic" / "versions"
        versions_dir.mkdir(parents=True)

        results: dict[str, GeneratorResult] = {"models": GeneratorResult(written=1)}

        with patch("prism.cli.console") as mock_console, patch("prism.cli.Path") as mock_path_cls:
            mock_path_cls.cwd.return_value = tmp_path
            _show_migration_warnings(mock_stack_spec, results)

            # Check that Panel was printed with initial migration message
            calls = mock_console.print.call_args_list
            panel_calls = [c for c in calls if len(c.args) > 0 and hasattr(c.args[0], "title")]
            assert any("Initial Migration" in str(c.args[0].title) for c in panel_calls)

    def test_model_changes_shows_migration_warning(
        self, tmp_path: Path, mock_stack_spec: MagicMock
    ) -> None:
        """Issue #55: When models were written, show migration needed warning."""
        # Create alembic/versions directory WITH a migration file
        versions_dir = tmp_path / "backend" / "test_project" / "alembic" / "versions"
        versions_dir.mkdir(parents=True)
        (versions_dir / "001_initial.py").write_text("# migration")

        results: dict[str, GeneratorResult] = {"models": GeneratorResult(written=3)}

        with patch("prism.cli.console") as mock_console, patch("prism.cli.Path") as mock_path_cls:
            mock_path_cls.cwd.return_value = tmp_path
            _show_migration_warnings(mock_stack_spec, results)

            calls = mock_console.print.call_args_list
            panel_calls = [c for c in calls if len(c.args) > 0 and hasattr(c.args[0], "title")]
            assert any("Migration May Be Needed" in str(c.args[0].title) for c in panel_calls)

    def test_no_warning_when_no_model_changes(
        self, tmp_path: Path, mock_stack_spec: MagicMock
    ) -> None:
        """No warning when models weren't written."""
        versions_dir = tmp_path / "backend" / "test_project" / "alembic" / "versions"
        versions_dir.mkdir(parents=True)
        (versions_dir / "001_initial.py").write_text("# migration")

        results: dict[str, GeneratorResult] = {"models": GeneratorResult(written=0)}

        with patch("prism.cli.console") as mock_console, patch("prism.cli.Path") as mock_path_cls:
            mock_path_cls.cwd.return_value = tmp_path
            _show_migration_warnings(mock_stack_spec, results)

            # No panel should be printed
            calls = mock_console.print.call_args_list
            panel_calls = [c for c in calls if len(c.args) > 0 and hasattr(c.args[0], "title")]
            assert len(panel_calls) == 0
