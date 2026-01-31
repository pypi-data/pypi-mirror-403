# IaC Blueprint Generator (iacgen)

> **Accelerate Terraform infrastructure provisioning with opinionated, best-practice blueprints**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI Version](https://img.shields.io/pypi/v/iacgen.svg)](https://pypi.org/project/iacgen/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/iacgen.svg)](https://pypi.org/project/iacgen/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-green.svg)](https://github.com/JRcodes/iac-generator)

---

## The Problem

Every time your team needs to provision new infrastructure, you face the same challenges:

- **Copy-paste drift**: Duplicating Terraform configs leads to inconsistencies
- **Boilerplate fatigue**: Writing the same module wiring patterns over and over
- **Onboarding friction**: New engineers struggle with "where do I start?"
- **Guardrails missing**: No enforcement of architectural best practices

**What if you could generate production-ready Terraform blueprints in under 30 seconds?**

---

## The Solution

**iacgen** is a CLI tool that automatically generates opinionated Terraform infrastructure blueprints for AWS-based architectures. Think of it as a "paved road" generator that enforces your platform's golden path patterns.

### Key Benefits

**Consistency**: Every project follows the same proven patterns  
**Speed**: Generate complete infrastructure in seconds, not hours  
**Best Practices**: Built-in dependency validation and module wiring  
**Developer Experience**: Simple CLI interface, minimal learning curve

---

## Current Status: v1.0.0 (Beta)

**What's Working:**
- CLI framework with Typer + Rich console output
- Complete `create` command with all flags (--vpc, --eks, --alb, --services, --name, --region, --dry-run, --force)
- VPC Terraform module templates (including NAT gateway and AZ handling)
- EKS Terraform module templates (IAM roles, node groups, existing VPC support)
- Service Terraform module templates (Kubernetes namespace, Deployment, Service, optional HPA)
- ALB Terraform module templates (security groups, ALB, target groups, listeners, path-based routing)
- Complete `recreate` command with config file loading
- Pydantic configuration models (VPCConfig, EKSConfig, ALBConfig, ServiceConfig, BlueprintConfig)
- Blueprint.json generation and persistence with validation
- **Validation engine with module dependency rules**
- **Jinja2 rendering engine with custom Terraform filters**
- **YAML-based preset system with built-in presets (microservice, simple-vpc, full-stack)**
- Comprehensive error handling with custom exceptions
- Debug mode (--debug flag for full tracebacks)
- Proper exit codes (0=success, 1=validation, 2=config, 3=file, 99=unknown)
- Package structure and Python 3.10+ support
- Test infrastructure with pytest (29+ tests for validator)

**Coming Soon:**
- Additional presets and example blueprints
- Improved error messages and documentation polish

---

## Installation

### From PyPI

```bash
pip install iacgen

# Verify installation
iacgen --help
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/JRcodes/iac-generator.git
cd iac-generator

# Install in development mode
pip install -e .

# Verify installation
iacgen --help
```

### Requirements

- Python 3.10 or higher
- pip (Python package manager)

---

## Quick Start

### Basic Usage

```bash
# Generate infrastructure with VPC and EKS
iacgen create --vpc --eks --output ./my-infra

# Generate EKS in an existing VPC (no new VPC created)
iacgen create \
  --eks \
  --eks-use-existing-vpc \
  --eks-vpc-id vpc-1234567890abcdef0 \
  --eks-private-subnet-ids subnet-a1b2c3,subnet-d4e5f6 \
  --output ./my-infra

# Add services to your infrastructure (backed by EKS)
iacgen create --vpc --eks --services api,worker --output ./my-infra

# Add an ALB in front of your infrastructure (generated VPC)
iacgen create --vpc --eks --alb --services api,worker --output ./my-infra

# Add an ALB using an existing VPC
iacgen create \
  --alb \
  --alb-use-existing-vpc \
  --alb-vpc-id vpc-1234567890abcdef0 \
  --alb-subnet-ids subnet-a1b2c3,subnet-d4e5f6 \
  --output ./my-infra

# Customize project name and region
iacgen create --vpc --eks --name myapp --region us-east-1 --output ./my-infra

# Preview without creating files (dry run)
iacgen create --vpc --eks --services api --dry-run

# Force overwrite existing output directory
iacgen create --vpc --eks --force --output ./my-infra

# Use a built-in preset configuration
iacgen create --preset microservice --output ./my-infra

# Regenerate from existing configuration
iacgen recreate ./my-infra/blueprint.json

# Regenerate to a different location
iacgen recreate ./my-infra/blueprint.json --output ./new-location

# Enable debug mode for troubleshooting
iacgen --debug create --vpc --eks
```

### Command Reference

| Command | Description | Status |
|---------|-------------|--------|
| `iacgen create` | Generate new Terraform blueprint | Available |
| `iacgen recreate` | Regenerate from config file | Available |
| `iacgen version` | Display version information | Available |
| `iacgen --debug` | Enable debug mode with full tracebacks | Available |

### Available Flags

**Create Command:**
- `--output, -o` - Output directory (default: `./infra`)
- `--vpc` - Include VPC module
- `--eks` - Include EKS cluster module
- `--eks-use-existing-vpc` - Use an existing VPC for EKS instead of generating one
- `--eks-vpc-id` - ID of an existing VPC (used with `--eks-use-existing-vpc`)
- `--eks-private-subnet-ids` - Comma-separated private subnet IDs for existing VPC (used with `--eks-use-existing-vpc`)
- `--alb` - Include ALB module
- `--alb-use-existing-vpc` - Use an existing VPC for the ALB instead of generating one
- `--alb-vpc-id` - ID of an existing VPC for the ALB (used with `--alb-use-existing-vpc`)
- `--alb-subnet-ids` - Comma-separated subnet IDs for the existing VPC (used with `--alb-use-existing-vpc`)
- `--services` - Comma-separated list of services
- `--preset` - Use predefined YAML preset (e.g. `microservice`, `simple-vpc`, `full-stack`)
- `--name, -n` - Project name (default: `infrastructure`)
- `--region, -r` - AWS region (default: `us-west-2`)
- `--dry-run` - Preview without writing files
- `--force, -f` - Overwrite existing output directory

**Recreate Command:**
- `--output, -o` - Override output directory
- `--force, -f` - Overwrite existing output directory

---

### Architecture Overview

```
┌─────────────┐
│  CLI Layer  │  ← Parse commands & flags
│   (Typer)   │
└──────┬──────┘
       │
┌──────▼─────────────┐
│  Preset Engine     │  ← Load YAML presets & apply CLI overrides
│ (PresetLoader)     │
└──────┬─────────────┘
       │
┌──────▼──────────┐
│ Config Builder  │  ← Build internal blueprint model
└──────┬──────────┘
       │
┌──────▼──────────┐
│   Validator     │  ← Enforce dependency rules
└──────┬──────────┘
       │
┌──────▼──────────┐
│    Renderer     │  ← Render Jinja2 templates
│   (Jinja2)      │
└──────┬──────────┘
       │
┌──────▼──────────┐
│   Filesystem    │  ← Write Terraform files
└─────────────────┘
```

### Preset System Overview

- Built-in presets live under `iacgen.presets` as YAML files packaged with the library.
- The `iacgen create --preset <name>` command loads the preset and then applies CLI flags as overrides.
- CLI flags such as `--vpc`, `--eks`, `--alb`, existing-VPC options, and `--services` can refine or extend what the preset specifies.

#### Built-in Presets

| Preset       | Description                                                | Modules Enabled by Default                 |
|--------------|------------------------------------------------------------|--------------------------------------------|
| `microservice` | Opinionated microservice stack with API gateway and backend service, fronted by an internet-facing ALB. | VPC, EKS, ALB, Services (`api-gateway`, `backend-service`) |
| `simple-vpc` | Minimal networking footprint for experiments or shared VPC use. | VPC only                                   |
| `full-stack` | Production-style stack with frontend, API, and worker services behind an ALB. | VPC, EKS, ALB, Services (`frontend`, `api`, `worker`) |

### Planned Terraform Modules (v1)

| Module | Purpose | Dependencies |
|--------|---------|--------------|
| **VPC** | Public/private subnets, NAT gateways | None |
| **EKS** | Kubernetes cluster + node groups | Requires VPC |
| **Service** | Kubernetes deployment manifests | Requires EKS |
| **ALB** | Application Load Balancer | Requires Service(s) |

### Dependency Validation Rules

The validator enforces architectural constraints to ensure valid infrastructure:

```bash
# Invalid: EKS without any VPC (generated or existing)
iacgen create --eks
# Error: [EKS_REQUIRES_VPC] EKS module is enabled but no VPC is available

# Valid: EKS with generated VPC
iacgen create --vpc --eks

# Valid: EKS with existing VPC (no new VPC created)
iacgen create \
  --eks \
  --eks-use-existing-vpc \
  --eks-vpc-id vpc-1234567890abcdef0 \
  --eks-private-subnet-ids subnet-a1b2c3,subnet-d4e5f6

# Invalid: EKS with --eks-use-existing-vpc but missing details
iacgen create --eks --eks-use-existing-vpc
# Error: [EKS_EXISTING_VPC_DETAILS_REQUIRED] existing_vpc_id and/or existing_private_subnet_ids are missing

# Valid: EKS with VPC
iacgen create --vpc --eks

# Invalid: ALB without services
iacgen create --vpc --eks --alb
# Error: [ALB_REQUIRES_SERVICES] ALB module is enabled but no services are defined

# Valid: ALB with services
iacgen create --vpc --eks --services api --alb

# Invalid: Services without EKS
iacgen create --vpc --services api
# Error: [SERVICES_REQUIRE_EKS] Services defined (api) but EKS module is not enabled

# Invalid: No modules enabled
iacgen create
# Error: [NO_MODULES_ENABLED] No modules or services are enabled
```

**Validation Rules Implemented:**
1. **EKS_REQUIRES_VPC**: EKS module cannot be enabled without either a generated VPC or a fully-specified existing VPC
2. **EKS_EXISTING_VPC_DETAILS_REQUIRED**: When using an existing VPC, `existing_vpc_id` and `existing_private_subnet_ids` must be provided
3. **SERVICES_REQUIRE_EKS**: Services cannot be defined without EKS module
4. **ALB_REQUIRES_SERVICES**: ALB module requires at least one service
5. **NO_MODULES_ENABLED**: At least one module or service must be enabled

---

## Generated Output Structure

```
my-infra/
├── main.tf              # Root Terraform configuration (AWS + EKS + Kubernetes providers, module wiring)
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── blueprint.json       # Config for regeneration
└── modules/
    ├── vpc/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── eks/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── service/
    │   └── ... (per-service configs: one directory per service)
    └── alb/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## Use Cases

### 1. New Microservice Onboarding

**Before iacgen:**
```bash
# 2-3 hours of manual work
# - Copy existing service Terraform
# - Update variable names
# - Fix module references
# - Debug dependency issues
# - Submit PR for review
```

**With iacgen:**
```bash
# 30 seconds
iacgen create --preset microservice --services user-api --output ./user-api-infra
cd user-api-infra
terraform init && terraform plan
```

### 2. Platform Standardization

Enforce your organization's golden path:

```bash
# All teams use the same blessed configuration
iacgen create --preset company-standard --services $SERVICE_NAME
```

### 3. Multi-Environment Provisioning

```bash
# Development environment
iacgen create --preset dev --services api,worker --output ./dev

# Production environment
iacgen create --preset prod --services api,worker,scheduler --output ./prod
```

---

## Development

### Project Structure

```
iac-generator/
├── src/iacgen/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Module entry point
│   ├── cli.py               # Typer CLI commands
│   ├── exceptions.py        # Custom exception classes
│   ├── config.py            # Pydantic models
│   ├── validator.py         # Validation logic
│   ├── renderer.py          # Jinja2 rendering engine
│   ├── preset_loader.py     # YAML preset loading and merging
│   ├── presets/             # Built-in preset package (YAML files)
│   └── templates/           # Terraform templates (VPC, EKS, Service, ALB)
│       ├── main.tf.j2
│       ├── variables.tf.j2
│       ├── outputs.tf.j2
│       └── modules/
│           ├── vpc/
│           ├── eks/
│           ├── alb/
│           └── service/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_validator.py    # Validator tests (29 tests)
│   ├── test_renderer.py     # Renderer tests
│   └── test_presets.py      # Preset loader tests
├── .python-version          # Python version specification
├── pyproject.toml           # Package metadata
└── README.md                # This file
```

### Running Tests

```bash
# Run all tests
pytest

# Run only VPC template tests
pytest tests/test_vpc_templates.py

# Run only EKS template tests
pytest tests/test_eks_templates.py

# Run only ALB template tests
pytest tests/test_alb_templates.py

# Run with coverage
pytest --cov=iacgen --cov-report=term-missing

# Run specific test file
pytest tests/test_renderer.py
```

### Code Quality

```bash
# Linting (when configured)
ruff check .

# Formatting (when configured)
ruff format .

# Type checking (when configured)
mypy src/
```

---

## Roadmap

### Phase 1: Core Foundation (Week 1-2) - COMPLETE
- [x] CLI framework with Typer
- [x] Rich console integration for colored output
- [x] Package structure
- [x] Complete command interface (create, recreate, version)
- [x] All CLI flags and options
- [x] Custom exception hierarchy
- [x] Error handling with exit codes
- [x] Debug mode support
- [x] Blueprint.json persistence
- [x] Configuration models (Pydantic)
- [x] Validation engine

### Phase 2: Template Engine (Week 2-3) - COMPLETE
- [x] Jinja2 renderer implementation
- [x] Custom Terraform filters (terraform_list, terraform_map, terraform_bool)
- [x] Context building and template rendering
- [x] Filesystem generator
- [x] Unit tests for rendering

### Phase 3: Terraform Modules (Week 3-4) - IN PROGRESS
- [x] VPC module templates (including NAT gateway and AZ handling)
- [x] EKS module templates (IAM roles, node groups, existing VPC support)
- [x] Service module templates (namespace, Deployment, Service, autoscaling)
- [x] ALB module templates
- [x] Root template integration (main.tf, variables.tf, outputs.tf)
- [x] CLI integration with renderer

### Phase 4: Presets & Polish (Week 4-5)
- [x] Preset system (YAML-based, with built-in `microservice`, `simple-vpc`, and `full-stack` presets)
- [x] `microservice` preset
- [ ] Error message improvements
- [ ] Integration tests
- [ ] Documentation

### Phase 5: Release Preparation (Week 5-6)
- [x] PyPI packaging
- [x] CI/CD pipeline (GitHub Actions)
- [ ] Example projects
- [ ] Architecture diagrams
- [ ] v1.0.0 release

### Future Enhancements (Post-v1)
- [ ] Terraform Cloud integration
- [ ] GitOps PR generation
- [ ] AWS cost estimation
- [ ] Multi-cloud support (Azure, GCP)
- [ ] Policy-as-code integrations

---

## Success Metrics

Our v1.0 release will meet these criteria:

- Generate working Terraform blueprint in **< 30 seconds**  
- Output passes `terraform init && terraform plan`  
- Support **3+ core modules** (VPC, EKS, Service)  
- Correct dependency wiring validated  
- **90%+ test coverage** for template rendering

---

## Contributing

This project is in active development. Contributions welcome!

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support & Contact

- **Issues**: [GitHub Issues](https://github.com/JRcodes/iac-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/JRcodes/iac-generator/discussions)

---

## Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting and colors
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [pytest](https://pytest.org/) - Testing framework

---

**By Nana Appiah(Co-authored by WARP AI terminal. Tasks managed by taskmaster-ai)**

*Last updated: January 2026*
