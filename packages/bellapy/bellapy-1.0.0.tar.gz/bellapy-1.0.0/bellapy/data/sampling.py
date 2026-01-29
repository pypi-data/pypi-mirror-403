"""Dataset sampling utilities"""

import json
import random
import os
from typing import Optional


def sample_dataset(
    input_file: str,
    output_file: Optional[str] = None,
    n: Optional[int] = None,
    ratio: Optional[float] = None,
    shuffle: bool = True,
    seed: Optional[int] = None,
    verbose: bool = True
) -> Optional[str]:
    """
    Sample a subset of dataset.

    Args:
        input_file: Input JSONL file
        output_file: Output file (default: input_sampled.jsonl)
        n: Number of examples to sample (mutually exclusive with ratio)
        ratio: Ratio of examples to sample 0.0-1.0 (mutually exclusive with n)
        shuffle: Shuffle before sampling
        seed: Random seed for reproducibility
        verbose: Print progress

    Returns:
        Path to output file
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', '_sampled.jsonl')

    if not os.path.exists(input_file):
        if verbose:
            print(f"❌ Error: {input_file} not found.")
        return None

    if n is None and ratio is None:
        if verbose:
            print("❌ Error: Must specify either n or ratio")
        return None

    if n is not None and ratio is not None:
        if verbose:
            print("❌ Error: Cannot specify both n and ratio")
        return None

    # Set random seed
    if seed is not None:
        random.seed(seed)

    # Load all lines
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    total = len(lines)

    # Calculate sample size
    if ratio is not None:
        n = int(total * ratio)

    if n > total:
        if verbose:
            print(f"⚠️  Warning: Requested {n} samples but only {total} available")
        n = total

    # Shuffle if requested
    if shuffle:
        random.shuffle(lines)

    # Sample
    sampled = lines[:n]

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        for line in sampled:
            f.write(line + "\n")

    if verbose:
        print(f"✅ Sampled {n} examples from {total}")
        print(f"   Output: {output_file}")

    return output_file


def stratified_sample(
    input_file: str,
    output_file: Optional[str] = None,
    ratio: float = 0.1,
    key: str = "user",
    seed: Optional[int] = None,
    verbose: bool = True
) -> Optional[str]:
    """
    Stratified sampling based on content length.

    Ensures samples are representative across different content lengths.

    Args:
        input_file: Input JSONL file
        output_file: Output file
        ratio: Sample ratio
        key: Key to stratify on ("user" or "assistant")
        seed: Random seed
        verbose: Print progress

    Returns:
        Path to output file
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', '_stratified.jsonl')

    if seed is not None:
        random.seed(seed)

    # Load and categorize by length
    short = []  # < 50 chars
    medium = []  # 50-200 chars
    long = []  # > 200 chars

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())

                # Get content
                if "messages" in data:
                    content = data["messages"][0]["content"] if key == "user" else data["messages"][1]["content"]
                else:
                    content = data.get(key, "")

                length = len(content)

                if length < 50:
                    short.append(line.strip())
                elif length < 200:
                    medium.append(line.strip())
                else:
                    long.append(line.strip())

            except Exception:
                continue

    # Sample from each bucket
    n_short = int(len(short) * ratio)
    n_medium = int(len(medium) * ratio)
    n_long = int(len(long) * ratio)

    sampled = (
        random.sample(short, n_short) if n_short > 0 else [] +
        random.sample(medium, n_medium) if n_medium > 0 else [] +
        random.sample(long, n_long) if n_long > 0 else []
    )

    random.shuffle(sampled)

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        for line in sampled:
            f.write(line + "\n")

    if verbose:
        print(f"✅ Stratified sample complete!")
        print(f"   Short (<50): {n_short}/{len(short)}")
        print(f"   Medium (50-200): {n_medium}/{len(medium)}")
        print(f"   Long (>200): {n_long}/{len(long)}")
        print(f"   Total: {len(sampled)}")
        print(f"   Output: {output_file}")

    return output_file
