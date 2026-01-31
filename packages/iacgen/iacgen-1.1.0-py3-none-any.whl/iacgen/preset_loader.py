"""Preset loading utilities for iacgen.

This module provides the PresetLoader class, responsible for discovering and
loading blueprint presets from YAML files. Presets can be bundled with the
package (built-in presets) or supplied via a custom presets directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Mapping
import sys

import yaml

from .config import BlueprintConfig
from .exceptions import PresetNotFoundError


BUILTIN_PRESETS_PACKAGE = "iacgen.presets"


@dataclass(slots=True)
class PresetLoader:
    """Load blueprint presets from YAML files.

    Presets can be discovered from two locations:

    1. A user-specified directory on disk ("custom presets")
    2. Built-in presets packaged under ``iacgen.presets``

    When a custom presets directory is provided, it takes precedence over
    built-in presets. Presets are identified by their base filename without
    extension (e.g. ``microservice.yml`` -> ``"microservice"``).
    """

    custom_presets_dir: Path | None = None

    def __post_init__(self) -> None:
        if isinstance(self.custom_presets_dir, str):  # type: ignore[unreachable]
            # Allow passing a string path even though the type is Path | None
            self.custom_presets_dir = Path(self.custom_presets_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_presets(self) -> list[str]:
        """Return the list of available preset names.

        Custom presets (from ``custom_presets_dir``) take precedence and are
        merged with built-in presets. Names are de-duplicated and sorted.
        """

        names: set[str] = set()

        # 1) Custom presets directory, if provided
        if self.custom_presets_dir is not None:
            names.update(self._discover_files_in_directory(self.custom_presets_dir))

        # 2) Built-in presets packaged under ``iacgen.presets``
        names.update(self._discover_builtin_presets())

        return sorted(names)

    def load_preset(self, name: str) -> dict[str, Any]:
        """Load a preset by name.

        Lookup order:
        1. Custom presets directory (if configured)
        2. Built-in presets package resources

        Raises:
            PresetNotFoundError: if no matching preset file can be found.
        """

        # 1) Try custom presets directory first
        if self.custom_presets_dir is not None:
            path = self._find_file_in_directory(self.custom_presets_dir, name)
            if path is not None:
                return self._load_yaml_file(path)

        # 2) Fall back to built-in presets
        data = self._load_builtin_preset(name)
        if data is not None:
            return data

        # No preset found anywhere -> raise descriptive error
        available = self.list_presets()
        raise PresetNotFoundError(name, available_presets=available)

    def apply_preset(self, name: str, overrides: Mapping[str, Any] | None = None) -> BlueprintConfig:
        """Load a preset and convert it into a :class:`BlueprintConfig`.

        ``overrides`` can be used to tweak values on top of the preset data.
        Values in ``overrides`` always take precedence over the preset values.
        """

        preset_data = self.load_preset(name)
        merged = self._merge_dicts(preset_data, dict(overrides or {}))
        return self._build_config(merged)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _is_yaml_file(path: Path) -> bool:
        return path.suffix.lower() in {".yml", ".yaml"} and path.is_file()

    def _discover_files_in_directory(self, directory: Path) -> Iterable[str]:
        if not directory.exists() or not directory.is_dir():
            return []

        names: set[str] = set()
        for entry in directory.iterdir():
            if self._is_yaml_file(entry):
                names.add(entry.stem)
        return names

    def _find_file_in_directory(self, directory: Path, name: str) -> Path | None:
        """Find a YAML file for the given name in ``directory``.

        Supports both ``.yml`` and ``.yaml`` extensions.
        """

        if not directory.exists() or not directory.is_dir():
            return None

        for ext in (".yml", ".yaml"):
            candidate = directory / f"{name}{ext}"
            if candidate.is_file():
                return candidate
        return None

    def _discover_builtin_presets(self) -> Iterable[str]:
        """Discover built-in presets from the ``iacgen.presets`` package.

        This primarily uses :mod:`importlib.resources` when
        ``BUILTIN_PRESETS_PACKAGE`` is a real package, but gracefully falls
        back to scanning ``sys.path`` for an ``iacgen/presets`` directory when
        running in a development environment where ``iacgen.presets`` is just a
        module (like this file).
        """

        names: set[str] = set()

        # Preferred path: importlib.resources for real packages / distributions
        try:
            for entry in resources.files(BUILTIN_PRESETS_PACKAGE).iterdir():  # type: ignore[attr-defined]
                if entry.is_file() and entry.suffix.lower() in {".yml", ".yaml"}:
                    names.add(entry.stem)
            return names
        except (ModuleNotFoundError, AttributeError, TypeError):
            # - ModuleNotFoundError: package not importable
            # - AttributeError: very old Python without resources.files()
            # - TypeError: ``BUILTIN_PRESETS_PACKAGE`` resolved to a module
            #   instead of a package (e.g. this file during development).
            #
            # In these cases we fall back to a simple filesystem-based lookup
            # that walks sys.path for a directory matching the dotted
            # ``BUILTIN_PRESETS_PACKAGE`` path, which keeps tests working even
            # when a temporary ``iacgen/presets`` package is created on disk.
            pass

        package_rel_path = Path(*BUILTIN_PRESETS_PACKAGE.split("."))
        for base in map(Path, sys.path):
            candidate_dir = base / package_rel_path
            if not candidate_dir.is_dir():
                continue
            for entry in candidate_dir.iterdir():
                if entry.is_file() and entry.suffix.lower() in {".yml", ".yaml"}:
                    names.add(entry.stem)

        return names

    def _load_builtin_preset(self, name: str) -> dict[str, Any] | None:
        """Load a built-in preset by name, if it exists.

        Returns the loaded dict or ``None`` if the preset is not found.
        """

        for ext in (".yml", ".yaml"):
            resource_name = f"{name}{ext}"

            # First try via importlib.resources for real packaged presets
            try:
                data = resources.files(BUILTIN_PRESETS_PACKAGE).joinpath(resource_name)  # type: ignore[attr-defined]
            except (ModuleNotFoundError, AttributeError, TypeError):
                data = None

            if data is not None and data.is_file():
                with data.open("r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}

            # Fallback: look for an ``iacgen/presets`` directory on sys.path,
            # which is how the tests simulate built-in presets.
            package_rel_path = Path(*BUILTIN_PRESETS_PACKAGE.split("."))
            for base in map(Path, sys.path):
                candidate = base / package_rel_path / resource_name
                if candidate.is_file():
                    with candidate.open("r", encoding="utf-8") as f:
                        return yaml.safe_load(f) or {}

        return None

    @staticmethod
    def _load_yaml_file(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # Always return a dict for easier downstream usage
        return data or {} if isinstance(data, dict) or data is None else {"value": data}

    # ------------------------------------------------------------------
    # Configuration building helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _merge_dicts(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
        """Recursively merge two mapping objects.

        - ``overrides`` wins for scalar and list values.
        - For nested dictionaries, values are merged recursively.
        """

        result: dict[str, Any] = dict(base)
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, Mapping):
                result[key] = PresetLoader._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _build_config(data: Mapping[str, Any]) -> BlueprintConfig:
        """Build a :class:`BlueprintConfig` from raw preset data.

        The input ``data`` is expected to follow the BlueprintConfig schema
        shape (top-level ``name``, ``region``, ``environment``, ``vpc``,
        ``eks``, ``alb``, ``services``). Missing sections fall back to the
        Pydantic default values defined on the models.
        """

        # Let BlueprintConfig and nested Pydantic models handle defaults and
        # validation. Any missing keys are simply left out so defaults apply.
        return BlueprintConfig(**dict(data))
