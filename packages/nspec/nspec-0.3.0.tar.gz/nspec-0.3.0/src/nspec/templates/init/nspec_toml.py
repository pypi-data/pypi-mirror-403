"""Template for nspec.toml configuration file."""

TEMPLATE = """\
# nspec.toml — Configuration for nspec specification management
# See: https://github.com/Novabuiltdevv/nspec

[paths]
# Directory names relative to docs_root (default: docs/)
# feature_requests = "10-feature-requests"
# implementation = "11-implementation"
# completed = "12-completed"
# completed_done = "done"
# completed_superseded = "superseded"
# completed_rejected = "rejected"
"""


def render() -> str:
    """Return the nspec.toml template content."""
    return TEMPLATE
