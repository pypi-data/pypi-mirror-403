"""
Cloud provider integration for DittoMation.

This package provides integration with cloud-based device testing platforms:
- Firebase Test Lab (Google Cloud)
- AWS Device Farm

Usage:
    from core.cloud import FirebaseTestLabProvider, AWSDeviceFarmProvider

    # Firebase Test Lab
    firebase = FirebaseTestLabProvider(project_id="my-project")
    devices = firebase.list_devices()

    # AWS Device Farm
    aws = AWSDeviceFarmProvider(project_arn="arn:aws:...")
    devices = aws.list_devices()
"""

from .base import CloudProvider
from .models import CloudDevice, TestArtifact, TestRun, TestRunStatus

__all__ = [
    "CloudProvider",
    "CloudDevice",
    "TestRun",
    "TestRunStatus",
    "TestArtifact",
]


# Lazy imports for providers (to avoid requiring boto3/gcloud at import time)
def get_firebase_provider():
    """Get Firebase Test Lab provider (requires gcloud CLI)."""
    from .firebase import FirebaseTestLabProvider

    return FirebaseTestLabProvider


def get_aws_provider():
    """Get AWS Device Farm provider (requires boto3)."""
    from .aws import AWSDeviceFarmProvider

    return AWSDeviceFarmProvider
