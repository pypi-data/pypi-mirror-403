"""CLI entry point for jvdeploy.

Provides command-line interface for generating Dockerfiles and deploying jvagent applications.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from jvdeploy import Bundler
from jvdeploy.config import DeployConfig, DeployConfigError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def setup_argparse() -> argparse.ArgumentParser:
    """Set up argument parser with all commands and options."""
    parser = argparse.ArgumentParser(
        prog="jvdeploy",
        description="Dockerfile generator and deployment tool for jvagent applications",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    # Create subparsers for main commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command (original functionality)
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate Dockerfile for jvagent application",
    )
    generate_parser.add_argument(
        "app_root",
        nargs="?",
        default=os.getcwd(),
        help="Path to jvagent app root directory (default: current directory)",
    )

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize deployment configuration",
    )
    init_parser.add_argument(
        "app_root",
        nargs="?",
        default=os.getcwd(),
        help="Path to jvagent app root directory (default: current directory)",
    )
    init_parser.add_argument(
        "--lambda",
        dest="lambda_config",
        action="store_true",
        help="Include Lambda configuration",
    )
    init_parser.add_argument(
        "--kubernetes",
        dest="k8s_config",
        action="store_true",
        help="Include Kubernetes configuration",
    )
    init_parser.add_argument(
        "--all",
        dest="all_config",
        action="store_true",
        default=True,
        help="Include both Lambda and Kubernetes configuration (default)",
    )
    init_parser.add_argument(
        "--config",
        default="deploy.yaml",
        help="Output config file path (default: deploy.yaml)",
    )

    # Deploy command with subcommands
    deploy_parser = subparsers.add_parser(
        "deploy",
        help="Deploy application to Lambda or Kubernetes",
    )
    deploy_subparsers = deploy_parser.add_subparsers(
        dest="platform", help="Deployment platform"
    )

    # Deploy lambda subcommand
    lambda_parser = deploy_subparsers.add_parser(
        "lambda",
        help="Deploy to AWS Lambda",
    )
    lambda_parser.add_argument(
        "app_root",
        nargs="?",
        default=os.getcwd(),
        help="Path to jvagent app root directory (default: current directory)",
    )
    lambda_parser.add_argument(
        "--config",
        default="deploy.yaml",
        help="Config file path (default: deploy.yaml)",
    )
    lambda_parser.add_argument(
        "--build",
        action="store_true",
        help="Build Docker image",
    )
    lambda_parser.add_argument(
        "--push",
        action="store_true",
        help="Push image to ECR",
    )
    lambda_parser.add_argument(
        "--update",
        action="store_true",
        help="Update Lambda function",
    )
    lambda_parser.add_argument(
        "--create-api",
        action="store_true",
        help="Create/update API Gateway",
    )
    lambda_parser.add_argument(
        "--all",
        dest="all_steps",
        action="store_true",
        help="Perform all deployment steps (default if no specific steps specified)",
    )
    lambda_parser.add_argument(
        "--region",
        help="Override AWS region",
    )
    lambda_parser.add_argument(
        "--function",
        help="Override Lambda function name",
    )
    lambda_parser.add_argument(
        "--env",
        action="append",
        help="Override environment variables (KEY=VALUE)",
    )
    lambda_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )

    # Deploy k8s subcommand
    k8s_parser = deploy_subparsers.add_parser(
        "k8s",
        help="Deploy to Kubernetes",
    )
    k8s_parser.add_argument(
        "app_root",
        nargs="?",
        default=os.getcwd(),
        help="Path to jvagent app root directory (default: current directory)",
    )
    k8s_parser.add_argument(
        "--config",
        default="deploy.yaml",
        help="Config file path (default: deploy.yaml)",
    )
    k8s_parser.add_argument(
        "--build",
        action="store_true",
        help="Build Docker image",
    )
    k8s_parser.add_argument(
        "--push",
        action="store_true",
        help="Push image to registry",
    )
    k8s_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply Kubernetes manifests",
    )
    k8s_parser.add_argument(
        "--all",
        dest="all_steps",
        action="store_true",
        help="Perform all deployment steps (default if no specific steps specified)",
    )
    k8s_parser.add_argument(
        "--namespace",
        help="Override Kubernetes namespace",
    )
    k8s_parser.add_argument(
        "--context",
        help="Override kubectl context",
    )
    k8s_parser.add_argument(
        "--env",
        action="append",
        help="Override environment variables (KEY=VALUE)",
    )
    k8s_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show manifests without applying",
    )

    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Check deployment status",
    )
    status_subparsers = status_parser.add_subparsers(
        dest="platform", help="Deployment platform"
    )

    # Status lambda subcommand
    status_lambda_parser = status_subparsers.add_parser(
        "lambda",
        help="Check Lambda deployment status",
    )
    status_lambda_parser.add_argument(
        "--config",
        default="deploy.yaml",
        help="Config file path (default: deploy.yaml)",
    )
    status_lambda_parser.add_argument(
        "--function",
        help="Lambda function name",
    )
    status_lambda_parser.add_argument(
        "--region",
        help="AWS region",
    )
    status_lambda_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # Status k8s subcommand
    status_k8s_parser = status_subparsers.add_parser(
        "k8s",
        help="Check Kubernetes deployment status",
    )
    status_k8s_parser.add_argument(
        "--config",
        default="deploy.yaml",
        help="Config file path (default: deploy.yaml)",
    )
    status_k8s_parser.add_argument(
        "--namespace",
        help="Kubernetes namespace",
    )
    status_k8s_parser.add_argument(
        "--context",
        help="kubectl context",
    )
    status_k8s_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    # Logs command
    logs_parser = subparsers.add_parser(
        "logs",
        help="View application logs",
    )
    logs_subparsers = logs_parser.add_subparsers(
        dest="platform", help="Deployment platform"
    )

    # Logs lambda subcommand
    logs_lambda_parser = logs_subparsers.add_parser(
        "lambda",
        help="View Lambda logs",
    )
    logs_lambda_parser.add_argument(
        "--config",
        default="deploy.yaml",
        help="Config file path (default: deploy.yaml)",
    )
    logs_lambda_parser.add_argument(
        "--function",
        help="Lambda function name",
    )
    logs_lambda_parser.add_argument(
        "--region",
        help="AWS region",
    )
    logs_lambda_parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Stream logs in real-time",
    )
    logs_lambda_parser.add_argument(
        "--tail",
        type=int,
        help="Show last N lines",
    )
    logs_lambda_parser.add_argument(
        "--since",
        help="Show logs since time (e.g., '5m', '1h', '2023-01-01')",
    )

    # Logs k8s subcommand
    logs_k8s_parser = logs_subparsers.add_parser(
        "k8s",
        help="View Kubernetes logs",
    )
    logs_k8s_parser.add_argument(
        "--config",
        default="deploy.yaml",
        help="Config file path (default: deploy.yaml)",
    )
    logs_k8s_parser.add_argument(
        "--namespace",
        help="Kubernetes namespace",
    )
    logs_k8s_parser.add_argument(
        "--pod",
        help="Specific pod name",
    )
    logs_k8s_parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Stream logs in real-time",
    )
    logs_k8s_parser.add_argument(
        "--tail",
        type=int,
        help="Show last N lines",
    )
    logs_k8s_parser.add_argument(
        "--since",
        help="Show logs since time",
    )

    # Destroy command
    destroy_parser = subparsers.add_parser(
        "destroy",
        help="Destroy deployment resources",
    )
    destroy_subparsers = destroy_parser.add_subparsers(
        dest="platform", help="Deployment platform"
    )

    # Destroy lambda subcommand
    destroy_lambda_parser = destroy_subparsers.add_parser(
        "lambda",
        help="Destroy Lambda deployment",
    )
    destroy_lambda_parser.add_argument(
        "--config",
        default="deploy.yaml",
        help="Config file path (default: deploy.yaml)",
    )
    destroy_lambda_parser.add_argument(
        "--function",
        help="Lambda function name",
    )
    destroy_lambda_parser.add_argument(
        "--delete-api",
        action="store_true",
        help="Also delete API Gateway",
    )
    destroy_lambda_parser.add_argument(
        "--delete-role",
        action="store_true",
        help="Also delete IAM role",
    )
    destroy_lambda_parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # Destroy k8s subcommand
    destroy_k8s_parser = destroy_subparsers.add_parser(
        "k8s",
        help="Destroy Kubernetes deployment",
    )
    destroy_k8s_parser.add_argument(
        "--config",
        default="deploy.yaml",
        help="Config file path (default: deploy.yaml)",
    )
    destroy_k8s_parser.add_argument(
        "--namespace",
        help="Kubernetes namespace",
    )
    destroy_k8s_parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )

    return parser


def handle_generate(args: argparse.Namespace) -> int:
    """Handle generate command."""
    app_root = Path(args.app_root).expanduser().resolve()

    if not app_root.exists() or not app_root.is_dir():
        logger.error(
            f"Error: Path '{args.app_root}' does not exist or is not a directory"
        )
        return 1

    logger.info(f"Initializing bundler for app: {app_root}")
    bundler = Bundler(app_root=str(app_root))

    success = bundler.generate_dockerfile()

    if not success:
        logger.error("Dockerfile generation failed")
        return 1

    print(f"\n✓ Dockerfile generated successfully in {app_root}")
    return 0


def handle_init(args: argparse.Namespace) -> int:
    """Handle init command to create deploy.yaml configuration."""
    try:
        app_root = Path(args.app_root).expanduser().resolve()

        if not app_root.exists() or not app_root.is_dir():
            logger.error(
                f"Error: Path '{args.app_root}' does not exist or is not a directory"
            )
            return 1

        # Determine output path
        output_path = app_root / args.config

        # Check if config already exists
        if output_path.exists():
            response = input(
                f"Configuration file '{output_path}' already exists. Overwrite? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("Initialization cancelled.")
                return 0

        # Load template
        import jvdeploy

        package_dir = Path(jvdeploy.__file__).parent
        template_path = package_dir / "templates" / "deploy.yaml.template"

        if not template_path.exists():
            logger.error(f"Template file not found: {template_path}")
            return 1

        # Read template
        with open(template_path, "r") as f:
            template_content = f.read()

        # Determine which sections to enable
        enable_lambda = args.lambda_config or args.all_config
        enable_k8s = args.k8s_config or args.all_config

        # Update enabled flags in template
        if enable_lambda and not enable_k8s:
            template_content = template_content.replace(
                "lambda:\n  enabled: false", "lambda:\n  enabled: true"
            )
        elif enable_k8s and not enable_lambda:
            template_content = template_content.replace(
                "kubernetes:\n  enabled: false", "kubernetes:\n  enabled: true"
            )
        elif enable_lambda and enable_k8s:
            template_content = template_content.replace(
                "lambda:\n  enabled: false", "lambda:\n  enabled: true"
            )
            template_content = template_content.replace(
                "kubernetes:\n  enabled: false", "kubernetes:\n  enabled: true"
            )

        # Write configuration file
        with open(output_path, "w") as f:
            f.write(template_content)

        print(f"\n✓ Created deployment configuration: {output_path}")
        print("\nNext steps:")
        print("  1. Edit deploy.yaml to configure your deployment")
        print("  2. Set required environment variables (e.g., JVAGENT_ADMIN_PASSWORD)")

        if enable_lambda:
            print("  3. Deploy to Lambda: jvdeploy deploy lambda --all")
        if enable_k8s:
            print("  3. Deploy to Kubernetes: jvdeploy deploy k8s --all")

        return 0

    except Exception as e:
        logger.error(f"Failed to initialize configuration: {e}", exc_info=True)
        return 1


def handle_deploy(args: argparse.Namespace) -> int:
    """Handle deploy command."""
    if not args.platform:
        logger.error("Error: Please specify a platform (lambda or k8s)")
        print("Usage: jvdeploy deploy {lambda|k8s} [options]")
        return 1

    # Check if no specific steps are requested, default to --all
    if args.platform == "lambda":
        if not any(
            [args.build, args.push, args.update, args.create_api, args.all_steps]
        ):
            args.all_steps = True
    elif args.platform == "k8s":
        if not any([args.build, args.push, args.apply, args.all_steps]):
            args.all_steps = True

    if args.platform == "lambda":
        return handle_deploy_lambda(args)
    elif args.platform == "k8s":
        return handle_deploy_k8s(args)
    else:
        logger.error(f"Unknown platform: {args.platform}")
        return 1


def handle_deploy_lambda(args: argparse.Namespace) -> int:
    """Handle Lambda deployment."""
    try:
        # Load configuration
        app_root = Path(args.app_root).expanduser().resolve()
        config_path = app_root / args.config

        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            print(
                f"\n💡 Tip: Run 'jvdeploy init' to create a deploy.yaml configuration"
            )
            return 1

        logger.info(f"Loading configuration from {config_path}")
        config = DeployConfig(str(config_path), str(app_root))

        if not config.is_lambda_enabled():
            logger.error("Lambda deployment is not enabled in configuration")
            print("\n💡 Set 'lambda.enabled: true' in deploy.yaml")
            return 1

        # Check if Dockerfile exists, generate if missing
        dockerfile_path = app_root / "Dockerfile"
        if not dockerfile_path.exists():
            logger.info("Dockerfile not found, generating...")
            bundler = Bundler(app_root=str(app_root))
            if not bundler.generate_dockerfile():
                logger.error("Failed to generate Dockerfile")
                return 1
            logger.info("✓ Dockerfile generated")

        # Apply overrides
        if args.region:
            config.config["lambda"]["region"] = args.region
        if args.function:
            config.config["lambda"]["function"]["name"] = args.function
        if args.env:
            config.override_env_vars(args.env)

        lambda_config = config.get_lambda_config()

        # Add app_root to config for Docker builder
        lambda_config["app_root"] = str(app_root)
        lambda_config["app"] = config.get_app_config()
        lambda_config["image"] = config.get_image_config()

        # Import and create deployer
        try:
            from jvdeploy.aws import LambdaDeployer
        except ImportError:
            logger.error(
                "boto3 is required for Lambda deployment. Install with: pip install boto3"
            )
            return 1

        deployer = LambdaDeployer(lambda_config, dry_run=args.dry_run)

        # Get account ID (auto-detect if needed)
        account_id = lambda_config.get("account_id")
        if not account_id:
            account_id = deployer.get_account_id()
            lambda_config["account_id"] = account_id

        # Get image URI with account_id
        image_uri = config.get_ecr_image_uri(
            lambda_config.get("region"), account_id=account_id
        )

        # Determine which steps to perform
        build_image = args.all_steps or args.build
        push_image = args.all_steps or args.push
        update_function = args.all_steps or args.update
        create_api = args.all_steps or args.create_api

        if args.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made\n")

        print(f"📦 Deploying to AWS Lambda")
        print(f"   Region: {lambda_config.get('region')}")
        print(f"   Function: {lambda_config.get('function', {}).get('name')}")
        print(f"   Image: {image_uri}")
        print()

        # Execute deployment
        results = deployer.deploy(
            image_uri=image_uri,
            build_image=build_image,
            push_image=push_image,
            update_function=update_function,
            create_api=create_api,
        )

        if results["success"]:
            print("\n✓ Lambda deployment completed successfully!")
            if results.get("function_arn"):
                print(f"  Function ARN: {results['function_arn']}")
            if results.get("api_url"):
                print(f"  API URL: {results['api_url']}")
            if results.get("function_url"):
                print(f"  Function URL: {results['function_url']}")
            return 0
        else:
            print("\n✗ Lambda deployment failed")
            for error in results.get("errors", []):
                print(f"  Error: {error}")
            return 1

    except DeployConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        return 1


def handle_deploy_k8s(args: argparse.Namespace) -> int:
    """Handle Kubernetes deployment."""
    print("⚠️  'deploy k8s' command not yet implemented")
    print(f"This will deploy your application to Kubernetes.")

    if args.dry_run:
        print("(Dry run mode - no changes would be made)")

    return 1


def handle_status(args: argparse.Namespace) -> int:
    """Handle status command."""
    if not args.platform:
        logger.error("Error: Please specify a platform (lambda or k8s)")
        print("Usage: jvdeploy status {lambda|k8s} [options]")
        return 1

    if args.platform == "lambda":
        return handle_status_lambda(args)
    elif args.platform == "k8s":
        return handle_status_k8s(args)
    else:
        logger.error(f"Unknown platform: {args.platform}")
        return 1


def handle_status_lambda(args: argparse.Namespace) -> int:
    """Handle Lambda status check."""
    try:
        # Load configuration if available
        config_path = Path(args.config)

        if config_path.exists():
            config = DeployConfig(str(config_path))
            lambda_config = config.get_lambda_config()

            if not lambda_config:
                logger.error("Lambda deployment is not enabled in configuration")
                return 1

            # Apply overrides
            if args.region:
                lambda_config["region"] = args.region
            if args.function:
                lambda_config["function"]["name"] = args.function
        else:
            # Create minimal config from CLI args
            if not args.function:
                logger.error("Function name required (--function or deploy.yaml)")
                return 1

            lambda_config = {
                "region": args.region or "us-east-1",
                "function": {"name": args.function},
            }

        # Import and create deployer
        try:
            from jvdeploy.aws import LambdaDeployer
        except ImportError:
            logger.error("boto3 is required. Install with: pip install boto3")
            return 1

        deployer = LambdaDeployer(lambda_config)
        status = deployer.get_function_status()

        if args.json:
            import json

            print(json.dumps(status, indent=2))
        else:
            print(f"\n📊 Lambda Function Status")
            print(f"   Function: {status.get('function_name')}")
            print(f"   State: {status.get('state')}")

            if status.get("state") != "NOT_FOUND":
                print(f"   ARN: {status.get('function_arn')}")
                print(f"   Memory: {status.get('memory')} MB")
                print(f"   Timeout: {status.get('timeout')} seconds")
                print(f"   Last Modified: {status.get('last_modified')}")
            else:
                print(f"   Error: {status.get('error')}")

        return 0

    except Exception as e:
        logger.error(f"Failed to get status: {e}", exc_info=True)
        return 1


def handle_status_k8s(args: argparse.Namespace) -> int:
    """Handle Kubernetes status check."""
    print("⚠️  'status k8s' command not yet implemented")
    print("This will show the Kubernetes deployment status.")
    return 1


def handle_logs(args: argparse.Namespace) -> int:
    """Handle logs command."""
    if not args.platform:
        logger.error("Error: Please specify a platform (lambda or k8s)")
        print("Usage: jvdeploy logs {lambda|k8s} [options]")
        return 1

    if args.platform == "lambda":
        return handle_logs_lambda(args)
    elif args.platform == "k8s":
        return handle_logs_k8s(args)
    else:
        logger.error(f"Unknown platform: {args.platform}")
        return 1


def handle_logs_lambda(args: argparse.Namespace) -> int:
    """Handle Lambda logs viewing."""
    try:
        import time as time_module
        from datetime import datetime, timedelta

        import boto3
    except ImportError:
        logger.error("boto3 is required. Install with: pip install boto3")
        return 1

    try:
        # Load configuration if available
        config_path = Path(args.config)

        if config_path.exists():
            config = DeployConfig(str(config_path))
            lambda_config = config.get_lambda_config()

            if not lambda_config:
                logger.error("Lambda deployment is not enabled in configuration")
                return 1

            region = args.region or lambda_config.get("region", "us-east-1")
            function_name = args.function or lambda_config.get("function", {}).get(
                "name"
            )
        else:
            if not args.function:
                logger.error("Function name required (--function or deploy.yaml)")
                return 1

            region = args.region or "us-east-1"
            function_name = args.function

        if not function_name:
            logger.error("Function name is required")
            return 1

        # Create CloudWatch Logs client
        logs_client = boto3.client("logs", region_name=region)
        log_group_name = f"/aws/lambda/{function_name}"

        # Calculate start time
        if args.since:
            # Simple time parsing (e.g., '5m', '1h', '2d')
            since = args.since
            if since.endswith("m"):
                minutes = int(since[:-1])
                start_time = int(
                    (datetime.now() - timedelta(minutes=minutes)).timestamp() * 1000
                )
            elif since.endswith("h"):
                hours = int(since[:-1])
                start_time = int(
                    (datetime.now() - timedelta(hours=hours)).timestamp() * 1000
                )
            elif since.endswith("d"):
                days = int(since[:-1])
                start_time = int(
                    (datetime.now() - timedelta(days=days)).timestamp() * 1000
                )
            else:
                start_time = int(
                    (datetime.now() - timedelta(minutes=10)).timestamp() * 1000
                )
        else:
            # Default: last 10 minutes
            start_time = int(
                (datetime.now() - timedelta(minutes=10)).timestamp() * 1000
            )

        print(f"\n📋 Lambda Logs: {function_name}")
        print(f"   Region: {region}")
        print(f"   Log Group: {log_group_name}\n")

        if args.follow:
            # Stream logs in real-time
            print("Streaming logs (Ctrl+C to stop)...\n")
            last_timestamp = start_time

            try:
                while True:
                    response = logs_client.filter_log_events(
                        logGroupName=log_group_name,
                        startTime=last_timestamp,
                        limit=100,
                    )

                    for event in response.get("events", []):
                        timestamp = datetime.fromtimestamp(event["timestamp"] / 1000)
                        print(
                            f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {event['message']}"
                        )
                        last_timestamp = max(last_timestamp, event["timestamp"] + 1)

                    time_module.sleep(2)

            except KeyboardInterrupt:
                print("\n\nStopped streaming logs.")
                return 0
        else:
            # Get logs once
            response = logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time,
                limit=args.tail if args.tail else 100,
            )

            events = response.get("events", [])

            if args.tail and len(events) > args.tail:
                events = events[-args.tail :]

            for event in events:
                timestamp = datetime.fromtimestamp(event["timestamp"] / 1000)
                print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {event['message']}")

            if not events:
                print("No log events found.")

        return 0

    except logs_client.exceptions.ResourceNotFoundException:
        logger.error(f"Log group not found: {log_group_name}")
        print("The Lambda function may not have been invoked yet.")
        return 1
    except Exception as e:
        logger.error(f"Failed to get logs: {e}", exc_info=True)
        return 1


def handle_logs_k8s(args: argparse.Namespace) -> int:
    """Handle Kubernetes logs viewing."""
    print("⚠️  'logs k8s' command not yet implemented")
    print("This will stream logs from Kubernetes pods.")
    return 1


def handle_destroy(args: argparse.Namespace) -> int:
    """Handle destroy command."""
    if not args.platform:
        logger.error("Error: Please specify a platform (lambda or k8s)")
        print("Usage: jvdeploy destroy {lambda|k8s} [options]")
        return 1

    if args.platform == "lambda":
        return handle_destroy_lambda(args)
    elif args.platform == "k8s":
        return handle_destroy_k8s(args)
    else:
        logger.error(f"Unknown platform: {args.platform}")
        return 1


def handle_destroy_lambda(args: argparse.Namespace) -> int:
    """Handle Lambda deployment destruction."""
    try:
        # Load configuration if available
        config_path = Path(args.config)

        if config_path.exists():
            config = DeployConfig(str(config_path))
            lambda_config = config.get_lambda_config()

            if not lambda_config:
                logger.error("Lambda deployment is not enabled in configuration")
                return 1

            if args.function:
                lambda_config["function"]["name"] = args.function
        else:
            if not args.function:
                logger.error("Function name required (--function or deploy.yaml)")
                return 1

            lambda_config = {
                "region": "us-east-1",
                "function": {"name": args.function},
                "api_gateway": {"name": f"{args.function}-api"},
                "iam": {"role_name": f"{args.function}-lambda-role"},
            }

        function_name = lambda_config.get("function", {}).get("name")

        # Confirm destruction
        if not args.yes:
            print(f"\n⚠️  WARNING: This will delete the following resources:")
            print(f"   - Lambda function: {function_name}")
            if args.delete_api:
                print(f"   - API Gateway")
            if args.delete_role:
                print(f"   - IAM role")

            response = input("\nAre you sure you want to continue? (yes/no): ")
            if response.lower() != "yes":
                print("Destruction cancelled.")
                return 0

        # Import and create deployer
        try:
            from jvdeploy.aws import LambdaDeployer
        except ImportError:
            logger.error("boto3 is required. Install with: pip install boto3")
            return 1

        deployer = LambdaDeployer(lambda_config)

        print(f"\n🗑️  Destroying Lambda deployment...")
        results = deployer.destroy(
            function_name=function_name,
            delete_api=args.delete_api,
            delete_role=args.delete_role,
        )

        print("\nDeleted resources:")
        for resource in results["deleted"]:
            print(f"  ✓ {resource}")

        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  ✗ {error}")
            return 1

        print("\n✓ Destruction completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Destruction failed: {e}", exc_info=True)
        return 1


def handle_destroy_k8s(args: argparse.Namespace) -> int:
    """Handle Kubernetes deployment destruction."""
    print("⚠️  'destroy k8s' command not yet implemented")
    print("This will destroy the Kubernetes deployment.")

    if not args.yes:
        print("Note: This command requires --yes flag for confirmation.")

    return 1


def main() -> None:
    """Main entry point for jvdeploy CLI."""
    try:
        parser = setup_argparse()
        args = parser.parse_args()

        # Handle debug flag
        if args.debug:
            logger.setLevel(logging.DEBUG)
            logging.getLogger("jvdeploy").setLevel(logging.DEBUG)

        # Handle no command (legacy behavior - generate)
        if not args.command:
            # Legacy: jvdeploy [path] with no subcommand
            # Default to generate behavior
            if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
                args.command = "generate"
                args.app_root = sys.argv[1]
            else:
                parser.print_help()
                sys.exit(0)

        # Dispatch to command handlers
        if args.command == "generate":
            exit_code = handle_generate(args)
        elif args.command == "init":
            exit_code = handle_init(args)
        elif args.command == "deploy":
            exit_code = handle_deploy(args)
        elif args.command == "status":
            exit_code = handle_status(args)
        elif args.command == "logs":
            exit_code = handle_logs(args)
        elif args.command == "destroy":
            exit_code = handle_destroy(args)
        else:
            parser.print_help()
            exit_code = 0

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
