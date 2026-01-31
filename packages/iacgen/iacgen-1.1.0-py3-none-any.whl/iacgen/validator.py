"""
Validation engine for iacgen blueprint configurations.

Enforces architectural constraints and dependency rules to ensure
valid infrastructure configurations.

Dependency Rules:
- EKS requires VPC
- ALB requires at least one service
- Services require EKS
"""

from dataclasses import dataclass
from typing import List

from iacgen.config import BlueprintConfig


@dataclass
class ValidationError:
    """Represents a validation error with code, message, and suggestion."""
    
    code: str
    message: str
    suggestion: str
    
    def __str__(self) -> str:
        """Return formatted error message."""
        return f"[{self.code}] {self.message}\n  Suggestion: {self.suggestion}"


class BlueprintValidator:
    """Validates BlueprintConfig against architectural rules and constraints."""
    
    def __init__(self, config: BlueprintConfig) -> None:
        """Initialize validator with a blueprint configuration.
        
        Args:
            config: The BlueprintConfig to validate
        """
        self.config = config
        self.errors: List[ValidationError] = []
    
    def validate(self) -> bool:
        """Run all validation rules against the configuration.
        
        Returns:
            True if validation passes, False if there are errors
        """
        # Clear previous errors
        self.errors = []
        
        # Rule 1: EKS requires VPC
        if self.config.eks.enabled and not self.config.vpc.enabled:
            self.errors.append(ValidationError(
                code="EKS_REQUIRES_VPC",
                message="EKS module is enabled but VPC module is not enabled",
                suggestion="Enable VPC module with --vpc flag or disable EKS with --no-eks"
            ))

        # Rule 1b: When using an existing VPC for EKS, VPC ID and private subnets are required
        eks_cfg = self.config.eks
        if eks_cfg.enabled and getattr(eks_cfg, "use_existing_vpc", False):
            missing_existing_vpc_id = not getattr(eks_cfg, "existing_vpc_id", None)
            missing_existing_subnets = not getattr(eks_cfg, "existing_private_subnet_ids", None)

            if missing_existing_vpc_id or missing_existing_subnets:
                parts = []
                if missing_existing_vpc_id:
                    parts.append("existing_vpc_id")
                if missing_existing_subnets:
                    parts.append("existing_private_subnet_ids")
                missing_str = ", ".join(parts)

                self.errors.append(
                    ValidationError(
                        code="EKS_EXISTING_VPC_DETAILS_REQUIRED",
                        message=(
                            "EKS is configured to use an existing VPC, but the following "
                            f"required fields are missing: {missing_str}"
                        ),
                        suggestion=(
                            "Provide both --eks-vpc-id and --eks-private-subnet-ids when "
                            "using --eks-use-existing-vpc, or disable use_existing_vpc."
                        ),
                    )
                )
        
        # Rule 2: Services require EKS
        if len(self.config.services) > 0 and not self.config.eks.enabled:
            service_names = ", ".join([svc.name for svc in self.config.services])
            self.errors.append(ValidationError(
                code="SERVICES_REQUIRE_EKS",
                message=f"Services defined ({service_names}) but EKS module is not enabled",
                suggestion="Enable EKS module with --eks flag or remove services"
            ))
        
        # Rule 3: ALB requires at least one service
        if self.config.alb.enabled and len(self.config.services) == 0:
            self.errors.append(ValidationError(
                code="ALB_REQUIRES_SERVICES",
                message="ALB module is enabled but no services are defined",
                suggestion="Add at least one service with --services flag or disable ALB with --alb=false",
            ))

        # Rule 3b: When using an existing VPC for ALB, VPC ID and subnets are required
        alb_cfg = self.config.alb
        if alb_cfg.enabled and getattr(alb_cfg, "use_existing_vpc", False):
            missing_vpc_id = not getattr(alb_cfg, "existing_vpc_id", None)
            missing_subnets = not getattr(alb_cfg, "existing_subnet_ids", None)

            if missing_vpc_id or missing_subnets:
                parts: list[str] = []
                if missing_vpc_id:
                    parts.append("existing_vpc_id")
                if missing_subnets:
                    parts.append("existing_subnet_ids")
                missing_str = ", ".join(parts)

                self.errors.append(
                    ValidationError(
                        code="ALB_EXISTING_VPC_DETAILS_REQUIRED",
                        message=(
                            "ALB is configured to use an existing VPC, but the following "
                            f"required fields are missing: {missing_str}"
                        ),
                        suggestion=(
                            "Provide both --alb-vpc-id and --alb-subnet-ids when "
                            "using --alb-use-existing-vpc, or disable use_existing_vpc."
                        ),
                    )
                )

        # Rule 4: At least one module must be enabled
        no_modules = (
            not self.config.vpc.enabled and
            not self.config.eks.enabled and
            not self.config.alb.enabled and
            len(self.config.services) == 0
        )
        if no_modules:
            self.errors.append(ValidationError(
                code="NO_MODULES_ENABLED",
                message="No modules or services are enabled",
                suggestion="Enable at least one module (--vpc, --eks, --alb) or define services (--services)"
            ))
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[ValidationError]:
        """Get the list of validation errors.
        
        Returns:
            List of ValidationError objects
        """
        return self.errors
    
    def format_errors(self) -> str:
        """Format all validation errors as a readable string.
        
        Returns:
            Formatted string containing all errors with suggestions
        """
        if not self.errors:
            return "No validation errors"
        
        formatted = f"Found {len(self.errors)} validation error(s):\n\n"
        for i, error in enumerate(self.errors, 1):
            formatted += f"{i}. {error}\n\n"
        
        return formatted.strip()
