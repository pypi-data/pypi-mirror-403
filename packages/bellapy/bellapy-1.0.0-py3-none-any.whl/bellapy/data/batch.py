"""Batch processing utilities for large datasets"""

import json
import os
from typing import Callable, Optional, List


def process_in_batches(
    input_file: str,
    output_file: str,
    process_fn: Callable[[List[dict]], List[dict]],
    batch_size: int = 100,
    verbose: bool = True
) -> str:
    """
    Process dataset in batches (for memory efficiency or API calls).

    Args:
        input_file: Input JSONL
        output_file: Output JSONL
        process_fn: Function that takes list of dicts, returns list of dicts
        batch_size: Examples per batch
        verbose: Print progress

    Returns:
        Output file path

    Example:
        def add_field(batch):
            for item in batch:
                item['processed'] = True
            return batch

        process_in_batches("input.jsonl", "output.jsonl", add_field, batch_size=50)
    """
    batch = []
    total = 0
    processed = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            total += 1
            try:
                data = json.loads(line.strip())
                batch.append(data)

                # Process when batch full
                if len(batch) >= batch_size:
                    results = process_fn(batch)
                    for result in results:
                        outfile.write(json.dumps(result, ensure_ascii=False) + "\n")
                    processed += len(results)
                    if verbose:
                        print(f"Processed {processed}/{total}...", end='\r')
                    batch = []

            except Exception as e:
                if verbose:
                    print(f"\n⚠️  Error on line {total}: {e}")

        # Process remaining
        if batch:
            results = process_fn(batch)
            for result in results:
                outfile.write(json.dumps(result, ensure_ascii=False) + "\n")
            processed += len(results)

    if verbose:
        print(f"\n✅ Batch processing complete!")
        print(f"   Total: {total}")
        print(f"   Processed: {processed}")
        print(f"   Output: {output_file}")

    return output_file


def chunk_dataset(
    input_file: str,
    output_dir: str,
    chunk_size: int = 1000,
    verbose: bool = True
) -> List[str]:
    """
    Split large dataset into smaller chunks.

    Args:
        input_file: Input JSONL
        output_dir: Directory for chunks
        chunk_size: Lines per chunk
        verbose: Print progress

    Returns:
        List of chunk file paths
    """
    os.makedirs(output_dir, exist_ok=True)

    chunk_files = []
    chunk_num = 0
    lines_in_chunk = 0
    current_chunk = None

    with open(input_file, "r", encoding="utf-8") as infile:
        for line in infile:
            # Start new chunk
            if lines_in_chunk == 0:
                if current_chunk:
                    current_chunk.close()

                chunk_file = os.path.join(output_dir, f"chunk_{chunk_num:04d}.jsonl")
                current_chunk = open(chunk_file, "w", encoding="utf-8")
                chunk_files.append(chunk_file)

            current_chunk.write(line)
            lines_in_chunk += 1

            # Finish chunk
            if lines_in_chunk >= chunk_size:
                current_chunk.close()
                if verbose:
                    print(f"Created chunk {chunk_num} ({chunk_size} lines)")
                chunk_num += 1
                lines_in_chunk = 0
                current_chunk = None

        # Close final chunk
        if current_chunk:
            current_chunk.close()
            if verbose:
                print(f"Created chunk {chunk_num} ({lines_in_chunk} lines)")

    if verbose:
        print(f"\n✅ Created {len(chunk_files)} chunks in {output_dir}")

    return chunk_files
