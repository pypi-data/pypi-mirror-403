"""Hier Config CLI - A command-line interface for network configuration analysis.

This package provides a CLI tool for analyzing network device configurations,
generating remediation steps, rollback configurations, and predicting future states.
"""

from hier_config_cli.__main__ import __version__, cli

__all__ = ["cli", "__version__"]
