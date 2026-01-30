"""
Configuration utilities for Revenium middleware.

This module provides configuration helpers for middleware behavior,
including selective metering control.
"""

import os


def is_selective_metering_enabled() -> bool:
    """
    Check if selective metering is enabled.

    When enabled, only functions decorated with @revenium_meter will be metered.
    When disabled (default), all API calls are metered automatically.

    The setting is controlled by the REVENIUM_SELECTIVE_METERING environment variable.
    Accepted values for enabled: "true", "1", "yes", "on" (case-insensitive)

    Returns:
        True if selective metering is enabled, False otherwise

    Example:
        # Enable selective metering
        export REVENIUM_SELECTIVE_METERING=true

        # Check in code
        if is_selective_metering_enabled():
            # Only meter decorated functions
            pass
    """
    env_value = os.environ.get("REVENIUM_SELECTIVE_METERING", "false").lower()
    return env_value in ("true", "1", "yes", "on")

