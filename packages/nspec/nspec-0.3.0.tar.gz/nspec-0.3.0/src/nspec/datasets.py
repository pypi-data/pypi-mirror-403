"""Dataset architecture for fRIMPL validation - Layer 2.

This module provides the four-dataset architecture that separates:
    - Active FRs (configurable, default: docs/10-feature-requests/)
    - Active IMPLs (configurable, default: docs/11-implementation/)
    - Completed FRs (configurable, default: docs/12-completed/done/)
    - Completed IMPLs (configurable, default: docs/12-completed/done/)

Directory paths are configurable via nspec.toml, environment variables,
or programmatically. See nspec.paths module for configuration details.

Each dataset is loaded with strict validation (Layer 1) before being
made available for cross-document validation (Layers 3-6).

Architecture:
    NspecDatasets - Container for all four datasets
    DatasetLoader - Loads and validates all documents
"""

from dataclasses import dataclass
from pathlib import Path

from nspec.paths import NspecPaths, get_paths
from nspec.validators import (
    FRMetadata,
    FRValidator,
    IMPLMetadata,
    IMPLValidator,
)


@dataclass
class NspecDatasets:
    """Four datasets representing complete fRIMPL state.

    This separates active work (in progress) from completed work,
    and separates feature specs (FR) from implementation plans (IMPL).

    Design rationale:
        - Active vs Completed: Different validation rules apply
        - FR vs IMPL: Different document types, different purposes
        - Clean separation enables efficient querying and validation
    """

    active_frs: dict[str, FRMetadata]  # Story ID → FR metadata
    active_impls: dict[str, IMPLMetadata]  # Story ID → IMPL metadata
    completed_frs: dict[str, FRMetadata]  # Story ID → FR metadata
    completed_impls: dict[str, IMPLMetadata]  # Story ID → IMPL metadata

    def all_story_ids(self) -> set[str]:
        """Get all story IDs across all datasets.

        Returns:
            Set of story IDs (both active and completed)
        """
        return set(self.active_frs.keys()) | set(self.completed_frs.keys())

    def get_fr(self, story_id: str) -> FRMetadata | None:
        """Get FR from active or completed datasets.

        Args:
            story_id: Story ID like "001" or "060a"

        Returns:
            FRMetadata if found, None otherwise
        """
        return self.active_frs.get(story_id) or self.completed_frs.get(story_id)

    def get_impl(self, story_id: str) -> IMPLMetadata | None:
        """Get IMPL from active or completed datasets.

        Args:
            story_id: Story ID like "001" or "060a"

        Returns:
            IMPLMetadata if found, None otherwise
        """
        return self.active_impls.get(story_id) or self.completed_impls.get(story_id)

    def is_active(self, story_id: str) -> bool:
        """Check if story is in active datasets.

        Args:
            story_id: Story ID to check

        Returns:
            True if FR is in active_frs
        """
        return story_id in self.active_frs

    def is_completed(self, story_id: str) -> bool:
        """Check if story is in completed datasets.

        Args:
            story_id: Story ID to check

        Returns:
            True if FR is in completed_frs
        """
        return story_id in self.completed_frs

    def active_story_count(self) -> int:
        """Count of active stories."""
        return len(self.active_frs)

    def completed_story_count(self) -> int:
        """Count of completed stories."""
        return len(self.completed_frs)

    def total_story_count(self) -> int:
        """Total count of all stories."""
        return len(self.all_story_ids())

    def get_active_stories(self) -> list[tuple[FRMetadata, IMPLMetadata | None]]:
        """Get all active stories with their FR and IMPL.

        Returns:
            List of (FR, IMPL) tuples, sorted by story ID
        """
        stories = []
        for story_id, fr in sorted(self.active_frs.items()):
            impl = self.active_impls.get(story_id)
            stories.append((fr, impl))
        return stories

    def get_completed_stories(self) -> list[tuple[FRMetadata, IMPLMetadata | None]]:
        """Get all completed stories with their FR and IMPL.

        Returns:
            List of (FR, IMPL) tuples, sorted by story ID
        """
        stories = []
        for story_id, fr in sorted(self.completed_frs.items()):
            impl = self.completed_impls.get(story_id)
            stories.append((fr, impl))
        return stories

    def calculate_loe_rollups(self) -> None:
        """Calculate LOE rollups from dependencies for all active stories.

        For each story with dependencies:
        - calculated_loe_parallel = max of all dep sequential LOEs (longest dep)
        - calculated_loe_sequential = sum of all active dep sequential LOEs
        - effective_loe = calculated value if has deps, else manual value

        This modifies IMPLMetadata objects in place.
        """
        from .validators import _format_hours_to_loe

        for story_id, fr in self.active_frs.items():
            impl = self.active_impls.get(story_id)
            if not impl or not fr.deps:
                continue

            # Calculate from active (non-completed) dependencies only
            dep_parallel_total = 0  # Max of deps (parallel execution)
            dep_sequential_total = 0  # Sum of deps (sequential execution)

            for dep_id in fr.deps:
                # Skip completed dependencies - they don't add to remaining work
                if dep_id in self.completed_impls:
                    continue
                if dep_id in self.active_impls:
                    dep_impl = self.active_impls[dep_id]
                    # Use effective_loe_hours which may itself be calculated
                    dep_hours = dep_impl.effective_loe_hours
                    dep_parallel_total = max(dep_parallel_total, dep_hours)
                    dep_sequential_total += dep_hours

            # Store calculated values
            impl.calculated_loe_parallel = dep_parallel_total if dep_parallel_total > 0 else None
            impl.calculated_loe_sequential = (
                dep_sequential_total if dep_sequential_total > 0 else None
            )

            # Set effective LOE: use calculated if deps exist and have LOE, else manual
            if dep_sequential_total > 0:
                is_epic = fr.priority.startswith("E")
                if is_epic:
                    # Epics show parallel,sequential format
                    par_str = _format_hours_to_loe(dep_parallel_total)
                    seq_str = _format_hours_to_loe(dep_sequential_total)
                    impl.effective_loe = f"{par_str},{seq_str}"
                    impl.effective_loe_hours = dep_sequential_total
                else:
                    # Regular stories use sequential (sum of deps)
                    impl.effective_loe = _format_hours_to_loe(dep_sequential_total)
                    impl.effective_loe_hours = dep_sequential_total


class DatasetLoader:
    """Load and validate all four fRIMPL datasets.

    This class orchestrates Layer 1 validation (format checking) while
    loading documents into the four datasets. Any format violations
    cause immediate failure - no silent fixes.

    Usage:
        loader = DatasetLoader(docs_root=Path("docs"))
        datasets = loader.load()  # Raises ValueError on any invalid document
    """

    def __init__(
        self,
        docs_root: Path | None = None,
        active_frs_dir: Path | None = None,
        active_impls_dir: Path | None = None,
        completed_frs_dir: Path | None = None,
        completed_impls_dir: Path | None = None,
        paths_config: NspecPaths | None = None,
        project_root: Path | None = None,
    ):
        """Initialize dataset loader.

        Can be initialized in three ways:

        1. Standard mode (production with configuration):
            DatasetLoader(docs_root=Path("docs"))
            Loads paths from nspec.toml (if exists), environment variables,
            or built-in defaults. Directory structure is configurable.

        2. Custom mode (testing with explicit paths):
            DatasetLoader(
                active_frs_dir=Path("tests/nspec/test_case/active-fr"),
                active_impls_dir=Path("tests/nspec/test_case/active-impl"),
                ...
            )
            Allows arbitrary directory paths for black-box testing.

        3. Custom configuration mode:
            DatasetLoader(
                docs_root=Path("docs"),
                paths_config=NspecPaths(feature_requests_dir="specs", ...)
            )
            Uses custom path configuration instead of loading from file/env.

        Args:
            docs_root: Root docs directory (standard mode)
            active_frs_dir: Custom active FR directory (testing mode)
            active_impls_dir: Custom active IMPL directory (testing mode)
            completed_frs_dir: Custom completed FR directory (testing mode)
            completed_impls_dir: Custom completed IMPL directory (testing mode)
            paths_config: Custom paths configuration (overrides file/env config)
            project_root: Project root for finding nspec.toml (default: cwd)
        """
        if docs_root:
            # Standard mode - use configuration system
            paths = get_paths(docs_root, config=paths_config, project_root=project_root)
            self.active_frs_dir = paths.active_frs_dir
            self.active_impls_dir = paths.active_impls_dir
            self.completed_frs_dir = paths.completed_frs_dir
            self.completed_impls_dir = paths.completed_impls_dir
            self.superseded_dir = paths.superseded_dir
        else:
            # Custom mode (testing) - use explicitly provided paths
            self.active_frs_dir = active_frs_dir
            self.active_impls_dir = active_impls_dir
            self.completed_frs_dir = completed_frs_dir
            self.completed_impls_dir = completed_impls_dir
            self.superseded_dir = None

        self.fr_validator = FRValidator()
        self.impl_validator = IMPLValidator()

    def load(self) -> NspecDatasets:
        """Load all datasets with strict validation.

        This is Layer 2 validation - each document goes through
        Layer 1 (format validation) before being added to datasets.

        Returns:
            NspecDatasets with all four datasets populated

        Raises:
            ValueError: If any document fails validation
        """
        active_frs = (
            self._load_frs(self.active_frs_dir, require_completed=False)
            if self.active_frs_dir
            else {}
        )
        active_impls = (
            self._load_impls(self.active_impls_dir, require_completed=False)
            if self.active_impls_dir
            else {}
        )
        completed_frs = (
            self._load_frs(self.completed_frs_dir, require_completed=True)
            if self.completed_frs_dir
            else {}
        )
        completed_impls = (
            self._load_impls(self.completed_impls_dir, require_completed=True)
            if self.completed_impls_dir
            else {}
        )

        # Also load superseded stories - they count as "completed" for dependency purposes
        if self.superseded_dir and self.superseded_dir.exists():
            superseded_frs = self._load_frs(
                self.superseded_dir, require_completed=False, allow_superseded=True
            )
            superseded_impls = self._load_impls(
                self.superseded_dir, require_completed=False, allow_superseded=True
            )
            completed_frs.update(superseded_frs)
            completed_impls.update(superseded_impls)

        datasets = NspecDatasets(
            active_frs=active_frs,
            active_impls=active_impls,
            completed_frs=completed_frs,
            completed_impls=completed_impls,
        )

        # Calculate LOE rollups from dependencies (must be done after all loading)
        datasets.calculate_loe_rollups()

        return datasets

    def _load_frs(
        self,
        directory: Path,
        require_completed: bool = False,
        allow_superseded: bool = False,
    ) -> dict[str, FRMetadata]:
        """Load and validate all FRs in directory.

        Args:
            directory: Directory containing FR-*.md files
            require_completed: If True, enforce all FRs have ✅ Completed status
            allow_superseded: If True, allow 🔄 Superseded status as valid

        Returns:
            Dict mapping story ID to FRMetadata

        Raises:
            ValueError: If any FR fails validation
        """
        if not directory or not directory.exists():
            return {}

        frs = {}
        for path in directory.glob("FR-*.md"):
            # Skip template files
            if "TEMPLATE" in path.stem.upper():
                continue

            try:
                content = path.read_text()
                metadata = self.fr_validator.validate(
                    path,
                    content,
                    require_completed=require_completed,
                    allow_superseded=allow_superseded,
                )
                # Check for duplicate story IDs (same ID, different slug)
                if metadata.story_id in frs:
                    existing = frs[metadata.story_id]
                    raise ValueError(
                        f"Duplicate story ID {metadata.story_id} detected:\n"
                        f"  - {existing.path.name}\n"
                        f"  - {path.name}\n"
                        f"Each story ID must be unique. Delete one or renumber."
                    )
                frs[metadata.story_id] = metadata
            except ValueError as e:
                # Add context about which file failed
                raise ValueError(
                    f"Failed to load FR from {path.relative_to(directory.parent)}:\n{e}"
                ) from None

        return frs

    def _load_impls(
        self,
        directory: Path,
        require_completed: bool = False,
        allow_superseded: bool = False,
    ) -> dict[str, IMPLMetadata]:
        """Load and validate all IMPLs in directory.

        Args:
            directory: Directory containing IMPL-*.md files
            require_completed: If True, enforce all IMPLs have ✅ Complete status
            allow_superseded: If True, allow ⚪ Hold status as valid (used for superseded)

        Returns:
            Dict mapping story ID to IMPLMetadata

        Raises:
            ValueError: If any IMPL fails validation
        """
        if not directory or not directory.exists():
            return {}

        impls = {}
        for path in directory.glob("IMPL-*.md"):
            # Skip template files
            if "TEMPLATE" in path.stem.upper():
                continue

            try:
                content = path.read_text()
                metadata = self.impl_validator.validate(
                    path,
                    content,
                    require_completed=require_completed,
                    allow_superseded=allow_superseded,
                )
                # Check for duplicate story IDs (same ID, different slug)
                if metadata.story_id in impls:
                    existing = impls[metadata.story_id]
                    raise ValueError(
                        f"Duplicate story ID {metadata.story_id} detected:\n"
                        f"  - {existing.path.name}\n"
                        f"  - {path.name}\n"
                        f"Each story ID must be unique. Delete one or renumber."
                    )
                impls[metadata.story_id] = metadata
            except ValueError as e:
                # Add context about which file failed
                raise ValueError(
                    f"Failed to load IMPL from {path.relative_to(directory.parent)}:\n{e}"
                ) from None

        return impls


class DatasetStats:
    """Compute statistics across datasets.

    Useful for reporting and dashboard generation.
    """

    def __init__(self, datasets: NspecDatasets):
        """Initialize with datasets."""
        self.datasets = datasets

    def priority_breakdown(self) -> dict[str, int]:
        """Count active stories by priority.

        Returns:
            Dict like {"P0": 3, "P1": 15, "P2": 25, "P3": 5}
        """
        breakdown = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for fr in self.datasets.active_frs.values():
            breakdown[fr.priority] += 1
        return breakdown

    def status_breakdown(self) -> dict[str, int]:
        """Count active stories by status.

        Returns:
            Dict like {"🟡 Proposed": 20, "🟢 In Progress": 15, ...}
        """
        breakdown: dict[str, int] = {}
        for fr in self.datasets.active_frs.values():
            breakdown[fr.status] = breakdown.get(fr.status, 0) + 1
        return breakdown

    def overall_progress(self) -> dict[str, float]:
        """Calculate overall progress across all active stories.

        Returns:
            Dict with:
                - ac_completion: Average AC completion %
                - task_completion: Average task completion %
                - overall_completion: Combined average
        """
        if not self.datasets.active_frs:
            return {
                "ac_completion": 0.0,
                "task_completion": 0.0,
                "overall_completion": 0.0,
            }

        total_ac_completion = 0
        total_task_completion = 0
        story_count = 0

        for story_id, fr in self.datasets.active_frs.items():
            impl = self.datasets.active_impls.get(story_id)

            total_ac_completion += fr.ac_completion_percent
            total_task_completion += impl.completion_percent if impl else 0
            story_count += 1

        ac_avg = total_ac_completion / story_count if story_count > 0 else 0
        task_avg = total_task_completion / story_count if story_count > 0 else 0
        overall_avg = (ac_avg + task_avg) / 2

        return {
            "ac_completion": round(ac_avg, 1),
            "task_completion": round(task_avg, 1),
            "overall_completion": round(overall_avg, 1),
        }

    def dependency_graph(self) -> dict[str, list[str]]:
        """Build dependency graph for active stories.

        Returns:
            Dict mapping story ID to list of dependency IDs
        """
        graph = {}
        for story_id, fr in self.datasets.active_frs.items():
            graph[story_id] = fr.deps
        return graph

    def stories_without_progress(self) -> list[str]:
        """Find active stories with 0% completion (no AC or tasks done).

        Returns:
            List of story IDs
        """
        zero_progress = []
        for story_id, fr in self.datasets.active_frs.items():
            impl = self.datasets.active_impls.get(story_id)

            ac_done = fr.ac_completion_percent == 0
            tasks_done = (impl.completion_percent == 0) if impl else True

            if ac_done and tasks_done:
                zero_progress.append(story_id)

        return sorted(zero_progress)

    def stories_near_completion(self, threshold: int = 80) -> list[str]:
        """Find active stories near completion.

        Args:
            threshold: Completion percentage threshold (default 80%)

        Returns:
            List of story IDs with completion >= threshold
        """
        near_complete = []
        for story_id, fr in self.datasets.active_frs.items():
            impl = self.datasets.active_impls.get(story_id)

            if not impl:
                continue

            # Average of AC and task completion
            overall = (fr.ac_completion_percent + impl.completion_percent) / 2

            if overall >= threshold:
                near_complete.append(story_id)

        return sorted(near_complete)
