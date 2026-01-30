"""Tests for Bundler class."""

from pathlib import Path

import pytest

from jvdeploy import Bundler


def test_bundler_init(mock_jvagent_app):
    """Test Bundler initialization."""
    bundler = Bundler(app_root=str(mock_jvagent_app))

    assert bundler.app_root.resolve() == mock_jvagent_app.resolve()
    assert isinstance(bundler.app_root, Path)


def test_bundler_init_relative_path(mock_jvagent_app, monkeypatch):
    """Test Bundler initialization with relative path."""
    # Change to parent directory
    monkeypatch.chdir(mock_jvagent_app.parent)

    bundler = Bundler(app_root=mock_jvagent_app.name)

    assert bundler.app_root.resolve() == mock_jvagent_app.resolve()


def test_bundler_validate_app_success(mock_jvagent_app):
    """Test app validation with valid app.yaml."""
    bundler = Bundler(app_root=str(mock_jvagent_app))

    assert bundler._validate_app() is True


def test_bundler_validate_app_missing_app_yaml(temp_dir):
    """Test app validation with missing app.yaml."""
    app_root = temp_dir / "invalid_app"
    app_root.mkdir()

    bundler = Bundler(app_root=str(app_root))

    assert bundler._validate_app() is False


def test_bundler_generate_dockerfile_success(mock_jvagent_app):
    """Test successful Dockerfile generation."""
    bundler = Bundler(app_root=str(mock_jvagent_app))

    success = bundler.generate_dockerfile()

    assert success is True

    # Check Dockerfile was created
    dockerfile_path = mock_jvagent_app / "Dockerfile"
    assert dockerfile_path.exists()

    # Check Dockerfile content
    dockerfile_content = dockerfile_path.read_text()
    assert "FROM registry.v75inc.dev/jvagent/jvagent-base:latest" in dockerfile_content
    assert "# Action-specific pip dependencies" in dockerfile_content
    assert "myorg/action1" in dockerfile_content
    assert "myorg/action2" in dockerfile_content
    assert "other/action3" in dockerfile_content


def test_bundler_generate_dockerfile_no_dependencies(mock_app_no_dependencies):
    """Test Dockerfile generation with no action dependencies."""
    bundler = Bundler(app_root=str(mock_app_no_dependencies))

    success = bundler.generate_dockerfile()

    assert success is True

    # Check Dockerfile was created
    dockerfile_path = mock_app_no_dependencies / "Dockerfile"
    assert dockerfile_path.exists()

    # Check Dockerfile content
    dockerfile_content = dockerfile_path.read_text()
    assert "FROM registry.v75inc.dev/jvagent/jvagent-base:latest" in dockerfile_content
    assert "# Action-specific pip dependencies" not in dockerfile_content


def test_bundler_generate_dockerfile_no_agents(mock_app_no_agents):
    """Test Dockerfile generation with no agents directory."""
    bundler = Bundler(app_root=str(mock_app_no_agents))

    success = bundler.generate_dockerfile()

    assert success is True

    # Check Dockerfile was created
    dockerfile_path = mock_app_no_agents / "Dockerfile"
    assert dockerfile_path.exists()

    # Check Dockerfile content
    dockerfile_content = dockerfile_path.read_text()
    assert "FROM registry.v75inc.dev/jvagent/jvagent-base:latest" in dockerfile_content


def test_bundler_generate_dockerfile_missing_app_yaml(temp_dir):
    """Test Dockerfile generation fails with missing app.yaml."""
    app_root = temp_dir / "invalid_app"
    app_root.mkdir()

    bundler = Bundler(app_root=str(app_root))

    success = bundler.generate_dockerfile()

    assert success is False

    # Dockerfile should not be created
    dockerfile_path = app_root / "Dockerfile"
    assert not dockerfile_path.exists()


def test_bundler_generate_dockerfile_overwrites_existing(mock_jvagent_app):
    """Test that Dockerfile generation overwrites existing Dockerfile."""
    bundler = Bundler(app_root=str(mock_jvagent_app))

    # Create an existing Dockerfile
    dockerfile_path = mock_jvagent_app / "Dockerfile"
    dockerfile_path.write_text("OLD CONTENT")

    success = bundler.generate_dockerfile()

    assert success is True

    # Check Dockerfile was overwritten
    dockerfile_content = dockerfile_path.read_text()
    assert "OLD CONTENT" not in dockerfile_content
    assert "FROM registry.v75inc.dev/jvagent/jvagent-base:latest" in dockerfile_content


def test_bundler_generate_dockerfile_missing_base_template(
    mock_jvagent_app, monkeypatch
):
    """Test Dockerfile generation fails with missing base template."""
    bundler = Bundler(app_root=str(mock_jvagent_app))

    # Mock Path.exists to make the base template appear missing
    original_exists = Path.exists

    def mock_exists(self):
        if self.name == "Dockerfile.base":
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", mock_exists)

    success = bundler.generate_dockerfile()

    assert success is False


def test_bundler_generate_dockerfile_exception_handling(mock_jvagent_app, monkeypatch):
    """Test that exceptions during generation are handled gracefully."""
    bundler = Bundler(app_root=str(mock_jvagent_app))

    # Mock the open function to raise an exception when reading Dockerfile.base
    import builtins

    original_open = builtins.open

    def mock_open(file, *args, **kwargs):
        if "Dockerfile.base" in str(file):
            raise RuntimeError("Unexpected error during generation")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open)

    success = bundler.generate_dockerfile()

    assert success is False

    # Dockerfile should not be created
    dockerfile_path = mock_jvagent_app / "Dockerfile"
    assert not dockerfile_path.exists()


def test_bundler_with_complex_action_structure(temp_dir):
    """Test Bundler with complex action structure."""
    app_root = temp_dir / "complex_app"
    app_root.mkdir()

    # Create app.yaml
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: complex_app\n")

    # Create multiple agents with multiple actions
    for i in range(3):
        for j in range(2):
            action_path = (
                app_root
                / "agents"
                / f"org{i}"
                / f"agent{i}"
                / "actions"
                / f"org{i}"
                / f"action{j}"
            )
            action_path.mkdir(parents=True)
            action_info = action_path / "info.yaml"
            action_info.write_text(
                f"""package:
  name: org{i}/action{j}
  dependencies:
    pip:
      - package{i}{j}>=1.0.0
"""
            )

    bundler = Bundler(app_root=str(app_root))
    success = bundler.generate_dockerfile()

    assert success is True

    # Check Dockerfile contains all actions
    dockerfile_path = app_root / "Dockerfile"
    dockerfile_content = dockerfile_path.read_text()

    for i in range(3):
        for j in range(2):
            assert f"org{i}/action{j}" in dockerfile_content
            assert f"package{i}{j}>=1.0.0" in dockerfile_content


def test_bundler_path_resolution(temp_dir):
    """Test that Bundler resolves paths correctly."""
    app_root = temp_dir / "test_app"
    app_root.mkdir()

    # Create app.yaml
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: test_app\n")

    # Test with string path
    bundler1 = Bundler(app_root=str(app_root))
    assert bundler1.app_root.resolve() == app_root.resolve()

    # Test with Path object
    bundler2 = Bundler(app_root=app_root)
    assert bundler2.app_root.resolve() == app_root.resolve()

    # Both should be equal
    assert bundler1.app_root.resolve() == bundler2.app_root.resolve()
