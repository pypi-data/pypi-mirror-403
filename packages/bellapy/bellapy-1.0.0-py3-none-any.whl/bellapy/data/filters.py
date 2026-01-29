"""Dataset filtering utilities"""

import json
import os
import re
from typing import Optional, Callable


def filter_by_length(
    input_file: str,
    output_file: Optional[str] = None,
    min_length: int = 0,
    max_length: int = 10000,
    key: str = "assistant",
    verbose: bool = True
) -> Optional[str]:
    """
    Filter dataset by content length.

    Args:
        input_file: Input JSONL file
        output_file: Output file
        min_length: Minimum character length
        max_length: Maximum character length
        key: Which content to measure ("user" or "assistant")
        verbose: Print progress

    Returns:
        Path to output file
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', '_filtered.jsonl')

    kept = 0
    removed = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                data = json.loads(line.strip())

                # Get content
                if "messages" in data:
                    content = data["messages"][0]["content"] if key == "user" else data["messages"][1]["content"]
                else:
                    content = data.get(key, data.get("EzrA", data.get("assistant", "")))

                length = len(content)

                if min_length <= length <= max_length:
                    outfile.write(line)
                    kept += 1
                else:
                    removed += 1

            except Exception:
                removed += 1

    if verbose:
        print(f"✅ Filtering complete!")
        print(f"   Kept: {kept}")
        print(f"   Removed: {removed}")
        print(f"   Output: {output_file}")

    return output_file


def filter_by_pattern(
    input_file: str,
    output_file: Optional[str] = None,
    pattern: str = "",
    inverse: bool = False,
    key: str = "assistant",
    verbose: bool = True
) -> Optional[str]:
    """
    Filter dataset by regex pattern.

    Args:
        input_file: Input JSONL file
        output_file: Output file
        pattern: Regex pattern to match
        inverse: If True, keep non-matches (exclude matches)
        key: Which content to search ("user" or "assistant")
        verbose: Print progress

    Returns:
        Path to output file
    """
    if not output_file:
        suffix = "_excluded.jsonl" if inverse else "_matched.jsonl"
        output_file = input_file.replace('.jsonl', suffix)

    kept = 0
    removed = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                data = json.loads(line.strip())

                # Get content
                if "messages" in data:
                    content = data["messages"][0]["content"] if key == "user" else data["messages"][1]["content"]
                else:
                    content = data.get(key, data.get("EzrA", data.get("assistant", "")))

                matches = bool(re.search(pattern, content, re.IGNORECASE))

                # Keep if matches and not inverse, or doesn't match and inverse
                if matches != inverse:
                    outfile.write(line)
                    kept += 1
                else:
                    removed += 1

            except Exception:
                removed += 1

    if verbose:
        action = "excluding" if inverse else "matching"
        print(f"✅ Pattern filtering ({action}) complete!")
        print(f"   Pattern: {pattern}")
        print(f"   Kept: {kept}")
        print(f"   Removed: {removed}")
        print(f"   Output: {output_file}")

    return output_file


def filter_by_quality(
    input_file: str,
    output_file: Optional[str] = None,
    min_words: int = 3,
    max_repetition: float = 0.5,
    remove_urls: bool = True,
    verbose: bool = True
) -> Optional[str]:
    """
    Filter dataset by quality heuristics.

    Removes:
    - Very short responses (< min_words)
    - Highly repetitive text
    - Responses that are mostly URLs

    Args:
        input_file: Input JSONL file
        output_file: Output file
        min_words: Minimum word count
        max_repetition: Max ratio of repeated words
        remove_urls: Remove responses that are mostly URLs
        verbose: Print progress

    Returns:
        Path to output file
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', '_quality.jsonl')

    kept = 0
    removed = 0
    removed_short = 0
    removed_repetitive = 0
    removed_urls = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                data = json.loads(line.strip())

                # Get assistant content
                if "messages" in data:
                    content = data["messages"][1]["content"]
                else:
                    content = data.get("EzrA", data.get("assistant", ""))

                # Check word count
                words = content.split()
                if len(words) < min_words:
                    removed_short += 1
                    removed += 1
                    continue

                # Check repetition
                unique_words = set(words)
                repetition_ratio = 1 - (len(unique_words) / len(words))
                if repetition_ratio > max_repetition:
                    removed_repetitive += 1
                    removed += 1
                    continue

                # Check URL ratio
                if remove_urls:
                    url_count = len(re.findall(r'https?://\S+|www\.\S+', content))
                    if url_count / len(words) > 0.3:  # More than 30% URLs
                        removed_urls += 1
                        removed += 1
                        continue

                # Passed all checks
                outfile.write(line)
                kept += 1

            except Exception:
                removed += 1

    if verbose:
        print(f"✅ Quality filtering complete!")
        print(f"   Kept: {kept}")
        print(f"   Removed total: {removed}")
        print(f"     - Too short: {removed_short}")
        print(f"     - Repetitive: {removed_repetitive}")
        print(f"     - URL-heavy: {removed_urls}")
        print(f"   Output: {output_file}")

    return output_file


def filter_custom(
    input_file: str,
    output_file: Optional[str] = None,
    filter_fn: Callable[[dict], bool] = None,
    verbose: bool = True
) -> Optional[str]:
    """
    Filter dataset with custom function.

    Args:
        input_file: Input JSONL file
        output_file: Output file
        filter_fn: Custom filter function, returns True to keep
        verbose: Print progress

    Returns:
        Path to output file

    Example:
        def my_filter(data):
            # Keep only examples with user questions
            user = data.get("user", "")
            return "?" in user

        filter_custom("input.jsonl", "output.jsonl", my_filter)
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', '_custom.jsonl')

    if filter_fn is None:
        print("❌ Error: filter_fn is required")
        return None

    kept = 0
    removed = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                data = json.loads(line.strip())

                if filter_fn(data):
                    outfile.write(line)
                    kept += 1
                else:
                    removed += 1

            except Exception:
                removed += 1

    if verbose:
        print(f"✅ Custom filtering complete!")
        print(f"   Kept: {kept}")
        print(f"   Removed: {removed}")
        print(f"   Output: {output_file}")

    return output_file
