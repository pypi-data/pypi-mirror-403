"""
Unit tests for the validation engine (BlueprintValidator).

Tests all validation rules, error formatting, and edge cases for
the validator module.
"""

import pytest
from iacgen.validator import BlueprintValidator, ValidationError
from iacgen.config import BlueprintConfig, VPCConfig, EKSConfig, ALBConfig, ServiceConfig


class TestValidationError:
    """Tests for ValidationError dataclass."""
    
    def test_validation_error_creation(self):
        """Test ValidationError can be created with all fields."""
        error = ValidationError(
            code="TEST_CODE",
            message="Test message",
            suggestion="Test suggestion"
        )
        
        assert error.code == "TEST_CODE"
        assert error.message == "Test message"
        assert error.suggestion == "Test suggestion"
    
    def test_validation_error_str_formatting(self):
        """Test ValidationError __str__ formats correctly."""
        error = ValidationError(
            code="EKS_REQUIRES_VPC",
            message="EKS needs VPC",
            suggestion="Enable VPC module"
        )
        
        formatted = str(error)
        assert "[EKS_REQUIRES_VPC]" in formatted
        assert "EKS needs VPC" in formatted
        assert "Suggestion: Enable VPC module" in formatted


class TestBlueprintValidator:
    """Tests for BlueprintValidator class."""
    
    def test_validator_init(self):
        """Test validator initialization with config."""
        config = BlueprintConfig(name="test")
        validator = BlueprintValidator(config)
        
        assert validator.config == config
        assert validator.errors == []
        assert isinstance(validator.errors, list)
    
    def test_get_errors(self):
        """Test get_errors returns error list."""
        config = BlueprintConfig(name="test")
        validator = BlueprintValidator(config)
        
        errors = validator.get_errors()
        assert errors == []
        assert isinstance(errors, list)


class TestEKSRequiresVPCRule:
    """Tests for EKS_REQUIRES_VPC validation rule."""
    
    def test_eks_without_vpc_fails(self):
        """Test EKS enabled without VPC fails validation."""
        config = BlueprintConfig(
            name="test-infra",
            eks=EKSConfig(enabled=True),
            vpc=VPCConfig(enabled=False)
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.errors) == 1
        assert validator.errors[0].code == "EKS_REQUIRES_VPC"
        assert "EKS module is enabled but VPC module is not enabled" in validator.errors[0].message
    
    def test_eks_with_vpc_passes(self):
        """Test EKS enabled with VPC passes validation."""
        config = BlueprintConfig(
            name="test-infra",
            eks=EKSConfig(enabled=True),
            vpc=VPCConfig(enabled=True)
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
        assert len(validator.errors) == 0
    
    def test_no_eks_no_vpc_passes(self):
        """Test neither EKS nor VPC enabled doesn't trigger EKS_REQUIRES_VPC."""
        config = BlueprintConfig(
            name="test-infra",
            eks=EKSConfig(enabled=False),
            vpc=VPCConfig(enabled=False)
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        # Will fail with NO_MODULES_ENABLED, not EKS_REQUIRES_VPC
        error_codes = [e.code for e in validator.errors]
        assert "EKS_REQUIRES_VPC" not in error_codes


class TestServicesRequireEKSRule:
    """Tests for SERVICES_REQUIRE_EKS validation rule."""
    
    def test_services_without_eks_fails(self):
        """Test services defined without EKS fails validation."""
        config = BlueprintConfig(
            name="test-infra",
            eks=EKSConfig(enabled=False),
            services=[
                ServiceConfig(name="api"),
                ServiceConfig(name="worker")
            ]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.errors) == 1
        assert validator.errors[0].code == "SERVICES_REQUIRE_EKS"
        assert "api, worker" in validator.errors[0].message
    
    def test_services_with_eks_and_vpc_passes(self):
        """Test services with EKS and VPC passes validation."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=True),
            eks=EKSConfig(enabled=True),
            services=[ServiceConfig(name="api")]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
        assert len(validator.errors) == 0
    
    def test_no_services_with_eks_passes(self):
        """Test no services defined doesn't trigger SERVICES_REQUIRE_EKS."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=True),
            eks=EKSConfig(enabled=True),
            services=[]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
        error_codes = [e.code for e in validator.errors]
        assert "SERVICES_REQUIRE_EKS" not in error_codes


class TestALBRequiresServicesRule:
    """Tests for ALB_REQUIRES_SERVICES validation rule."""
    
    def test_alb_without_services_fails(self):
        """Test ALB enabled without services fails validation."""
        config = BlueprintConfig(
            name="test-infra",
            alb=ALBConfig(enabled=True),
            services=[]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.errors) == 1
        assert validator.errors[0].code == "ALB_REQUIRES_SERVICES"
        assert "ALB module is enabled but no services are defined" in validator.errors[0].message
    
    def test_alb_with_services_and_eks_and_vpc_passes(self):
        """Test ALB with services (and EKS+VPC) passes validation."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=True),
            eks=EKSConfig(enabled=True),
            alb=ALBConfig(enabled=True),
            services=[ServiceConfig(name="api")]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
        assert len(validator.errors) == 0
    
    def test_no_alb_no_services_passes(self):
        """Test no ALB doesn't trigger ALB_REQUIRES_SERVICES."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=True),
            alb=ALBConfig(enabled=False),
            services=[]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
        error_codes = [e.code for e in validator.errors]
        assert "ALB_REQUIRES_SERVICES" not in error_codes


class TestNoModulesEnabledRule:
    """Tests for NO_MODULES_ENABLED validation rule."""
    
    def test_no_modules_enabled_fails(self):
        """Test no modules enabled fails validation."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=False),
            eks=EKSConfig(enabled=False),
            alb=ALBConfig(enabled=False),
            services=[]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.errors) == 1
        assert validator.errors[0].code == "NO_MODULES_ENABLED"
        assert "No modules or services are enabled" in validator.errors[0].message
    
    def test_vpc_only_passes(self):
        """Test only VPC enabled passes validation."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=True)
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
        assert len(validator.errors) == 0
    
    def test_services_only_fails_with_services_require_eks(self):
        """Test only services defined fails with SERVICES_REQUIRE_EKS."""
        config = BlueprintConfig(
            name="test-infra",
            services=[ServiceConfig(name="api")]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        # Should fail with SERVICES_REQUIRE_EKS, not NO_MODULES_ENABLED
        assert result is False
        assert len(validator.errors) == 1
        assert validator.errors[0].code == "SERVICES_REQUIRE_EKS"


class TestMultipleErrors:
    """Tests for configurations with multiple validation errors."""
    
    def test_eks_without_vpc_and_alb_without_services(self):
        """Test multiple violations are all reported."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=False),
            eks=EKSConfig(enabled=True),
            alb=ALBConfig(enabled=True),
            services=[]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is False
        assert len(validator.errors) == 2
        
        error_codes = [e.code for e in validator.errors]
        assert "EKS_REQUIRES_VPC" in error_codes
        assert "ALB_REQUIRES_SERVICES" in error_codes
    
    def test_services_without_eks_and_alb_enabled(self):
        """Test services without EKS is caught."""
        config = BlueprintConfig(
            name="test-infra",
            alb=ALBConfig(enabled=True),
            services=[ServiceConfig(name="api")]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is False
        # Only SERVICES_REQUIRE_EKS should trigger (ALB has services)
        assert len(validator.errors) == 1
        assert validator.errors[0].code == "SERVICES_REQUIRE_EKS"


class TestValidConfigurations:
    """Tests for valid configurations that should pass."""
    
    def test_valid_full_stack(self):
        """Test valid full stack configuration passes."""
        config = BlueprintConfig(
            name="production-infra",
            region="us-east-1",
            vpc=VPCConfig(enabled=True, cidr_block="10.0.0.0/16"),
            eks=EKSConfig(enabled=True, cluster_version="1.29"),
            alb=ALBConfig(enabled=True),
            services=[
                ServiceConfig(name="api", replicas=3),
                ServiceConfig(name="worker", replicas=2)
            ]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
        assert len(validator.errors) == 0
    
    def test_valid_vpc_eks_only(self):
        """Test valid VPC+EKS configuration passes."""
        config = BlueprintConfig(
            name="cluster-only",
            vpc=VPCConfig(enabled=True),
            eks=EKSConfig(enabled=True)
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
        assert len(validator.errors) == 0
    
    def test_valid_vpc_only(self):
        """Test valid VPC-only configuration passes."""
        config = BlueprintConfig(
            name="network-only",
            vpc=VPCConfig(enabled=True)
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
        assert len(validator.errors) == 0


class TestValidateMethodBehavior:
    """Tests for validate() method behavior."""
    
    def test_validate_clears_previous_errors(self):
        """Test validate() clears errors from previous runs."""
        config = BlueprintConfig(
            name="test-infra",
            eks=EKSConfig(enabled=True),
            vpc=VPCConfig(enabled=False)
        )
        
        validator = BlueprintValidator(config)
        
        # First validation
        result1 = validator.validate()
        assert result1 is False
        assert len(validator.errors) == 1
        
        # Fix config
        validator.config.vpc.enabled = True
        
        # Second validation should clear previous errors
        result2 = validator.validate()
        assert result2 is True
        assert len(validator.errors) == 0


class TestFormatErrors:
    """Tests for format_errors() method."""
    
    def test_format_errors_with_no_errors(self):
        """Test format_errors with no validation errors."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=True)
        )
        
        validator = BlueprintValidator(config)
        validator.validate()
        
        formatted = validator.format_errors()
        assert formatted == "No validation errors"
    
    def test_format_errors_with_single_error(self):
        """Test format_errors with one validation error."""
        config = BlueprintConfig(
            name="test-infra",
            eks=EKSConfig(enabled=True),
            vpc=VPCConfig(enabled=False)
        )
        
        validator = BlueprintValidator(config)
        validator.validate()
        
        formatted = validator.format_errors()
        assert "Found 1 validation error" in formatted
        assert "EKS_REQUIRES_VPC" in formatted
        assert "Suggestion:" in formatted
    
    def test_format_errors_with_multiple_errors(self):
        """Test format_errors with multiple validation errors."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=False),
            eks=EKSConfig(enabled=True),
            alb=ALBConfig(enabled=True),
            services=[]
        )
        
        validator = BlueprintValidator(config)
        validator.validate()
        
        formatted = validator.format_errors()
        assert "Found 2 validation error(s)" in formatted
        assert "1." in formatted
        assert "2." in formatted
        assert "EKS_REQUIRES_VPC" in formatted
        assert "ALB_REQUIRES_SERVICES" in formatted
    
    def test_format_errors_structure(self):
        """Test format_errors has correct structure."""
        config = BlueprintConfig(
            name="test-infra",
            eks=EKSConfig(enabled=True)
        )
        
        validator = BlueprintValidator(config)
        validator.validate()
        
        formatted = validator.format_errors()
        
        # Should have numbered errors
        assert "1. [" in formatted
        # Should have suggestion for each error
        assert "Suggestion:" in formatted


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_empty_services_list(self):
        """Test empty services list is handled correctly."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=True),
            services=[]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        # Should pass - empty services doesn't trigger SERVICES_REQUIRE_EKS
        assert result is True
    
    def test_single_service(self):
        """Test single service with proper deps passes."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=True),
            eks=EKSConfig(enabled=True),
            services=[ServiceConfig(name="api")]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
    
    def test_multiple_services(self):
        """Test multiple services with proper deps passes."""
        config = BlueprintConfig(
            name="test-infra",
            vpc=VPCConfig(enabled=True),
            eks=EKSConfig(enabled=True),
            services=[
                ServiceConfig(name="api"),
                ServiceConfig(name="worker"),
                ServiceConfig(name="scheduler")
            ]
        )
        
        validator = BlueprintValidator(config)
        result = validator.validate()
        
        assert result is True
