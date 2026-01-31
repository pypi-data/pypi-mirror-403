"""
IaC Blueprint Generator (iacgen)

A CLI tool that automatically generates Terraform infrastructure blueprints
based on user input. Provides consistent, opinionated, best-practice project
scaffolding for AWS-based architectures (VPC, EKS, microservices, ALB, etc.).

Accelerates infrastructure provisioning, reduces copy/paste drift, and enforces
golden-path patterns for DevOps/Platform Engineers and SREs.

Example usage:
    $ iacgen create --vpc --eks --services api,worker --output ./infra
    $ iacgen create --preset microservice --output ./infra
    $ iacgen recreate blueprint.json

"""

__version__ = "1.1.0"

# Public API exports
from iacgen.config import (
    BlueprintConfig,
    VPCConfig,
    EKSConfig,
    ALBConfig,
    ServiceConfig,
    ModuleType,
)
from iacgen.validator import (
    BlueprintValidator,
    ValidationError,
)

__all__ = [
    "__version__",
    "BlueprintConfig",
    "VPCConfig",
    "EKSConfig",
    "ALBConfig",
    "ServiceConfig",
    "ModuleType",
    "BlueprintValidator",
    "ValidationError",
]
