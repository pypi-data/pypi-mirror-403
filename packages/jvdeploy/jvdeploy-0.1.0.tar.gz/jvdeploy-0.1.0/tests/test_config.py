"""Tests for configuration management module."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from jvdeploy.config import DeployConfig, DeployConfigError


def create_test_config(config_dict, temp_dir):
    """Helper to create a temporary config file."""
    config_path = Path(temp_dir) / "deploy.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_dict, f)
    return str(config_path)


def test_load_valid_config():
    """Test loading a valid configuration."""
    config_dict = {
        "version": "1.0",
        "app": {
            "name": "test-app",
            "version": "1.0.0",
        },
        "image": {
            "name": "test-app",
            "tag": "latest",
        },
        "lambda": {
            "enabled": True,
            "region": "us-east-1",
            "function": {"name": "test-function"},
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        assert config.get_app_config()["name"] == "test-app"
        assert config.is_lambda_enabled() is True


def test_missing_config_file():
    """Test error when config file doesn't exist."""
    with pytest.raises(DeployConfigError, match="Configuration file not found"):
        DeployConfig("/nonexistent/deploy.yaml")


def test_missing_required_fields():
    """Test error when required fields are missing."""
    config_dict = {
        "version": "1.0",
        # Missing 'app' section
        "image": {"name": "test"},
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        with pytest.raises(DeployConfigError, match="missing required 'app' section"):
            DeployConfig(config_path)


def test_env_var_interpolation():
    """Test environment variable interpolation."""
    os.environ["TEST_PASSWORD"] = "secret123"
    os.environ["TEST_LEVEL"] = "DEBUG"

    config_dict = {
        "version": "1.0",
        "app": {"name": "test-app"},
        "image": {"name": "test-app"},
        "lambda": {
            "enabled": True,
            "environment": {
                "PASSWORD": "${TEST_PASSWORD}",
                "LOG_LEVEL": "${TEST_LEVEL}",
            },
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        lambda_config = config.get_lambda_config()
        assert lambda_config["environment"]["PASSWORD"] == "secret123"
        assert lambda_config["environment"]["LOG_LEVEL"] == "DEBUG"

    # Cleanup
    del os.environ["TEST_PASSWORD"]
    del os.environ["TEST_LEVEL"]


def test_template_variable_resolution():
    """Test template variable resolution."""
    config_dict = {
        "version": "1.0",
        "app": {
            "name": "my-app",
            "version": "2.0.0",
        },
        "image": {
            "name": "{{app.name}}",
            "tag": "{{app.version}}",
        },
        "lambda": {
            "enabled": True,
            "function": {
                "name": "{{app.name}}-function",
            },
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        image_config = config.get_image_config()
        assert image_config["name"] == "my-app"
        assert image_config["tag"] == "2.0.0"

        lambda_config = config.get_lambda_config()
        assert lambda_config["function"]["name"] == "my-app-function"


def test_get_full_image_name():
    """Test getting full image name with tag."""
    config_dict = {
        "version": "1.0",
        "app": {"name": "test-app"},
        "image": {
            "name": "myorg/test-app",
            "tag": "1.2.3",
        },
        "lambda": {"enabled": True},
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        assert config.get_full_image_name() == "myorg/test-app:1.2.3"


def test_get_ecr_image_uri():
    """Test getting ECR image URI."""
    config_dict = {
        "version": "1.0",
        "app": {"name": "test-app"},
        "image": {
            "name": "test-app",
            "tag": "1.0.0",
        },
        "lambda": {
            "enabled": True,
            "region": "us-west-2",
            "account_id": "123456789012",
            "ecr": {
                "repository_name": "test-app",
            },
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        expected = "123456789012.dkr.ecr.us-west-2.amazonaws.com/test-app:1.0.0"
        assert config.get_ecr_image_uri() == expected


def test_override_env_vars():
    """Test overriding environment variables."""
    config_dict = {
        "version": "1.0",
        "app": {"name": "test-app"},
        "image": {"name": "test-app"},
        "lambda": {
            "enabled": True,
            "environment": {
                "LOG_LEVEL": "INFO",
                "DEBUG": "false",
            },
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        config.override_env_vars(["LOG_LEVEL=DEBUG", "DEBUG=true"])

        lambda_config = config.get_lambda_config()
        assert lambda_config["environment"]["LOG_LEVEL"] == "DEBUG"
        assert lambda_config["environment"]["DEBUG"] == "true"


def test_lambda_enabled():
    """Test checking if Lambda is enabled."""
    config_dict = {
        "version": "1.0",
        "app": {"name": "test-app"},
        "image": {"name": "test-app"},
        "lambda": {
            "enabled": True,
        },
        "kubernetes": {
            "enabled": False,
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        assert config.is_lambda_enabled() is True
        assert config.is_k8s_enabled() is False


def test_k8s_enabled():
    """Test checking if Kubernetes is enabled."""
    config_dict = {
        "version": "1.0",
        "app": {"name": "test-app"},
        "image": {"name": "test-app"},
        "lambda": {
            "enabled": False,
        },
        "kubernetes": {
            "enabled": True,
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        assert config.is_lambda_enabled() is False
        assert config.is_k8s_enabled() is True


def test_no_platform_enabled():
    """Test error when no platform is enabled."""
    config_dict = {
        "version": "1.0",
        "app": {"name": "test-app"},
        "image": {"name": "test-app"},
        "lambda": {
            "enabled": False,
        },
        "kubernetes": {
            "enabled": False,
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        with pytest.raises(
            DeployConfigError,
            match="At least one deployment platform.*must be enabled",
        ):
            DeployConfig(config_path)


def test_invalid_yaml():
    """Test error with invalid YAML."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "deploy.yaml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(DeployConfigError, match="Invalid YAML"):
            DeployConfig(str(config_path))


def test_get_lambda_config_when_disabled():
    """Test getting Lambda config when disabled returns None."""
    config_dict = {
        "version": "1.0",
        "app": {"name": "test-app"},
        "image": {"name": "test-app"},
        "lambda": {
            "enabled": False,
        },
        "kubernetes": {
            "enabled": True,
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        assert config.get_lambda_config() is None


def test_to_dict():
    """Test getting full configuration as dictionary."""
    config_dict = {
        "version": "1.0",
        "app": {"name": "test-app"},
        "image": {"name": "test-app"},
        "lambda": {"enabled": True},
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = create_test_config(config_dict, temp_dir)
        config = DeployConfig(config_path)

        full_config = config.to_dict()
        assert isinstance(full_config, dict)
        assert full_config["version"] == "1.0"
        assert full_config["app"]["name"] == "test-app"
