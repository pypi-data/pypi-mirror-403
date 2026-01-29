"""Metricly CLI - Command-line interface for Metricly.

This package provides a terminal-based interface to Metricly's
metric query and dashboard capabilities.

Usage:
    metricly login          # Authenticate via Google OAuth
    metricly whoami         # Show current user and org
    metricly metrics list   # List available metrics
    metricly query -m revenue -g month  # Query metrics
"""

from .main import app

__all__ = ["app"]
