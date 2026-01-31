"""Tests for the PresetLoader class.

These tests focus on YAML loading, discovery, and error handling, including
custom presets directory precedence and PresetNotFoundError behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import sys

import pytest

from iacgen.config import BlueprintConfig
from iacgen.exceptions import PresetNotFoundError
from iacgen.presets import PresetLoader


class TestPresetLoaderCustomDirectory:
    def test_list_presets_discovers_yaml_files(self, tmp_path: Path) -> None:
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        (presets_dir / "microservice.yml").write_text("name: microservice\nreplicas: 3\n", encoding="utf-8")
        (presets_dir / "data-platform.yaml").write_text("name: data-platform\n", encoding="utf-8")

        loader = PresetLoader(custom_presets_dir=presets_dir)
        names = loader.list_presets()

        # Custom directory presets should be discovered, even if built-in presets
        # are also available.
        assert "microservice" in names
        assert "data-platform" in names

    def test_load_preset_reads_yaml_from_custom_directory(self, tmp_path: Path) -> None:
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        (presets_dir / "microservice.yml").write_text("name: microservice\nreplicas: 3\n", encoding="utf-8")

        loader = PresetLoader(custom_presets_dir=presets_dir)
        data = loader.load_preset("microservice")

        assert data["name"] == "microservice"
        assert data["replicas"] == 3

    def test_load_preset_raises_preset_not_found_for_unknown_name(self, tmp_path: Path) -> None:
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        (presets_dir / "microservice.yml").write_text("name: microservice\n", encoding="utf-8")

        loader = PresetLoader(custom_presets_dir=presets_dir)

        with pytest.raises(PresetNotFoundError) as exc:
            loader.load_preset("does-not-exist")

        message = str(exc.value)
        # Should mention the missing name and list available presets
        assert "does-not-exist" in message
        assert "microservice" in message


class TestPresetLoaderBuiltinPresets:
    """Tests for real built-in presets bundled with the package."""

    def test_list_presets_includes_builtin_presets(self) -> None:
        loader = PresetLoader(custom_presets_dir=None)
        names = loader.list_presets()

        # At minimum, the three core built-in presets from task 10.4 should be present.
        assert {"microservice", "simple-vpc", "full-stack"}.issubset(set(names))

    def test_load_preset_reads_builtin_yaml(self) -> None:
        loader = PresetLoader(custom_presets_dir=None)
        data = loader.load_preset("microservice")

        assert data["name"] == "microservice"
        # The built-in microservice preset should define at least one service
        # with replicas set to 2.
        assert any(svc.get("replicas") == 2 for svc in data.get("services", []))


class TestPresetLoaderPrecedence:
    def test_custom_presets_take_precedence_over_builtin(self, tmp_path: Path) -> None:
        # Fake built-in package with one version of the preset
        root = tmp_path / "iacgen"
        presets_pkg = root / "presets"
        presets_pkg.mkdir(parents=True)
        (root / "__init__.py").write_text("", encoding="utf-8")
        (presets_pkg / "__init__.py").write_text("", encoding="utf-8")
        (presets_pkg / "microservice.yml").write_text("name: microservice\nreplicas: 1\n", encoding="utf-8")

        sys.path.insert(0, str(tmp_path))

        try:
            # Custom directory with an overriding version
            custom_dir = tmp_path / "custom-presets"
            custom_dir.mkdir()
            (custom_dir / "microservice.yml").write_text("name: microservice\nreplicas: 5\n", encoding="utf-8")

            loader = PresetLoader(custom_presets_dir=custom_dir)
            data = loader.load_preset("microservice")

            # Custom version should win
            assert data["replicas"] == 5
        finally:
            sys.path = [p for p in sys.path if p != str(tmp_path)]


class TestPresetLoaderNoPresetsAvailable:
    def test_raises_preset_not_found_with_available_list_in_message(self, tmp_path: Path) -> None:
        # No custom dir; loader should fall back to built-in presets and include
        # them in the error message when a preset is not found.
        loader = PresetLoader(custom_presets_dir=tmp_path / "does-not-exist")

        with pytest.raises(PresetNotFoundError) as exc:
            loader.load_preset("anything")

        message = str(exc.value)
        assert "anything" in message
        assert "available presets" in message.lower()


class TestPresetLoaderConfigBuilding:
    def test_merge_dicts_performs_deep_merge_with_overrides(self) -> None:
        base = {
            "name": "base",
            "vpc": {"enabled": False, "cidr_block": "10.0.0.0/16"},
            "eks": {"enabled": False},
        }
        overrides = {
            "name": "override",
            "vpc": {"enabled": True},
        }

        merged = PresetLoader._merge_dicts(base, overrides)

        assert merged["name"] == "override"
        assert merged["vpc"]["enabled"] is True
        # Unoverridden nested values should be preserved
        assert merged["vpc"]["cidr_block"] == "10.0.0.0/16"

    def test_build_config_creates_blueprint_config_from_minimal_data(self) -> None:
        data = {
            "name": "my-stack",
            "region": "us-west-2",
            "environment": "dev",
            "vpc": {"enabled": True},
        }

        cfg = PresetLoader._build_config(data)

        assert isinstance(cfg, BlueprintConfig)
        assert cfg.name == "my-stack"
        assert cfg.vpc.enabled is True
        # Missing sections (eks, alb, services) should fall back to defaults
        assert cfg.eks.enabled is False
        assert cfg.alb.enabled is False
        assert cfg.services == []

    def test_apply_preset_loads_yaml_and_applies_overrides(self, tmp_path: Path) -> None:
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir()
        # Basic preset with VPC enabled and one service
        presets_yaml = """
        name: microservice-stack
        region: us-east-1
        environment: dev
        vpc:
          enabled: true
        eks:
          enabled: true
        services:
          - name: api
            replicas: 2
        """
        (presets_dir / "microservice.yml").write_text(presets_yaml, encoding="utf-8")

        loader = PresetLoader(custom_presets_dir=presets_dir)

        # Override region and add another service via overrides
        overrides = {
            "region": "eu-west-1",
            "services": [
                {"name": "api", "replicas": 3},
                {"name": "worker", "replicas": 1},
            ],
        }

        cfg = loader.apply_preset("microservice", overrides=overrides)

        assert isinstance(cfg, BlueprintConfig)
        assert cfg.name == "microservice-stack"
        assert cfg.region == "eu-west-1"  # override wins
        assert cfg.vpc.enabled is True
        assert cfg.eks.enabled is True
        assert [s.name for s in cfg.services] == ["api", "worker"]
        assert [s.replicas for s in cfg.services] == [3, 1]
