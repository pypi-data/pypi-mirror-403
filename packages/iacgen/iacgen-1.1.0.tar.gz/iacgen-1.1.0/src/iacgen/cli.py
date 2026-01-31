"""
CLI interface for iacgen using Typer.

Provides commands for creating, recreating, and managing Terraform blueprints.
"""

import json
import sys
import traceback
import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from iacgen import __version__
from iacgen.exceptions import (
    IacgenError,
    ValidationError,
    ConfigError,
    RenderError,
    FileError,
    PresetNotFoundError,
)

from iacgen.config import BlueprintConfig
from iacgen.validator import BlueprintValidator
from iacgen.renderer import BlueprintRenderer
from iacgen.presets import PresetLoader

# Exit codes
EXIT_SUCCESS = 0
EXIT_VALIDATION_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_FILE_ERROR = 3
EXIT_UNKNOWN_ERROR = 99

# Rich console for styled output
console = Console()

# Global debug flag (set via app callback)
_debug_mode = False

def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"[green]{message}[/green]")

def print_error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"[red]{message}[/red]")

def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    console.print(f"[yellow]{message}[/yellow]")


def handle_error(error: Exception, exit_code: int = EXIT_UNKNOWN_ERROR) -> None:
    """Handle errors with appropriate formatting and debug info."""
    if isinstance(error, ValidationError):
        print_error(f"\n❌ Validation Error: {error.message}")
        if error.errors:
            console.print("\n[bold red]Validation errors:[/bold red]")
            for err in error.errors:
                console.print(f"  • {err}")
        if error.suggestions:
            console.print("\n[bold yellow]Suggestions:[/bold yellow]")
            for suggestion in error.suggestions:
                console.print(f"  • {suggestion}")
    elif isinstance(error, ConfigError):
        print_error(f"\n❌ Configuration Error: {error.message}")
        if hasattr(error, 'suggestions') and error.suggestions:
            console.print("\n[bold yellow]Suggestions:[/bold yellow]")
            for suggestion in error.suggestions:
                console.print(f"  • {suggestion}")
    elif isinstance(error, FileError):
        print_error(f"\n❌ File Error: {error.message}")
    elif isinstance(error, RenderError):
        print_error(f"\n❌ Render Error: {error.message}")
    elif isinstance(error, IacgenError):
        print_error(f"\n❌ Error: {error.message}")
    else:
        print_error(f"\n❌ Unexpected error: {str(error)}")
    
    if _debug_mode:
        console.print("\n[dim]Full traceback:[/dim]")
        console.print(traceback.format_exc())
    else:
        console.print("\n[dim]Run with --debug for full traceback[/dim]")
    
    raise typer.Exit(code=exit_code)


app = typer.Typer(
    name="iacgen",
    help="IaC Blueprint Generator - Generate Terraform infrastructure blueprints",
    add_completion=False,
)


@app.callback()
def main(
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode with full tracebacks",
    ),
) -> None:
    """IaC Blueprint Generator - Generate Terraform infrastructure blueprints."""
    global _debug_mode
    _debug_mode = debug
    if debug:
        console.print("[dim]Debug mode enabled[/dim]\n")


@app.command()
def create(
    output: Path = typer.Option(
        "./infra",
        "--output",
        "-o",
        help="Output directory for generated Terraform files",
    ),
    vpc: bool = typer.Option(
        False,
        "--vpc",
        help="Include VPC module",
    ),
    eks: bool = typer.Option(
        False,
        "--eks",
        help="Include EKS cluster module",
    ),
    eks_use_existing_vpc: bool = typer.Option(
        False,
        "--eks-use-existing-vpc",
        help=(
            "Use an existing VPC for the EKS cluster instead of the generated VPC. "
            "Requires --eks-vpc-id and --eks-private-subnet-ids."
        ),
    ),
    eks_vpc_id: Optional[str] = typer.Option(
        None,
        "--eks-vpc-id",
        help="ID of an existing VPC to use for the EKS cluster (used with --eks-use-existing-vpc)",
    ),
    eks_private_subnet_ids: Optional[str] = typer.Option(
        None,
        "--eks-private-subnet-ids",
        help=(
            "Comma-separated list of private subnet IDs in the existing VPC "
            "for the EKS cluster (used with --eks-use-existing-vpc)"
        ),
    ),
    alb: bool = typer.Option(
        False,
        "--alb",
        help="Include Application Load Balancer module",
    ),
    alb_use_existing_vpc: bool = typer.Option(
        False,
        "--alb-use-existing-vpc",
        help=(
            "Use an existing VPC for the ALB instead of the generated VPC. "
            "Requires --alb-vpc-id and --alb-subnet-ids."
        ),
    ),
    alb_vpc_id: Optional[str] = typer.Option(
        None,
        "--alb-vpc-id",
        help="ID of an existing VPC to use for the ALB (used with --alb-use-existing-vpc)",
    ),
    alb_subnet_ids: Optional[str] = typer.Option(
        None,
        "--alb-subnet-ids",
        help=(
            "Comma-separated list of subnet IDs in the existing VPC "
            "for the ALB (used with --alb-use-existing-vpc)"
        ),
    ),
    services: Optional[str] = typer.Option(
        None,
        "--services",
        help="Comma-separated list of service names",
    ),
    preset: Optional[str] = typer.Option(
        None,
        "--preset",
        help="Use a predefined preset configuration",
    ),
    name: str = typer.Option(
        "infrastructure",
        "--name",
        "-n",
        help="Project name",
    ),
    environment: str = typer.Option(
        "dev",
        "--env",
        "--environment",
        help="Deployment environment (e.g. dev, staging, prod)",
    ),
    region: str = typer.Option(
        "us-west-2",
        "--region",
        "-r",
        help="AWS region",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview without writing files",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing output directory",
    ),
):
    """
    Create a new Terraform infrastructure blueprint.
    
    Examples:
        iacgen create --vpc --eks --services api,worker --output ./infra
        iacgen create --preset microservice --name myapp --region us-west-2
        iacgen create --vpc --eks --dry-run
        iacgen create --preset microservice --force

    Notes:
        - Service modules default their Kubernetes namespace to the logical
          environment (e.g. "dev", "staging", "prod").
        - You can point services at an existing namespace by overriding the
          generated Terraform variable `namespace` (and setting
          `create_namespace = false`) in your Terraform configuration.
    """
    try:
        console.print("[bold]Creating infrastructure blueprint...[/bold]\n")

        # Step 1: Parse services string into list
        service_list: list[str] = [s.strip() for s in services.split(",")] if services else []

        # Parse EKS existing VPC subnet IDs if provided
        eks_private_subnet_list: list[str] = []
        if eks_private_subnet_ids:
            eks_private_subnet_list = [
                s.strip() for s in eks_private_subnet_ids.split(",") if s.strip()
            ]

        # Parse ALB existing VPC subnet IDs if provided
        alb_subnet_list: list[str] = []
        if alb_subnet_ids:
            alb_subnet_list = [
                s.strip() for s in alb_subnet_ids.split(",") if s.strip()
            ]

        # Step 2: Build configuration, optionally starting from a preset
        if preset:
            console.print(f"[blue]Loading preset:[/blue] {preset}")

            # Load preset configuration and apply CLI overrides on top. Presets
            # provide a sensible baseline while CLI flags act as overrides.
            try:
                loader = PresetLoader()

                overrides: dict[str, object] = {
                    "name": name,
                    "region": region,
                    "environment": environment,
                }

                # Module flags: enabling a module on the CLI should always win
                # over the preset (we only ever turn things on here).
                if vpc:
                    vpc_overrides = overrides.setdefault("vpc", {})  # type: ignore[assignment]
                    assert isinstance(vpc_overrides, dict)
                    vpc_overrides["enabled"] = True

                if eks:
                    eks_overrides = overrides.setdefault("eks", {})  # type: ignore[assignment]
                    assert isinstance(eks_overrides, dict)
                    eks_overrides["enabled"] = True

                if alb:
                    alb_overrides = overrides.setdefault("alb", {})  # type: ignore[assignment]
                    assert isinstance(alb_overrides, dict)
                    alb_overrides["enabled"] = True

                # EKS existing-VPC options
                if eks_use_existing_vpc or eks_vpc_id or eks_private_subnet_list:
                    eks_overrides = overrides.setdefault("eks", {})  # type: ignore[assignment]
                    assert isinstance(eks_overrides, dict)
                    if eks_use_existing_vpc:
                        eks_overrides["use_existing_vpc"] = True
                    if eks_vpc_id:
                        eks_overrides["existing_vpc_id"] = eks_vpc_id
                    if eks_private_subnet_list:
                        eks_overrides["existing_private_subnet_ids"] = eks_private_subnet_list

                # ALB existing-VPC options
                if alb_use_existing_vpc or alb_vpc_id or alb_subnet_list:
                    alb_overrides = overrides.setdefault("alb", {})  # type: ignore[assignment]
                    assert isinstance(alb_overrides, dict)
                    if alb_use_existing_vpc:
                        alb_overrides["use_existing_vpc"] = True
                    if alb_vpc_id:
                        alb_overrides["existing_vpc_id"] = alb_vpc_id
                    if alb_subnet_list:
                        alb_overrides["existing_subnet_ids"] = alb_subnet_list

                # CLI services override the preset's service list when provided.
                if service_list:
                    overrides["services"] = [{"name": svc_name} for svc_name in service_list]

                config = loader.apply_preset(preset, overrides=overrides)

            except PresetNotFoundError as e:
                # Surface the rich PresetNotFoundError message and suggestions,
                # but exit with a configuration error code for the CLI.
                handle_error(e, EXIT_CONFIG_ERROR)
        else:
            # No preset specified – build configuration purely from CLI args.
            config = BlueprintConfig.from_cli_args(
                name=name,
                region=region,
                environment=environment,
                vpc=vpc,
                eks=eks,
                alb=alb,
                services=service_list,
                eks_use_existing_vpc=eks_use_existing_vpc,
                eks_vpc_id=eks_vpc_id,
                eks_private_subnet_ids=eks_private_subnet_list,
                alb_use_existing_vpc=alb_use_existing_vpc,
                alb_vpc_id=alb_vpc_id,
                alb_subnet_ids=alb_subnet_list,
            )

        # Display configuration summary
        _display_config_summary(
            name=config.name,
            region=config.region,
            environment=config.environment,
            output=output,
            preset=preset,
            vpc=config.vpc.enabled,
            eks=config.eks.enabled,
            alb=config.alb.enabled,
            service_list=[svc.name for svc in config.services],
            dry_run=dry_run,
            force=force,
        )

        # Step 4: Validate configuration
        console.print("\n[blue]Validating configuration...[/blue]")
        validator = BlueprintValidator(config)
        
        if not validator.validate():
            print_error("\n❌ Configuration validation failed:\n")
            console.print(validator.format_errors())
            console.print("\n[dim]Fix the validation errors and try again[/dim]")
            raise typer.Exit(code=EXIT_VALIDATION_ERROR)
        
        console.print("[green]✓[/green] Configuration validation passed")

        # Soft warning: ALB enabled without any services
        if config.alb.enabled and not config.services:
            print_warning(
                "ALB module is enabled but no services are defined. "
                "Ensure you attach at least one target group or update your blueprint if this is intentional."
            )

        # Step 5: Dry run - preview and exit without writing
        if dry_run:
            console.print("\n[yellow]Dry run mode:[/yellow] Skipping file generation")
            console.print(f"[dim]Would write to:[/dim] {output.absolute()}")
            print_success("\n✓ Dry run complete")
            raise typer.Exit(code=0)

        # Step 6: Check if output directory exists
        if output.exists():
            if not force:
                print_error(f"\n❌ Output directory already exists: {output.absolute()}")
                console.print("[yellow]Use --force to overwrite[/yellow]")
                raise typer.Exit(code=1)
            else:
                print_warning(f"⚠️  Overwriting existing directory: {output.absolute()}")

        # Step 7: Render Terraform files
        console.print("\n[blue]Rendering Terraform files...[/blue]")
        try:
            renderer = BlueprintRenderer(config)
            rendered_paths = renderer.render(output)
            console.print(f"[green]✓[/green] Rendered {len(rendered_paths)} files")
        except RenderError as e:
            handle_error(e, EXIT_FILE_ERROR)

        # Step 8: Print success message
        print_success(f"\n✓ Blueprint created successfully at {output.absolute()}")
        raise typer.Exit(code=EXIT_SUCCESS)

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit codes
        raise
    except ValidationError as e:
        handle_error(e, EXIT_VALIDATION_ERROR)
    except PresetNotFoundError as e:
        handle_error(e, EXIT_CONFIG_ERROR)
    except ConfigError as e:
        handle_error(e, EXIT_CONFIG_ERROR)
    except FileError as e:
        handle_error(e, EXIT_FILE_ERROR)
    except (FileNotFoundError, PermissionError, OSError) as e:
        handle_error(
            FileError(f"File operation failed: {str(e)}", suggestions=["Check file paths and permissions"]),
            EXIT_FILE_ERROR
        )
    except Exception as e:
        handle_error(e, EXIT_UNKNOWN_ERROR)


def _display_config_summary(
    name: str,
    region: str,
    environment: str,
    output: Path,
    preset: Optional[str],
    vpc: bool,
    eks: bool,
    alb: bool,
    service_list: list[str],
    dry_run: bool,
    force: bool,
) -> None:
    """Display configuration summary in a panel."""
    lines = [
        f"[bold]Project:[/bold] {name}",
        f"[bold]Region:[/bold] {region}",
        f"[bold]Environment:[/bold] {environment}",
        f"[bold]Output:[/bold] {output}",
    ]

    if preset:
        lines.append(f"[bold]Preset:[/bold] {preset}")

    modules: list[str] = []
    if vpc:
        modules.append("VPC")
    if eks:
        modules.append("EKS")
    if alb:
        modules.append("ALB")
    if modules:
        lines.append(f"[bold]Modules:[/bold] {', '.join(modules)}")

    if service_list:
        lines.append(f"[bold]Services:[/bold] {', '.join(service_list)}")

    if dry_run:
        lines.append("[yellow]Mode:[/yellow] Dry run (preview only)")
    if force:
        lines.append("[yellow]Force:[/yellow] Overwrite existing output directory")

    console.print(Panel("\n".join(lines), title="[bold cyan]Configuration[/bold cyan]", border_style="cyan"))


@app.command()
def recreate(
    config_file: Path = typer.Argument(
        ...,
        help="Path to blueprint.json configuration file",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Override output directory (defaults to config file's parent directory)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing output directory",
    ),
):
    """
    Recreate Terraform blueprint from existing configuration file.
    
    Examples:
        iacgen recreate blueprint.json
        iacgen recreate infra/blueprint.json --output ./new-infra
        iacgen recreate blueprint.json --force
    """
    try:
        console.print("[bold]Recreating infrastructure from configuration...[/bold]\n")

        # Step 1-3: Load BlueprintConfig from JSON file
        console.print(f"[blue]Reading configuration:[/blue] {config_file}")
        config = BlueprintConfig.from_json(config_file)
        console.print("[green]✓[/green] Configuration loaded successfully")

        # Step 4: Extract output directory (config file parent or override)
        if output is None:
            # Use config file's parent directory as default
            output = config_file.parent
            console.print(f"[dim]Using default output directory:[/dim] {output.absolute()}")
        else:
            console.print(f"[blue]Output directory override:[/blue] {output.absolute()}")

        # Display configuration summary
        _display_summary_env = getattr(config, "environment", "dev")
        _display_config_summary(
            name=config.name,
            region=config.region,
            environment=_display_summary_env,
            output=output,
            preset=None,  # Not stored in blueprint.json
            vpc=config.vpc.enabled,
            eks=config.eks.enabled,
            alb=config.alb.enabled,
            service_list=[svc.name for svc in config.services],
            dry_run=False,
            force=force,
        )

        # Step 5: Validate the loaded config
        console.print("\n[blue]Validating configuration...[/blue]")
        validator = BlueprintValidator(config)
        
        if not validator.validate():
            print_error("\n❌ Configuration validation failed:\n")
            console.print(validator.format_errors())
            console.print("\n[dim]Fix the validation errors in the configuration file and try again[/dim]")
            raise typer.Exit(code=EXIT_VALIDATION_ERROR)
        
        console.print("[green]✓[/green] Configuration validation passed")

        # Step 6: Check if output directory exists
        if output.exists():
            if not force:
                raise FileError(
                    f"Output directory already exists: {output.absolute()}",
                    suggestions=["Use --force to overwrite", "Choose a different output directory with --output"]
                )
            else:
                print_warning(f"⚠️  Overwriting existing directory: {output.absolute()}")

        # Step 7: Call renderer to regenerate files
        console.print("\n[blue]Rendering Terraform files...[/blue]")
        try:
            renderer = BlueprintRenderer(config)
            rendered_paths = renderer.render(output)
            console.print(f"[green]✓[/green] Rendered {len(rendered_paths)} files")
        except RenderError as e:
            handle_error(e, EXIT_FILE_ERROR)

        # Step 8: Print success message
        print_success(f"\n✓ Blueprint recreated successfully at {output.absolute()}")
        raise typer.Exit(code=EXIT_SUCCESS)

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit codes
        raise
    except ValidationError as e:
        handle_error(e, EXIT_VALIDATION_ERROR)
    except ConfigError as e:
        handle_error(e, EXIT_CONFIG_ERROR)
    except FileError as e:
        handle_error(e, EXIT_FILE_ERROR)
    except (FileNotFoundError, PermissionError, OSError) as e:
        handle_error(
            FileError(f"File operation failed: {str(e)}", suggestions=["Check file paths and permissions"]),
            EXIT_FILE_ERROR
        )
    except Exception as e:
        handle_error(e, EXIT_UNKNOWN_ERROR)


@app.command()
def version():
    """
    Display the iacgen version.
    """
    console.print(f"[blue]iacgen version[/blue] {__version__}")


if __name__ == "__main__":
    app()
