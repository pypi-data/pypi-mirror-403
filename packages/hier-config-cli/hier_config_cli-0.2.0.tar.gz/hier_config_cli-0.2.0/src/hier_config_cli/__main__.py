"""Hier Config CLI Tool - A command-line interface for network configuration analysis."""

import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import click
import yaml
from hier_config import HConfig, Platform, WorkflowRemediation, get_hconfig
from hier_config.utils import read_text_from_file

F = TypeVar("F", bound=Callable[..., Any])

__version__ = "0.2.0"

# Mapping for driver platforms - includes all hier-config supported platforms
PLATFORM_MAP = {
    "ios": Platform.CISCO_IOS,
    "nxos": Platform.CISCO_NXOS,
    "iosxr": Platform.CISCO_XR,
    "eos": Platform.ARISTA_EOS,
    "junos": Platform.JUNIPER_JUNOS,
    "vyos": Platform.VYOS,
    "fortios": Platform.FORTINET_FORTIOS,
    "generic": Platform.GENERIC,
    "hp_comware5": Platform.HP_COMWARE5,
    "hp_procurve": Platform.HP_PROCURVE,
}

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(verbose: int) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
    """
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def get_output_text(hconfig: HConfig, platform: Platform) -> str:
    """Get text output from HConfig based on platform.

    Args:
        hconfig: The hierarchical configuration object
        platform: The platform type

    Returns:
        Formatted configuration text appropriate for the platform
    """
    lines = []
    for line in hconfig.all_children_sorted():
        # Use platform-appropriate text formatting
        if platform in (Platform.JUNIPER_JUNOS,):
            # Juniper uses curly braces and different syntax
            lines.append(line.text)
        else:
            # Cisco-style platforms (IOS, NXOS, XR, EOS, etc.)
            lines.append(line.cisco_style_text())
    return "\n".join(lines)


def format_output(hconfig: HConfig, platform: Platform, output_format: str) -> str:
    """Format configuration output in the requested format.

    Args:
        hconfig: The hierarchical configuration object
        platform: The platform type
        output_format: Output format (text, json, yaml)

    Returns:
        Formatted output string

    Raises:
        ValueError: If output format is not supported
    """
    if output_format == "text":
        return get_output_text(hconfig, platform)
    elif output_format == "json":
        config_dict = {"config": get_output_text(hconfig, platform).split("\n")}
        return json.dumps(config_dict, indent=2)
    elif output_format == "yaml":
        config_dict = {"config": get_output_text(hconfig, platform).split("\n")}
        return yaml.dump(config_dict, default_flow_style=False)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def process_configs(
    platform_str: str,
    running_config_path: str,
    generated_config_path: str,
    operation: str,
) -> tuple[HConfig, Platform]:
    """Process configuration files and return the result.

    Args:
        platform_str: Platform name string
        running_config_path: Path to running configuration
        generated_config_path: Path to generated configuration
        operation: Operation type (remediation, rollback, future)

    Returns:
        Tuple of (result HConfig, Platform enum)

    Raises:
        click.ClickException: If processing fails
    """
    try:
        platform_enum = PLATFORM_MAP[platform_str.lower()]
        logger.info(f"Using platform: {platform_str}")
    except KeyError:
        raise click.ClickException(
            f"Unknown platform: {platform_str}. "
            f"Use 'list-platforms' to see available platforms."
        ) from None

    try:
        logger.info(f"Reading running config from: {running_config_path}")
        running_config_text = read_text_from_file(running_config_path)
    except FileNotFoundError:
        raise click.ClickException(
            f"Running config file not found: {running_config_path}"
        ) from None
    except PermissionError:
        raise click.ClickException(
            f"Permission denied reading running config: {running_config_path}"
        ) from None
    except Exception as e:
        raise click.ClickException(f"Error reading running config: {e}") from e

    try:
        logger.info(f"Reading generated config from: {generated_config_path}")
        generated_config_text = read_text_from_file(generated_config_path)
    except FileNotFoundError:
        raise click.ClickException(
            f"Generated config file not found: {generated_config_path}"
        ) from None
    except PermissionError:
        raise click.ClickException(
            f"Permission denied reading generated config: {generated_config_path}"
        ) from None
    except Exception as e:
        raise click.ClickException(f"Error reading generated config: {e}") from e

    try:
        logger.info("Parsing configurations")
        running_hconfig = get_hconfig(platform_enum, running_config_text)
        generated_hconfig = get_hconfig(platform_enum, generated_config_text)
    except Exception as e:
        raise click.ClickException(f"Error parsing configuration: {e}") from e

    try:
        logger.info(f"Generating {operation} configuration")
        if operation == "future":
            result = running_hconfig.future(generated_hconfig)
        else:
            workflow = WorkflowRemediation(running_hconfig, generated_hconfig)
            result = (
                workflow.remediation_config
                if operation == "remediation"
                else workflow.rollback_config
            )
    except Exception as e:
        raise click.ClickException(f"Error generating {operation}: {e}") from e

    return result, platform_enum


@click.group()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (use -v for INFO, -vv for DEBUG)",
)
@click.pass_context
def cli(ctx: click.Context, verbose: int) -> None:
    """Hier Config CLI Tool - Network configuration analysis and remediation.

    This tool provides commands to analyze network device configurations,
    generate remediation steps, rollback configurations, and predict future states.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


def common_options(func: F) -> F:
    """Reusable options for platform, running config, and generated config."""
    func = click.option(
        "--platform",
        type=click.Choice(list(PLATFORM_MAP.keys()), case_sensitive=False),
        required=True,
        help="Platform driver to use (e.g., ios, nxos, iosxr, eos, junos, vyos, fortios, generic).",
    )(func)
    func = click.option(
        "--running-config",
        type=click.Path(exists=True, readable=True),
        required=True,
        help="Path to the running configuration file.",
    )(func)
    func = click.option(
        "--generated-config",
        type=click.Path(exists=True, readable=True),
        required=True,
        help="Path to the generated (intended) configuration file.",
    )(func)
    func = click.option(
        "--format",
        "output_format",
        type=click.Choice(["text", "json", "yaml"], case_sensitive=False),
        default="text",
        help="Output format (default: text).",
    )(func)
    func = click.option(
        "--output",
        "-o",
        "output_file",
        type=click.Path(),
        default=None,
        help="Write output to file instead of stdout.",
    )(func)
    return func


@cli.command()
@common_options
def remediation(
    platform: str,
    running_config: str,
    generated_config: str,
    output_format: str,
    output_file: str | None,
) -> None:
    """Generate the remediation configuration.

    Compares the running configuration with the generated (intended) configuration
    and produces the commands needed to transform the running config into the
    generated config.

    Example:
        hier-config-cli remediation --platform ios \\
            --running-config running.conf --generated-config intended.conf
    """
    result, platform_enum = process_configs(
        platform, running_config, generated_config, "remediation"
    )

    try:
        output = format_output(result, platform_enum, output_format)
    except ValueError as e:
        raise click.ClickException(str(e)) from e

    if output_file:
        try:
            Path(output_file).write_text(output)
            click.echo(f"Remediation configuration written to: {output_file}", err=True)
        except Exception as e:
            raise click.ClickException(f"Error writing output file: {e}") from e
    else:
        click.echo("\n=== Remediation Configuration ===")
        click.echo(output)


@cli.command()
@common_options
def rollback(
    platform: str,
    running_config: str,
    generated_config: str,
    output_format: str,
    output_file: str | None,
) -> None:
    """Generate the rollback configuration.

    Produces the commands needed to revert from the generated configuration
    back to the running configuration. This is useful for preparing rollback
    procedures before making changes.

    Example:
        hier-config-cli rollback --platform ios \\
            --running-config running.conf --generated-config intended.conf
    """
    result, platform_enum = process_configs(platform, running_config, generated_config, "rollback")

    try:
        output = format_output(result, platform_enum, output_format)
    except ValueError as e:
        raise click.ClickException(str(e)) from e

    if output_file:
        try:
            Path(output_file).write_text(output)
            click.echo(f"Rollback configuration written to: {output_file}", err=True)
        except Exception as e:
            raise click.ClickException(f"Error writing output file: {e}") from e
    else:
        click.echo("\n=== Rollback Configuration ===")
        click.echo(output)


@cli.command()
@common_options
def future(
    platform: str,
    running_config: str,
    generated_config: str,
    output_format: str,
    output_file: str | None,
) -> None:
    """Generate the future configuration.

    Predicts what the complete configuration will look like after applying
    the generated configuration to the running configuration.

    Example:
        hier-config-cli future --platform ios \\
            --running-config running.conf --generated-config intended.conf
    """
    result, platform_enum = process_configs(platform, running_config, generated_config, "future")

    try:
        output = format_output(result, platform_enum, output_format)
    except ValueError as e:
        raise click.ClickException(str(e)) from e

    if output_file:
        try:
            Path(output_file).write_text(output)
            click.echo(f"Future configuration written to: {output_file}", err=True)
        except Exception as e:
            raise click.ClickException(f"Error writing output file: {e}") from e
    else:
        click.echo("\n=== Future Configuration ===")
        click.echo(output)


@cli.command()
def list_platforms() -> None:
    """List all available platforms.

    Shows all supported network device platforms that can be used
    with the --platform option.
    """
    click.echo("\n=== Available Platforms ===")
    for platform in sorted(PLATFORM_MAP.keys()):
        click.echo(f"  {platform}")
    click.echo()


@cli.command()
def version() -> None:
    """Show the version and exit."""
    click.echo(f"hier-config-cli version {__version__}")


if __name__ == "__main__":
    cli()
