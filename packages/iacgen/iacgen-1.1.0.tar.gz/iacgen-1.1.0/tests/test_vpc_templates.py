"""Tests for VPC Terraform module templates rendered by BlueprintRenderer.

Covers:
- Rendering with default VPCConfig values
- NAT gateway combinations (enable_nat_gateway / single_nat_gateway)
- Different availability_zones values
- Kubernetes tags including cluster name
- Basic HCL validity via `terraform validate` when available
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import pytest

from iacgen.config import BlueprintConfig, VPCConfig, EKSConfig
from iacgen.renderer import BlueprintRenderer


def _render_to_tmp(tmp_path: Path, config: BlueprintConfig) -> Path:
    """Helper to render a config into a temp directory and return it."""

    renderer = BlueprintRenderer(config)
    renderer.render(tmp_path)
    return tmp_path


class TestVPCTemplatesBasic:
    """Basic rendering scenarios for the VPC module."""

    def test_render_with_default_vpc_config(self, tmp_path: Path) -> None:
        """Rendering with default VPCConfig values should succeed and produce VPC files."""

        config = BlueprintConfig(name="test", vpc=VPCConfig(enabled=True))

        out_dir = _render_to_tmp(tmp_path, config)

        vpc_dir = out_dir / "modules" / "vpc"
        assert (vpc_dir / "main.tf").exists()
        assert (vpc_dir / "variables.tf").exists()
        assert (vpc_dir / "outputs.tf").exists()

        content = (vpc_dir / "main.tf").read_text()
        assert "resource \"aws_vpc\" \"this\"" in content
        assert "10.0.0.0/16" in content  # default cidr_block


class TestNATGatewayCombinations:
    """Tests around enable_nat_gateway and single_nat_gateway combinations."""

    @pytest.mark.parametrize(
        "enable_nat,single_nat,expected_count_fragment",
        [
            (True, True, "count = 1"),
            (True, False, "length(local.azs)"),
            (False, True, "count = 0"),
            (False, False, "count = 0"),
        ],
    )
    def test_nat_gateway_count_logic(
        self,
        tmp_path: Path,
        enable_nat: bool,
        single_nat: bool,
        expected_count_fragment: str,
    ) -> None:
        """Verify nat gateway count expressions reflect config flags."""

        vpc_cfg = VPCConfig(
            enabled=True,
            enable_nat_gateway=enable_nat,
            single_nat_gateway=single_nat,
        )
        config = BlueprintConfig(name="test", vpc=vpc_cfg)

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "vpc" / "main.tf").read_text()

        assert expected_count_fragment in main_tf


class TestAvailabilityZones:
    """Ensure availability_zones setting affects locals and subnets."""

    @pytest.mark.parametrize("az_count", [1, 2, 3])
    def test_availability_zones_variations(self, tmp_path: Path, az_count: int) -> None:
        config = BlueprintConfig(
            name="test",
            vpc=VPCConfig(enabled=True, availability_zones=az_count),
        )

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "vpc" / "main.tf").read_text()

        # locals.az_count should match
        assert f"az_count = {az_count}" in main_tf


class TestKubernetesTags:
    """Verify Kubernetes-related tags include the cluster name."""

    def test_kubernetes_cluster_tag_includes_cluster_name(self, tmp_path: Path) -> None:
        config = BlueprintConfig(
            name="demo",
            vpc=VPCConfig(enabled=True),
            eks=EKSConfig(enabled=True),
        )

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "vpc" / "main.tf").read_text()

        # The tag uses `{{ name }}-eks` so the rendered file should contain this literal
        assert "kubernetes.io/cluster/demo-eks" in main_tf


class TestTerraformValidate:
    """Optional integration with `terraform validate` if terraform is installed.

    These tests are marked as slow / optional as they shell out.
    """

    @pytest.mark.slow
    def test_terraform_validate_vpc_only(self, tmp_path: Path) -> None:
        """Run `terraform validate` on a rendered VPC-only config when terraform is present."""

        if os.system("terraform version > /dev/null 2>&1") != 0:
            pytest.skip("terraform not installed; skipping integration validate test")

        config = BlueprintConfig(name="tf-validate", vpc=VPCConfig(enabled=True))
        out_dir = _render_to_tmp(tmp_path, config)

        # Run `terraform init` and `terraform validate` in the rendered directory
        rc_init = os.system(f"cd {out_dir} && terraform init -backend=false > /dev/null 2>&1")
        if rc_init != 0:
            pytest.skip("terraform init failed in test environment; skipping validate")

        rc_validate = os.system(f"cd {out_dir} && terraform validate > /dev/null 2>&1")
        assert rc_validate == 0
