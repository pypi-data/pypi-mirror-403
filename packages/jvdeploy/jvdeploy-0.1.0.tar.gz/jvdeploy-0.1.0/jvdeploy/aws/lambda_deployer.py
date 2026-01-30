"""AWS Lambda deployment orchestrator.

Handles end-to-end deployment of jvagent applications to AWS Lambda,
including ECR image management, IAM roles, Lambda functions, and API Gateway.
"""

import logging
import os
import time
from typing import Any, Dict, Optional

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class LambdaDeployerError(Exception):
    """Exception raised for Lambda deployment errors."""

    pass


class LambdaDeployer:
    """Orchestrate deployment of jvagent applications to AWS Lambda."""

    def __init__(self, config: Dict[str, Any], dry_run: bool = False):
        """Initialize Lambda deployer.

        Args:
            config: Lambda deployment configuration
            dry_run: If True, only show what would be done without making changes
        """
        self.config = config
        self.dry_run = dry_run
        self.region = config.get("region", "us-east-1")
        self.account_id = config.get("account_id")

        # Initialize AWS clients (lazy-loaded when needed)
        self._ecr_client = None
        self._iam_client = None
        self._lambda_client = None
        self._apigateway_client = None
        self._apigatewayv2_client = None
        self._sts_client = None
        self._efs_client = None

        logger.info(f"Initialized Lambda deployer for region {self.region}")
        if self.dry_run:
            logger.info("Running in DRY RUN mode - no changes will be made")

    @property
    def ecr_client(self):
        """Lazy-load ECR client."""
        if self._ecr_client is None:
            try:
                import boto3

                self._ecr_client = boto3.client("ecr", region_name=self.region)
            except ImportError:
                raise LambdaDeployerError(
                    "boto3 is required for Lambda deployment. Install with: pip install boto3"
                )
        return self._ecr_client

    @property
    def iam_client(self):
        """Lazy-load IAM client."""
        if self._iam_client is None:
            try:
                import boto3

                self._iam_client = boto3.client("iam", region_name=self.region)
            except ImportError:
                raise LambdaDeployerError(
                    "boto3 is required for Lambda deployment. Install with: pip install boto3"
                )
        return self._iam_client

    @property
    def lambda_client(self):
        """Lazy-load Lambda client."""
        if self._lambda_client is None:
            try:
                import boto3

                self._lambda_client = boto3.client("lambda", region_name=self.region)
            except ImportError:
                raise LambdaDeployerError(
                    "boto3 is required for Lambda deployment. Install with: pip install boto3"
                )
        return self._lambda_client

    @property
    def apigatewayv2_client(self):
        """Lazy-load API Gateway V2 client (for HTTP APIs)."""
        if self._apigatewayv2_client is None:
            try:
                import boto3

                self._apigatewayv2_client = boto3.client(
                    "apigatewayv2", region_name=self.region
                )
            except ImportError:
                raise LambdaDeployerError(
                    "boto3 is required for Lambda deployment. Install with: pip install boto3"
                )
        return self._apigatewayv2_client

    @property
    def sts_client(self):
        """Lazy-load STS client."""
        if self._sts_client is None:
            try:
                import boto3

                self._sts_client = boto3.client("sts", region_name=self.region)
            except ImportError:
                raise LambdaDeployerError(
                    "boto3 is required for Lambda deployment. Install with: pip install boto3"
                )
        return self._sts_client

    @property
    def efs_client(self):
        """Lazy-load EFS client."""
        if self._efs_client is None:
            try:
                import boto3

                self._efs_client = boto3.client("efs", region_name=self.region)
            except ImportError:
                raise LambdaDeployerError(
                    "boto3 is required for Lambda deployment. Install with: pip install boto3"
                )
        return self._efs_client

    def get_account_id(self) -> str:
        """Get AWS account ID from credentials.

        Returns:
            AWS account ID

        Raises:
            LambdaDeployerError: If unable to get account ID
        """
        if self.account_id:
            return self.account_id

        try:
            response = self.sts_client.get_caller_identity()
            self.account_id = response["Account"]
            logger.info(f"Auto-detected AWS account ID: {self.account_id}")
            return self.account_id
        except Exception as e:
            raise LambdaDeployerError(f"Failed to get AWS account ID: {e}") from e

    def deploy(
        self,
        image_uri: str,
        build_image: bool = True,
        push_image: bool = True,
        update_function: bool = True,
        create_api: bool = True,
    ) -> Dict[str, Any]:
        """Execute full Lambda deployment pipeline.

        Args:
            image_uri: Full ECR image URI
            build_image: Whether to build the Docker image
            push_image: Whether to push image to ECR
            update_function: Whether to update/create Lambda function
            create_api: Whether to create/update API Gateway

        Returns:
            Dictionary with deployment results
        """
        results = {
            "success": False,
            "ecr_repository": None,
            "image_uri": image_uri,
            "iam_role_arn": None,
            "function_arn": None,
            "api_url": None,
            "function_url": None,
            "errors": [],
        }

        try:
            # Step 0: Ensure we have account_id
            if not self.account_id:
                logger.info("Auto-detecting AWS account ID...")
                self.account_id = self.get_account_id()

            # Step 1: Ensure ECR repository exists
            logger.info("Step 1: Ensuring ECR repository exists...")
            ecr_config = self.config.get("ecr", {})
            repository_name = ecr_config.get("repository_name")

            if not repository_name:
                raise LambdaDeployerError("ECR repository_name is required")

            repo = self._ensure_ecr_repository(repository_name)
            results["ecr_repository"] = repo

            # Step 2: Build and push image (if requested)
            if build_image or push_image:
                logger.info("Step 2: Building and pushing Docker image...")
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would build and push image: {image_uri}")
                else:
                    # Import docker builder
                    try:
                        from jvdeploy.docker_builder import DockerBuilder
                    except ImportError as e:
                        raise LambdaDeployerError(
                            f"Failed to import docker_builder: {e}"
                        )

                    # Get image config from config
                    image_config = self.config.get("image", {})
                    app_config = self.config.get("app", {})

                    # Determine app root (parent of config if not in config)
                    app_root = self.config.get("app_root", ".")

                    # Create Docker builder
                    builder = DockerBuilder(
                        app_root=app_root,
                        image_name=image_config.get("name", "app"),
                        image_tag=image_config.get("tag", "latest"),
                        platform=image_config.get("build", {}).get(
                            "platform", "linux/amd64"
                        ),
                    )

                    # Build and push to ECR
                    logger.info("Building and pushing Docker image to ECR...")
                    builder.build_and_push_to_ecr(
                        ecr_uri=image_uri,
                        region=self.region,
                        account_id=self.account_id,
                        no_cache=not image_config.get("build", {}).get("cache", True),
                    )
                    logger.info(f"✓ Image ready: {image_uri}")

            # Step 3: Ensure IAM role exists
            logger.info("Step 3: Ensuring IAM role exists...")
            iam_config = self.config.get("iam", {})
            role_arn = iam_config.get("role_arn")

            if not role_arn:
                # Create role if it doesn't exist
                role_name = iam_config.get("role_name")
                if not role_name:
                    raise LambdaDeployerError(
                        "Either iam.role_arn or iam.role_name must be provided"
                    )

                role_arn = self._ensure_iam_role(
                    role_name, iam_config.get("policies", [])
                )

            results["iam_role_arn"] = role_arn

            # Step 4: Create or update Lambda function
            if update_function:
                logger.info("Step 4: Creating/updating Lambda function...")
                function_config = self.config.get("function", {})
                function_arn = self._deploy_lambda_function(
                    image_uri=image_uri,
                    role_arn=role_arn,
                    function_config=function_config,
                )
                results["function_arn"] = function_arn

                # Ensure SQLite permissions if needed
                self._ensure_sqlite_permissions(
                    image_uri=image_uri,
                    role_arn=role_arn,
                    function_config=function_config,
                )

            # Step 5: Create or update API Gateway / Function URL
            if create_api:
                # Function URL
                function_url_config = self.config.get("function_url", {})
                if function_url_config.get("enabled", False):
                    logger.info("Step 5a: Configuring Lambda Function URL...")
                    function_url = self._deploy_function_url(
                        function_config.get("name"), function_url_config
                    )
                    results["function_url"] = function_url

                # API Gateway
                api_config = self.config.get("api_gateway", {})
                if api_config.get("enabled", False):
                    logger.info("Step 5b: Creating/updating API Gateway...")
                    api_url = self._deploy_api_gateway(
                        function_config.get("name"), api_config
                    )
                    results["api_url"] = api_url

            results["success"] = True
            logger.info("✓ Lambda deployment completed successfully!")

            return results

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            results["errors"].append(str(e))
            raise LambdaDeployerError(f"Deployment failed: {e}") from e

    def _ensure_efs_access_point(
        self, file_system_id: str, access_point_arn: Optional[str] = None
    ) -> str:
        """Ensure EFS Access Point exists.

        Args:
            file_system_id: EFS File System ID
            access_point_arn: Optional specific Access Point ARN

        Returns:
            Access Point ARN
        """
        try:
            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would ensure EFS access point for {file_system_id}"
                )
                return (
                    access_point_arn
                    or f"arn:aws:elasticfilesystem:{self.region}:123456789012:access-point/fsap-1234567890abcdef0"
                )

            # If ARN provided, just use it
            if access_point_arn:
                return access_point_arn

            app_name = self.config.get("app", {}).get("name", "jvagent")

            # Look for existing access points
            try:
                paginator = self.efs_client.get_paginator("describe_access_points")
                for page in paginator.paginate(FileSystemId=file_system_id):
                    for ap in page.get("AccessPoints", []):
                        # Check tags for app name
                        tags = {t["Key"]: t["Value"] for t in ap.get("Tags", [])}
                        if tags.get("JvAgentApp") == app_name:
                            arn = ap["AccessPointArn"]
                            logger.info(
                                f"Found existing EFS access point for {app_name}: {arn}"
                            )
                            return arn
            except ClientError as e:
                if e.response["Error"]["Code"] == "FileSystemNotFound":
                    logger.warning(
                        f"File system {file_system_id} reported as not found during access point search. "
                        "Attempting to create access point anyway..."
                    )
                else:
                    raise

            # None found, create one
            logger.info(
                f"Creating new EFS access point for {app_name} on {file_system_id}..."
            )
            response = self.efs_client.create_access_point(
                FileSystemId=file_system_id,
                PosixUser={
                    "Uid": 1000,
                    "Gid": 1000,
                },
                RootDirectory={
                    "Path": f"/{app_name}",
                    "CreationInfo": {
                        "OwnerUid": 1000,
                        "OwnerGid": 1000,
                        "Permissions": "777",
                    },
                },
                Tags=[
                    {
                        "Key": "Name",
                        "Value": f"{app_name}-access-point",
                    },
                    {
                        "Key": "JvAgentApp",
                        "Value": app_name,
                    },
                ],
            )
            arn = response["AccessPointArn"]
            access_point_id = response["AccessPointId"]
            logger.info(f"✓ Created EFS access point: {arn}")

            # Wait for access point to be available
            logger.info("Waiting for access point to become available...")
            max_retries = 30
            for i in range(max_retries):
                try:
                    desc = self.efs_client.describe_access_points(
                        AccessPointId=access_point_id
                    )
                    state = desc["AccessPoints"][0]["LifeCycleState"]
                    if state == "available":
                        logger.info("✓ Access point is available")
                        return arn
                    logger.debug(f"Access point state: {state}, waiting...")
                except Exception as e:
                    logger.warning(f"Error checking access point state: {e}")

                time.sleep(2)

            logger.warning(
                "Timed out waiting for access point to become available. Proceeding anyway..."
            )
            return arn

        except Exception as e:
            raise LambdaDeployerError(f"Failed to ensure EFS access point: {e}") from e

    def _ensure_ecr_repository(self, repository_name: str) -> Dict[str, Any]:
        """Ensure ECR repository exists, create if missing.

        Args:
            repository_name: Name of the ECR repository

        Returns:
            Repository information dictionary
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would ensure ECR repository: {repository_name}")
            return {"repositoryName": repository_name, "repositoryUri": "dry-run-uri"}

        try:
            response = self.ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            repository = response["repositories"][0]
            logger.info(f"ECR repository '{repository_name}' already exists")
            return repository

        except self.ecr_client.exceptions.RepositoryNotFoundException:
            # Repository doesn't exist, create it
            ecr_config = self.config.get("ecr", {})
            if not ecr_config.get("create_if_missing", True):
                raise LambdaDeployerError(
                    f"ECR repository '{repository_name}' does not exist and "
                    f"create_if_missing is False"
                )

            logger.info(f"Creating ECR repository: {repository_name}")
            response = self.ecr_client.create_repository(
                repositoryName=repository_name,
                imageScanningConfiguration={"scanOnPush": True},
            )
            repository = response["repository"]
            logger.info(f"✓ Created ECR repository: {repository['repositoryUri']}")
            return repository

    def _ensure_iam_role(self, role_name: str, policies: list) -> str:
        """Ensure IAM role exists with required policies.

        Args:
            role_name: Name of the IAM role
            policies: List of policy ARNs to attach

        Returns:
            Role ARN
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would ensure IAM role: {role_name}")
            return f"arn:aws:iam::123456789012:role/{role_name}"

        try:
            # Check if role exists
            response = self.iam_client.get_role(RoleName=role_name)
            role_arn = response["Role"]["Arn"]
            logger.info(f"IAM role '{role_name}' already exists")

            # Ensure policies are attached
            for policy_arn in policies:
                try:
                    self.iam_client.attach_role_policy(
                        RoleName=role_name, PolicyArn=policy_arn
                    )
                    logger.debug(f"Attached policy {policy_arn} to role {role_name}")
                except Exception as e:
                    logger.debug(f"Policy {policy_arn} may already be attached: {e}")

            return role_arn

        except self.iam_client.exceptions.NoSuchEntityException:
            # Role doesn't exist, create it
            logger.info(f"Creating IAM role: {role_name}")

            # Trust policy for Lambda
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }

            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=str(trust_policy).replace("'", '"'),
                Description=f"Role for Lambda function {role_name}",
            )
            role_arn = response["Role"]["Arn"]
            logger.info(f"✓ Created IAM role: {role_arn}")

            # Attach policies
            for policy_arn in policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name, PolicyArn=policy_arn
                )
                logger.info(f"✓ Attached policy: {policy_arn}")

            # Wait for role to propagate
            logger.info("Waiting for IAM role to propagate...")
            time.sleep(10)

            return role_arn

    def _get_efs_vpc_config(self, file_system_id: str) -> Dict[str, Any]:
        """Auto-detect VPC configuration from EFS file system.

        Args:
            file_system_id: EFS File System ID

        Returns:
            VPC configuration dictionary with SubnetIds and SecurityGroupIds
        """
        try:
            logger.info(
                f"Auto-detecting VPC configuration from EFS {file_system_id}..."
            )

            # Get mount targets
            mount_targets = self.efs_client.describe_mount_targets(
                FileSystemId=file_system_id
            )["MountTargets"]

            if not mount_targets:
                raise LambdaDeployerError(
                    f"No mount targets found for EFS {file_system_id}"
                )

            subnet_ids = list(set(mt["SubnetId"] for mt in mount_targets))
            security_group_ids = set()

            # Get security groups from mount targets
            for mt in mount_targets:
                sgs = self.efs_client.describe_mount_target_security_groups(
                    MountTargetId=mt["MountTargetId"]
                )["SecurityGroups"]
                security_group_ids.update(sgs)

            vpc_config = {
                "SubnetIds": subnet_ids,
                "SecurityGroupIds": list(security_group_ids),
            }

            logger.info(
                f"✓ Auto-detected VPC config: {len(subnet_ids)} subnets, {len(security_group_ids)} SGs"
            )
            return vpc_config

        except Exception as e:
            raise LambdaDeployerError(
                f"Failed to auto-detect VPC config from EFS: {e}"
            ) from e

    def _build_lambda_config(
        self, image_uri: str, role_arn: str, function_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build Lambda function configuration dictionary.

        Args:
            image_uri: Full ECR image URI
            role_arn: IAM role ARN
            function_config: Function configuration

        Returns:
            Configuration dictionary for create/update_function
        """
        function_name = function_config.get("name")

        config = {
            "FunctionName": function_name,
            "Role": role_arn,
            "Code": {"ImageUri": image_uri},
            "PackageType": "Image",
            "Timeout": function_config.get("timeout", 300),
            "MemorySize": function_config.get("memory", 1024),
            "EphemeralStorage": {"Size": function_config.get("ephemeral_storage", 512)},
        }

        # Add description if provided
        if description := function_config.get("description"):
            config["Description"] = description

        # Add environment variables
        env_vars = self.config.get("environment", {})
        if env_vars:
            config["Environment"] = {"Variables": env_vars}

        # Add VPC configuration if enabled
        vpc_config = self.config.get("vpc", {})
        if vpc_config.get("enabled", False):
            config["VpcConfig"] = {
                "SubnetIds": vpc_config.get("subnet_ids", []),
                "SecurityGroupIds": vpc_config.get("security_group_ids", []),
            }

        # Add EFS configuration if enabled
        efs_config = self.config.get("efs", {})
        if efs_config.get("enabled", False):
            file_system_id = efs_config.get("file_system_id")
            if not file_system_id:
                raise LambdaDeployerError(
                    "efs.file_system_id is required when EFS is enabled"
                )

            access_point_arn = self._ensure_efs_access_point(
                file_system_id, efs_config.get("access_point_arn")
            )

            config["FileSystemConfigs"] = [
                {
                    "Arn": access_point_arn,
                    "LocalMountPath": efs_config.get("mount_path", "/mnt/efs"),
                }
            ]

            # EFS requires VPC, so if not configured, try to auto-detect from EFS
            if "VpcConfig" not in config:
                logger.info(
                    "EFS enabled but VPC not configured. Auto-detecting from EFS..."
                )
                config["VpcConfig"] = self._get_efs_vpc_config(file_system_id)

        return config

    def _deploy_lambda_function(
        self, image_uri: str, role_arn: str, function_config: Dict[str, Any]
    ) -> str:
        """Create or update Lambda function.

        Args:
            image_uri: Full ECR image URI
            role_arn: IAM role ARN
            function_config: Function configuration

        Returns:
            Function ARN
        """
        function_name = function_config.get("name")
        if not function_name:
            raise LambdaDeployerError("function.name is required")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would deploy Lambda function: {function_name}")
            return f"arn:aws:lambda:{self.region}:123456789012:function:{function_name}"

        # Build function configuration
        config = self._build_lambda_config(image_uri, role_arn, function_config)

        try:
            # Try to update existing function
            logger.info(f"Checking if function '{function_name}' exists...")
            self.lambda_client.get_function(FunctionName=function_name)

            # Function exists, update it
            logger.info(f"Updating Lambda function: {function_name}")

            # Update function code
            self.lambda_client.update_function_code(
                FunctionName=function_name, ImageUri=image_uri
            )

            # Wait for update to complete
            logger.info("Waiting for function code update to complete...")
            waiter = self.lambda_client.get_waiter("function_updated")
            waiter.wait(FunctionName=function_name)

            # Update function configuration
            update_config = {
                k: v
                for k, v in config.items()
                if k not in ["FunctionName", "Code", "PackageType"]
            }
            self.lambda_client.update_function_configuration(
                FunctionName=function_name, **update_config
            )

            # Wait for configuration update
            logger.info("Waiting for function configuration update to complete...")
            waiter.wait(FunctionName=function_name)

            response = self.lambda_client.get_function(FunctionName=function_name)
            function_arn = response["Configuration"]["FunctionArn"]
            logger.info(f"✓ Updated Lambda function: {function_arn}")

            return function_arn

        except self.lambda_client.exceptions.ResourceNotFoundException:
            # Function doesn't exist, create it
            logger.info(f"Creating Lambda function: {function_name}")

            response = self.lambda_client.create_function(**config)
            function_arn = response["FunctionArn"]

            # Wait for function to be active
            logger.info("Waiting for function to become active...")
            waiter = self.lambda_client.get_waiter("function_active")
            waiter.wait(FunctionName=function_name)

            logger.info(f"✓ Created Lambda function: {function_arn}")
            return function_arn

    def _ensure_sqlite_permissions(
        self, image_uri: str, role_arn: str, function_config: Dict[str, Any]
    ) -> None:
        """Ensure SQLite database permissions are correct on EFS.

        Args:
            image_uri: Full ECR image URI
            role_arn: IAM role ARN
            function_config: Function configuration
        """
        # Check if we need to run this
        env_vars = self.config.get("environment", {})
        db_type = env_vars.get("JVSPATIAL_DB_TYPE", "json")
        db_path = env_vars.get("JVSPATIAL_DB_PATH")

        if db_type != "sqlite" or not db_path:
            return

        # Check if EFS is enabled
        if not self.config.get("efs", {}).get("enabled", False):
            return

        logger.info(f"Ensuring write permissions for SQLite DB at {db_path}...")

        if self.dry_run:
            logger.info("[DRY RUN] Would run permission fix lambda")
            return

        setup_function_name = f"{function_config.get('name')}-setup-{int(time.time())}"

        try:
            # Build config for setup function
            setup_config = self._build_lambda_config(
                image_uri, role_arn, function_config
            )
            setup_config["FunctionName"] = setup_function_name

            # Override command to fix permissions and satisfy Lambda Adapter
            # 1. Create directory/file and set permissions
            # 2. Start a dummy web server on 8080 so Lambda Adapter thinks we are healthy
            #    and the Invoke request succeeds.
            cmd = (
                f"mkdir -p $(dirname {db_path}) && "
                f"touch {db_path} && "
                f"chmod 666 {db_path} && "
                f"chmod 777 $(dirname {db_path}) && "
                "python3 -c 'import http.server, socketserver; "
                'print("Starting dummy server..."); '
                'server = socketserver.TCPServer(("0.0.0.0", 8080), http.server.SimpleHTTPRequestHandler); '
                "server.serve_forever()'"
            )

            setup_config["ImageConfig"] = {
                "EntryPoint": ["/bin/sh", "-c"],
                "Command": [cmd],
            }

            # Create setup function
            logger.info(f"Creating temporary setup function: {setup_function_name}")
            self.lambda_client.create_function(**setup_config)

            # Wait for active
            waiter = self.lambda_client.get_waiter("function_active")
            waiter.wait(FunctionName=setup_function_name)

            # Invoke function
            logger.info("Invoking setup function...")
            response = self.lambda_client.invoke(
                FunctionName=setup_function_name,
                InvocationType="RequestResponse",
                LogType="Tail",
            )

            if response.get("FunctionError"):
                logger.error(f"Setup function failed: {response.get('FunctionError')}")
                # Try to get logs
                import base64

                if "LogResult" in response:
                    logs = base64.b64decode(response["LogResult"]).decode("utf-8")
                    logger.error(f"Logs:\n{logs}")
            else:
                logger.info("✓ SQLite permissions fixed successfully")

        except Exception as e:
            logger.warning(f"Failed to fix SQLite permissions: {e}")

        finally:
            # Cleanup
            try:
                logger.info(f"Deleting temporary setup function: {setup_function_name}")
                self.lambda_client.delete_function(FunctionName=setup_function_name)
            except Exception as e:
                logger.warning(f"Failed to delete setup function: {e}")

    def _deploy_api_gateway(
        self, function_name: str, api_config: Dict[str, Any]
    ) -> str:
        """Create or update API Gateway.

        Args:
            function_name: Lambda function name
            api_config: API Gateway configuration

        Returns:
            API Gateway URL
        """
        api_type = api_config.get("type", "HTTP")

        if api_type == "HTTP":
            return self._deploy_http_api(function_name, api_config)
        else:
            raise LambdaDeployerError(
                f"API Gateway type '{api_type}' not yet supported"
            )

    def _deploy_http_api(self, function_name: str, api_config: Dict[str, Any]) -> str:
        """Create or update HTTP API (API Gateway v2).

        Args:
            function_name: Lambda function name
            api_config: API Gateway configuration

        Returns:
            API URL
        """
        api_name = api_config.get("name", f"{function_name}-api")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would create HTTP API: {api_name}")
            stage_name = api_config.get("stage_name", "$default")
            suffix = f"/{stage_name}" if stage_name != "$default" else ""
            return f"https://api-id.execute-api.{self.region}.amazonaws.com{suffix}"

        # Check if API already exists
        response = self.apigatewayv2_client.get_apis()
        existing_api = None
        for api in response.get("Items", []):
            if api["Name"] == api_name:
                existing_api = api
                break

        if existing_api:
            api_id = existing_api["ApiId"]
            logger.info(f"HTTP API '{api_name}' already exists: {api_id}")
        else:
            # Create new API
            logger.info(f"Creating HTTP API: {api_name}")

            cors_config = api_config.get("cors", {})
            create_params = {
                "Name": api_name,
                "ProtocolType": "HTTP",
                "Target": f"arn:aws:lambda:{self.region}:{self.account_id}:function:{function_name}",
            }

            if cors_config.get("enabled", False):
                create_params["CorsConfiguration"] = {
                    "AllowOrigins": cors_config.get("allow_origins", ["*"]),
                    "AllowMethods": cors_config.get("allow_methods", ["*"]),
                    "AllowHeaders": cors_config.get("allow_headers", ["*"]),
                }

            response = self.apigatewayv2_client.create_api(**create_params)
            api_id = response["ApiId"]
            logger.info(f"✓ Created HTTP API: {api_id}")

        # Get the API endpoint
        stage_name = api_config.get("stage_name", "$default")
        if stage_name == "$default":
            api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com"
        else:
            api_url = (
                f"https://{api_id}.execute-api.{self.region}.amazonaws.com/{stage_name}"
            )

        # Ensure Lambda permission exists
        self._add_api_gateway_permission(function_name, api_id)

        logger.info(f"✓ API Gateway URL: {api_url}")
        return api_url

    def _add_api_gateway_permission(self, function_name: str, api_id: str):
        """Add permission for API Gateway to invoke Lambda function.

        Args:
            function_name: Lambda function name
            api_id: API Gateway ID
        """
        statement_id = f"ApiGatewayInvoke-{api_id}"
        source_arn = f"arn:aws:execute-api:{self.region}:{self.account_id}:{api_id}/*/*"

        try:
            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=statement_id,
                Action="lambda:InvokeFunction",
                Principal="apigateway.amazonaws.com",
                SourceArn=source_arn,
            )
            logger.info("✓ Added API Gateway invocation permission")
        except self.lambda_client.exceptions.ResourceConflictException:
            # Permission already exists
            logger.debug("API Gateway invocation permission already exists")
        except Exception as e:
            logger.warning(f"Failed to add API Gateway permission: {e}")

    def _deploy_function_url(
        self, function_name: str, url_config: Dict[str, Any]
    ) -> str:
        """Create or update Lambda Function URL.

        Args:
            function_name: Lambda function name
            url_config: Function URL configuration

        Returns:
            Function URL
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create Function URL for: {function_name}")
            return f"https://dry-run-url.lambda-url.{self.region}.on.aws/"

        auth_type = url_config.get("auth_type", "NONE")
        invoke_mode = url_config.get("invoke_mode", "BUFFERED")
        cors_config = url_config.get("cors", {})

        logger.info(f"Configuring Function URL for: {function_name}")

        # Prepare configuration parameters
        params = {
            "FunctionName": function_name,
            "AuthType": auth_type,
            "InvokeMode": invoke_mode,
        }

        if cors_config.get("enabled", False):
            params["Cors"] = {
                "AllowOrigins": cors_config.get("allow_origins", ["*"]),
                "AllowMethods": cors_config.get("allow_methods", ["*"]),
                "AllowHeaders": cors_config.get("allow_headers", ["*"]),
                "MaxAge": cors_config.get("max_age", 0),
                "AllowCredentials": cors_config.get("allow_credentials", False),
            }

        try:
            # Try to create function URL
            response = self.lambda_client.create_function_url_config(**params)
            function_url = response["FunctionUrl"]
            logger.info(f"✓ Created Function URL: {function_url}")

        except self.lambda_client.exceptions.ResourceConflictException:
            # URL config already exists, update it
            logger.info("Function URL config already exists, updating...")

            # Update params for update call (remove FunctionName from kwargs if we passed it as arg)
            update_params = params.copy()
            update_params.pop("FunctionName")

            response = self.lambda_client.update_function_url_config(
                FunctionName=function_name, **update_params
            )
            function_url = response["FunctionUrl"]
            logger.info(f"✓ Updated Function URL: {function_url}")

        # Add permission for public access if AuthType is NONE
        if auth_type == "NONE":
            self._add_function_url_permission(function_name)

        return function_url

    def _add_function_url_permission(self, function_name: str):
        """Add permission for public access to Function URL.

        Args:
            function_name: Lambda function name
        """
        statement_id = "FunctionURLAllowPublicAccess"

        try:
            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=statement_id,
                Action="lambda:InvokeFunctionUrl",
                Principal="*",
                FunctionUrlAuthType="NONE",
            )
            logger.info("✓ Added public access permission for Function URL")
        except self.lambda_client.exceptions.ResourceConflictException:
            # Permission already exists
            logger.debug("Public access permission already exists")

    def get_function_status(
        self, function_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Lambda function status.

        Args:
            function_name: Function name (uses config if not provided)

        Returns:
            Function status information
        """
        if not function_name:
            function_name = self.config.get("function", {}).get("name")

        if not function_name:
            raise LambdaDeployerError("Function name is required")

        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            config = response["Configuration"]

            return {
                "function_name": config["FunctionName"],
                "function_arn": config["FunctionArn"],
                "state": config["State"],
                "last_modified": config["LastModified"],
                "memory": config["MemorySize"],
                "timeout": config["Timeout"],
                "runtime": config.get("Runtime", "container"),
                "image_uri": config.get("PackageType") == "Image",
            }

        except self.lambda_client.exceptions.ResourceNotFoundException:
            return {
                "function_name": function_name,
                "state": "NOT_FOUND",
                "error": f"Function '{function_name}' not found",
            }

    def destroy(
        self,
        function_name: Optional[str] = None,
        delete_api: bool = False,
        delete_role: bool = False,
    ) -> Dict[str, Any]:
        """Destroy Lambda deployment resources.

        Args:
            function_name: Function name (uses config if not provided)
            delete_api: Whether to delete API Gateway
            delete_role: Whether to delete IAM role

        Returns:
            Dictionary with destruction results
        """
        if not function_name:
            function_name = self.config.get("function", {}).get("name")

        if not function_name:
            raise LambdaDeployerError("Function name is required")

        results = {"deleted": [], "errors": []}

        if self.dry_run:
            logger.info(f"[DRY RUN] Would delete Lambda function: {function_name}")
            if delete_api:
                logger.info("[DRY RUN] Would delete API Gateway")
            if delete_role:
                logger.info("[DRY RUN] Would delete IAM role")
            return results

        # Delete Lambda function
        try:
            self.lambda_client.delete_function(FunctionName=function_name)
            logger.info(f"✓ Deleted Lambda function: {function_name}")
            results["deleted"].append(f"function:{function_name}")
        except self.lambda_client.exceptions.ResourceNotFoundException:
            logger.warning(f"Function '{function_name}' not found")
        except Exception as e:
            error = f"Failed to delete function: {e}"
            logger.error(error)
            results["errors"].append(error)

        # Delete API Gateway if requested
        if delete_api:
            try:
                api_name = self.config.get("api_gateway", {}).get(
                    "name", f"{function_name}-api"
                )
                response = self.apigatewayv2_client.get_apis()
                for api in response.get("Items", []):
                    if api["Name"] == api_name:
                        self.apigatewayv2_client.delete_api(ApiId=api["ApiId"])
                        logger.info(f"✓ Deleted API Gateway: {api_name}")
                        results["deleted"].append(f"api:{api_name}")
                        break
            except Exception as e:
                error = f"Failed to delete API Gateway: {e}"
                logger.error(error)
                results["errors"].append(error)

        # Delete IAM role if requested
        if delete_role:
            try:
                role_name = self.config.get("iam", {}).get("role_name")
                if role_name:
                    # Detach policies first
                    response = self.iam_client.list_attached_role_policies(
                        RoleName=role_name
                    )
                    for policy in response.get("AttachedPolicies", []):
                        self.iam_client.detach_role_policy(
                            RoleName=role_name, PolicyArn=policy["PolicyArn"]
                        )

                    # Delete role
                    self.iam_client.delete_role(RoleName=role_name)
                    logger.info(f"✓ Deleted IAM role: {role_name}")
                    results["deleted"].append(f"role:{role_name}")
            except Exception as e:
                error = f"Failed to delete IAM role: {e}"
                logger.error(error)
                results["errors"].append(error)

        return results
