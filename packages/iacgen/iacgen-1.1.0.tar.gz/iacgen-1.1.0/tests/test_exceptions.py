"""Tests for custom exception classes in iacgen."""

import pytest

from iacgen.exceptions import IacgenError, PresetNotFoundError


class TestPresetNotFoundError:
    def test_is_subclass_of_iacgen_error(self):
        err = PresetNotFoundError("microservice", ["microservice", "data-platform"])
        assert isinstance(err, IacgenError)

    def test_message_includes_preset_name_and_available_presets(self):
        err = PresetNotFoundError("unknown-preset", ["microservice", "data-platform"])
        message = str(err)
        assert "unknown-preset" in message
        assert "microservice" in message
        assert "data-platform" in message

    def test_handles_empty_available_presets_gracefully(self):
        err = PresetNotFoundError("unknown-preset", [])
        message = str(err)
        assert "unknown-preset" in message
        # Should still be a meaningful message even when no presets are available
        assert "no presets are currently available" in message.lower()