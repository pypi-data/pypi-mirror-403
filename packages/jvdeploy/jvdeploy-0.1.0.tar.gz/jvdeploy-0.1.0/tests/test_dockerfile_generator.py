"""Tests for dockerfile_generator module."""

from pathlib import Path

import pytest
from jvdeploy.dockerfile_generator import (
    discover_action_dependencies,
    generate_dockerfile,
    generate_dockerfile_run_commands,
)


def test_discover_action_dependencies(mock_jvagent_app):
    """Test discovering action dependencies from app structure."""
    dependencies = discover_action_dependencies(mock_jvagent_app)

    assert len(dependencies) == 3
    assert "myorg/action1" in dependencies
    assert "myorg/action2" in dependencies
    assert "other/action3" in dependencies

    assert dependencies["myorg/action1"] == ["openai>=1.0.0", "httpx>=0.24.0"]
    assert dependencies["myorg/action2"] == ["requests>=2.31.0", "pydantic>=2.0.0"]
    assert dependencies["other/action3"] == ["numpy>=1.24.0"]


def test_discover_action_dependencies_no_agents(mock_app_no_agents):
    """Test discovering dependencies when no agents directory exists."""
    dependencies = discover_action_dependencies(mock_app_no_agents)

    assert len(dependencies) == 0


def test_discover_action_dependencies_no_dependencies(mock_app_no_dependencies):
    """Test discovering dependencies when actions have no dependencies."""
    dependencies = discover_action_dependencies(mock_app_no_dependencies)

    assert len(dependencies) == 0


def test_discover_action_dependencies_invalid_yaml(temp_dir):
    """Test discovering dependencies with invalid YAML files."""
    app_root = temp_dir / "test_app"
    app_root.mkdir()

    # Create app.yaml
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: test_app\n")

    # Create action with invalid YAML
    action_path = (
        app_root / "agents" / "myorg" / "agent1" / "actions" / "myorg" / "action1"
    )
    action_path.mkdir(parents=True)
    action_info = action_path / "info.yaml"
    action_info.write_text("invalid: yaml: content: [")

    dependencies = discover_action_dependencies(app_root)

    # Should return empty dict, not crash
    assert len(dependencies) == 0


def test_discover_action_dependencies_missing_package_section(temp_dir):
    """Test discovering dependencies with missing package section."""
    app_root = temp_dir / "test_app"
    app_root.mkdir()

    # Create app.yaml
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: test_app\n")

    # Create action without package section
    action_path = (
        app_root / "agents" / "myorg" / "agent1" / "actions" / "myorg" / "action1"
    )
    action_path.mkdir(parents=True)
    action_info = action_path / "info.yaml"
    action_info.write_text("name: test\n")

    dependencies = discover_action_dependencies(app_root)

    assert len(dependencies) == 0


def test_discover_action_dependencies_empty_pip_list(temp_dir):
    """Test discovering dependencies with empty pip list."""
    app_root = temp_dir / "test_app"
    app_root.mkdir()

    # Create app.yaml
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: test_app\n")

    # Create action with empty pip list
    action_path = (
        app_root / "agents" / "myorg" / "agent1" / "actions" / "myorg" / "action1"
    )
    action_path.mkdir(parents=True)
    action_info = action_path / "info.yaml"
    action_info.write_text(
        """package:
  name: myorg/action1
  dependencies:
    pip: []
"""
    )

    dependencies = discover_action_dependencies(app_root)

    assert len(dependencies) == 0


def test_generate_dockerfile_run_commands_empty():
    """Test generating RUN commands with no dependencies."""
    commands = generate_dockerfile_run_commands({})

    assert commands == ""


def test_generate_dockerfile_run_commands_single_action():
    """Test generating RUN commands for a single action."""
    dependencies = {
        "myorg/action1": ["openai>=1.0.0", "httpx>=0.24.0"],
    }

    commands = generate_dockerfile_run_commands(dependencies)

    assert "# Action-specific pip dependencies" in commands
    assert "# Dependencies for myorg/action1" in commands
    assert (
        "RUN /opt/venv/bin/pip install --no-cache-dir openai>=1.0.0 httpx>=0.24.0"
        in commands
    )


def test_generate_dockerfile_run_commands_multiple_actions():
    """Test generating RUN commands for multiple actions."""
    dependencies = {
        "myorg/action1": ["openai>=1.0.0", "httpx>=0.24.0"],
        "myorg/action2": ["requests>=2.31.0", "pydantic>=2.0.0"],
        "other/action3": ["numpy>=1.24.0"],
    }

    commands = generate_dockerfile_run_commands(dependencies)

    assert "# Action-specific pip dependencies" in commands
    assert "# Dependencies for myorg/action1" in commands
    assert "# Dependencies for myorg/action2" in commands
    assert "# Dependencies for other/action3" in commands
    assert (
        "RUN /opt/venv/bin/pip install --no-cache-dir openai>=1.0.0 httpx>=0.24.0"
        in commands
    )
    assert (
        "RUN /opt/venv/bin/pip install --no-cache-dir requests>=2.31.0 pydantic>=2.0.0"
        in commands
    )
    assert "RUN /opt/venv/bin/pip install --no-cache-dir numpy>=1.24.0" in commands


def test_generate_dockerfile_run_commands_deduplication():
    """Test that duplicate dependencies within an action are deduplicated."""
    dependencies = {
        "myorg/action1": ["openai>=1.0.0", "httpx>=0.24.0", "openai>=1.0.0"],
    }

    commands = generate_dockerfile_run_commands(dependencies)

    # Should only have one openai package
    assert commands.count("openai>=1.0.0") == 1


def test_generate_dockerfile_run_commands_sorted():
    """Test that actions are sorted alphabetically."""
    dependencies = {
        "zorg/action_z": ["pkg1"],
        "aorg/action_a": ["pkg2"],
        "borg/action_b": ["pkg3"],
    }

    commands = generate_dockerfile_run_commands(dependencies)

    # Actions should appear in alphabetical order
    lines = commands.split("\n")
    action_lines = [line for line in lines if line.startswith("# Dependencies for")]

    assert action_lines[0] == "# Dependencies for aorg/action_a"
    assert action_lines[1] == "# Dependencies for borg/action_b"
    assert action_lines[2] == "# Dependencies for zorg/action_z"


def test_generate_dockerfile_with_dependencies(mock_jvagent_app, mock_base_template):
    """Test generating Dockerfile with action dependencies."""
    dockerfile_content = generate_dockerfile(mock_jvagent_app, mock_base_template)

    # Check base template content is present
    assert "FROM registry.v75inc.dev/jvagent/jvagent-base:latest" in dockerfile_content
    assert "WORKDIR /var/task" in dockerfile_content
    assert "COPY . /var/task/" in dockerfile_content

    # Check action dependencies are present
    assert "# Action-specific pip dependencies" in dockerfile_content
    assert "# Dependencies for myorg/action1" in dockerfile_content
    assert "# Dependencies for myorg/action2" in dockerfile_content
    assert "# Dependencies for other/action3" in dockerfile_content

    # Check RUN commands are present
    assert (
        "RUN /opt/venv/bin/pip install --no-cache-dir openai>=1.0.0 httpx>=0.24.0"
        in dockerfile_content
    )
    assert (
        "RUN /opt/venv/bin/pip install --no-cache-dir requests>=2.31.0 pydantic>=2.0.0"
        in dockerfile_content
    )
    assert (
        "RUN /opt/venv/bin/pip install --no-cache-dir numpy>=1.24.0"
        in dockerfile_content
    )

    # Check placeholder is replaced
    assert "{{ACTION_DEPENDENCIES}}" not in dockerfile_content


def test_generate_dockerfile_no_dependencies(
    mock_app_no_dependencies, mock_base_template
):
    """Test generating Dockerfile with no action dependencies."""
    dockerfile_content = generate_dockerfile(
        mock_app_no_dependencies, mock_base_template
    )

    # Check base template content is present
    assert "FROM registry.v75inc.dev/jvagent/jvagent-base:latest" in dockerfile_content
    assert "WORKDIR /var/task" in dockerfile_content
    assert "COPY . /var/task/" in dockerfile_content

    # Check no dependency sections are present
    assert "# Action-specific pip dependencies" not in dockerfile_content
    assert "RUN /opt/venv/bin/pip install" not in dockerfile_content

    # Check placeholder is removed
    assert "{{ACTION_DEPENDENCIES}}" not in dockerfile_content


def test_generate_dockerfile_no_agents(mock_app_no_agents, mock_base_template):
    """Test generating Dockerfile with no agents directory."""
    dockerfile_content = generate_dockerfile(mock_app_no_agents, mock_base_template)

    # Check base template content is present
    assert "FROM registry.v75inc.dev/jvagent/jvagent-base:latest" in dockerfile_content

    # Check no dependency sections are present
    assert "# Action-specific pip dependencies" not in dockerfile_content

    # Check placeholder is removed
    assert "{{ACTION_DEPENDENCIES}}" not in dockerfile_content


def test_generate_dockerfile_missing_template(mock_jvagent_app, temp_dir):
    """Test generating Dockerfile with missing base template."""
    missing_template = temp_dir / "missing.base"

    with pytest.raises(FileNotFoundError) as exc_info:
        generate_dockerfile(mock_jvagent_app, missing_template)

    assert "Base Dockerfile template not found" in str(exc_info.value)


def test_generate_dockerfile_version_specifiers(temp_dir, mock_base_template):
    """Test generating Dockerfile with various version specifiers."""
    app_root = temp_dir / "test_app"
    app_root.mkdir()

    # Create app.yaml
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: test_app\n")

    # Create action with various version specifiers
    action_path = (
        app_root / "agents" / "myorg" / "agent1" / "actions" / "myorg" / "action1"
    )
    action_path.mkdir(parents=True)
    action_info = action_path / "info.yaml"
    action_info.write_text(
        """package:
  name: myorg/action1
  dependencies:
    pip:
      - openai>=1.0.0
      - httpx==0.24.0
      - requests<3.0.0
      - pydantic~=2.0.0
"""
    )

    dockerfile_content = generate_dockerfile(app_root, mock_base_template)

    # All version specifiers should be preserved
    assert "openai>=1.0.0" in dockerfile_content
    assert "httpx==0.24.0" in dockerfile_content
    assert "requests<3.0.0" in dockerfile_content
    assert "pydantic~=2.0.0" in dockerfile_content


def test_generate_dockerfile_whitespace_handling(temp_dir, mock_base_template):
    """Test that whitespace in dependencies is handled correctly."""
    app_root = temp_dir / "test_app"
    app_root.mkdir()

    # Create app.yaml
    app_yaml = app_root / "app.yaml"
    app_yaml.write_text("name: test_app\n")

    # Create action with whitespace in dependencies
    action_path = (
        app_root / "agents" / "myorg" / "agent1" / "actions" / "myorg" / "action1"
    )
    action_path.mkdir(parents=True)
    action_info = action_path / "info.yaml"
    action_info.write_text(
        """package:
  name: myorg/action1
  dependencies:
    pip:
      - " openai>=1.0.0 "
      - "  httpx>=0.24.0"
      - ""
"""
    )

    dockerfile_content = generate_dockerfile(app_root, mock_base_template)

    # Whitespace should be stripped
    assert "openai>=1.0.0" in dockerfile_content
    assert "httpx>=0.24.0" in dockerfile_content
    # Empty string should be filtered out
    assert dockerfile_content.count("RUN") == 1
