"""Dataset processing utilities: deduplication, merging, statistics"""

import json
import hashlib
import os
from typing import Optional, List, Tuple
from pathlib import Path


def deduplicate(
    input_file: str,
    output_file: Optional[str] = None,
    verbose: bool = True
) -> Optional[str]:
    """
    Remove exact duplicates using MD5 hash.

    Args:
        input_file: Path to input JSONL file
        output_file: Path to output file (default: input_UNIQUE.jsonl)
        verbose: Print progress messages

    Returns:
        Path to output file, or None if error
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', '_UNIQUE.jsonl')

    if not os.path.exists(input_file):
        if verbose:
            print(f"❌ Error: {input_file} not found.")
        return None

    if verbose:
        print(f"🚀 Deduplicating {input_file}...")

    seen_hashes = set()
    unique_count = 0
    duplicate_count = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            line = line.strip()
            if not line:
                continue

            line_hash = hashlib.md5(line.encode("utf-8")).hexdigest()

            if line_hash not in seen_hashes:
                outfile.write(line + "\n")
                seen_hashes.add(line_hash)
                unique_count += 1
            else:
                duplicate_count += 1

    if verbose:
        print(f"\n✅ Deduplication Complete!")
        print(f"   - Unique: {unique_count}")
        print(f"   - Duplicates removed: {duplicate_count}")
        print(f"   - Output: {output_file}")

    return output_file


def merge_files(
    output_file: str,
    input_files: List[str],
    dedupe: bool = True,
    verbose: bool = True
) -> Optional[str]:
    """
    Merge multiple JSONL files with optional deduplication.

    Args:
        output_file: Path to output merged file
        input_files: List of input file paths
        dedupe: Remove duplicates during merge
        verbose: Print progress messages

    Returns:
        Path to output file, or None if error
    """
    if verbose:
        print(f"🔗 Merging {len(input_files)} files...")

    total_count = 0
    unique_messages = set() if dedupe else None

    with open(output_file, "w", encoding="utf-8") as outfile:
        for file_path in input_files:
            if not os.path.exists(file_path):
                if verbose:
                    print(f"⚠️  Warning: {file_path} not found. Skipping.")
                continue

            count = 0
            with open(file_path, "r", encoding="utf-8") as infile:
                for line in infile:
                    try:
                        data = json.loads(line)

                        if dedupe:
                            msg_key = json.dumps(data, sort_keys=True)
                            if msg_key in unique_messages:
                                continue
                            unique_messages.add(msg_key)

                        outfile.write(line.strip() + "\n")
                        count += 1
                        total_count += 1

                    except Exception as e:
                        if verbose:
                            print(f"⚠️  Error in {file_path}: {e}")
                        continue

            if verbose:
                print(f"   ✓ {file_path}: {count} examples")

    if verbose:
        print(f"\n✅ Merge Complete!")
        print(f"   - Total examples: {total_count}")
        print(f"   - Output: {output_file}")

    return output_file


def get_stats(input_file: str, verbose: bool = True) -> dict:
    """
    Get statistics about a dataset.

    Args:
        input_file: Path to JSONL file
        verbose: Print statistics

    Returns:
        Dictionary containing dataset statistics
    """
    if not os.path.exists(input_file):
        if verbose:
            print(f"❌ Error: {input_file} not found.")
        return {}

    stats = {
        "total": 0,
        "duplicates": 0,
        "formats": {"messages": 0, "user_ezra": 0, "user_assistant": 0, "other": 0},
        "user_lengths": [],
        "assistant_lengths": [],
    }

    seen_hashes = set()

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                stats["total"] += 1

                # Check for duplicates
                line_hash = hashlib.md5(line.strip().encode("utf-8")).hexdigest()
                if line_hash in seen_hashes:
                    stats["duplicates"] += 1
                seen_hashes.add(line_hash)

                # Detect format and collect lengths
                if "messages" in data:
                    stats["formats"]["messages"] += 1
                    if len(data["messages"]) >= 2:
                        stats["user_lengths"].append(len(data["messages"][0]["content"]))
                        stats["assistant_lengths"].append(len(data["messages"][1]["content"]))
                elif "user" in data and "EzrA" in data:
                    stats["formats"]["user_ezra"] += 1
                    stats["user_lengths"].append(len(data["user"]))
                    stats["assistant_lengths"].append(len(data["EzrA"]))
                elif "user" in data and "assistant" in data:
                    stats["formats"]["user_assistant"] += 1
                    stats["user_lengths"].append(len(data["user"]))
                    stats["assistant_lengths"].append(len(data["assistant"]))
                else:
                    stats["formats"]["other"] += 1

            except Exception:
                continue

    if verbose and stats["total"] > 0:
        print(f"📊 Dataset Statistics: {input_file}\n")
        print(f"Total Examples: {stats['total']}")
        print(f"Duplicates: {stats['duplicates']} ({stats['duplicates']/stats['total']*100:.1f}%)")
        print(f"\nFormats:")
        for fmt, count in stats["formats"].items():
            print(f"  - {fmt}: {count}")

        if stats["user_lengths"]:
            avg_user = sum(stats["user_lengths"]) / len(stats["user_lengths"])
            avg_assistant = sum(stats["assistant_lengths"]) / len(stats["assistant_lengths"])
            print(f"\nContent Lengths:")
            print(f"  - User avg: {avg_user:.0f} chars")
            print(f"  - Assistant avg: {avg_assistant:.0f} chars")
            print(f"  - User min/max: {min(stats['user_lengths'])}/{max(stats['user_lengths'])}")
            print(f"  - Assistant min/max: {min(stats['assistant_lengths'])}/{max(stats['assistant_lengths'])}")

    return stats


def split_dataset(
    input_file: str,
    train_ratio: float = 0.9,
    shuffle: bool = True,
    verbose: bool = True
) -> Tuple[Optional[str], Optional[str]]:
    """
    Split dataset into train/test sets.

    Args:
        input_file: Path to input JSONL file
        train_ratio: Ratio of training data (0.0-1.0)
        shuffle: Shuffle data before splitting
        verbose: Print progress messages

    Returns:
        Tuple of (train_file, test_file) paths
    """
    if not os.path.exists(input_file):
        if verbose:
            print(f"❌ Error: {input_file} not found.")
        return None, None

    base = input_file.replace('.jsonl', '')
    train_file = f"{base}_train.jsonl"
    test_file = f"{base}_test.jsonl"

    if verbose:
        print(f"✂️  Splitting {input_file}...")

    # Load all lines
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    total = len(lines)

    # Shuffle if requested
    if shuffle:
        import random
        random.shuffle(lines)

    train_size = int(total * train_ratio)

    # Write splits
    with open(train_file, "w", encoding="utf-8") as f:
        for line in lines[:train_size]:
            f.write(line + "\n")

    with open(test_file, "w", encoding="utf-8") as f:
        for line in lines[train_size:]:
            f.write(line + "\n")

    if verbose:
        print(f"\n✅ Split Complete!")
        print(f"   - Train: {train_size} examples ({train_file})")
        print(f"   - Test: {total - train_size} examples ({test_file})")

    return train_file, test_file
