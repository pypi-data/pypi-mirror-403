"""Configuration management for jvdeploy deployments.

Handles loading, validation, and processing of deploy.yaml configuration files.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class DeployConfigError(Exception):
    """Exception raised for configuration errors."""

    pass


class DeployConfig:
    """Manage deployment configuration from deploy.yaml."""

    def __init__(self, config_path: str, app_root: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to deploy.yaml configuration file
            app_root: Path to app root directory (defaults to config file directory)
        """
        self.config_path = Path(config_path)
        self.app_root = Path(app_root) if app_root else self.config_path.parent
        self.raw_config: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}

        self._load_config()
        self._validate()
        self._interpolate_env_vars()
        self._resolve_templates()

    def _load_config(self) -> None:
        """Load YAML configuration from file."""
        if not self.config_path.exists():
            raise DeployConfigError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, "r") as f:
                self.raw_config = yaml.safe_load(f) or {}
                self.config = self.raw_config.copy()
            logger.debug(f"Loaded configuration from {self.config_path}")
        except yaml.YAMLError as e:
            raise DeployConfigError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise DeployConfigError(f"Failed to load configuration file: {e}")

    def _validate(self) -> None:
        """Validate configuration structure and required fields."""
        if not isinstance(self.config, dict):
            raise DeployConfigError("Configuration must be a dictionary")

        # Validate version
        if "version" not in self.config:
            logger.warning("Configuration missing 'version' field, assuming '1.0'")
            self.config["version"] = "1.0"

        # Validate app section
        if "app" not in self.config:
            raise DeployConfigError("Configuration missing required 'app' section")

        app_config = self.config["app"]
        if not isinstance(app_config, dict):
            raise DeployConfigError("'app' section must be a dictionary")

        if "name" not in app_config:
            raise DeployConfigError("'app.name' is required")

        # Validate image section
        if "image" not in self.config:
            raise DeployConfigError("Configuration missing required 'image' section")

        # Check that at least one platform is enabled
        lambda_enabled = self.config.get("lambda", {}).get("enabled", False)
        k8s_enabled = self.config.get("kubernetes", {}).get("enabled", False)

        if not lambda_enabled and not k8s_enabled:
            raise DeployConfigError(
                "At least one deployment platform (lambda or kubernetes) must be enabled"
            )

        logger.debug("Configuration validation passed")

    def _interpolate_env_vars(self) -> None:
        """Replace ${VAR_NAME} with environment variables recursively."""

        def interpolate_value(value: Any) -> Any:
            """Recursively interpolate environment variables in values."""
            if isinstance(value, str):
                # Find all ${VAR_NAME} patterns
                pattern = r"\$\{([^}]+)\}"
                matches = re.finditer(pattern, value)

                for match in matches:
                    var_name = match.group(1)
                    env_value = os.environ.get(var_name)

                    if env_value is None:
                        logger.warning(
                            f"Environment variable '{var_name}' not found, leaving as-is"
                        )
                    else:
                        value = value.replace(match.group(0), env_value)

                return value

            elif isinstance(value, dict):
                return {k: interpolate_value(v) for k, v in value.items()}

            elif isinstance(value, list):
                return [interpolate_value(item) for item in value]

            else:
                return value

        self.config = interpolate_value(self.config)
        logger.debug("Environment variable interpolation complete")

    def _resolve_templates(self) -> None:
        """Resolve {{variable}} template references recursively."""

        def resolve_value(value: Any, context: Dict[str, Any]) -> Any:
            """Recursively resolve template variables in values."""
            if isinstance(value, str):
                # Find all {{variable}} patterns
                pattern = r"\{\{([^}]+)\}\}"
                matches = re.finditer(pattern, value)

                for match in matches:
                    template_var = match.group(1).strip()
                    resolved = self._get_nested_value(context, template_var)

                    if resolved is None:
                        logger.warning(
                            f"Template variable '{template_var}' not found, leaving as-is"
                        )
                    else:
                        # Convert to string for replacement
                        value = value.replace(match.group(0), str(resolved))

                return value

            elif isinstance(value, dict):
                return {k: resolve_value(v, context) for k, v in value.items()}

            elif isinstance(value, list):
                return [resolve_value(item, context) for item in value]

            else:
                return value

        self.config = resolve_value(self.config, self.config)
        logger.debug("Template variable resolution complete")

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get a nested value from dictionary using dot notation.

        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., 'app.name')

        Returns:
            Value at path, or None if not found
        """
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration section.

        Returns:
            Dictionary containing app configuration
        """
        return self.config.get("app", {})

    def get_image_config(self) -> Dict[str, Any]:
        """Get Docker image configuration section.

        Returns:
            Dictionary containing image configuration
        """
        return self.config.get("image", {})

    def get_lambda_config(self) -> Optional[Dict[str, Any]]:
        """Get Lambda deployment configuration.

        Returns:
            Dictionary containing Lambda configuration, or None if disabled
        """
        lambda_config = self.config.get("lambda", {})
        if not lambda_config.get("enabled", False):
            return None
        return lambda_config

    def get_k8s_config(self) -> Optional[Dict[str, Any]]:
        """Get Kubernetes deployment configuration.

        Returns:
            Dictionary containing Kubernetes configuration, or None if disabled
        """
        k8s_config = self.config.get("kubernetes", {})
        if not k8s_config.get("enabled", False):
            return None
        return k8s_config

    def is_lambda_enabled(self) -> bool:
        """Check if Lambda deployment is enabled.

        Returns:
            True if Lambda deployment is enabled
        """
        return self.config.get("lambda", {}).get("enabled", False)

    def is_k8s_enabled(self) -> bool:
        """Check if Kubernetes deployment is enabled.

        Returns:
            True if Kubernetes deployment is enabled
        """
        return self.config.get("kubernetes", {}).get("enabled", False)

    def override_env_vars(self, env_overrides: Optional[list[str]]) -> None:
        """Override environment variables in configuration.

        Args:
            env_overrides: List of KEY=VALUE strings to override
        """
        if not env_overrides:
            return

        for override in env_overrides:
            if "=" not in override:
                logger.warning(
                    f"Invalid environment override format: '{override}' (expected KEY=VALUE)"
                )
                continue

            key, value = override.split("=", 1)

            # Override in Lambda environment
            lambda_config = self.config.get("lambda")
            if lambda_config and "environment" in lambda_config:
                lambda_config["environment"][key] = value
                logger.debug(f"Overriding Lambda environment: {key}={value}")

            # Override in Kubernetes environment
            k8s_config = self.config.get("kubernetes")
            if k8s_config and "deployment" in k8s_config:
                container_config = k8s_config["deployment"].get("container", {})
                if "environment" in container_config:
                    container_config["environment"][key] = value
                    logger.debug(f"Overriding Kubernetes environment: {key}={value}")

    def get_full_image_name(self) -> str:
        """Get the full Docker image name with tag.

        Returns:
            Full image name (e.g., 'myorg/myapp:1.0.0')
        """
        image_config = self.get_image_config()
        name = image_config.get("name", self.get_app_config().get("name"))
        tag = image_config.get("tag", "latest")
        return f"{name}:{tag}"

    def get_ecr_image_uri(
        self, region: Optional[str] = None, account_id: Optional[str] = None
    ) -> str:
        """Get the full ECR image URI for Lambda deployment.

        Args:
            region: AWS region (uses config if not provided)
            account_id: AWS account ID (uses config if not provided, will be auto-detected if missing)

        Returns:
            Full ECR URI (e.g., '123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0.0')
        """
        lambda_config = self.get_lambda_config()
        if not lambda_config:
            raise DeployConfigError("Lambda configuration is not enabled")

        region = region or lambda_config.get("region", "us-east-1")

        # Use provided account_id, then config, then will be auto-detected later
        if account_id is None:
            account_id = lambda_config.get("account_id")

        # If still no account_id, return a placeholder that will be filled in later
        if not account_id:
            account_id = "{ACCOUNT_ID}"
            logger.warning(
                "account_id not set, will be auto-detected from AWS credentials"
            )

        ecr_config = lambda_config.get("ecr", {})
        repo_name = ecr_config.get("repository_name", self.get_app_config().get("name"))
        tag = self.get_image_config().get("tag", "latest")

        return f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repo_name}:{tag}"

    def to_dict(self) -> Dict[str, Any]:
        """Get the full processed configuration as a dictionary.

        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()


def load_config(
    config_path: str = "deploy.yaml", app_root: Optional[str] = None
) -> DeployConfig:
    """Load deployment configuration from file.

    Args:
        config_path: Path to deploy.yaml file
        app_root: Path to app root directory

    Returns:
        DeployConfig instance

    Raises:
        DeployConfigError: If configuration cannot be loaded or is invalid
    """
    return DeployConfig(config_path=config_path, app_root=app_root)
