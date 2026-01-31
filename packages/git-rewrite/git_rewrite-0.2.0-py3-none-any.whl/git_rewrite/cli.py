# ────────────────────────────────────────────────────────────────────────────────────────
#   cli.py
#   ──────
#
#   Main CLI for git-rewrite with subcommand dispatch.
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
#   Imports
# ────────────────────────────────────────────────────────────────────────────────────────

import argparse
import sys
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────────────────
#   Argument Parsing
# ────────────────────────────────────────────────────────────────────────────────────────


SCAN_DESCRIPTION = """\
Scan a git repository for sensitive words without modifying anything.

This command streams through all commits and blobs using git fast-export,
searching for occurrences of words defined in your config file.
Use this to audit a repository before sanitising it.

The config file should be JSON with a "words" array:
  {"words": ["secretword", "internalname"]}

Example:
  git-rewrite scan -r ./my-repo -c dirty-words.json
  git-rewrite scan -r ./my-repo -c dirty-words.json -v  # verbose
"""

SANITISE_DESCRIPTION = """\
Rewrite git history to remove or replace sensitive words.

Creates a NEW repository with sanitised history. The original is never modified.
Uses git fast-export/fast-import for efficient streaming.

Features:
  - Replace words in file contents, commit messages, author/committer names
  - Map specific words to specific replacements (or use default "REDACTED")
  - Map author names to specific email addresses
  - Exclude specific files from the output (e.g., lock files)
  - Remap submodule commit references if you've sanitised submodules too

Config file (JSON):
  - words: list of words to find/replace
  - word_mapping: dict mapping words to replacements
  - email_mapping: dict mapping author names to emails
  - exclude_files: list of files to exclude

Example:
  git-rewrite sanitise -r ./dirty-repo -o ./clean-repo -c config.json
  git-rewrite sanitise --sample-config  # print example config
"""

FLATTEN_DESCRIPTION = """\
Flatten submodules by inlining their contents into the main repository.

Creates a NEW repository where submodule references (gitlinks) are replaced
with the actual file contents from those submodules at each commit.
Useful for merging submodule history into a monorepo.

The command will:
  1. Scan history to find all submodule paths and URLs
  2. Clone or use existing checkouts of submodule repositories
  3. Stream history, replacing gitlinks with actual file trees
  4. Write a commit mapping file (old SHA -> new SHA)

Use --scan-only to just list submodules without flattening.

Example:
  git-rewrite flatten -r ./repo-with-submodules -o ./flat-repo
  git-rewrite flatten -r ./repo --scan-only  # list submodules
"""

REMAP_DESCRIPTION = """\
Remap submodule commit references using a mapping file.

When you sanitise or rewrite a submodule repository, its commit SHAs change.
If you have a parent repository that references those submodules, the gitlink
references become invalid. This command updates those references.

The mapping file format is: old_sha new_sha (one per line)
This is the output from a previous sanitise operation.

Optionally rewrite submodule URLs in .gitmodules with --url-rewrite.

Example:
  git-rewrite remap -r ./parent -o ./remapped -m mapping.txt
  git-rewrite remap -r ./repo -o ./out -m map.txt \\
      --url-rewrite ../old-submodule.git ../new-submodule.git
"""

COMPOSE_DESCRIPTION = """\
Compose multiple commit mapping files into one.

When chaining operations (e.g., flatten -> sanitise), each produces a mapping
file. This command composes them: given A->B and B->C mappings, produces A->C.

Mapping files are processed in order, following the chain of transformations.
The format is: old_sha new_sha (one per line).

Example:
  git-rewrite compose -m flatten.txt -m sanitise.txt -o combined.txt
  git-rewrite compose -m a.txt -m b.txt -m c.txt -o final.txt
"""


# ────────────────────────────────────────────────────────────────────────────────────────
def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="git-rewrite",
        description=(
            "Git history rewriting tools for sanitising, flattening, and remapping."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan subcommand
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan repository for sensitive words (read-only)",
        description=SCAN_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_scan_arguments(scan_parser)

    # sanitise subcommand
    sanitise_parser = subparsers.add_parser(
        "sanitise",
        help="Rewrite history to remove sensitive words",
        description=SANITISE_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_sanitise_arguments(sanitise_parser)

    # flatten subcommand
    flatten_parser = subparsers.add_parser(
        "flatten",
        help="Flatten submodules into main repository",
        description=FLATTEN_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_flatten_arguments(flatten_parser)

    # remap subcommand
    remap_parser = subparsers.add_parser(
        "remap",
        help="Remap submodule commit references",
        description=REMAP_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_remap_arguments(remap_parser)

    # compose subcommand
    compose_parser = subparsers.add_parser(
        "compose",
        help="Compose multiple commit mapping files",
        description=COMPOSE_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_compose_arguments(compose_parser)

    return parser


# ────────────────────────────────────────────────────────────────────────────────────────
def add_scan_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the scan subcommand."""
    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        required=True,
        help="Path to the git repository",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        required=True,
        help="Path to JSON config file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )


# ────────────────────────────────────────────────────────────────────────────────────────
def add_sanitise_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the sanitise subcommand."""
    parser.add_argument(
        "--sample-config",
        action="store_true",
        help="Print sample config and exit",
    )
    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        help="Path to source repository",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path for output repository",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to JSON config file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete output directory if exists",
    )
    parser.add_argument(
        "-d",
        "--default",
        default="REDACTED",
        help="Default replacement word (default: REDACTED)",
    )
    parser.add_argument(
        "-m",
        "--commit-map",
        type=Path,
        help="Path to write commit mapping file",
    )
    parser.add_argument(
        "-s",
        "--submodule-map",
        type=Path,
        help="Path to submodule commit mapping file",
    )
    parser.add_argument(
        "--copy-remotes",
        action="store_true",
        help="Copy git remotes from source to output repository",
    )


# ────────────────────────────────────────────────────────────────────────────────────────
def add_flatten_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the flatten subcommand."""
    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        required=True,
        help="Path to source repository",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path for output repository",
    )
    parser.add_argument(
        "-m",
        "--commit-map",
        type=Path,
        help="Path to write commit mapping file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete output directory if exists",
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only scan and list submodules",
    )
    parser.add_argument(
        "--copy-remotes",
        action="store_true",
        help="Copy git remotes from source to output repository",
    )


# ────────────────────────────────────────────────────────────────────────────────────────
def add_remap_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the remap subcommand."""
    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        required=True,
        help="Path to source repository",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path for output repository",
    )
    parser.add_argument(
        "-m",
        "--commit-map",
        type=Path,
        required=True,
        help="Path to commit mapping file (old_sha new_sha per line)",
    )
    parser.add_argument(
        "--submodule-path",
        type=str,
        help="Specific submodule path to remap (for gitlink filtering)",
    )
    parser.add_argument(
        "--url-rewrite",
        nargs=2,
        action="append",
        metavar=("OLD_URL", "NEW_URL"),
        help="Rewrite URL in .gitmodules (can be specified multiple times)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete output directory if exists",
    )
    parser.add_argument(
        "--copy-remotes",
        action="store_true",
        help="Copy git remotes from source to output repository",
    )


# ────────────────────────────────────────────────────────────────────────────────────────
def add_compose_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for the compose subcommand."""
    parser.add_argument(
        "-m",
        "--mapping",
        type=Path,
        action="append",
        dest="mappings",
        required=True,
        help="Mapping file to include (can be specified multiple times, in order)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path for output mapping file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )


# ────────────────────────────────────────────────────────────────────────────────────────
#   Main Entry Point
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def main() -> int:
    """Main entry point."""
    from . import compose
    from . import flatten
    from . import remap
    from . import sanitise
    from . import scan

    parser = create_parser()
    args = parser.parse_args()

    if args.version:
        from . import __version__ as version

        print(f"git-rewrite {version}")
        return 0

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "scan": scan.run,
        "sanitise": sanitise.run,
        "flatten": flatten.run,
        "remap": remap.run,
        "compose": compose.run,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
