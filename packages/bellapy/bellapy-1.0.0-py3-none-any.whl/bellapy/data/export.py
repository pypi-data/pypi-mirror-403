"""Export datasets to different formats (CSV, Parquet, etc.)"""

import json
import csv
from typing import Optional


def to_csv(
    input_file: str,
    output_file: Optional[str] = None,
    verbose: bool = True
) -> Optional[str]:
    """
    Export JSONL to CSV.

    Args:
        input_file: Input JSONL
        output_file: Output CSV (default: input.csv)
        verbose: Print progress

    Returns:
        Output file path
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', '.csv')

    rows = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())

                # Flatten to simple format
                if "messages" in data:
                    user = data["messages"][0].get("content", "") if len(data["messages"]) > 0 else ""
                    assistant = data["messages"][1].get("content", "") if len(data["messages"]) > 1 else ""
                else:
                    user = data.get("user", "")
                    assistant = data.get("assistant", data.get("EzrA", ""))

                rows.append({"user": user, "assistant": assistant})

            except:
                continue

    # Write CSV
    with open(output_file, "w", newline='', encoding="utf-8") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=["user", "assistant"])
            writer.writeheader()
            writer.writerows(rows)

    if verbose:
        print(f"✅ Exported to CSV: {output_file} ({len(rows)} rows)")

    return output_file


def to_parquet(
    input_file: str,
    output_file: Optional[str] = None,
    verbose: bool = True
) -> Optional[str]:
    """
    Export JSONL to Parquet (requires pyarrow or fastparquet).

    Args:
        input_file: Input JSONL
        output_file: Output Parquet (default: input.parquet)
        verbose: Print progress

    Returns:
        Output file path
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', '.parquet')

    try:
        import pandas as pd
    except ImportError:
        print("❌ Error: pandas required for Parquet export")
        print("   Install: pip install pandas pyarrow")
        return None

    # Load to DataFrame
    data = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line.strip())

                # Flatten
                if "messages" in item:
                    user = item["messages"][0].get("content", "") if len(item["messages"]) > 0 else ""
                    assistant = item["messages"][1].get("content", "") if len(item["messages"]) > 1 else ""
                else:
                    user = item.get("user", "")
                    assistant = item.get("assistant", item.get("EzrA", ""))

                data.append({"user": user, "assistant": assistant})

            except:
                continue

    df = pd.DataFrame(data)
    df.to_parquet(output_file, index=False)

    if verbose:
        print(f"✅ Exported to Parquet: {output_file} ({len(df)} rows)")

    return output_file


def to_txt(
    input_file: str,
    output_file: Optional[str] = None,
    format_template: str = "User: {user}\nAssistant: {assistant}\n\n---\n\n",
    verbose: bool = True
) -> Optional[str]:
    """
    Export JSONL to plain text with custom formatting.

    Args:
        input_file: Input JSONL
        output_file: Output TXT (default: input.txt)
        format_template: Template string with {user} and {assistant}
        verbose: Print progress

    Returns:
        Output file path
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', '.txt')

    count = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                data = json.loads(line.strip())

                # Extract content
                if "messages" in data:
                    user = data["messages"][0].get("content", "") if len(data["messages"]) > 0 else ""
                    assistant = data["messages"][1].get("content", "") if len(data["messages"]) > 1 else ""
                else:
                    user = data.get("user", "")
                    assistant = data.get("assistant", data.get("EzrA", ""))

                # Write formatted
                outfile.write(format_template.format(user=user, assistant=assistant))
                count += 1

            except:
                continue

    if verbose:
        print(f"✅ Exported to TXT: {output_file} ({count} conversations)")

    return output_file
