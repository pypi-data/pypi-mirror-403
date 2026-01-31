"""Tests for ALB Terraform module templates rendered by BlueprintRenderer.

Covers:
- Basic rendering of ALB templates
- HTTPS vs HTTP-only configurations
- Internal vs internet-facing ALBs
- Per-service target groups and health checks
- Listener rule priority generation (loop.index * 10)
- Security group rules for ports 80/443
"""

from __future__ import annotations

from pathlib import Path

import pytest

from iacgen.config import BlueprintConfig, VPCConfig, ALBConfig, ServiceConfig
from iacgen.renderer import BlueprintRenderer


def _render_to_tmp(tmp_path: Path, config: BlueprintConfig) -> Path:
    """Helper to render a config into a temp directory and return it."""

    renderer = BlueprintRenderer(config)
    renderer.render(tmp_path)
    return tmp_path


class TestALBTemplatesBasic:
    """Basic rendering scenarios for the ALB module."""

    def test_render_with_default_alb_config(self, tmp_path: Path) -> None:
        """Rendering with default ALBConfig + VPC should produce ALB files and core resources."""

        config = BlueprintConfig(
            name="test",
            vpc=VPCConfig(enabled=True),
            alb=ALBConfig(enabled=True),
        )

        out_dir = _render_to_tmp(tmp_path, config)

        alb_dir = out_dir / "modules" / "alb"
        assert (alb_dir / "main.tf").exists()
        assert (alb_dir / "variables.tf").exists()
        assert (alb_dir / "outputs.tf").exists()

        content = (alb_dir / "main.tf").read_text()
        assert "resource \"aws_lb\" \"main\"" in content
        assert "resource \"aws_security_group\" \"alb\"" in content
        assert "resource \"aws_lb_listener\" \"http\"" in content


class TestHTTPSConfiguration:
    """Verify enable_https flag controls HTTPS listener and redirect behavior."""

    @pytest.mark.parametrize("enable_https", [True, False])
    def test_https_listener_and_redirect(self, tmp_path: Path, enable_https: bool) -> None:
        config = BlueprintConfig(
            name="https-test",
            vpc=VPCConfig(enabled=True),
            alb=ALBConfig(enabled=True, enable_https=enable_https),
        )

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "alb" / "main.tf").read_text()

        if enable_https:
            # HTTPS listener should exist and HTTP listener should redirect
            assert "resource \"aws_lb_listener\" \"https\"" in main_tf
            assert "type = \"redirect\"" in main_tf
            assert "status_code = \"HTTP_301\"" in main_tf
        else:
            # No HTTPS listener and HTTP listener forwards to default target group
            assert "resource \"aws_lb_listener\" \"https\"" not in main_tf
            assert "type             = \"forward\"" in main_tf
            assert "target_group_arn = aws_lb_target_group.default.arn" in main_tf


class TestInternalALB:
    """Ensure internal flag maps to ALB internal attribute."""

    @pytest.mark.parametrize("internal", [True, False])
    def test_internal_flag(self, tmp_path: Path, internal: bool) -> None:
        config = BlueprintConfig(
            name="internal-test",
            vpc=VPCConfig(enabled=True),
            alb=ALBConfig(enabled=True, internal=internal),
        )

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "alb" / "main.tf").read_text()

        expected = "internal           = true" if internal else "internal           = false"
        assert expected in main_tf


class TestServiceTargetGroups:
    """Validate per-service target groups and health checks."""

    def test_target_groups_created_for_each_service(self, tmp_path: Path) -> None:
        services = [
            ServiceConfig(name="api"),
            ServiceConfig(name="worker"),
        ]
        config = BlueprintConfig(
            name="tg-test",
            vpc=VPCConfig(enabled=True),
            alb=ALBConfig(enabled=True),
            services=services,
        )

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "alb" / "main.tf").read_text()

        # One target group per service
        assert "resource \"aws_lb_target_group\" \"api\"" in main_tf
        assert "resource \"aws_lb_target_group\" \"worker\"" in main_tf

        # Health check configuration
        assert "health_check" in main_tf
        assert "path                = \"/health\"" in main_tf
        assert "matcher             = \"200-399\"" in main_tf


class TestListenerRulePriorities:
    """Ensure listener rule priorities follow loop.index * 10 pattern."""

    def test_listener_rule_priorities_based_on_services(self, tmp_path: Path) -> None:
        services = [
            ServiceConfig(name="api"),
            ServiceConfig(name="worker"),
            ServiceConfig(name="admin"),
        ]
        config = BlueprintConfig(
            name="priority-test",
            vpc=VPCConfig(enabled=True),
            alb=ALBConfig(enabled=True, enable_https=True),
            services=services,
        )

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "alb" / "main.tf").read_text()

        # loop.index * 10 → 10, 20, 30, ...
        assert "priority     = 10" in main_tf
        assert "priority     = 20" in main_tf
        assert "priority     = 30" in main_tf


class TestSecurityGroupRules:
    """Verify ALB security group ingress rules for HTTP/HTTPS."""

    @pytest.mark.parametrize("enable_https", [True, False])
    def test_security_group_ingress_ports(self, tmp_path: Path, enable_https: bool) -> None:
        config = BlueprintConfig(
            name="sg-test",
            vpc=VPCConfig(enabled=True),
            alb=ALBConfig(enabled=True, enable_https=enable_https),
        )

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "alb" / "main.tf").read_text()

        # Port 80 should always be present
        assert "from_port   = 80" in main_tf
        assert "to_port     = 80" in main_tf

        if enable_https:
            # Port 443 ingress is present
            assert "from_port   = 443" in main_tf
            assert "to_port     = 443" in main_tf
        else:
            # Port 443 ingress should not be configured
            assert "from_port   = 443" not in main_tf
            assert "to_port     = 443" not in main_tf