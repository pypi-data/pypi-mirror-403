"""Dataset validation utilities"""

import json
import os
from typing import Optional, List, Dict


def validate_format(
    input_file: str,
    expected_format: str = "auto",
    fix: bool = False,
    output_file: Optional[str] = None,
    verbose: bool = True
) -> Dict:
    """
    Validate dataset format and optionally fix issues.

    Args:
        input_file: Input JSONL file
        expected_format: Expected format ("messages", "simple", "auto")
        fix: Attempt to fix format issues
        output_file: Output file if fixing (default: input_fixed.jsonl)
        verbose: Print progress

    Returns:
        Validation report dict
    """
    if not os.path.exists(input_file):
        if verbose:
            print(f"❌ Error: {input_file} not found.")
        return {}

    if fix and not output_file:
        output_file = input_file.replace('.jsonl', '_fixed.jsonl')

    report = {
        "total_lines": 0,
        "valid": 0,
        "invalid": 0,
        "errors": [],
        "format_counts": {"messages": 0, "simple": 0, "unknown": 0}
    }

    outfile = open(output_file, "w", encoding="utf-8") if fix else None

    with open(input_file, "r", encoding="utf-8") as infile:
        for i, line in enumerate(infile, 1):
            report["total_lines"] += 1

            try:
                data = json.loads(line.strip())

                # Detect format
                if "messages" in data:
                    report["format_counts"]["messages"] += 1

                    # Validate messages structure
                    if not isinstance(data["messages"], list):
                        raise ValueError("messages must be a list")

                    if len(data["messages"]) < 2:
                        raise ValueError("messages must have at least 2 entries")

                    for msg in data["messages"]:
                        if "role" not in msg or "content" not in msg:
                            raise ValueError("message missing role or content")

                    report["valid"] += 1
                    if outfile:
                        outfile.write(line)

                elif "user" in data and ("assistant" in data or "EzrA" in data):
                    report["format_counts"]["simple"] += 1

                    # Validate simple format
                    user = data.get("user", "")
                    assistant = data.get("assistant", data.get("EzrA", ""))

                    if not user or not assistant:
                        raise ValueError("user or assistant content is empty")

                    report["valid"] += 1
                    if outfile:
                        outfile.write(line)

                else:
                    report["format_counts"]["unknown"] += 1
                    raise ValueError("unknown format")

            except json.JSONDecodeError as e:
                report["invalid"] += 1
                report["errors"].append(f"Line {i}: Invalid JSON - {str(e)}")

            except ValueError as e:
                report["invalid"] += 1
                report["errors"].append(f"Line {i}: {str(e)}")

            except Exception as e:
                report["invalid"] += 1
                report["errors"].append(f"Line {i}: {str(e)}")

    if outfile:
        outfile.close()

    if verbose:
        print(f"\n📊 Validation Report: {input_file}")
        print(f"   Total lines: {report['total_lines']}")
        print(f"   ✅ Valid: {report['valid']}")
        print(f"   ❌ Invalid: {report['invalid']}")
        print(f"\n   Format distribution:")
        print(f"     - Messages: {report['format_counts']['messages']}")
        print(f"     - Simple: {report['format_counts']['simple']}")
        print(f"     - Unknown: {report['format_counts']['unknown']}")

        if report["errors"] and len(report["errors"]) <= 10:
            print(f"\n   Errors:")
            for error in report["errors"]:
                print(f"     {error}")
        elif report["errors"]:
            print(f"\n   Errors (showing first 10 of {len(report['errors'])}):")
            for error in report["errors"][:10]:
                print(f"     {error}")

        if fix and output_file:
            print(f"\n   Fixed file: {output_file}")

    return report


def check_duplicates_detailed(
    input_file: str,
    show_examples: bool = False,
    verbose: bool = True
) -> Dict:
    """
    Detailed duplicate analysis.

    Args:
        input_file: Input JSONL file
        show_examples: Show example duplicates
        verbose: Print report

    Returns:
        Duplicate report dict
    """
    import hashlib
    from collections import defaultdict

    hashes = defaultdict(list)
    total = 0

    with open(input_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            total += 1
            line_hash = hashlib.md5(line.strip().encode("utf-8")).hexdigest()
            hashes[line_hash].append((i, line.strip()))

    duplicates = {h: lines for h, lines in hashes.items() if len(lines) > 1}

    report = {
        "total": total,
        "unique": len(hashes),
        "duplicate_groups": len(duplicates),
        "total_duplicates": sum(len(lines) - 1 for lines in duplicates.values()),
        "examples": []
    }

    if show_examples and duplicates:
        # Show first 3 duplicate groups
        for i, (hash_val, lines) in enumerate(list(duplicates.items())[:3]):
            try:
                example = json.loads(lines[0][1])
                report["examples"].append({
                    "count": len(lines),
                    "line_numbers": [l[0] for l in lines],
                    "content": example
                })
            except:
                pass

    if verbose:
        print(f"\n🔍 Duplicate Analysis: {input_file}")
        print(f"   Total: {report['total']}")
        print(f"   Unique: {report['unique']}")
        print(f"   Duplicates: {report['total_duplicates']}")
        print(f"   Duplicate groups: {report['duplicate_groups']}")

        if show_examples and report["examples"]:
            print(f"\n   Example duplicates:")
            for ex in report["examples"]:
                print(f"     - Found {ex['count']} times at lines: {ex['line_numbers'][:5]}")

    return report
