# ────────────────────────────────────────────────────────────────────────────────────────
#   scanner.py
#   ──────────
#
#   Repository scanning for dirty words using git fast-export.
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

import re
import subprocess
from collections import defaultdict
from pathlib import Path
from ..sanitise.patterns import build_combined_pattern

# ────────────────────────────────────────────────────────────────────────────────────────
#   Functions
# ────────────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────────────
def scan_content_fast(
    content: str,
    pattern: re.Pattern[str],
) -> dict[str, int]:
    """Scan content with combined pattern and return match counts by word."""
    matches: defaultdict[str, int] = defaultdict(int)
    for match in pattern.finditer(content):
        word = match.group(0).lower()
        matches[word] += 1
    return dict(matches)


# ────────────────────────────────────────────────────────────────────────────────────────
def scan_repository(
    repo_path: Path,
    dirty_words: list[str],
    verbose: bool = False,
) -> tuple[dict[str, int], dict[str, int]]:
    """
    Scan repository using fast-export streaming for speed.

    Returns:
        Tuple of (blob_matches, commit_matches) where each is a dict
        mapping dirty word to count of occurrences.
    """
    blob_matches: dict[str, int] = defaultdict(int)
    commit_matches: dict[str, int] = defaultdict(int)

    pattern = build_combined_pattern(dirty_words)

    print("Scanning repository...")

    export_proc = subprocess.Popen(
        ["git", "fast-export", "--all"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    assert export_proc.stdout is not None

    commit_count = 0
    blob_count = 0
    in_data = False
    data_remaining = 0
    data_buffer = b""
    in_commit_message = False
    last_blob_update = 0
    in_blobs_phase = True

    for line in export_proc.stdout:
        if in_data:
            data_buffer += line
            data_remaining -= len(line)

            if data_remaining <= 0:
                in_data = False
                try:
                    text = data_buffer.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        text = data_buffer.decode("latin-1")
                    except UnicodeDecodeError:
                        data_buffer = b""
                        in_commit_message = False
                        continue

                matches = scan_content_fast(text, pattern)
                target = commit_matches if in_commit_message else blob_matches
                for word, count in matches.items():
                    target[word] += count
                    if verbose:
                        location = "commit message" if in_commit_message else "blob"
                        print(f"  Found '{word}' x{count} in {location}")

                if not in_commit_message:
                    blob_count += 1
                    if blob_count - last_blob_update >= 100:
                        print(f"  Scanned {blob_count} blobs...")
                        last_blob_update = blob_count

                data_buffer = b""
                in_commit_message = False

        elif line.startswith(b"data "):
            size_str = line[5:].strip().decode("utf-8")
            data_remaining = int(size_str)
            in_data = True
            data_buffer = b""

        elif line.startswith(b"commit "):
            if in_blobs_phase:
                in_blobs_phase = False
                print(
                    f"  Finished scanning {blob_count} blobs, now scanning commits..."
                )
            commit_count += 1
            in_commit_message = True
            if commit_count % 100 == 0:
                print(f"  Scanned {commit_count} commits...")

        elif line.startswith(b"blob"):
            in_commit_message = False

    export_proc.wait()
    print(f"  Done: {commit_count} commits, {blob_count} blobs")

    return dict(blob_matches), dict(commit_matches)
