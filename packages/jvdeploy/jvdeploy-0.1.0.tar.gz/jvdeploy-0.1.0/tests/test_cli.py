"""Tests for CLI module."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from jvdeploy.cli import handle_generate, handle_init, main


def test_main_help_flag(monkeypatch, capsys):
    """Test main function with help flag."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower()
    assert "generate" in captured.out.lower()
    assert "deploy" in captured.out.lower()


def test_main_version_flag(monkeypatch, capsys):
    """Test main function with version flag."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "--version"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "0.1.0" in captured.out


def test_main_no_command(monkeypatch, capsys):
    """Test main function with no command shows help."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower()


def test_generate_command_success(mock_jvagent_app, monkeypatch, capsys):
    """Test generate command with successful execution."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "generate", str(mock_jvagent_app)])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    # Check Dockerfile was created
    dockerfile_path = mock_jvagent_app / "Dockerfile"
    assert dockerfile_path.exists()

    captured = capsys.readouterr()
    assert "Dockerfile generated successfully" in captured.out


def test_generate_command_current_directory(mock_jvagent_app, monkeypatch, capsys):
    """Test generate command in current directory."""
    monkeypatch.chdir(mock_jvagent_app)
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "generate"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    # Check Dockerfile was created
    dockerfile_path = mock_jvagent_app / "Dockerfile"
    assert dockerfile_path.exists()


def test_generate_command_invalid_path(monkeypatch, capsys):
    """Test generate command with invalid path."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "generate", "/invalid/path"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_generate_command_missing_app_yaml(temp_dir, monkeypatch):
    """Test generate command fails with missing app.yaml."""
    app_root = temp_dir / "invalid_app"
    app_root.mkdir()

    monkeypatch.setattr(sys, "argv", ["jvdeploy", "generate", str(app_root)])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_init_command_help(monkeypatch, capsys):
    """Test init command help."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "init", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "init" in captured.out.lower()
    assert "--lambda" in captured.out.lower()
    assert "--kubernetes" in captured.out.lower()


def test_deploy_command_help(monkeypatch, capsys):
    """Test deploy command help."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "deploy", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "deploy" in captured.out.lower()
    assert "lambda" in captured.out.lower()


def test_deploy_lambda_help(monkeypatch, capsys):
    """Test deploy lambda command help."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "deploy", "lambda", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "lambda" in captured.out.lower()
    assert "--all" in captured.out.lower()
    assert "--dry-run" in captured.out.lower()


def test_status_command_help(monkeypatch, capsys):
    """Test status command help."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "status", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "status" in captured.out.lower()


def test_logs_command_help(monkeypatch, capsys):
    """Test logs command help."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "logs", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "logs" in captured.out.lower()


def test_destroy_command_help(monkeypatch, capsys):
    """Test destroy command help."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "destroy", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "destroy" in captured.out.lower()


def test_debug_flag(mock_jvagent_app, monkeypatch, capsys):
    """Test debug flag enables debug logging."""
    monkeypatch.setattr(
        sys, "argv", ["jvdeploy", "--debug", "generate", str(mock_jvagent_app)]
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


def test_main_keyboard_interrupt(mock_jvagent_app, monkeypatch, capsys):
    """Test main function handles keyboard interrupt gracefully."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "generate", str(mock_jvagent_app)])

    with patch("jvdeploy.cli.Bundler") as mock_bundler_class:
        mock_bundler = Mock()
        mock_bundler.generate_dockerfile.side_effect = KeyboardInterrupt()
        mock_bundler_class.return_value = mock_bundler

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 130

        captured = capsys.readouterr()
        assert "cancelled by user" in captured.out


def test_main_unexpected_exception(mock_jvagent_app, monkeypatch):
    """Test main function handles unexpected exceptions."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "generate", str(mock_jvagent_app)])

    with patch("jvdeploy.cli.Bundler") as mock_bundler_class:
        mock_bundler = Mock()
        mock_bundler.generate_dockerfile.side_effect = RuntimeError("Unexpected error")
        mock_bundler_class.return_value = mock_bundler

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1


def test_bundler_generation_fails(mock_jvagent_app, monkeypatch):
    """Test when bundler generation fails."""
    monkeypatch.setattr(sys, "argv", ["jvdeploy", "generate", str(mock_jvagent_app)])

    with patch("jvdeploy.cli.Bundler") as mock_bundler_class:
        mock_bundler = Mock()
        mock_bundler.generate_dockerfile.return_value = False
        mock_bundler_class.return_value = mock_bundler

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
