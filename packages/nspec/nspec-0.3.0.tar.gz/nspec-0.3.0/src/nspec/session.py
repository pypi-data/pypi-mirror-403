"""Session Management - Handoff and session tracking for nspec stories.

Provides tools for:
- Generating session handoff summaries
- Initializing work sessions
- Logging session notes
- Tracking modified files and sync state

Note: Directory paths are configurable via nspec.toml.
See nspec.paths module for configuration details.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from nspec.paths import NspecPaths, get_paths


class TaskInfo(NamedTuple):
    """Information about an IMPL task."""

    text: str
    completed: bool
    obsolete: bool
    delegated: bool
    delegated_to: str | None


def find_story_files(
    story_id: str,
    docs_root: Path,
    paths_config: NspecPaths | None = None,
    project_root: Path | None = None,
) -> tuple[Path | None, Path | None]:
    """Find FR and IMPL files for a story.

    Args:
        story_id: Story ID to find
        docs_root: Root docs directory
        paths_config: Optional custom paths configuration
        project_root: Project root for finding nspec.toml (default: cwd)

    Returns:
        Tuple of (fr_path, impl_path), either may be None if not found
    """
    paths = get_paths(docs_root, config=paths_config, project_root=project_root)
    fr_dir = paths.active_frs_dir
    impl_dir = paths.active_impls_dir
    completed_dir = paths.completed_done

    # Search active directories first
    fr_path = None
    impl_path = None

    for pattern in [f"FR-{story_id}-*.md", f"FR-{story_id}.md"]:
        matches = list(fr_dir.glob(pattern))
        if matches:
            fr_path = matches[0]
            break

    for pattern in [f"IMPL-{story_id}-*.md", f"IMPL-{story_id}.md"]:
        matches = list(impl_dir.glob(pattern))
        if matches:
            impl_path = matches[0]
            break

    # Check completed directory if not found
    if not fr_path:
        for pattern in [f"FR-{story_id}-*.md", f"FR-{story_id}.md"]:
            matches = list(completed_dir.glob(pattern))
            if matches:
                fr_path = matches[0]
                break

    if not impl_path:
        for pattern in [f"IMPL-{story_id}-*.md", f"IMPL-{story_id}.md"]:
            matches = list(completed_dir.glob(pattern))
            if matches:
                impl_path = matches[0]
                break

    return fr_path, impl_path


def parse_impl_tasks(content: str) -> list[TaskInfo]:
    """Parse tasks from IMPL file content.

    Args:
        content: IMPL file content

    Returns:
        List of TaskInfo objects
    """
    tasks = []
    # Match checkbox items: - [ ] text, - [x] text, - [~] text, - [→123] text (delegated)
    pattern = r"^- \[([x~\s]|→[0-9A-Za-z]{3,})\]\s+(.+)$"

    for line in content.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            marker = match.group(1)
            text = match.group(2).strip()

            completed = marker == "x"
            obsolete = marker == "~"
            delegated = marker.startswith("→")
            delegated_to = marker[1:] if delegated and len(marker) > 1 else None

            tasks.append(
                TaskInfo(
                    text=text,
                    completed=completed,
                    obsolete=obsolete,
                    delegated=delegated,
                    delegated_to=delegated_to,
                )
            )

    return tasks


def get_git_status(project_root: Path) -> list[str]:
    """Get list of uncommitted files.

    Args:
        project_root: Project root directory

    Returns:
        List of uncommitted file paths
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            return [line[3:] for line in lines if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def get_last_commit_info(project_root: Path) -> tuple[str, str, str]:
    """Get info about the last commit.

    Args:
        project_root: Project root directory

    Returns:
        Tuple of (hash, message, relative_time)
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H|%s|%ar"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split("|", 2)
            if len(parts) == 3:
                return parts[0], parts[1], parts[2]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "", "Unknown", "Unknown"


def generate_handoff(story_id: str, docs_root: Path, project_root: Path | None = None) -> str:
    """Generate a structured session handoff summary.

    Args:
        story_id: Story ID to generate handoff for
        docs_root: Docs root directory
        project_root: Project root (defaults to cwd)

    Returns:
        Formatted handoff summary string
    """
    if project_root is None:
        project_root = Path.cwd()

    fr_path, impl_path = find_story_files(story_id, docs_root)

    if not impl_path:
        return f"Error: IMPL file not found for story {story_id}"

    impl_content = impl_path.read_text()
    tasks = parse_impl_tasks(impl_content)

    # Get status from IMPL
    status_match = re.search(r"\*\*Status:\*\*\s*(.+)", impl_content)
    status = status_match.group(1).strip() if status_match else "Unknown"

    # Categorize tasks
    completed = [t for t in tasks if t.completed]
    pending = [t for t in tasks if not t.completed and not t.obsolete and not t.delegated]
    obsolete = [t for t in tasks if t.obsolete]
    delegated = [t for t in tasks if t.delegated]

    # Get git info
    uncommitted_files = get_git_status(project_root)
    commit_hash, commit_msg, commit_time = get_last_commit_info(project_root)

    # Generate date
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"Session Handoff - Story {story_id}",
        "=" * 60,
        "",
        f"**Status:** {status}",
        f"**Date:** {date_str}",
        f"**Last Commit:** {commit_hash[:7]} - {commit_msg} ({commit_time})",
        "",
        "## Task Summary",
        f"- Completed: {len(completed)}",
        f"- Pending: {len(pending)}",
        f"- Delegated: {len(delegated)}",
        f"- Obsolete: {len(obsolete)}",
        "",
        "## Completed Tasks",
    ]
    lines.extend([f"  [x] {t.text}" for t in completed])

    lines.extend(["", "## Pending Tasks"])
    lines.extend([f"  [ ] {t.text}" for t in pending])

    if uncommitted_files:
        lines.extend(["", f"## Uncommitted Files ({len(uncommitted_files)})"])
        for f in uncommitted_files[:20]:
            lines.append(f"  - {f}")
        if len(uncommitted_files) > 20:
            lines.append(f"  ... and {len(uncommitted_files) - 20} more")

    lines.extend(
        [
            "",
            "## Suggested Handoff Note Template",
            "```markdown",
            f"### Session Handoff - {date_str}",
            "",
            f"**Completed:** {', '.join(t.text[:30] for t in completed[:3]) or 'None'}",
            "**Current:** [describe current work]",
            "**Blocker:** [if any]",
            f"**Next:** {pending[0].text if pending else 'Continue with remaining tasks'}",
            "```",
            "",
            "## Suggested Commit Message",
            "```bash",
            f'git commit -m "wip: Story {story_id} - [describe progress]"',
            "```",
        ]
    )

    return "\n".join(lines)


def initialize_session(story_id: str, docs_root: Path, project_root: Path | None = None) -> str:
    """Initialize session context for a story.

    Shows where work left off, blockers, and suggested first action.

    Args:
        story_id: Story ID to start working on
        docs_root: Docs root directory
        project_root: Project root (defaults to cwd)

    Returns:
        Formatted session start summary
    """
    if project_root is None:
        project_root = Path.cwd()

    fr_path, impl_path = find_story_files(story_id, docs_root)

    if not impl_path:
        return f"Error: IMPL file not found for story {story_id}"

    impl_content = impl_path.read_text()
    fr_content = fr_path.read_text() if fr_path else ""

    tasks = parse_impl_tasks(impl_content)

    # Get status
    status_match = re.search(r"\*\*Status:\*\*\s*(.+)", impl_content)
    status = status_match.group(1).strip() if status_match else "Unknown"

    # Get title
    title_match = re.search(r"^#\s+(?:IMPL-\d+[a-z]?:\s*)?(.+)$", impl_content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else f"Story {story_id}"

    # Categorize tasks
    completed = [t for t in tasks if t.completed]
    pending = [t for t in tasks if not t.completed and not t.obsolete and not t.delegated]

    # Look for blockers in execution notes
    exec_notes_match = re.search(r"## Execution Notes\n([\s\S]*?)(?=\n##|$)", impl_content)
    exec_notes = exec_notes_match.group(1) if exec_notes_match else ""

    blocker_match = re.search(r"\*\*Blocker[s]?:\*\*\s*(.+)", exec_notes, re.IGNORECASE)
    blocker = blocker_match.group(1).strip() if blocker_match else None

    # Get uncommitted files
    uncommitted = get_git_status(project_root)

    lines = [
        f"Session Start - Story {story_id}",
        "=" * 60,
        "",
        f"**Title:** {title}",
        f"**Status:** {status}",
        f"**Progress:** {len(completed)}/{len(tasks)} tasks ({int(len(completed) / len(tasks) * 100) if tasks else 0}%)",
        "",
    ]

    if blocker:
        lines.extend(
            [
                "## BLOCKER",
                f"  {blocker}",
                "",
            ]
        )

    lines.extend(
        [
            "## Pending Tasks",
        ]
    )
    for t in pending[:5]:
        lines.append(f"  [ ] {t.text}")
    if len(pending) > 5:
        lines.append(f"  ... and {len(pending) - 5} more")

    if uncommitted:
        lines.extend(
            [
                "",
                f"## Uncommitted Changes ({len(uncommitted)})",
            ]
        )
        for f in uncommitted[:5]:
            lines.append(f"  - {f}")
        if len(uncommitted) > 5:
            lines.append(f"  ... and {len(uncommitted) - 5} more")

    # Suggested first action
    lines.extend(
        [
            "",
            "## Suggested First Action",
        ]
    )
    if blocker:
        lines.append(f"  Resolve blocker: {blocker}")
    elif uncommitted:
        lines.append("  Review/commit uncommitted changes")
    elif pending:
        lines.append(f"  Start: {pending[0].text}")
    else:
        lines.append("  All tasks complete - advance status or archive story")

    lines.extend(
        [
            "",
            "## Quick Commands",
            f"  make nspec.task {story_id}     # View full task breakdown",
            f"  make nspec.advance-status {story_id}  # Advance status",
        ]
    )

    return "\n".join(lines)


def append_session_log(
    story_id: str,
    note: str,
    docs_root: Path,
) -> str:
    """Append a timestamped note to IMPL Execution Notes.

    Args:
        story_id: Story ID
        note: Note to append
        docs_root: Docs root directory

    Returns:
        Success/error message
    """
    _, impl_path = find_story_files(story_id, docs_root)

    if not impl_path:
        return f"Error: IMPL file not found for story {story_id}"

    content = impl_path.read_text()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    formatted_note = f"\n- **{timestamp}:** {note}"

    # Find or create Execution Notes section
    if "## Execution Notes" in content:
        # Append to existing section
        parts = content.split("## Execution Notes", 1)
        # Find end of section (next ## or end of file)
        rest = parts[1]
        next_section = re.search(r"\n##\s", rest)
        if next_section:
            insert_pos = next_section.start()
            new_content = (
                parts[0]
                + "## Execution Notes"
                + rest[:insert_pos]
                + formatted_note
                + rest[insert_pos:]
            )
        else:
            new_content = content + formatted_note
    else:
        # Create new section at end
        new_content = content.rstrip() + "\n\n## Execution Notes\n" + formatted_note

    impl_path.write_text(new_content)
    return f"Added note to IMPL-{story_id}: {note[:50]}..."


def get_modified_files(project_root: Path, since_commit: str | None = None) -> list[str]:
    """Get files modified since a commit or in working tree.

    Args:
        project_root: Project root directory
        since_commit: Git ref to compare against (default: HEAD, 'staged' for staged only)

    Returns:
        List of modified file paths
    """
    try:
        if since_commit == "staged":
            cmd = ["git", "diff", "--cached", "--name-only"]
        elif since_commit:
            cmd = ["git", "diff", "--name-only", since_commit]
        else:
            cmd = ["git", "status", "--porcelain"]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if since_commit == "staged" or since_commit:
                return [line for line in lines if line.strip()]
            else:
                # Parse porcelain format
                return [line[3:] for line in lines if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def sync_story_state(
    story_id: str,
    docs_root: Path,
    project_root: Path | None = None,
    force: bool = False,
) -> str:
    """Validate and synchronize story state.

    Checks IMPL task checkboxes vs code existence.

    Args:
        story_id: Story ID to sync
        docs_root: Docs root directory
        project_root: Project root (defaults to cwd)
        force: If True, auto-fix detected mismatches

    Returns:
        Sync status report
    """
    if project_root is None:
        project_root = Path.cwd()

    _, impl_path = find_story_files(story_id, docs_root)

    if not impl_path:
        return f"Error: IMPL file not found for story {story_id}"

    impl_content = impl_path.read_text()
    tasks = parse_impl_tasks(impl_content)

    uncommitted = get_git_status(project_root)

    lines = [
        f"Story {story_id} Sync Status",
        "=" * 40,
        "",
        f"Tasks: {sum(1 for t in tasks if t.completed)}/{len(tasks)} complete",
        f"Uncommitted files: {len(uncommitted)}",
        "",
    ]

    if uncommitted:
        lines.extend(
            [
                "## Uncommitted Files",
            ]
        )
        for f in uncommitted[:10]:
            lines.append(f"  - {f}")
        if len(uncommitted) > 10:
            lines.append(f"  ... and {len(uncommitted) - 10} more")

    # Note: Full code verification would require pattern extraction from tasks
    # This is a simplified version that reports basic state

    lines.extend(
        [
            "",
            "## Recommendations",
        ]
    )

    if uncommitted:
        lines.append("  - Commit or stash uncommitted changes")

    pending = [t for t in tasks if not t.completed and not t.obsolete and not t.delegated]
    if not pending:
        lines.append("  - All tasks complete - consider advancing status")
    else:
        lines.append(f"  - {len(pending)} tasks remaining")

    return "\n".join(lines)
