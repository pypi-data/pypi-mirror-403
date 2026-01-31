"""Centralized path configuration for nspec directories.

This module provides configurable paths for the nspec directory structure.
Instead of hardcoding paths like "10-feature-requests", "11-implementation",
and "12-completed" throughout the codebase, all code should use these
centralized path definitions.

Configuration priority (highest to lowest):
1. CLI arguments (--fr-dir, --impl-dir, etc.)
2. Environment variables (NSPEC_FR_DIR, NSPEC_IMPL_DIR, etc.)
3. nspec.toml file in project root
4. Built-in defaults

Default structure:
    docs/
    ├── {feature_requests_dir}/     # Active FR documents (default: 10-feature-requests)
    ├── {implementation_dir}/        # Active IMPL documents (default: 11-implementation)
    └── {completed_dir}/             # Completed work (default: 12-completed)
        ├── done/                    # Completed FRs and IMPLs
        ├── superseded/              # Superseded stories
        └── rejected/                # Rejected stories

Example nspec.toml:
    [paths]
    feature_requests = "10-feature-requests"
    implementation = "11-implementation"
    completed = "12-completed"
    completed_done = "done"
    completed_superseded = "superseded"
    completed_rejected = "rejected"
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# =============================================================================
# Default Directory Names (can be overridden via environment or config)
# =============================================================================

# Environment variable names for configuration
ENV_FR_DIR = "NSPEC_FR_DIR"
ENV_IMPL_DIR = "NSPEC_IMPL_DIR"
ENV_COMPLETED_DIR = "NSPEC_COMPLETED_DIR"
ENV_COMPLETED_DONE_SUBDIR = "NSPEC_COMPLETED_DONE_SUBDIR"
ENV_COMPLETED_SUPERSEDED_SUBDIR = "NSPEC_COMPLETED_SUPERSEDED_SUBDIR"
ENV_COMPLETED_REJECTED_SUBDIR = "NSPEC_COMPLETED_REJECTED_SUBDIR"

# Default directory names
DEFAULT_FR_DIR = "10-feature-requests"
DEFAULT_IMPL_DIR = "11-implementation"
DEFAULT_COMPLETED_DIR = "12-completed"
DEFAULT_COMPLETED_DONE_SUBDIR = "done"
DEFAULT_COMPLETED_SUPERSEDED_SUBDIR = "superseded"
DEFAULT_COMPLETED_REJECTED_SUBDIR = "rejected"


def _load_toml_config(project_root: Path | None = None) -> dict[str, Any]:
    """Load configuration from nspec.toml if it exists.

    Args:
        project_root: Project root directory to search for nspec.toml.
                      If None, searches from current directory upward.

    Returns:
        Dictionary with 'paths' section from nspec.toml, or empty dict if not found
    """
    if project_root is None:
        project_root = Path.cwd()

    # Search upward for nspec.toml (stop at git root or filesystem root)
    search_dir = project_root
    for _ in range(10):  # Limit search depth
        config_file = search_dir / "nspec.toml"
        if config_file.exists():
            try:
                import tomllib
            except ImportError:
                # Python < 3.11, try tomli
                try:
                    import tomli as tomllib  # type: ignore
                except ImportError:
                    # No TOML library available, skip file config
                    return {}

            try:
                with open(config_file, "rb") as f:
                    config = tomllib.load(f)
                    return config.get("paths", {})
            except Exception:
                # Failed to parse TOML, ignore and use defaults
                return {}

        # Stop at git root
        if (search_dir / ".git").exists():
            break

        # Move up one directory
        parent = search_dir.parent
        if parent == search_dir:  # Reached filesystem root
            break
        search_dir = parent

    return {}


def _get_config_value(
    key: str,
    env_var: str,
    default: str,
    toml_config: dict[str, Any] | None = None,
) -> str:
    """Get configuration value with priority: env var > TOML > default.

    Args:
        key: Key name in TOML config
        env_var: Environment variable name
        default: Default value if not found elsewhere
        toml_config: Loaded TOML configuration dict

    Returns:
        Configuration value from highest priority source
    """
    # Priority 1: Environment variable
    env_value = os.environ.get(env_var)
    if env_value is not None:
        return env_value

    # Priority 2: TOML config
    if toml_config and key in toml_config:
        return str(toml_config[key])

    # Priority 3: Default
    return default


@dataclass
class NspecPaths:
    """Configuration for nspec directory paths.

    This dataclass holds all the directory names used by the nspec system.
    It can be initialized with custom values or will use defaults from:
    1. Environment variables (highest priority after explicit values)
    2. nspec.toml file
    3. Built-in defaults

    Usage:
        # Use defaults (loads from nspec.toml if exists, then env vars, then defaults)
        paths = NspecPaths.from_config()

        # Use custom paths (CLI override)
        paths = NspecPaths(
            feature_requests_dir="feature-specs",
            implementation_dir="impl-plans",
        )

        # Get absolute paths relative to docs_root
        resolved = paths.resolve(docs_root=Path("docs"))
    """

    # Directory names (not full paths)
    feature_requests_dir: str
    implementation_dir: str
    completed_dir: str
    completed_done_subdir: str
    completed_superseded_subdir: str
    completed_rejected_subdir: str

    @classmethod
    def from_config(cls, project_root: Path | None = None) -> "NspecPaths":
        """Create NspecPaths from configuration sources.

        Loads configuration with priority:
        1. Environment variables
        2. nspec.toml file
        3. Built-in defaults

        Args:
            project_root: Project root to search for nspec.toml.
                         If None, searches from current directory.

        Returns:
            NspecPaths with configuration loaded from available sources
        """
        toml_config = _load_toml_config(project_root)

        return cls(
            feature_requests_dir=_get_config_value(
                "feature_requests", ENV_FR_DIR, DEFAULT_FR_DIR, toml_config
            ),
            implementation_dir=_get_config_value(
                "implementation", ENV_IMPL_DIR, DEFAULT_IMPL_DIR, toml_config
            ),
            completed_dir=_get_config_value(
                "completed", ENV_COMPLETED_DIR, DEFAULT_COMPLETED_DIR, toml_config
            ),
            completed_done_subdir=_get_config_value(
                "completed_done",
                ENV_COMPLETED_DONE_SUBDIR,
                DEFAULT_COMPLETED_DONE_SUBDIR,
                toml_config,
            ),
            completed_superseded_subdir=_get_config_value(
                "completed_superseded",
                ENV_COMPLETED_SUPERSEDED_SUBDIR,
                DEFAULT_COMPLETED_SUPERSEDED_SUBDIR,
                toml_config,
            ),
            completed_rejected_subdir=_get_config_value(
                "completed_rejected",
                ENV_COMPLETED_REJECTED_SUBDIR,
                DEFAULT_COMPLETED_REJECTED_SUBDIR,
                toml_config,
            ),
        )

    def resolve(self, docs_root: Path) -> "ResolvedPaths":
        """Resolve directory names to absolute paths relative to docs_root.

        Args:
            docs_root: The root docs directory (e.g., Path("docs"))

        Returns:
            ResolvedPaths with all paths resolved relative to docs_root
        """
        completed_base = docs_root / self.completed_dir
        return ResolvedPaths(
            docs_root=docs_root,
            feature_requests=docs_root / self.feature_requests_dir,
            implementation=docs_root / self.implementation_dir,
            completed=completed_base,
            completed_done=completed_base / self.completed_done_subdir,
            completed_superseded=completed_base / self.completed_superseded_subdir,
            completed_rejected=completed_base / self.completed_rejected_subdir,
            config=self,
        )


@dataclass
class ResolvedPaths:
    """Resolved absolute paths for nspec directories.

    This is the primary interface for accessing nspec paths throughout
    the codebase. Get an instance via NspecPaths.resolve(docs_root).

    Attributes:
        docs_root: The root docs directory
        feature_requests: Directory for active FR documents
        implementation: Directory for active IMPL documents
        completed: Base directory for completed work
        completed_done: Subdirectory for completed stories
        completed_superseded: Subdirectory for superseded stories
        completed_rejected: Subdirectory for rejected stories
        config: The NspecPaths configuration used to create this
    """

    docs_root: Path
    feature_requests: Path
    implementation: Path
    completed: Path
    completed_done: Path
    completed_superseded: Path
    completed_rejected: Path
    config: NspecPaths

    # Aliases for backward compatibility and clarity
    @property
    def active_frs_dir(self) -> Path:
        """Alias for feature_requests (active FR directory)."""
        return self.feature_requests

    @property
    def active_impls_dir(self) -> Path:
        """Alias for implementation (active IMPL directory)."""
        return self.implementation

    @property
    def completed_frs_dir(self) -> Path:
        """Alias for completed_done (completed FR/IMPL directory)."""
        return self.completed_done

    @property
    def completed_impls_dir(self) -> Path:
        """Alias for completed_done (completed FR/IMPL are co-located)."""
        return self.completed_done

    @property
    def superseded_dir(self) -> Path:
        """Alias for completed_superseded."""
        return self.completed_superseded

    @property
    def rejected_dir(self) -> Path:
        """Alias for completed_rejected."""
        return self.completed_rejected


# =============================================================================
# Convenience Functions
# =============================================================================

# Module-level default configuration (can be replaced for testing)
_default_config: NspecPaths | None = None


def get_default_config(project_root: Path | None = None) -> NspecPaths:
    """Get the default NspecPaths configuration.

    This returns a singleton configuration that reads from:
    1. nspec.toml file (if exists)
    2. Environment variables
    3. Built-in defaults

    The configuration can be replaced via set_default_config() for testing.

    Args:
        project_root: Project root to search for nspec.toml.
                     If None, searches from current directory.

    Returns:
        NspecPaths with configuration loaded from available sources
    """
    global _default_config
    if _default_config is None:
        _default_config = NspecPaths.from_config(project_root)
    return _default_config


def set_default_config(config: NspecPaths | None) -> None:
    """Set the default NspecPaths configuration.

    Primarily used for testing to override the default paths.

    Args:
        config: New default configuration, or None to reset to defaults
    """
    global _default_config
    _default_config = config


def get_paths(
    docs_root: Path,
    config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> ResolvedPaths:
    """Get resolved paths for a docs root directory.

    This is the primary entry point for getting nspec paths throughout
    the codebase. It handles configuration loading and path resolution.

    Configuration priority:
    1. Explicit config parameter (if provided)
    2. Environment variables
    3. nspec.toml file
    4. Built-in defaults

    Args:
        docs_root: The root docs directory (e.g., Path("docs"))
        config: Optional custom configuration. If None, loads from sources.
        project_root: Project root for finding nspec.toml. If None, uses cwd.

    Returns:
        ResolvedPaths with all paths resolved relative to docs_root

    Example:
        # Load from nspec.toml (if exists) + env vars + defaults
        paths = get_paths(Path("docs"))
        fr_dir = paths.feature_requests  # Path("docs/10-feature-requests")
        impl_dir = paths.implementation  # Path("docs/11-implementation")

        # Override with custom config
        custom_config = NspecPaths(feature_requests_dir="specs")
        paths = get_paths(Path("docs"), config=custom_config)
    """
    if project_root is None:
        # Prefer the docs_root's parent (project root) over CWD to avoid
        # accidentally reading nspec.toml from whatever directory the process
        # happens to be launched in.
        project_root = docs_root.parent

    if config is None:
        config = get_default_config(project_root)
    return config.resolve(docs_root)


def reset_default_config() -> None:
    """Reset the default configuration to None (will be recreated on next access).

    Useful in tests to ensure environment variable changes are picked up.
    """
    global _default_config
    _default_config = None
