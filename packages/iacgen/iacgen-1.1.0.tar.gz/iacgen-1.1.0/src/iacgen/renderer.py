"""
Template rendering engine for iacgen.

This module is responsible for:
- Initialising the Jinja2 environment and loading templates
- Providing helpers/filters that are shared across templates
- Exposing a high-level BlueprintRenderer API used by the CLI
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from jinja2 import Environment, PackageLoader, TemplateError, TemplateNotFound, select_autoescape

from iacgen.config import BlueprintConfig
from iacgen.exceptions import RenderError


class BlueprintRenderer:
    """Core Jinja2 rendering engine for iacgen.

    This class owns the Jinja2 Environment instance and provides
    a simple API that higher-level code (e.g. the CLI) can use to
    render Terraform templates.
    """

    def __init__(self, config: BlueprintConfig) -> None:
        """Create a new renderer for the given blueprint configuration.

        Args:
            config: Validated BlueprintConfig instance that will be used
                to build template context during rendering.

        Raises:
            RenderError: If the Jinja2 environment cannot be initialised.
        """

        self.config = config

        try:
            # Use PackageLoader so templates are loaded from the installed
            # iacgen package (iacgen/templates/...). This works both in
            # editable installs (pip install -e .) and normal installs.
            loader = PackageLoader("iacgen", "templates")

            # HCL/Terraform is not HTML, so we must not autoescape characters
            # like quotes. Autoescaping is only useful for formats such as
            # HTML or XML; here it would turn '"' into '&#34;' etc.
            self.env = Environment(
                loader=loader,
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True,
            )

            # Register core filters that templates can rely on.
            self._register_filters()
        except Exception as exc:  # pragma: no cover - defensive guard
            # Wrap any unexpected Jinja2/package loader issues in a
            # domain-specific error so the CLI can present a friendly
            # message to the user.
            raise RenderError(
                f"Failed to initialise template renderer: {exc}",
                suggestions=[
                    "Ensure the iacgen templates are installed correctly",
                    "Reinstall the package with 'pip install -e .'",
                ],
            ) from exc

    # ------------------------------------------------------------------
    # Context building & file rendering helpers
    # ------------------------------------------------------------------

    def _build_context(self) -> dict[str, Any]:
        """Build the base Jinja2 context from the BlueprintConfig.

        This context is shared across all templates. It includes the
        raw config objects as well as convenience boolean flags used
        in many Terraform templates.
        """

        config: Any = self.config

        services = list(config.services)

        context: dict[str, Any] = {
            "name": config.name,
            "region": config.region,
            "environment": config.environment,
            "vpc": config.vpc,
            "eks": config.eks,
            "alb": config.alb,
            "services": services,
            # Convenience flags for conditional blocks in templates
            "has_vpc": bool(config.vpc.enabled),
            "has_eks": bool(config.eks.enabled),
            "has_alb": bool(config.alb.enabled),
            "has_services": bool(services),
        }

        return context

    def _render_file(
        self,
        template_name: str,
        output_path: Path,
        extra_context: Mapping[str, Any] | None = None,
    ) -> Path:
        """Render a single template to the given output path.

        Args:
            template_name: Name of the Jinja2 template, relative to the
                loader root (e.g. "main.tf.j2").
            output_path: Filesystem path where rendered content will be
                written.
            extra_context: Optional additional context to merge with the
                base context returned by :meth:`_build_context`.

        Raises:
            RenderError: If template loading, rendering or file I/O fails.
        """

        try:
            template = self.env.get_template(template_name)
        except TemplateError as exc:
            raise RenderError(
                f"Failed to load template '{template_name}': {exc}",
                suggestions=[
                    "Ensure the template file exists in iacgen/templates",
                    "Check for typos in the template name",
                ],
            ) from exc

        context = self._build_context()
        if extra_context:
            # extra_context wins on key collisions so callers can
            # override defaults for specific templates.
            context.update(dict(extra_context))

        try:
            rendered = template.render(context)
        except TemplateError as exc:
            raise RenderError(
                f"Failed to render template '{template_name}': {exc}",
                suggestions=[
                    "Check template syntax and variables",
                    "Run with --debug to see full traceback",
                ],
            ) from exc

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered)
        except OSError as exc:
            raise RenderError(
                f"Failed to write rendered file to {output_path}: {exc}",
                suggestions=[
                    "Check directory permissions",
                    "Verify there is enough disk space",
                ],
            ) from exc

        return output_path

    # ------------------------------------------------------------------
    # Module rendering helpers
    # ------------------------------------------------------------------

    def _render_module(
        self,
        module_name: str,
        output_dir: Path,
        context: Dict[str, Any] | None = None,
    ) -> list[Path]:
        """Render a module directory with standard Terraform files.

        - Create ``output_dir`` if needed
        - Iterate over standard Terraform templates:
          ["main.tf.j2", "variables.tf.j2", "outputs.tf.j2"]
        - Attempt to load each from ``modules/<module_name>/<template>``
        - Render and write to corresponding ``*.tf`` files
        - Gracefully skip missing templates (some modules may not
          provide all files)

        Returns:
            List of successfully rendered file paths.
        """

        output_dir.mkdir(parents=True, exist_ok=True)

        rendered_paths: list[Path] = []
        templates = [
            "main.tf.j2",
            "variables.tf.j2",
            "outputs.tf.j2",
        ]

        base_context = self._build_context()
        if context:
            base_context.update(dict(context))

        for template_name in templates:
            template_path = f"modules/{module_name}/{template_name}"
            output_name = template_name.replace(".j2", "")
            output_path = output_dir / output_name

            try:
                template = self.env.get_template(template_path)
            except TemplateNotFound:
                # Some modules might not define all standard files; this
                # is expected (e.g. no outputs.tf for certain modules).
                continue
            except TemplateError as exc:
                # Non-existence is handled above; other template errors
                # should surface as a RenderError.
                raise RenderError(
                    f"Failed to load template '{template_path}': {exc}",
                    suggestions=[
                        "Check template syntax and location",
                        "Ensure the template is packaged under iacgen/templates",
                    ],
                ) from exc

            try:
                rendered = template.render(base_context)
            except TemplateError as exc:
                raise RenderError(
                    f"Failed to render template '{template_path}': {exc}",
                    suggestions=[
                        "Check template variables and conditionals",
                        "Run with --debug to see full traceback",
                    ],
                ) from exc

            try:
                output_path.write_text(rendered)
            except OSError as exc:
                raise RenderError(
                    f"Failed to write rendered file to {output_path}: {exc}",
                    suggestions=[
                        "Check directory permissions",
                        "Verify there is enough disk space",
                    ],
                ) from exc

            rendered_paths.append(output_path)

        return rendered_paths

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self, output_dir: Path) -> list[Path]:
        """Render the full Terraform blueprint to ``output_dir``.
        1) Ensure output_dir exists
        2) Render root templates (main.tf, variables.tf, outputs.tf,
           terraform.tfvars)
        3) Create modules/ and render core modules (vpc, eks, alb)
        4) Render one service module per configured service
        5) Write blueprint.json used by the recreate command
        6) Return list of all rendered file paths
        """

        rendered_paths: list[Path] = []

        # 1) Ensure output_dir exists
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RenderError(
                f"Failed to create output directory {output_dir}: {exc}",
                suggestions=[
                    "Check directory permissions",
                    "Verify the path is correct and writable",
                ],
            ) from exc

        # 2) Render root templates
        root_templates = [
            ("main.tf.j2", "main.tf"),
            ("variables.tf.j2", "variables.tf"),
            ("outputs.tf.j2", "outputs.tf"),
            ("terraform.tfvars.j2", "terraform.tfvars"),
        ]

        for template_name, output_name in root_templates:
            template_path = template_name
            output_path = output_dir / output_name

            try:
                rendered_path = self._render_file(template_path, output_path)
            except RenderError:
                # Surface domain-specific errors unchanged so the CLI can
                # present useful suggestions.
                raise
            except Exception as exc:  # pragma: no cover - defensive
                raise RenderError(
                    f"Unexpected error rendering '{template_path}': {exc}",
                    suggestions=[
                        "Run with --debug to see full traceback",
                        "Check template logic for unhandled edge cases",
                    ],
                ) from exc

            rendered_paths.append(rendered_path)

        # 3) Modules directory
        modules_root = output_dir / "modules"
        try:
            modules_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RenderError(
                f"Failed to create modules directory {modules_root}: {exc}",
                suggestions=["Check directory permissions"],
            ) from exc

        cfg = self.config

        # 4) Core infrastructure modules
        if cfg.vpc.enabled:
            rendered_paths.extend(
                self._render_module("vpc", modules_root / "vpc")
            )

        if cfg.eks.enabled:
            rendered_paths.extend(
                self._render_module("eks", modules_root / "eks")
            )

        if cfg.alb.enabled:
            rendered_paths.extend(
                self._render_module("alb", modules_root / "alb")
            )

        # 5) Service modules – one directory per service under modules/service
        if cfg.services:
            services_root = modules_root / "service"
            for idx, service in enumerate(cfg.services):
                service_dir = services_root / service.name
                service_ctx: Dict[str, Any] = {
                    "service": service,
                    "service_index": idx,
                }
                rendered_paths.extend(
                    self._render_module("service", service_dir, context=service_ctx)
                )

        # 6) blueprint.json for recreate command
        blueprint_path = output_dir / "blueprint.json"
        try:
            cfg.to_json(blueprint_path)
        except Exception as exc:
            # ConfigError is raised from to_json for most issues; this
            # catch-all keeps the renderer API uniform.
            raise RenderError(
                f"Failed to write blueprint configuration to {blueprint_path}: {exc}",
                suggestions=[
                    "Check file permissions",
                    "Ensure the disk is not full",
                ],
            ) from exc

        rendered_paths.append(blueprint_path)

        return rendered_paths

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters used by Terraform templates.

        Centralising registration makes it easy to see which helpers are available 
        inside templates.
        """

        self.env.filters["terraform_list"] = self._terraform_list
        self.env.filters["terraform_map"] = self._terraform_map
        self.env.filters["terraform_bool"] = self._terraform_bool
        self.env.filters["terraform_quote"] = self._terraform_quote

    # --- Terraform filter implementations ---------------------------------

    def _terraform_list(self, value: Any) -> str:
        """Render Python values as Terraform list literals.

        Examples:
            ["a", "b"] -> ["a", "b"]
            [1, 2]       -> [1, 2]
            "a"          -> ["a"]
            None         -> []
        """

        if value is None:
            return "[]"

        if isinstance(value, (list, tuple, set)):
            items = [self._terraform_primitive(v) for v in value]
            return f"[{', '.join(items)}]"

        # Treat single values as a single-element list for ergonomics in
        # templates.
        return f"[{self._terraform_primitive(value)}]"

    def _terraform_map(self, value: Any) -> str:
        """Render a mapping/dict as a Terraform map/object literal.

        Non-mapping values are returned via `_terraform_primitive`.
        """

        if value is None:
            return "{}"

        if isinstance(value, Mapping):
            parts: list[str] = []
            for key, v in value.items():
                # Keys in Terraform maps are almost always strings.
                key_str = str(key)
                parts.append(f"{key_str} = {self._terraform_primitive(v)}")
            inner = ", ".join(parts)
            return f"{{{inner}}}"

        return self._terraform_primitive(value)

    @staticmethod
    def _terraform_bool(value: Any) -> str:
        """Render a value as a Terraform boolean expression.

        Truthiness is respected but output is the Terraform literals
        `true` or `false`.
        """

        return "true" if bool(value) else "false"

    @staticmethod
    def _terraform_quote(value: Any) -> str:
        """Render a value as a Terraform string literal.

        This is useful in templates when you need explicit quoting.
        """

        if value is None:
            return '""'

        if not isinstance(value, str):
            value = str(value)

        escaped = value.replace("\"", "\\\"")
        return f'"{escaped}"'

    @staticmethod
    def _terraform_primitive(value: Any) -> str:
        """Convert a primitive Python value to a Terraform expression.

        Strings are quoted, booleans/literals are rendered as-is.
        """

        if isinstance(value, str):
            escaped = value.replace("\"", "\\\"")
            return f'"{escaped}"'

        if isinstance(value, bool):
            return "true" if value else "false"

        if value is None:
            return "null"

        return str(value)
