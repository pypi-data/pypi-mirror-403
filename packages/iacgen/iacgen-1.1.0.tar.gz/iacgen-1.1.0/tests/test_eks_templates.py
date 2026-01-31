"""Tests for EKS Terraform module templates rendered by BlueprintRenderer.

Covers:
- Rendering with default EKSConfig values
- Node group scaling configuration (min/max/desired)
- VPC dependency wiring between VPC and EKS modules
- IAM roles and policy attachments for cluster and nodes
- Optional HCL validity via `terraform validate` when available
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from iacgen.config import BlueprintConfig, VPCConfig, EKSConfig
from iacgen.renderer import BlueprintRenderer


def _render_to_tmp(tmp_path: Path, config: BlueprintConfig) -> Path:
    """Helper to render a config into a temp directory and return it."""

    renderer = BlueprintRenderer(config)
    renderer.render(tmp_path)
    return tmp_path


class TestEKSTemplatesBasic:
    """Basic rendering scenarios for the EKS module."""

    def test_render_with_default_eks_config(self, tmp_path: Path) -> None:
        """Rendering with default EKSConfig + VPC should produce EKS files."""

        config = BlueprintConfig(name="test", vpc=VPCConfig(enabled=True), eks=EKSConfig(enabled=True))

        out_dir = _render_to_tmp(tmp_path, config)

        eks_dir = out_dir / "modules" / "eks"
        assert (eks_dir / "main.tf").exists()
        assert (eks_dir / "variables.tf").exists()
        assert (eks_dir / "outputs.tf").exists()

        content = (eks_dir / "main.tf").read_text()
        assert "resource \"aws_eks_cluster\" \"main\"" in content


class TestNodeScalingConfig:
    """Ensure node group scaling_config reflects blueprint values."""

    @pytest.mark.parametrize(
        "desired,min_size,max_size",
        [
            (1, 1, 1),
            (2, 1, 3),
            (3, 2, 5),
        ],
    )
    def test_node_scaling_block(self, tmp_path: Path, desired: int, min_size: int, max_size: int) -> None:
        config = BlueprintConfig(
            name="scaling",
            vpc=VPCConfig(enabled=True),
            eks=EKSConfig(
                enabled=True,
                node_desired_size=desired,
                node_min_size=min_size,
                node_max_size=max_size,
            ),
        )

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "eks" / "main.tf").read_text()

        assert f"desired_size = {desired}" in main_tf
        assert f"min_size     = {min_size}" in main_tf
        assert f"max_size     = {max_size}" in main_tf


class TestVPCDependencyWiring:
    """Verify EKS correctly depends on VPC outputs and variables."""

    def test_eks_variables_require_vpc_inputs(self, tmp_path: Path) -> None:
        """vpc_id and private_subnet_ids must be required inputs (no defaults)."""

        # Render just enough to get module templates written
        config = BlueprintConfig(name="deps", vpc=VPCConfig(enabled=True), eks=EKSConfig(enabled=True))
        out_dir = _render_to_tmp(tmp_path, config)

        vars_tf = (out_dir / "modules" / "eks" / "variables.tf").read_text()

        # Ensure vpc_id and private_subnet_ids are defined without default assignments
        assert "variable \"vpc_id\"" in vars_tf
        assert "default" not in "".join(line for line in vars_tf.splitlines() if "vpc_id" in line)

        assert "variable \"private_subnet_ids\"" in vars_tf
        assert "default" not in "".join(line for line in vars_tf.splitlines() if "private_subnet_ids" in line)

    def test_root_wires_module_vpc_outputs(self, tmp_path: Path) -> None:
        """Root main.tf should pass module.vpc outputs into module.eks."""

        config = BlueprintConfig(name="deps", vpc=VPCConfig(enabled=True), eks=EKSConfig(enabled=True))
        out_dir = _render_to_tmp(tmp_path, config)

        root_main = (out_dir / "main.tf").read_text()

        assert "vpc_id             = module.vpc.vpc_id" in root_main
        assert "private_subnet_ids = module.vpc.private_subnet_ids" in root_main


class TestIAMResources:
    """Validate key IAM role and policy resources for EKS."""

    def test_cluster_and_node_iam_roles_and_policies(self, tmp_path: Path) -> None:
        config = BlueprintConfig(name="iam", vpc=VPCConfig(enabled=True), eks=EKSConfig(enabled=True))

        out_dir = _render_to_tmp(tmp_path, config)
        main_tf = (out_dir / "modules" / "eks" / "main.tf").read_text()

        # Cluster IAM role and policy
        assert "resource \"aws_iam_role\" \"cluster\"" in main_tf
        assert "AmazonEKSClusterPolicy" in main_tf

        # Node IAM role and policies
        assert "resource \"aws_iam_role\" \"node\"" in main_tf
        assert "AmazonEKSWorkerNodePolicy" in main_tf
        assert "AmazonEKS_CNI_Policy" in main_tf
        assert "AmazonEC2ContainerRegistryReadOnly" in main_tf


class TestTerraformValidate:
    """Optional integration with `terraform validate` if terraform is installed.

    These tests are marked as slow / optional as they shell out.
    """

    @pytest.mark.slow
    def test_terraform_validate_vpc_and_eks(self, tmp_path: Path) -> None:
        """Run `terraform validate` on a rendered VPC+EKS config when terraform is present."""

        if os.system("terraform version > /dev/null 2>&1") != 0:
            pytest.skip("terraform not installed; skipping integration validate test")

        config = BlueprintConfig(
            name="tf-validate-eks",
            vpc=VPCConfig(enabled=True),
            eks=EKSConfig(enabled=True),
        )
        out_dir = _render_to_tmp(tmp_path, config)

        # Run `terraform init` and `terraform validate` in the rendered directory
        rc_init = os.system(f"cd {out_dir} && terraform init -backend=false > /dev/null 2>&1")
        if rc_init != 0:
            pytest.skip("terraform init failed in test environment; skipping validate")

        rc_validate = os.system(f"cd {out_dir} && terraform validate > /dev/null 2>&1")
        assert rc_validate == 0
