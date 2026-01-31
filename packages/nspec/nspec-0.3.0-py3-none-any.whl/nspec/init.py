"""Project initialization for nspec.

Detects the project stack (language, package manager, test framework, CI platform)
and scaffolds nspec configuration files, directory structure, and CI config.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# FR template (matches docs/frs/active/TEMPLATE.md)
FR_TEMPLATE = """\
# FR-XXX: Title

**Priority:** 🟡 P2
**Status:** 🟡 Proposed
deps: []

## Overview
Description of the feature request.

## Acceptance Criteria
- [ ] AC-F1: First acceptance criterion
"""

# IMPL template (matches docs/impls/active/TEMPLATE.md)
IMPL_TEMPLATE = """\
# IMPL-XXX: Title

**Status:** 🟡 Planning
**LOE:** N/A

## Tasks
- [ ] 1. First task
"""

# Runner prefix mapping per detected stack
RUNNER_PREFIXES: dict[tuple[str, str], str] = {
    ("python", "poetry"): "poetry run nspec",
    ("python", "pip"): "python -m nspec",
    ("python", "hatch"): "hatch run nspec",
    ("python", "uv"): "uv run nspec",
    ("node", "npm"): "npx nspec",
    ("node", "yarn"): "npx nspec",
    ("node", "pnpm"): "npx nspec",
    ("rust", "cargo"): "cargo run --bin nspec --",
    ("go", "go"): "go run . --",
}

DEFAULT_RUNNER_PREFIX = "nspec"


@dataclass
class DetectedStack:
    """Result of project stack detection."""

    language: str = "unknown"
    package_manager: str = "unknown"
    test_framework: str = "unknown"
    ci_platform: str = "none"

    @property
    def runner_prefix(self) -> str:
        """Return the nspec runner prefix for this stack."""
        return RUNNER_PREFIXES.get((self.language, self.package_manager), DEFAULT_RUNNER_PREFIX)


def detect_stack(project_root: Path) -> DetectedStack:
    """Detect the project's language, package manager, test framework, and CI platform.

    Args:
        project_root: Root directory of the project to analyze.

    Returns:
        DetectedStack with detected values, or defaults for undetectable fields.
    """
    stack = DetectedStack()

    # Detect language and package manager
    _detect_language(project_root, stack)

    # Detect test framework
    _detect_test_framework(project_root, stack)

    # Detect CI platform
    _detect_ci_platform(project_root, stack)

    return stack


def _detect_language(project_root: Path, stack: DetectedStack) -> None:
    """Detect language and package manager from project files."""
    # Python — check pyproject.toml for build system
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        stack.language = "python"
        content = pyproject.read_text()

        if "poetry" in content.lower():
            stack.package_manager = "poetry"
        elif "hatchling" in content.lower() or "hatch" in content.lower():
            stack.package_manager = "hatch"
        elif (project_root / "uv.lock").exists():
            stack.package_manager = "uv"
        else:
            stack.package_manager = "pip"
        return

    # Python — setup.py / requirements.txt fallback
    if (project_root / "setup.py").exists() or (project_root / "requirements.txt").exists():
        stack.language = "python"
        if (project_root / "uv.lock").exists():
            stack.package_manager = "uv"
        else:
            stack.package_manager = "pip"
        return

    # Node.js
    package_json = project_root / "package.json"
    if package_json.exists():
        stack.language = "node"
        if (project_root / "pnpm-lock.yaml").exists():
            stack.package_manager = "pnpm"
        elif (project_root / "yarn.lock").exists():
            stack.package_manager = "yarn"
        else:
            stack.package_manager = "npm"
        return

    # Rust
    if (project_root / "Cargo.toml").exists():
        stack.language = "rust"
        stack.package_manager = "cargo"
        return

    # Go
    if (project_root / "go.mod").exists():
        stack.language = "go"
        stack.package_manager = "go"
        return


def _detect_test_framework(project_root: Path, stack: DetectedStack) -> None:
    """Detect test framework from project files."""
    if stack.language == "python":
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text().lower()
            if "pytest" in content:
                stack.test_framework = "pytest"
                return
            if "unittest" in content:
                stack.test_framework = "unittest"
                return
        # Check for test directories
        if (project_root / "tests").exists() or (project_root / "test").exists():
            stack.test_framework = "pytest"
            return
        stack.test_framework = "pytest"
        return

    if stack.language == "node":
        package_json = project_root / "package.json"
        if package_json.exists():
            content = package_json.read_text().lower()
            if "vitest" in content:
                stack.test_framework = "vitest"
                return
            if "jest" in content:
                stack.test_framework = "jest"
                return
            if "mocha" in content:
                stack.test_framework = "mocha"
                return
        stack.test_framework = "jest"
        return

    if stack.language == "rust":
        stack.test_framework = "cargo-test"
        return

    if stack.language == "go":
        stack.test_framework = "go-test"
        return


def _detect_ci_platform(project_root: Path, stack: DetectedStack) -> None:
    """Detect CI platform from project files."""
    if (project_root / ".github" / "workflows").exists():
        stack.ci_platform = "github"
        return

    if (project_root / "cloudbuild.yaml").exists() or (project_root / "cloudbuild.yml").exists():
        stack.ci_platform = "cloudbuild"
        return

    if (project_root / ".gitlab-ci.yml").exists():
        stack.ci_platform = "gitlab"
        return


def scaffold_project(
    project_root: Path,
    docs_root: Path | None = None,
    stack: DetectedStack | None = None,
    ci_platform_override: str | None = None,
    force: bool = False,
) -> list[Path]:
    """Scaffold a new nspec project structure.

    Creates nspec.toml, nspec.mk, docs directories with templates, and CI config.

    Args:
        project_root: Root directory of the project.
        docs_root: Docs directory path. Defaults to project_root / "docs".
        stack: Detected stack. If None, auto-detects.
        ci_platform_override: Override CI platform (github/cloudbuild/gitlab/none).
        force: If True, overwrite existing files.

    Returns:
        List of paths that were created.

    Raises:
        FileExistsError: If files already exist and force is False.
    """
    if stack is None:
        stack = detect_stack(project_root)

    if docs_root is None:
        docs_root = project_root / "docs"

    ci_platform = ci_platform_override if ci_platform_override else stack.ci_platform
    created: list[Path] = []

    # 1. nspec.toml
    created.extend(
        _write_file(
            project_root / "nspec.toml",
            _generate_nspec_toml(),
            force=force,
        )
    )

    # 2. nspec.mk
    created.extend(
        _write_file(
            project_root / "nspec.mk",
            _generate_nspec_mk(stack),
            force=force,
        )
    )

    # 3. Docs directories
    dirs_to_create = [
        docs_root / "frs" / "active",
        docs_root / "impls" / "active",
        docs_root / "completed" / "done",
        docs_root / "completed" / "superseded",
        docs_root / "completed" / "rejected",
    ]

    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        created.append(d)

    # 4. FR template
    created.extend(
        _write_file(
            docs_root / "frs" / "active" / "TEMPLATE.md",
            FR_TEMPLATE,
            force=force,
        )
    )

    # 5. IMPL template
    created.extend(
        _write_file(
            docs_root / "impls" / "active" / "TEMPLATE.md",
            IMPL_TEMPLATE,
            force=force,
        )
    )

    # 6. CI config
    if ci_platform and ci_platform != "none":
        ci_files = _generate_ci_config(ci_platform)
        for rel_path, content in ci_files:
            created.extend(
                _write_file(
                    project_root / rel_path,
                    content,
                    force=force,
                )
            )

    return created


def _write_file(path: Path, content: str, *, force: bool = False) -> list[Path]:
    """Write content to a file, creating parent directories as needed.

    Returns:
        List containing the path if written, empty list if skipped.

    Raises:
        FileExistsError: If file exists and force is False.
    """
    if path.exists() and not force:
        raise FileExistsError(f"File already exists: {path} (use --force to overwrite)")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return [path]


def _generate_nspec_toml() -> str:
    """Generate nspec.toml content."""
    from nspec.templates.init.nspec_toml import render

    return render()


def _generate_nspec_mk(stack: DetectedStack) -> str:
    """Generate nspec.mk content for the given stack."""
    from nspec.templates.init.nspec_mk import render

    return render(runner_prefix=stack.runner_prefix)


def _generate_ci_config(platform: str) -> list[tuple[str, str]]:
    """Generate CI config file(s) for the given platform.

    Returns:
        List of (relative_path, content) tuples.
    """
    if platform == "github":
        from nspec.templates.init.ci_github import render

        return [(".github/workflows/nspec.yml", render())]

    if platform == "cloudbuild":
        from nspec.templates.init.ci_cloudbuild import render

        return [("cloudbuild.yaml", render())]

    if platform == "gitlab":
        from nspec.templates.init.ci_gitlab import render

        return [(".gitlab-ci.yml", render())]

    return []
