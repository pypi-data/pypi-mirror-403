"""Command-line interface for nspec management.

This module provides the CLI entry point. Business logic is delegated to:
- validator.py: NspecValidator for validation and generation
- table_formatter.py: NspecTableFormatter for table display
- session.py: Session handoff and management
- crud.py: CRUD operations for stories

Note: Directory paths are configurable via nspec.toml.
See nspec.paths module for configuration details.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from nspec.crud import (
    add_dependency,
    check_acceptance_criteria,
    check_impl_task,
    clean_dangling_deps,
    complete_story,
    create_adr,
    create_new_story,
    delete_story,
    finalize_story,
    list_adrs,
    move_dependency,
    next_status,
    reject_story,
    remove_dependency,
    set_loe,
    set_priority,
    set_status,
    supersede_story,
    validate_story_criteria,
)
from nspec.datasets import DatasetLoader
from nspec.paths import get_paths
from nspec.session import (
    append_session_log,
    generate_handoff,
    get_modified_files,
    initialize_session,
    sync_story_state,
)
from nspec.spinner import spinner
from nspec.statuses import print_status_codes
from nspec.table_formatter import NspecTableFormatter
from nspec.validator import NspecValidator

logger = logging.getLogger("nspec")

# Exceptions expected during nspec CLI operations
_NspecCliErrors = (RuntimeError, ValueError, KeyError, TypeError, OSError, IOError)


def run_validation_check(
    docs_root: Path, operation_name: str, project_root: Path | None = None
) -> bool:
    """Run validation after a mutation operation and report results."""
    print(f"\nRunning validation after {operation_name}...")
    validator = NspecValidator(docs_root=docs_root, project_root=project_root)
    success, errors = validator.validate()

    if success:
        print("Validation passed - nspec is consistent")
        return True
    else:
        print(f"Validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        print("\nFix these errors before proceeding with other nspec operations.")
        return False


# =============================================================================
# Command Handlers
# =============================================================================


def handle_statusline(args) -> int:
    """Output compact status line for Claude Code integration.

    Format: E{epic} · T{story} · [{completed}/{total}]

    Uses the same TaskParser as the TUI for consistent counts.
    """
    from nspec.tasks import TaskParser

    project_root = getattr(args, "project_root", None) or Path.cwd()
    novabuilt_dir = project_root / ".novabuilt.dev"

    # Read current story
    current_story_file = novabuilt_dir / "current_story"
    if current_story_file.exists():
        story_id = current_story_file.read_text().strip()
    else:
        story_id = "---"

    # Read active epic
    active_epic_file = novabuilt_dir / "active_epic"
    if active_epic_file.exists():
        epic_id = active_epic_file.read_text().strip()
    else:
        epic_id = "---"

    # Get task counts using the same parser as TUI
    completed = 0
    total = 0

    if story_id and story_id != "---":
        paths = get_paths(args.docs_root, project_root=getattr(args, "project_root", None))
        impl_files = list(paths.active_impls_dir.glob(f"IMPL-{story_id}-*.md"))

        if impl_files:
            impl_path = impl_files[0]
            content = impl_path.read_text()
            parser = TaskParser()
            tasks = parser.parse(content, impl_path)

            def count_all(task_list):
                t, c = 0, 0
                for task in task_list:
                    t += 1
                    if task.completed:
                        c += 1
                    if task.children:
                        ct, cc = count_all(task.children)
                        t += ct
                        c += cc
                return t, c

            total, completed = count_all(tasks)

    # Output compact format
    print(f"E{epic_id} · S{story_id} · [{completed}/{total}]")
    return 0


def handle_validate(args) -> int:
    """Run all validation layers."""
    validator = NspecValidator(
        docs_root=args.docs_root,
        strict_mode=getattr(args, "strict_epic_grouping", False),
        strict_completion_parity=not getattr(args, "no_strict_completion_parity", False),
        project_root=getattr(args, "project_root", None),
    )
    success, errors = validator.validate()

    if success:
        print("✅ Nspec validation passed - no errors found")
        return 0
    else:
        print(f"\nFound {len(errors)} errors:")
        for error in errors:
            print(error)
            print()
        return 1


def handle_generate(args) -> int:
    """Generate NSPEC.md from validated fRIMPLs."""
    # Pass 0: Auto-clean dangling dependencies
    cleaned = clean_dangling_deps(args.docs_root)
    if cleaned:
        for story_id, path, removed in cleaned:
            print(f"Story {story_id}: removed dangling deps {removed}")

    # Pass 1: Validate
    validator = NspecValidator(
        docs_root=args.docs_root, project_root=getattr(args, "project_root", None)
    )
    with spinner("Loading"):
        success, errors = validator.validate()

    if not success:
        print(f"\nValidation failed with {len(errors)} errors. Cannot generate.")
        for error in errors:
            print(error)
            print()
        print("Fix errors first, then run --generate again.")
        return 1

    # Pass 2: Generate files
    validator.generate_nspec(Path("NSPEC.md"))
    validator.generate_nspec_completed(Path("NSPEC_COMPLETED.md"))
    return 0


def handle_dashboard(args) -> int:
    """Generate + stats in one call."""
    # Clean dangling deps
    cleaned = clean_dangling_deps(args.docs_root)
    if cleaned:
        for story_id, path, removed in cleaned:
            print(f"Story {story_id}: removed dangling deps {removed}")

    # Auto-assign ungrouped stories to default epic (if specified)
    default_epic = getattr(args, "default_epic", None)
    if default_epic:
        from nspec.crud import auto_assign_ungrouped_to_epic

        try:
            assigned = auto_assign_ungrouped_to_epic(default_epic, args.docs_root)
            if assigned:
                for story_id, epic_id in assigned:
                    print(f"Story {story_id}: auto-assigned to Epic {epic_id}")
        except (FileNotFoundError, ValueError) as e:
            print(f"Auto-assign failed: {e}")

    # Validate and generate
    validator = NspecValidator(
        docs_root=args.docs_root,
        strict_mode=getattr(args, "strict_epic_grouping", False),
        strict_completion_parity=not getattr(args, "no_strict_completion_parity", False),
        project_root=getattr(args, "project_root", None),
    )
    validator.verbose_status = getattr(args, "verbose_status", False)
    validator.epic_filter = getattr(args, "epic", None)

    with spinner("Loading"):
        success, errors = validator.validate()

    if not success:
        print(f"\nValidation failed with {len(errors)} errors.")
        for error in errors:
            print(error)
            print()
        return 1

    # Generate files
    validator.generate_nspec(Path("NSPEC.md"))
    validator.generate_nspec_completed(Path("NSPEC_COMPLETED.md"))

    # Show stats (without calendar)
    formatter = NspecTableFormatter(
        datasets=validator.datasets,
        ordered_active_stories=validator.ordered_active_stories,
        verbose_status=validator.verbose_status,
        epic_filter=validator.epic_filter,
    )
    formatter.show_stats(show_calendar=False)
    return 0


def handle_stats(args) -> int:
    """Show engineering metrics dashboard."""
    from nspec.dev_metrics import print_dev_metrics

    print_dev_metrics(Path("."))
    return 0


def handle_progress(args) -> int:
    """Show task/AC progress."""
    validator = NspecValidator(
        docs_root=args.docs_root, project_root=getattr(args, "project_root", None)
    )

    try:
        loader = DatasetLoader(
            docs_root=args.docs_root, project_root=getattr(args, "project_root", None)
        )
        validator.datasets = loader.load()
    except ValueError as e:
        print(f"Failed to load datasets: {e}")
        return 1

    if args.progress == "__summary__":
        validator.show_progress(show_all=args.all)
    else:
        validator.show_progress(story_id=args.progress)
    return 0


def handle_deps(args) -> int:
    """List direct dependencies of a story/epic."""
    loader = DatasetLoader(args.docs_root, project_root=getattr(args, "project_root", None))
    datasets = loader.load()

    fr = datasets.active_frs.get(args.deps)
    if not fr:
        print(f"Story {args.deps} not found in active nspec")
        return 1

    if not fr.deps:
        print(f"Story {args.deps} has no dependencies")
        return 0

    title = fr.path.stem.replace(f"FR-{args.deps}-", "").replace("-", " ").title()
    print(f"\nDependencies of {args.deps}: {title}")
    print(f"   Priority: {fr.priority} | Status: {fr.status}")
    print(f"   Count: {len(fr.deps)} dependencies\n")

    for dep_id in sorted(fr.deps, key=lambda x: int(x) if x.isdigit() else 0):
        dep_fr = datasets.active_frs.get(dep_id)
        if dep_fr:
            dep_title = dep_fr.path.stem.replace(f"FR-{dep_id}-", "").replace("-", " ").title()
            dep_impl = datasets.active_impls.get(dep_id)
            impl_status = dep_impl.status if dep_impl else "N/A"
            print(f"   {dep_id}: {dep_title}")
            print(f"        FR: {dep_fr.status} | IMPL: {impl_status} | Pri: {dep_fr.priority}")
        else:
            dep_fr = datasets.completed_frs.get(dep_id)
            if dep_fr:
                print(f"   {dep_id}: (completed)")
            else:
                print(f"   {dep_id}: (not found)")

    print()
    return 0


def handle_context(args) -> int:
    """Output LLM-friendly context for epic's dependencies."""
    from collections import defaultdict

    loader = DatasetLoader(args.docs_root, project_root=getattr(args, "project_root", None))
    datasets = loader.load()

    epic_fr = datasets.active_frs.get(args.context)
    if not epic_fr:
        print(f"Epic {args.context} not found in active nspec")
        return 1

    if not epic_fr.deps:
        print(f"Epic {args.context} has no dependencies")
        return 0

    epic_title = epic_fr.path.stem.replace(f"FR-{args.context}-", "").replace("-", " ").title()

    # Collect all incomplete deps
    incomplete: dict[str, dict] = {}
    completed: list[str] = []

    for dep_id in epic_fr.deps:
        dep_fr = datasets.active_frs.get(dep_id)
        if dep_fr:
            dep_impl = datasets.active_impls.get(dep_id)
            dep_title = dep_fr.path.stem.replace(f"FR-{dep_id}-", "").replace("-", " ")
            incomplete[dep_id] = {
                "title": dep_title,
                "fr_status": dep_fr.status,
                "impl_status": dep_impl.status if dep_impl else "N/A",
                "priority": dep_fr.priority,
                "upstream": list(dep_fr.deps) if dep_fr.deps else [],
            }
        else:
            if datasets.completed_frs.get(dep_id):
                completed.append(dep_id)

    # Build reverse dependency map
    downstream: dict[str, list[str]] = defaultdict(list)
    for story_id, info in incomplete.items():
        for up_id in info["upstream"]:
            if up_id in incomplete:
                downstream[up_id].append(story_id)

    # Categorize stories
    ready_to_start: list[tuple[str, str]] = []
    blocked_by_active: list[tuple[str, str, list[str]]] = []
    active_work: list[tuple[str, str]] = []

    for story_id, info in incomplete.items():
        blockers = [u for u in info["upstream"] if u in incomplete]
        is_active = "Active" in info["impl_status"] or "Active" in info["fr_status"]
        is_hold = "Hold" in info["impl_status"] or "hold" in info["impl_status"].lower()

        if is_active and not is_hold:
            active_work.append((story_id, info["title"]))
        elif not blockers:
            ready_to_start.append((story_id, info["title"]))
        else:
            active_blockers = [
                b
                for b in blockers
                if incomplete.get(b, {}).get("impl_status", "").find("Active") >= 0
            ]
            if active_blockers:
                blocked_by_active.append((story_id, info["title"], active_blockers))
            else:
                ready_to_start.append((story_id, info["title"]))

    # Output YAML-like format
    print(f"""# LLM Context: Epic {args.context}
epic:
  id: {args.context}
  title: "{epic_title}"
  total_deps: {len(epic_fr.deps)}
  completed: {len(completed)}
  remaining: {len(incomplete)}

active_work:""")
    if active_work:
        for sid, title in sorted(active_work):
            print(f"  - {sid}: {title}")
    else:
        print("  []")

    print("\nready_to_start:")
    if ready_to_start:
        for sid, title in sorted(ready_to_start):
            print(f"  - {sid}: {title}")
    else:
        print("  []")

    print("\nblocked_by_active:")
    if blocked_by_active:
        for sid, title, blockers in sorted(blocked_by_active):
            print(f"  - {sid}: {title}")
            print(f"    blocked_by: [{', '.join(blockers)}]")
    else:
        print("  []")

    return 0


# =============================================================================
# Session Commands
# =============================================================================


def handle_handoff(args) -> int:
    """Generate session handoff summary."""
    if not args.id:
        print("Error: --id required for --handoff")
        return 1

    output = generate_handoff(args.id, args.docs_root)
    print(output)
    return 0


def handle_session_start(args) -> int:
    """Initialize session context."""
    if not args.id:
        print("Error: --id required for --session-start")
        return 1

    output = initialize_session(args.id, args.docs_root)
    print(output)
    return 0


def handle_session_log(args) -> int:
    """Append note to execution notes."""
    if not args.id or not args.note:
        print("Error: --id and --note required for --session-log")
        return 1

    output = append_session_log(args.id, args.note, args.docs_root)
    print(output)
    return 0


def handle_modified_files(args) -> int:
    """List modified files."""
    files = get_modified_files(Path.cwd(), args.since_commit)
    for f in files:
        print(f)
    return 0


def handle_sync(args) -> int:
    """Sync story state."""
    if not args.id:
        print("Error: --id required for --sync")
        return 1

    output = sync_story_state(args.id, args.docs_root, force=args.force)
    print(output)
    return 0


# =============================================================================
# CRUD Commands
# =============================================================================


def resolve_epic(explicit_epic: str | None, docs_root: Path) -> str:
    """Resolve epic ID: explicit or default 226.

    Args:
        explicit_epic: Explicitly provided epic ID (--epic flag)
        docs_root: Path to docs/ directory

    Returns:
        Resolved epic ID
    """
    # Explicit epic takes priority, otherwise default to 226
    if explicit_epic:
        return explicit_epic

    # Default epic 226 (post-M1 platform features) for loose ideas
    return "226"


def validate_epic_exists(epic_id: str, docs_root: Path, project_root: Path | None = None) -> bool:
    """Validate that epic ID exists in active nspec.

    Args:
        epic_id: Epic ID to validate
        docs_root: Path to docs/ directory

    Returns:
        True if epic exists

    Raises:
        ValueError: If epic doesn't exist
    """
    paths = get_paths(docs_root, project_root=project_root)
    pattern = f"FR-{epic_id.zfill(3)}-*.md"
    matches = list(paths.active_frs_dir.glob(pattern))

    if not matches:
        raise ValueError(f"Epic {epic_id} not found in {paths.active_frs_dir}")

    return True


def handle_create_new(args) -> int:
    """Create new FR+IMPL from templates."""
    if not args.title:
        print("Error: --title required for --create-new")
        return 1

    try:
        # Resolve epic FIRST (before creating anything)
        epic_id = resolve_epic(getattr(args, "epic", None), args.docs_root)

        # Validate epic exists BEFORE creating files
        validate_epic_exists(
            epic_id, args.docs_root, project_root=getattr(args, "project_root", None)
        )

        # Create story files
        fr_path, impl_path, story_id = create_new_story(
            title=args.title,
            priority=args.priority,
            docs_root=args.docs_root,
            fr_template=getattr(args, "fr_template", None),
            impl_template=getattr(args, "impl_template", None),
        )

        # Add story to epic (atomic with creation)
        move_dependency(
            story_id=story_id,
            target_epic_id=epic_id,
            docs_root=args.docs_root,
        )

        # Git add if requested
        if args.git_add:
            import subprocess

            subprocess.run(["git", "add", str(fr_path), str(impl_path)], check=True)

        print(f"Created Story {story_id} in Epic {epic_id}")
        print(str(fr_path))
        print(str(impl_path))
        return 0
    except (ValueError, FileNotFoundError) as e:
        print(f"Failed to create story: {e}")
        return 1


def handle_delete(args) -> int:
    """Delete FR+IMPL for a story."""
    if not args.id:
        print("Error: --id required for --delete")
        return 1

    try:
        fr_path, impl_path = delete_story(
            story_id=args.id,
            docs_root=args.docs_root,
            force=args.force,
        )
        print(f"Deleted Story {args.id}")
        print(f"   Removed: {fr_path.name}")
        print(f"   Removed: {impl_path.name}")
        return 0
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Failed to delete story: {e}")
        return 1


def handle_complete(args) -> int:
    """Move FR+IMPL to completed directory."""
    if not args.id:
        print("Error: --id required for --complete")
        return 1

    try:
        fr_old, fr_new, impl_old, impl_new = complete_story(
            story_id=args.id,
            docs_root=args.docs_root,
        )
        print(str(fr_old))
        print(str(fr_new))
        print(str(impl_old))
        print(str(impl_new))
        return 0
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Failed to complete story: {e}")
        return 1


def handle_supersede(args) -> int:
    """Move FR+IMPL to superseded directory."""
    if not args.id:
        print("Error: --id required for --supersede")
        return 1

    try:
        fr_old, fr_new, impl_old, impl_new = supersede_story(
            story_id=args.id,
            docs_root=args.docs_root,
            force=args.force,
        )
        print(str(fr_old))
        print(str(fr_new))
        print(str(impl_old))
        print(str(impl_new))
        return 0
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Failed to supersede story: {e}")
        return 1


def handle_reject(args) -> int:
    """Archive story as rejected."""
    if not args.id:
        print("Error: --id required for --reject")
        return 1

    try:
        fr_old, fr_new, impl_old, impl_new = reject_story(
            story_id=args.id,
            docs_root=args.docs_root,
            force=args.force,
        )
        print(str(fr_old))
        print(str(fr_new))
        print(str(impl_old))
        print(str(impl_new))
        return 0
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Failed to reject story: {e}")
        return 1


def handle_finalize(args) -> int:
    """Show completion status."""
    if not args.id:
        print("Error: --id required for --finalize")
        return 1

    try:
        finalize_story(
            story_id=args.id,
            docs_root=args.docs_root,
            execute=args.execute,
        )
        return 0
    except FileNotFoundError as e:
        print(f"Failed to finalize story: {e}")
        return 1


def handle_add_dep(args) -> int:
    """Add dependency to a story."""
    if not args.to or not args.dep:
        print("Error: --to and --dep required for --add-dep")
        return 1

    try:
        result = add_dependency(
            story_id=args.to,
            dependency_id=args.dep,
            docs_root=args.docs_root,
        )
        print(f"Added dependency {args.dep} to Story {args.to}")
        print(f"   Updated: {result['path']}")
        if result.get("moved_from"):
            print(f"   Moved from Epic {result['moved_from']}")

        run_validation_check(args.docs_root, "dependency addition")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to add dependency: {e}")
        return 1


def handle_remove_dep(args) -> int:
    """Remove dependency from a story."""
    if not args.to or not args.dep:
        print("Error: --to and --dep required for --remove-dep")
        return 1

    try:
        fr_path = remove_dependency(
            story_id=args.to,
            dependency_id=args.dep,
            docs_root=args.docs_root,
        )
        print(f"Removed dependency {args.dep} from Story {args.to}")
        print(f"   Updated: {fr_path}")

        run_validation_check(args.docs_root, "dependency removal")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to remove dependency: {e}")
        return 1


def handle_move_dep(args) -> int:
    """Move story to target epic."""
    if not args.to or not args.dep:
        print("Error: --to and --dep required for --move-dep")
        return 1

    try:
        result = move_dependency(
            story_id=args.dep,
            target_epic_id=args.to,
            docs_root=args.docs_root,
        )

        print(f"Moved Story {args.dep} to Epic {args.to}")
        if result["removed_from"]:
            for epic_id in result["removed_from"]:
                print(f"   Removed from Epic {epic_id}")
        if result["added_to"]:
            print(f"   Added to Epic {result['added_to']}")
        if result["priority_bumped"]:
            print(f"   Priority bumped to {result['priority_bumped']}")

        run_validation_check(args.docs_root, "dependency move")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to move dependency: {e}")
        return 1


def handle_set_priority(args) -> int:
    """Change priority for a story."""
    if not args.id or not args.priority:
        print("Error: --id and --priority required for --set-priority")
        return 1

    try:
        fr_path = set_priority(
            story_id=args.id,
            priority=args.priority,
            docs_root=args.docs_root,
        )
        print(f"Updated Story {args.id} to {args.priority}")
        print(f"   Updated: {fr_path}")

        run_validation_check(args.docs_root, "priority change")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to set priority: {e}")
        return 1


def handle_set_loe(args) -> int:
    """Set LOE for a story."""
    if not args.id or not args.loe:
        print("Error: --id and --loe required for --set-loe")
        return 1

    try:
        impl_path = set_loe(
            story_id=args.id,
            loe=args.loe,
            docs_root=args.docs_root,
        )
        print(f"Updated Story {args.id} LOE to {args.loe}")
        print(f"   Updated: {impl_path}")

        run_validation_check(args.docs_root, "LOE change")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to set LOE: {e}")
        return 1


def handle_set_status(args) -> int:
    """Set status for FR and IMPL files atomically."""
    if not args.id or args.fr_status is None or args.impl_status is None:
        print("Error: --id, --fr-status, and --impl-status required")
        return 1

    try:
        set_status(
            story_id=args.id,
            fr_status=args.fr_status,
            impl_status=args.impl_status,
            docs_root=args.docs_root,
            force=args.force,
        )
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to set status: {e}")
        return 1


def handle_next_status(args) -> int:
    """Auto-advance IMPL to next logical state."""
    if not args.id:
        print("Error: --id required for --next-status")
        return 1

    try:
        next_status(
            story_id=args.id,
            docs_root=args.docs_root,
        )
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to advance status: {e}")
        return 1


def handle_check_criteria(args) -> int:
    """Mark acceptance criterion as complete or obsolete."""
    if not args.id or not args.criteria_id:
        print("Error: --id and --criteria-id required for --check-criteria")
        return 1

    marker = getattr(args, "marker", "x")
    marker_desc = "complete" if marker == "x" else "obsolete"

    try:
        fr_path = check_acceptance_criteria(
            story_id=args.id,
            criteria_id=args.criteria_id,
            docs_root=args.docs_root,
            marker=marker,
        )
        print(f"Marked {args.criteria_id} as {marker_desc} for Story {args.id}")
        print(f"   Updated: {fr_path}")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to check criteria: {e}")
        return 1


def handle_check_task(args) -> int:
    """Mark IMPL task as complete or obsolete."""
    if not args.id or not args.task_id:
        print("Error: --id and --task-id required for --check-task")
        return 1

    marker = getattr(args, "marker", "x")
    marker_desc = "complete" if marker == "x" else "obsolete"

    try:
        impl_path = check_impl_task(
            story_id=args.id,
            task_id=args.task_id,
            docs_root=args.docs_root,
            marker=marker,
        )
        print(f"Marked task '{args.task_id}' as {marker_desc} for Story {args.id}")
        print(f"   Updated: {impl_path}")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"Failed to check task: {e}")
        return 1


def handle_validate_criteria(args) -> int:
    """Validate acceptance criteria for a story."""
    if not args.id:
        print("Error: --id required for --validate-criteria")
        return 1

    try:
        is_valid, violations = validate_story_criteria(
            story_id=args.id,
            docs_root=args.docs_root,
            strict=args.strict,
        )

        if is_valid:
            print(f"Story {args.id} acceptance criteria validation passed")
            return 0
        else:
            print(f"Story {args.id} acceptance criteria validation failed:\n")
            for violation in violations:
                print(f"   {violation}")
            return 1
    except _NspecCliErrors as e:
        print(f"Validation error: {e}")
        return 1


def handle_create_adr(args) -> int:
    """Create a new ADR."""
    if not args.title:
        print("Error: --title required for --create-adr")
        return 1

    try:
        adr_id, fr_path = create_adr(args.title, args.docs_root)
        print(f"Created ADR-{adr_id}: {args.title}")
        print(f"   {fr_path}")
        return 0
    except _NspecCliErrors as e:
        print(f"Error creating ADR: {e}")
        return 1


def handle_list_adrs(args) -> int:
    """List all ADRs."""
    try:
        adrs = list_adrs(args.docs_root)
        if not adrs:
            print("No ADRs found (FR-900-999 range)")
            return 0

        print(f"\nArchitecture Decision Records ({len(adrs)} total)")
        print("=" * 60)
        for adr_id, status, title, path in adrs:
            status_emoji = {
                "DRAFT": "D",
                "PROPOSED": "P",
                "ACCEPTED": "A",
                "DEPRECATED": "!",
                "SUPERSEDED": ">",
            }.get(status.upper(), "?")
            print(f"  ADR-{adr_id}: [{status_emoji}] {status}")
            print(f"           {title}")
            print()
        return 0
    except _NspecCliErrors as e:
        print(f"Error listing ADRs: {e}")
        return 1


# =============================================================================
# Main Entry Point
# =============================================================================


def handle_init(args: argparse.Namespace) -> int:
    """Initialize a new nspec project."""
    from nspec.init import detect_stack, scaffold_project

    project_root = Path.cwd()
    docs_root = getattr(args, "docs_root", None) or project_root / "docs"

    stack = detect_stack(project_root)
    ci_override = getattr(args, "ci", None)
    force = getattr(args, "force", False)

    print(f"Detected stack: {stack.language}/{stack.package_manager}")
    if stack.ci_platform != "none":
        print(f"Detected CI: {stack.ci_platform}")

    try:
        created = scaffold_project(
            project_root=project_root,
            docs_root=docs_root,
            stack=stack,
            ci_platform_override=ci_override,
            force=force,
        )
    except FileExistsError as e:
        print(f"Error: {e}")
        return 1

    print(f"\nCreated {len(created)} files/directories:")
    for p in created:
        if p.is_file():
            try:
                rel = p.relative_to(project_root)
            except ValueError:
                rel = p
            print(f"  {rel}")

    print("\nNext steps:")
    print("  1. Review nspec.toml and adjust paths if needed")
    print("  2. Add 'include nspec.mk' to your Makefile")
    print("  3. Create your first story: nspec --create-new --title 'My Feature'")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="Nspec management - validation, generation, and CRUD operations"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command")
    init_parser = subparsers.add_parser("init", help="Initialize a new nspec project")
    init_parser.add_argument(
        "--ci",
        type=str,
        choices=["github", "cloudbuild", "gitlab", "none"],
        default=None,
        help="CI platform (auto-detected if not specified)",
    )
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    init_parser.add_argument(
        "--docs-root", type=Path, default=None, help="Docs root directory (default: docs/)"
    )

    # TUI mode
    parser.add_argument("--tui", action="store_true", help="Launch interactive TUI")
    parser.add_argument(
        "--statusline", action="store_true", help="Output compact status line for Claude Code"
    )

    # Core commands
    parser.add_argument("--validate", action="store_true", help="Run all validation layers")
    parser.add_argument("--generate", action="store_true", help="Generate NSPEC.md")
    parser.add_argument("--dashboard", action="store_true", help="Generate + stats combined")
    parser.add_argument("--stats", action="store_true", help="Show engineering metrics")
    parser.add_argument("--progress", nargs="?", const="__summary__", help="Show progress")
    parser.add_argument("--all", action="store_true", help="Show all stories (with --progress)")
    parser.add_argument("--deps", type=str, metavar="STORY_ID", help="List dependencies")
    parser.add_argument("--context", type=str, metavar="EPIC_ID", help="LLM context for epic")
    parser.add_argument("--status-codes", action="store_true", help="Print status codes")

    # Session commands
    parser.add_argument("--handoff", action="store_true", help="Generate session handoff")
    parser.add_argument("--session-start", action="store_true", help="Initialize session")
    parser.add_argument("--session-log", action="store_true", help="Append session note")
    parser.add_argument("--note", type=str, help="Note text (for --session-log)")
    parser.add_argument("--modified-files", action="store_true", help="List modified files")
    parser.add_argument("--since-commit", type=str, help="Git ref for --modified-files")
    parser.add_argument("--sync", action="store_true", help="Sync story state")

    # CRUD commands
    parser.add_argument("--create-new", action="store_true", help="Create new FR+IMPL")
    parser.add_argument("--delete", action="store_true", help="Delete FR+IMPL")
    parser.add_argument("--complete", action="store_true", help="Archive as completed")
    parser.add_argument("--supersede", action="store_true", help="Archive as superseded")
    parser.add_argument("--reject", action="store_true", help="Archive as rejected")
    parser.add_argument("--finalize", action="store_true", help="Show completion status")
    parser.add_argument("--execute", action="store_true", help="Execute finalization")

    # Dependency commands
    parser.add_argument("--add-dep", action="store_true", help="Add dependency")
    parser.add_argument("--remove-dep", action="store_true", help="Remove dependency")
    parser.add_argument("--move-dep", action="store_true", help="Move to epic")
    parser.add_argument("--to", type=str, help="Target story/epic ID")
    parser.add_argument("--dep", type=str, help="Dependency ID")

    # Property commands
    parser.add_argument("--set-priority", action="store_true", help="Change priority")
    parser.add_argument("--set-loe", action="store_true", help="Set LOE estimate")
    parser.add_argument("--loe", type=str, help="LOE value (5d, 3w, etc)")
    parser.add_argument("--_set_frimpl_status", action="store_true", help="[Internal] Set status")
    parser.add_argument("--next-status", action="store_true", help="Advance to next status")
    parser.add_argument("--fr-status", type=int, help="FR status code")
    parser.add_argument("--impl-status", type=int, help="IMPL status code")

    # Task/criteria commands
    parser.add_argument(
        "--check-criteria", action="store_true", help="Mark criterion complete/obsolete"
    )
    parser.add_argument("--check-task", action="store_true", help="Mark task complete/obsolete")
    parser.add_argument("--validate-criteria", action="store_true", help="Validate criteria")
    parser.add_argument("--criteria-id", type=str, help="Criteria ID (e.g., AC-F1)")
    parser.add_argument("--task-id", type=str, help="Task ID to mark (e.g., 1.1)")
    parser.add_argument(
        "--marker",
        type=str,
        default="x",
        choices=["x", "~"],
        help="Marker: x=complete, ~=obsolete (default: x)",
    )
    parser.add_argument("--strict", action="store_true", help="Strict validation")

    # ADR commands
    parser.add_argument("--create-adr", action="store_true", help="Create new ADR")
    parser.add_argument("--list-adrs", action="store_true", help="List all ADRs")

    # Common options
    parser.add_argument("--id", type=str, help="Story ID")
    parser.add_argument("--title", type=str, help="Story/ADR title")
    parser.add_argument("--priority", type=str, default="P2", help="Priority (P0-P3)")
    parser.add_argument("--force", action="store_true", help="Skip safety checks")
    parser.add_argument("--git-add", action="store_true", help="Git add created files")
    parser.add_argument("--docs-root", type=Path, default=Path("docs"), help="Docs root")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root for nspec.toml and .novabuilt.dev (default: parent of --docs-root)",
    )
    parser.add_argument("--verbose-status", action="store_true", help="Full status text")
    parser.add_argument(
        "--epic", type=str, help="Epic ID (for --create-new: target epic; for views: filter)"
    )
    parser.add_argument(
        "--fr-template", type=str, help="Path to FR template (relative to docs root or absolute)"
    )
    parser.add_argument(
        "--impl-template",
        type=str,
        help="Path to IMPL template (relative to docs root or absolute)",
    )
    parser.add_argument("--strict-epic-grouping", action="store_true", help="Require epic grouping")
    parser.add_argument("--no-strict-completion-parity", action="store_true")
    parser.add_argument("--default-epic", type=str, help="Default epic for ungrouped stories")

    return parser


def main() -> int:
    """Main CLI entry point."""
    # Configure logging
    log_level = logging.DEBUG if os.environ.get("NSPEC_DEBUG") == "Y" else logging.WARNING
    logging.basicConfig(level=log_level, format="%(message)s", stream=sys.stdout)

    parser = build_parser()
    args = parser.parse_args()

    # Subcommand dispatch (before flag-based dispatch)
    if args.command == "init":
        return handle_init(args)

    if getattr(args, "project_root", None) is None:
        args.project_root = args.docs_root.parent

    # TUI mode - launch interactive interface
    if args.tui:
        from nspec.tui import main as tui_main

        tui_main(docs_root=args.docs_root, project_root=args.project_root)
        return 0

    # Status line for Claude Code integration
    if args.statusline:
        return handle_statusline(args)

    # Dispatch to handlers
    if args.status_codes:
        print_status_codes()
        return 0

    if args.validate:
        return handle_validate(args)
    if args.generate:
        return handle_generate(args)
    if args.dashboard:
        return handle_dashboard(args)
    if args.stats:
        return handle_stats(args)
    if args.progress:
        return handle_progress(args)
    if args.deps:
        return handle_deps(args)
    if args.context:
        return handle_context(args)

    # Session commands
    if args.handoff:
        return handle_handoff(args)
    if args.session_start:
        return handle_session_start(args)
    if args.session_log:
        return handle_session_log(args)
    if args.modified_files:
        return handle_modified_files(args)
    if args.sync:
        return handle_sync(args)

    # CRUD commands
    if args.create_new:
        return handle_create_new(args)
    if args.delete:
        return handle_delete(args)
    if args.complete:
        return handle_complete(args)
    if args.supersede:
        return handle_supersede(args)
    if args.reject:
        return handle_reject(args)
    if args.finalize:
        return handle_finalize(args)

    # Dependency commands
    if args.add_dep:
        return handle_add_dep(args)
    if args.remove_dep:
        return handle_remove_dep(args)
    if args.move_dep:
        return handle_move_dep(args)

    # Property commands
    if args.set_priority:
        return handle_set_priority(args)
    if args.set_loe:
        return handle_set_loe(args)
    if args._set_frimpl_status:
        return handle_set_status(args)
    if args.next_status:
        return handle_next_status(args)

    # Task/criteria commands
    if args.check_criteria:
        return handle_check_criteria(args)
    if args.check_task:
        return handle_check_task(args)
    if args.validate_criteria:
        return handle_validate_criteria(args)

    # ADR commands
    if args.create_adr:
        return handle_create_adr(args)
    if args.list_adrs:
        return handle_list_adrs(args)

    # No command specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
