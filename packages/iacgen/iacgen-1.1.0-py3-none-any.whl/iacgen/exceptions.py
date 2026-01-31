"""
Custom exceptions for iacgen.

Provides a hierarchy of exceptions for better error handling and reporting.
"""


class IacgenError(Exception):
    """Base exception for all iacgen errors."""

    def __init__(self, message: str, suggestions: list[str] | None = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(self.message)


class ValidationError(IacgenError):
    """Raised when configuration validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None, suggestions: list[str] | None = None):
        self.errors = errors or []
        super().__init__(message, suggestions)


class ConfigError(IacgenError):
    """Raised when configuration loading or parsing fails."""

    pass


class RenderError(IacgenError):
    """Raised when template rendering fails."""

    pass


class FileError(IacgenError):
    """Raised when file operations fail."""

    pass


class PresetNotFoundError(IacgenError):
    """Raised when a requested preset cannot be found.

    Includes the missing preset name and a list of available presets (if any)
    to help users discover valid options.
    """

    def __init__(self, preset_name: str, available_presets: list[str] | None = None):
        self.preset_name = preset_name
        self.available_presets = available_presets or []

        if self.available_presets:
            presets_list = ", ".join(sorted(self.available_presets))
            message = (
                f"Preset '{self.preset_name}' was not found. "
                f"Available presets: {presets_list}."
            )
            suggestions = [
                "Check for typos in the preset name.",
                "Run the CLI help or list command to see all supported presets.",
            ]
        else:
            message = (
                f"Preset '{self.preset_name}' was not found and no presets are currently "
                "available."
            )
            suggestions = [
                "Ensure presets are defined in your configuration or presets directory.",
            ]

        super().__init__(message, suggestions=suggestions)
