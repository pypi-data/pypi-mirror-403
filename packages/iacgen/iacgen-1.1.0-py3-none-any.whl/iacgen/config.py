"""
Configuration models for iacgen using Pydantic.

Defines the data structures for blueprint configuration, services, and modules.
"""

import json
import re
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ValidationError

from iacgen.exceptions import ConfigError


class ModuleType(str, Enum):
    """Supported Terraform module types."""

    VPC = "vpc"
    EKS = "eks"
    ALB = "alb"
    SERVICE = "service"


class ServiceConfig(BaseModel):
    """Configuration for a single service."""

    name: str = Field(..., description="Service name")
    replicas: int = Field(default=2, description="Number of replicas")
    port: int = Field(default=8080, description="Service port")
    cpu: str = Field(default="256m", description="CPU request (Kubernetes format)")
    memory: str = Field(default="512Mi", description="Memory request (Kubernetes format)")

    @field_validator("replicas")
    @classmethod
    def validate_replicas(cls, number_of_replicas: int) -> int:
        """Ensure replicas is at least 1."""
        if number_of_replicas < 1:
            raise ValueError("replicas must be at least 1")
        return number_of_replicas

    @field_validator("port")
    @classmethod
    def validate_port(cls, port_number: int) -> int:
        """Ensure port is in valid range (1-65535)."""
        if not 1 <= port_number <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return port_number

    @field_validator("cpu")
    @classmethod
    def validate_cpu(cls, cpu_value: str) -> str:
        """Validate CPU follows Kubernetes resource format (e.g., '250m', '0.5', '1')."""
        # Match patterns like: 100m, 0.5, 1, 2
        if not re.match(r"^\d+(\.\d+)?[m]?$", cpu_value):
            raise ValueError(
                "cpu must follow Kubernetes format (e.g., '250m' for millicores or '1' for cores)"
            )
        return cpu_value

    @field_validator("memory")
    @classmethod
    def validate_memory(cls, memory_value: str) -> str:
        """Validate memory follows Kubernetes resource format (e.g., '512Mi', '1Gi')."""
        # Match patterns like: 512Mi, 1Gi, 256M, 2G
        if not re.match(r"^\d+(\.\d+)?(Mi|Gi|M|G|Ki|K)?$", memory_value):
            raise ValueError(
                "memory must follow Kubernetes format (e.g., '512Mi', '1Gi', '256M')"
            )
        return memory_value


class VPCConfig(BaseModel):
    """Configuration for VPC module."""

    enabled: bool = Field(default=False, description="Enable VPC module")
    cidr_block: str = Field(default="10.0.0.0/16", description="VPC CIDR block")
    availability_zones: int = Field(default=3, description="Number of availability zones")
    enable_nat_gateway: bool = Field(default=True, description="Enable NAT gateway")
    single_nat_gateway: bool = Field(default=True, description="Use single NAT gateway for all AZs")

    @field_validator("cidr_block")
    @classmethod
    def validate_cidr(cls, cidr: str) -> str:
        """Validate CIDR block format (e.g., '10.0.0.0/16')."""
        # Basic CIDR validation: IP address followed by /prefix
        cidr_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$"
        if not re.match(cidr_pattern, cidr):
            raise ValueError("cidr_block must be in format X.X.X.X/Y (e.g., '10.0.0.0/16')")
        
        # Validate IP octets and prefix
        ip_part, prefix_part = cidr.split("/")
        octets = ip_part.split(".")
        
        for octet in octets:
            if not 0 <= int(octet) <= 255:
                raise ValueError(f"Invalid IP octet: {octet} (must be 0-255)")
        
        prefix = int(prefix_part)
        if not 0 <= prefix <= 32:
            raise ValueError(f"Invalid CIDR prefix: {prefix} (must be 0-32)")
        
        return cidr

    @field_validator("availability_zones")
    @classmethod
    def validate_azs(cls, num_azs: int) -> int:
        """Ensure at least 1 availability zone."""
        if num_azs < 1:
            raise ValueError("availability_zones must be at least 1")
        return num_azs


class EKSConfig(BaseModel):
    """Configuration for EKS module.

    By default, EKS clusters are created in the VPC managed by this blueprint
    (when ``vpc.enabled`` is True). For cases where an existing VPC should be
    reused instead of creating a new one, set ``use_existing_vpc=True`` and
    provide ``existing_vpc_id`` and ``existing_private_subnet_ids``.
    """

    enabled: bool = Field(default=False, description="Enable EKS module")

    # Cluster & node configuration
    cluster_version: str = Field(default="1.28", description="Kubernetes version")
    node_instance_type: str = Field(default="t3.medium", description="EC2 instance type for nodes")
    node_desired_size: int = Field(default=2, description="Desired number of nodes")
    node_min_size: int = Field(default=1, description="Minimum number of nodes")
    node_max_size: int = Field(default=4, description="Maximum number of nodes")

    # Optional support for reusing an existing VPC instead of the generated one
    use_existing_vpc: bool = Field(
        default=False,
        description=(
            "Use an existing VPC instead of the generated VPC. When true, "
            "existing_vpc_id and existing_private_subnet_ids must be provided."
        ),
    )
    existing_vpc_id: Optional[str] = Field(
        default=None,
        description="ID of an existing VPC to use for the EKS cluster",
    )
    existing_private_subnet_ids: Optional[list[str]] = Field(
        default=None,
        description="Private subnet IDs in the existing VPC for the EKS cluster",
    )

    @field_validator("node_min_size")
    @classmethod
    def validate_min_size(cls, min_size: int) -> int:
        """Ensure min_size is at least 1."""
        if min_size < 1:
            raise ValueError("node_min_size must be at least 1")
        return min_size

    @field_validator("node_max_size")
    @classmethod
    def validate_max_size(cls, max_size: int, info) -> int:
        """Ensure max_size is greater than or equal to min_size."""
        min_size = info.data.get("node_min_size", 1)
        if max_size < min_size:
            raise ValueError(f"node_max_size ({max_size}) must be >= node_min_size ({min_size})")
        return max_size

    @field_validator("node_desired_size")
    @classmethod
    def validate_desired_size(cls, desired_size: int, info) -> int:
        """Ensure desired_size is between min_size and max_size."""
        min_size = info.data.get("node_min_size", 1)
        max_size = info.data.get("node_max_size", 4)
        
        if desired_size < min_size:
            raise ValueError(f"node_desired_size ({desired_size}) must be >= node_min_size ({min_size})")
        if desired_size > max_size:
            raise ValueError(f"node_desired_size ({desired_size}) must be <= node_max_size ({max_size})")
        
        return desired_size


class ALBConfig(BaseModel):
    """Configuration for Application Load Balancer module.

    By default, ALBs are created in the VPC managed by this blueprint when
    ``vpc.enabled`` is True. To reuse an existing VPC instead, set
    ``use_existing_vpc=True`` and provide ``existing_vpc_id`` and
    ``existing_subnet_ids``.
    """

    enabled: bool = Field(default=False, description="Enable ALB module")
    internal: bool = Field(default=False, description="Create internal load balancer")
    enable_https: bool = Field(default=True, description="Enable HTTPS listener")

    # Optional support for reusing an existing VPC instead of the generated one
    use_existing_vpc: bool = Field(
        default=False,
        description=(
            "Use an existing VPC instead of the generated VPC. When true, "
            "existing_vpc_id and existing_subnet_ids must be provided."
        ),
    )
    existing_vpc_id: Optional[str] = Field(
        default=None,
        description="ID of an existing VPC to use for the ALB",
    )
    existing_subnet_ids: Optional[list[str]] = Field(
        default=None,
        description="Subnet IDs in the existing VPC where the ALB will be placed",
    )


class BlueprintConfig(BaseModel):
    """Main configuration container for infrastructure blueprint."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Project/infrastructure name"
    )
    region: str = Field(
        default="us-west-2",
        description="AWS region for infrastructure deployment"
    )
    environment: str = Field(
        default="dev",
        description="Logical environment name (e.g., dev, staging, prod)"
    )
    vpc: VPCConfig = Field(
        default_factory=VPCConfig,
        description="VPC module configuration"
    )
    eks: EKSConfig = Field(
        default_factory=EKSConfig,
        description="EKS cluster configuration"
    )
    alb: ALBConfig = Field(
        default_factory=ALBConfig,
        description="Application Load Balancer configuration"
    )
    services: List[ServiceConfig] = Field(
        default_factory=list,
        description="List of service configurations"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "my-infrastructure",
                    "region": "us-west-2",
                    "environment": "dev",
                    "vpc": {"enabled": True},
                    "eks": {"enabled": True},
                    "services": [
                        {"name": "api", "replicas": 3, "port": 8080}
                    ]
                }
            ]
        }
    }

    def to_json(self, path: Path) -> None:
        """Write configuration to a JSON file.
        
        Args:
            path: Path to output JSON file
            
        Raises:
            ConfigError: If file cannot be written or permission denied
        """
        try:
            json_content = self.model_dump_json(indent=2)
            path.write_text(json_content)
        except PermissionError as e:
            raise ConfigError(
                f"Permission denied writing to {path.absolute()}",
                suggestions=["Check file permissions", "Try a different directory"]
            ) from e
        except OSError as e:
            raise ConfigError(
                f"Failed to write configuration to {path.absolute()}: {str(e)}",
                suggestions=["Check disk space", "Verify path is valid"]
            ) from e
        except Exception as e:
            raise ConfigError(
                f"Unexpected error writing configuration: {str(e)}"
            ) from e

    @classmethod
    def from_cli_args(cls, **kwargs) -> "BlueprintConfig":
        """Build BlueprintConfig from CLI arguments.
        
        Args:
            **kwargs: CLI arguments including:
                - name: str (default: 'infrastructure')
                - region: str (default: 'us-east-1')
                - vpc: bool (if True, enables VPC module)
                - eks: bool (if True, enables EKS module)
                - alb: bool (if True, enables ALB module)
                - services: List[str] (list of service names)
                
        Returns:
            Validated BlueprintConfig instance
        """
        # Extract and set defaults
        name = kwargs.get("name", "infrastructure")
        region = kwargs.get("region", "us-west-2")
        environment = kwargs.get("environment", "dev")
        
        # Build VPC config
        vpc_enabled = kwargs.get("vpc", False)
        vpc = VPCConfig(enabled=vpc_enabled)
        
        # Build EKS config
        eks_enabled = kwargs.get("eks", False)
        use_existing_vpc = kwargs.get("eks_use_existing_vpc", False)
        existing_vpc_id = kwargs.get("eks_vpc_id")
        existing_private_subnet_ids = kwargs.get("eks_private_subnet_ids") or []
        eks = EKSConfig(
            enabled=eks_enabled,
            use_existing_vpc=use_existing_vpc,
            existing_vpc_id=existing_vpc_id,
            existing_private_subnet_ids=existing_private_subnet_ids or None,
        )
        
        # Build ALB config
        alb_enabled = kwargs.get("alb", False)
        alb_use_existing_vpc = kwargs.get("alb_use_existing_vpc", False)
        alb_vpc_id = kwargs.get("alb_vpc_id")
        alb_subnet_ids = kwargs.get("alb_subnet_ids") or []
        alb = ALBConfig(
            enabled=alb_enabled,
            use_existing_vpc=alb_use_existing_vpc,
            existing_vpc_id=alb_vpc_id,
            existing_subnet_ids=alb_subnet_ids or None,
        )
        
        # Build services list
        service_names = kwargs.get("services", [])
        services = [ServiceConfig(name=svc_name) for svc_name in service_names]
        
        # Create and return config
        return cls(
            name=name,
            region=region,
            environment=environment,
            vpc=vpc,
            eks=eks,
            alb=alb,
            services=services
        )

    @classmethod
    def from_json(cls, path: Path) -> "BlueprintConfig":
        """Load configuration from a JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Validated BlueprintConfig instance
            
        Raises:
            ConfigError: If file not found, invalid JSON, or validation fails
        """
        # Check if file exists
        if not path.exists():
            raise ConfigError(
                f"Configuration file not found: {path.absolute()}",
                suggestions=[
                    "Check the file path is correct",
                    "Ensure the file was created with 'to_json()'"
                ]
            )
        
        # Read file content
        try:
            json_content = path.read_text()
        except PermissionError as e:
            raise ConfigError(
                f"Permission denied reading {path.absolute()}",
                suggestions=["Check file permissions"]
            ) from e
        except OSError as e:
            raise ConfigError(
                f"Failed to read configuration from {path.absolute()}: {str(e)}"
            ) from e
        
        # Parse and validate JSON
        try:
            return cls.model_validate_json(json_content)
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"Invalid JSON in configuration file: {path.absolute()}\n"
                f"Error: {e.msg} at line {e.lineno}, column {e.colno}",
                suggestions=[
                    "Validate JSON syntax",
                    "Check for trailing commas or missing quotes",
                    "Use a JSON validator tool"
                ]
            ) from e
        except ValidationError as e:
            # Build detailed error message from Pydantic validation errors
            error_details = []
            for error in e.errors():
                loc = " -> ".join(str(l) for l in error["loc"])
                msg = error["msg"]
                error_details.append(f"{loc}: {msg}")
            
            raise ConfigError(
                f"Configuration validation failed for {path.absolute()}:\n" +
                "\n".join(f"  - {detail}" for detail in error_details),
                suggestions=[
                    "Check field names and types match BlueprintConfig schema",
                    "Ensure required fields are present",
                    "Verify field values meet validation constraints"
                ]
            ) from e
        except Exception as e:
            raise ConfigError(
                f"Unexpected error loading configuration: {str(e)}"
            ) from e

