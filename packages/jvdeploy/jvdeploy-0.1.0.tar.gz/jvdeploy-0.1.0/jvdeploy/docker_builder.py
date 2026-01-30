"""Docker builder for jvagent applications.

Handles building Docker images and pushing them to ECR.
"""

import base64
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DockerBuilderError(Exception):
    """Exception raised for Docker build errors."""

    pass


class DockerBuilder:
    """Build and push Docker images for jvagent applications."""

    def __init__(
        self,
        app_root: str,
        image_name: str,
        image_tag: str = "latest",
        platform: str = "linux/amd64",
    ):
        """Initialize Docker builder.

        Args:
            app_root: Path to application root directory
            image_name: Name of the Docker image (without tag)
            image_tag: Image tag (default: latest)
            platform: Target platform (default: linux/amd64)
        """
        self.app_root = Path(app_root)
        self.image_name = image_name
        self.image_tag = image_tag
        self.platform = platform

        if not self.app_root.exists():
            raise DockerBuilderError(f"App root directory not found: {app_root}")

        logger.info(f"Initialized Docker builder for {self.app_root}")

    def check_docker(self) -> bool:
        """Check if Docker is installed and running.

        Returns:
            True if Docker is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def build(
        self, dockerfile_path: Optional[str] = None, no_cache: bool = False
    ) -> str:
        """Build Docker image.

        Args:
            dockerfile_path: Path to Dockerfile (default: {app_root}/Dockerfile)
            no_cache: If True, build without using cache

        Returns:
            Full image name with tag

        Raises:
            DockerBuilderError: If build fails
        """
        if not self.check_docker():
            raise DockerBuilderError(
                "Docker is not installed or not running. "
                "Please install Docker and ensure the daemon is running."
            )

        # Use default Dockerfile if not specified
        if dockerfile_path is None:
            dockerfile_path = self.app_root / "Dockerfile"
        else:
            dockerfile_path = Path(dockerfile_path)

        if not dockerfile_path.exists():
            raise DockerBuilderError(
                f"Dockerfile not found: {dockerfile_path}\n"
                f"Tip: Run 'jvdeploy generate' to create a Dockerfile first"
            )

        full_image_name = f"{self.image_name}:{self.image_tag}"

        logger.info(f"Building Docker image: {full_image_name}")
        logger.info(f"  Platform: {self.platform}")
        logger.info(f"  Context: {self.app_root}")
        logger.info(f"  Dockerfile: {dockerfile_path}")

        # Build Docker command
        # Use buildx with --load flag to create standard Docker image
        # --load saves the image to Docker daemon in standard format (not manifest list)
        # This ensures Lambda-compatible images while supporting cross-platform builds
        cmd = [
            "docker",
            "buildx",
            "build",
            "--platform",
            self.platform,
            "--provenance=false",
            "--load",  # Load image into Docker daemon (creates standard image, not manifest)
            "-t",
            full_image_name,
            "-f",
            str(dockerfile_path),
        ]

        if no_cache:
            cmd.append("--no-cache")

        cmd.append(str(self.app_root))

        # Execute build
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.app_root),
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"Docker build failed:")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                raise DockerBuilderError(
                    f"Docker build failed with exit code {result.returncode}\n"
                    f"Error: {result.stderr}"
                )

            logger.info(f"✓ Successfully built image: {full_image_name}")
            return full_image_name

        except subprocess.TimeoutExpired:
            raise DockerBuilderError("Docker build timed out after 10 minutes")
        except Exception as e:
            raise DockerBuilderError(f"Docker build failed: {e}") from e

    def tag(self, source_tag: str, target_tag: str) -> None:
        """Tag an existing image with a new tag.

        Args:
            source_tag: Full source image name with tag
            target_tag: Full target image name with tag

        Raises:
            DockerBuilderError: If tagging fails
        """
        logger.info(f"Tagging image: {source_tag} -> {target_tag}")

        cmd = ["docker", "tag", source_tag, target_tag]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise DockerBuilderError(f"Docker tag failed: {result.stderr}")

            logger.info(f"✓ Successfully tagged image: {target_tag}")

        except subprocess.TimeoutExpired:
            raise DockerBuilderError("Docker tag timed out")
        except Exception as e:
            raise DockerBuilderError(f"Docker tag failed: {e}") from e

    def push(self, image_uri: str) -> None:
        """Push Docker image to registry.

        Args:
            image_uri: Full image URI to push to

        Raises:
            DockerBuilderError: If push fails
        """
        if not self.check_docker():
            raise DockerBuilderError("Docker is not installed or not running")

        logger.info(f"Pushing Docker image: {image_uri}")

        cmd = ["docker", "push", image_uri]

        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout for push
            )

            if result.returncode != 0:
                logger.error(f"Docker push failed:")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                raise DockerBuilderError(
                    f"Docker push failed with exit code {result.returncode}\n"
                    f"Error: {result.stderr}"
                )

            logger.info(f"✓ Successfully pushed image: {image_uri}")

        except subprocess.TimeoutExpired:
            raise DockerBuilderError("Docker push timed out after 30 minutes")
        except Exception as e:
            raise DockerBuilderError(f"Docker push failed: {e}") from e

    def get_aws_account_id(self, region: str) -> str:
        """Get AWS account ID from current credentials.

        Args:
            region: AWS region

        Returns:
            AWS account ID

        Raises:
            DockerBuilderError: If unable to get account ID
        """
        try:
            import boto3

            sts_client = boto3.client("sts", region_name=region)
            response = sts_client.get_caller_identity()
            account_id = response["Account"]
            logger.debug(f"Got AWS account ID: {account_id}")
            return account_id

        except ImportError:
            raise DockerBuilderError(
                "boto3 is required for AWS operations. "
                "Install with: pip install boto3"
            )
        except Exception as e:
            raise DockerBuilderError(f"Failed to get AWS account ID: {e}") from e

    def ecr_login(self, region: str, account_id: Optional[str] = None) -> None:
        """Authenticate Docker with ECR.

        Args:
            region: AWS region
            account_id: AWS account ID (optional, will be auto-detected if not provided)

        Raises:
            DockerBuilderError: If authentication fails
        """
        # Auto-detect account ID if not provided
        if account_id is None:
            account_id = self.get_aws_account_id(region)

        logger.info(f"Authenticating with ECR in {region}")

        try:
            import boto3

            ecr_client = boto3.client("ecr", region_name=region)

            # Get ECR login token
            response = ecr_client.get_authorization_token()
            auth_data = response["authorizationData"][0]
            token = auth_data["authorizationToken"]
            endpoint = auth_data["proxyEndpoint"]

            # Decode token (it's base64 encoded "AWS:password")
            decoded = base64.b64decode(token).decode("utf-8")
            username, password = decoded.split(":", 1)

            # Docker login
            cmd = [
                "docker",
                "login",
                "--username",
                username,
                "--password-stdin",
                endpoint,
            ]

            result = subprocess.run(
                cmd,
                input=password,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise DockerBuilderError(f"Docker login to ECR failed: {result.stderr}")

            logger.info(f"✓ Successfully authenticated with ECR")

        except ImportError:
            raise DockerBuilderError(
                "boto3 is required for ECR authentication. "
                "Install with: pip install boto3"
            )
        except Exception as e:
            raise DockerBuilderError(f"ECR authentication failed: {e}") from e

    def build_and_push_to_ecr(
        self,
        ecr_uri: str,
        region: str,
        account_id: Optional[str] = None,
        dockerfile_path: Optional[str] = None,
        no_cache: bool = False,
    ) -> str:
        """Build Docker image and push to ECR (convenience method).

        Args:
            ecr_uri: Full ECR image URI
            region: AWS region
            account_id: AWS account ID (optional, will be auto-detected if not provided)
            dockerfile_path: Path to Dockerfile (optional)
            no_cache: If True, build without cache

        Returns:
            Full ECR image URI

        Raises:
            DockerBuilderError: If build or push fails
        """
        # Auto-detect account ID if not provided
        if account_id is None:
            account_id = self.get_aws_account_id(region)
        logger.info("=== Starting Docker build and push to ECR ===")

        # Step 1: Build the image locally
        local_image = self.build(dockerfile_path=dockerfile_path, no_cache=no_cache)

        # Step 2: Tag with ECR URI
        logger.info(f"Tagging image for ECR: {ecr_uri}")
        self.tag(local_image, ecr_uri)

        # Step 3: Authenticate with ECR
        self.ecr_login(region=region, account_id=account_id)

        # Step 4: Push to ECR
        self.push(ecr_uri)

        logger.info(f"=== Successfully built and pushed to ECR ===")
        return ecr_uri


def build_and_push(
    app_root: str,
    image_name: str,
    image_tag: str,
    ecr_uri: str,
    region: str,
    account_id: Optional[str] = None,
    platform: str = "linux/amd64",
    no_cache: bool = False,
) -> str:
    """Build and push Docker image to ECR (convenience function).

    Args:
        app_root: Path to application root
        image_name: Docker image name
        image_tag: Docker image tag
        ecr_uri: Full ECR image URI
        region: AWS region
        account_id: AWS account ID (optional, will be auto-detected if not provided)
        platform: Target platform (default: linux/amd64)
        no_cache: If True, build without cache

    Returns:
        Full ECR image URI

    Raises:
        DockerBuilderError: If build or push fails
    """
    builder = DockerBuilder(
        app_root=app_root,
        image_name=image_name,
        image_tag=image_tag,
        platform=platform,
    )

    return builder.build_and_push_to_ecr(
        ecr_uri=ecr_uri,
        region=region,
        account_id=account_id,
        no_cache=no_cache,
    )
