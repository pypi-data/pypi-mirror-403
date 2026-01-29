"""Feature flags for controlling experimental functionality."""

import os
from enum import Enum


class FeatureFlag(str, Enum):
    """Available feature flags."""

    SONARQUBE_INTEGRATION = "MESSIRVE_FF_SONARQUBE"
    ADVANCED_ANALYSIS = "MESSIRVE_FF_ADVANCED_ANALYSIS"
    PARALLEL_EXECUTION = "MESSIRVE_FF_PARALLEL"
    SHADOW_LOGIC = "MESSIRVE_FF_SHADOW"
    COUPLING_ANALYSIS = "MESSIRVE_FF_COUPLING"


class FeatureFlags:
    """Feature flag manager for controlling experimental features.

    Feature flags can be enabled via environment variables or programmatically
    using the enable/disable methods.

    Example:
        # Via environment variable
        MESSIRVE_FF_SONARQUBE=true messirve run tasks.yaml

        # Programmatically
        FeatureFlags.enable(FeatureFlag.SONARQUBE_INTEGRATION)
        if FeatureFlags.is_enabled(FeatureFlag.SONARQUBE_INTEGRATION):
            run_sonarqube_analysis()
    """

    _overrides: dict[str, bool] = {}

    @classmethod
    def is_enabled(cls, flag: FeatureFlag) -> bool:
        """Check if a feature flag is enabled.

        Checks programmatic overrides first, then environment variables.

        Args:
            flag: The feature flag to check.

        Returns:
            True if the flag is enabled, False otherwise.
        """
        if flag.value in cls._overrides:
            return cls._overrides[flag.value]
        return os.environ.get(flag.value, "").lower() in ("1", "true", "yes")

    @classmethod
    def enable(cls, flag: FeatureFlag) -> None:
        """Enable a feature flag programmatically.

        Args:
            flag: The feature flag to enable.
        """
        cls._overrides[flag.value] = True

    @classmethod
    def disable(cls, flag: FeatureFlag) -> None:
        """Disable a feature flag programmatically.

        Args:
            flag: The feature flag to disable.
        """
        cls._overrides[flag.value] = False

    @classmethod
    def reset(cls) -> None:
        """Reset all programmatic overrides.

        After calling this, flags will only be controlled by environment variables.
        """
        cls._overrides.clear()

    @classmethod
    def get_enabled_flags(cls) -> list[FeatureFlag]:
        """Get a list of all enabled feature flags.

        Returns:
            List of enabled FeatureFlag values.
        """
        return [flag for flag in FeatureFlag if cls.is_enabled(flag)]
