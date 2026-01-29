"""Dataset comparison and diffing utilities"""

import json
import hashlib
from typing import Dict, List, Set


def compare_datasets(
    file1: str,
    file2: str,
    verbose: bool = True
) -> Dict:
    """
    Compare two datasets and find differences.

    Args:
        file1: First JSONL file
        file2: Second JSONL file
        verbose: Print report

    Returns:
        Comparison report dict
    """
    # Load both datasets
    set1 = {}
    set2 = {}

    with open(file1, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                # Hash content
                content_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                set1[content_hash] = data
            except:
                continue

    with open(file2, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                content_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                set2[content_hash] = data
            except:
                continue

    # Find differences
    only_in_1 = set(set1.keys()) - set(set2.keys())
    only_in_2 = set(set2.keys()) - set(set1.keys())
    in_both = set(set1.keys()) & set(set2.keys())

    report = {
        "file1": file1,
        "file2": file2,
        "file1_total": len(set1),
        "file2_total": len(set2),
        "in_both": len(in_both),
        "only_in_file1": len(only_in_1),
        "only_in_file2": len(only_in_2),
        "similarity": len(in_both) / max(len(set1), len(set2)) if max(len(set1), len(set2)) > 0 else 0
    }

    if verbose:
        print(f"\n🔍 Dataset Comparison")
        print(f"   File 1: {file1} ({report['file1_total']} examples)")
        print(f"   File 2: {file2} ({report['file2_total']} examples)")
        print(f"\n   Results:")
        print(f"     In both: {report['in_both']}")
        print(f"     Only in file 1: {report['only_in_file1']}")
        print(f"     Only in file 2: {report['only_in_file2']}")
        print(f"     Similarity: {report['similarity']*100:.1f}%")

    return report


def extract_diff(
    file1: str,
    file2: str,
    output_only_1: str = "only_in_1.jsonl",
    output_only_2: str = "only_in_2.jsonl",
    verbose: bool = True
):
    """
    Extract examples that differ between two datasets.

    Args:
        file1: First JSONL
        file2: Second JSONL
        output_only_1: Output for examples only in file1
        output_only_2: Output for examples only in file2
        verbose: Print progress
    """
    # Load and hash
    hashes1 = {}
    hashes2 = set()

    with open(file1, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                content_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                hashes1[content_hash] = line.strip()
            except:
                continue

    with open(file2, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                content_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                hashes2.add(content_hash)
            except:
                continue

    # Find unique to file1
    only_1 = {h: line for h, line in hashes1.items() if h not in hashes2}

    # Write only_in_1
    with open(output_only_1, "w", encoding="utf-8") as f:
        for line in only_1.values():
            f.write(line + "\n")

    # Find unique to file2 (requires re-read)
    with open(file2, "r", encoding="utf-8") as infile, \
         open(output_only_2, "w", encoding="utf-8") as outfile:
        for line in infile:
            try:
                data = json.loads(line.strip())
                content_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                if content_hash not in hashes1:
                    outfile.write(line)
            except:
                continue

    if verbose:
        print(f"\n✅ Diff extraction complete!")
        print(f"   Only in {file1}: {len(only_1)} examples → {output_only_1}")
        print(f"   Only in {file2}: (see file) → {output_only_2}")
