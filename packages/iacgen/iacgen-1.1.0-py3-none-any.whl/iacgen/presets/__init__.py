"""Built-in preset package for iacgen.

This package exposes :class:`PresetLoader` for public import and also serves as
the home for built-in YAML preset files that are shipped with the library.

Usage
-----

    from iacgen.presets import PresetLoader

"""

from __future__ import annotations

from iacgen.preset_loader import PresetLoader, BUILTIN_PRESETS_PACKAGE

__all__ = ["PresetLoader", "BUILTIN_PRESETS_PACKAGE"]
