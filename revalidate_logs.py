"""
Revalidation Script
-------------------
Re-parses and re-validates all existing JSON log files using the current
parser and simulators. Useful after fixing the parser or simulators to
retroactively correct past results.

Usage:
    python revalidate_logs.py                # dry-run (shows changes, writes nothing)
    python revalidate_logs.py --apply        # applies changes to JSON files
"""

import os
import sys
import json
import glob
import argparse

from parser import extract_responses
from main import get_simulator
from config import TEST_RUN


def revalidate_all(log_dir, apply_changes=False):
    json_files = sorted(glob.glob(os.path.join(log_dir, "**", "*.json"), recursive=True))

    if not json_files:
        print(f"No JSON files found in {log_dir}")
        return

    total = 0
    changed = 0
    errors = 0
    flipped_to_correct = 0
    flipped_to_incorrect = 0

    print(f"Scanning {len(json_files)} log files in: {log_dir}")
    print(f"Mode: {'APPLY (writing changes)' if apply_changes else 'DRY-RUN (no changes written)'}")
    print("=" * 80)

    for filepath in json_files:
        filename = os.path.basename(filepath)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  [ERROR] Could not read {filename}: {e}")
            errors += 1
            continue

        meta = data.get("metadata", {})
        raw_response = data.get("raw_response", "")
        old_correct = meta.get("is_correct")
        old_error = meta.get("error_message", "")

        # Re-parse the response with the current parser
        _, final_moves = extract_responses(raw_response)

        # Re-validate with the simulator
        new_correct = False
        new_error = ""

        if not final_moves:
            new_error = "Invalid format or cut off (could not parse move list)"
        else:
            try:
                puzzle = meta.get("puzzle")
                n = meta.get("complexity_n")
                sim = get_simulator(puzzle, n, meta)
                if sim:
                    new_correct, new_error = sim.validate_full_solution(final_moves)
                    if new_correct:
                        new_error = ""
                else:
                    new_error = "Simulator not found"
            except Exception as e:
                new_error = f"Simulator error: {e}"

        total += 1

        # Check if result changed
        if new_correct != old_correct or new_error != old_error:
            changed += 1
            direction = ""
            if old_correct and not new_correct:
                flipped_to_incorrect += 1
                direction = "CORRECT → INCORRECT"
            elif not old_correct and new_correct:
                flipped_to_correct += 1
                direction = "INCORRECT → CORRECT"
            else:
                direction = "error message changed"

            print(f"  [CHANGED] {filename}")
            print(f"           {direction}")
            print(f"           Old: is_correct={old_correct}, error={old_error!r}")
            print(f"           New: is_correct={new_correct}, error={new_error!r}")

            if apply_changes:
                meta["is_correct"] = new_correct
                meta["error_message"] = new_error
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

    # Summary
    print("=" * 80)
    print(f"Total files scanned:       {total}")
    print(f"Read errors:               {errors}")
    print(f"Unchanged:                 {total - changed}")
    print(f"Changed:                   {changed}")
    if changed > 0:
        print(f"  Flipped to CORRECT:      {flipped_to_correct}")
        print(f"  Flipped to INCORRECT:    {flipped_to_incorrect}")
        print(f"  Error message only:      {changed - flipped_to_correct - flipped_to_incorrect}")
    if apply_changes:
        print(f"\n✅ All changes have been written to disk.")
    else:
        print(f"\n⚠️  Dry-run mode — no files were modified. Use --apply to write changes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-validate all experiment log files.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write changes to the JSON files. Without this flag, runs in dry-run mode.",
    )
    parser.add_argument(
        "--log-dir",
        default=None,
        help="Path to the log directory. Defaults to logs/<TEST_RUN>.",
    )
    args = parser.parse_args()

    log_dir = args.log_dir or os.path.join("logs", TEST_RUN)

    if not os.path.isdir(log_dir):
        print(f"Error: Log directory does not exist: {log_dir}")
        sys.exit(1)

    revalidate_all(log_dir, apply_changes=args.apply)
