"""AWS deployment modules for jvdeploy.

Provides functionality for deploying jvagent applications to AWS Lambda,
including ECR, IAM, Lambda, and API Gateway management.
"""

from jvdeploy.aws.lambda_deployer import LambdaDeployer

__all__ = ["LambdaDeployer"]
