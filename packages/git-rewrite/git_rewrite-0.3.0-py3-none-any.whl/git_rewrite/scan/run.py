# ────────────────────────────────────────────────────────────────────────────────────────
#   scan/run.py
#   ───────────
#
#   CLI runner for the scan subcommand.
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
from ..sanitise.config import load_config
from .scanner import scan_repository

# ────────────────────────────────────────────────────────────────────────────────────────
#   Runner
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def run(args: argparse.Namespace) -> int:
    """Run the scan subcommand."""
    # Validate paths
    if not args.repo.exists():
        print(f"Error: Repository not found: {args.repo}", file=sys.stderr)
        return 1
    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        return 1

    # Load config
    config = load_config(args.config)
    words = config.get("words", [])

    if not words:
        print("Error: No words specified in config file", file=sys.stderr)
        return 1

    print(f"Scanning for {len(words)} dirty words...")
    blob_matches, commit_matches = scan_repository(args.repo, words, args.verbose)

    # Report results
    total_blob = sum(blob_matches.values())
    total_commit = sum(commit_matches.values())

    print("\n" + "=" * 60)
    print("SCAN RESULTS")
    print("=" * 60)

    if blob_matches:
        print("\nMatches in file contents:")
        for word, count in sorted(blob_matches.items(), key=lambda x: -x[1]):
            print(f"  {word}: {count}")

    if commit_matches:
        print("\nMatches in commit messages:")
        for word, count in sorted(commit_matches.items(), key=lambda x: -x[1]):
            print(f"  {word}: {count}")

    print(f"\nTotal: {total_blob} in files, {total_commit} in commits")

    if total_blob == 0 and total_commit == 0:
        print("\nNo dirty words found!")

    return 0
