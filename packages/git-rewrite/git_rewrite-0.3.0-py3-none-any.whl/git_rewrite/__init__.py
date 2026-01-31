# ────────────────────────────────────────────────────────────────────────────────────────
#   git-rewrite
#   ───────────
#
#   Git history rewriting tools.
#
#   Subcommands:
#   - scan: Scan for sensitive words (read-only)
#   - sanitise: Rewrite to remove sensitive words
#   - flatten: Flatten submodules into repository
#   - remap: Remap submodule commit references
#
#   (c) 2026 Cyber Assessment Labs — MIT License; see LICENSE in the project root.
#
#   Authors
#   ───────
#   bena (via Claude)
#
#   Version History
#   ───────────────
#   Jan 2026 - Created
# ────────────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────────────
#   Version
# ────────────────────────────────────────────────────────────────────────────────────────

__version__: str

try:
    from importlib.metadata import version

    __version__ = version("git-rewrite")
except Exception:
    __version__ = "0.0.0+dev"

__all__ = ["__version__"]
