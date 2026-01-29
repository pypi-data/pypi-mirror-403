"""Dataset format conversion utilities"""

import json
import os
from typing import Optional, Dict, Any


def to_openai_format(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert item to OpenAI fine-tuning format.

    Handles:
    - {"user": "...", "assistant": "..."} → {"messages": [...]}
    - {"user": "...", "EzrA": "..."} → {"messages": [...]}
    - Already in messages format → pass through

    Args:
        item: Dictionary with conversation data

    Returns:
        Dictionary in OpenAI messages format
    """
    if "messages" in item:
        # Already in OpenAI format
        return item

    # Convert simple format to messages
    user_text = item.get("user", "")
    assistant_text = item.get("EzrA", item.get("assistant", ""))

    return {
        "messages": [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text}
        ]
    }


def to_hf_format(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert item to HuggingFace format (similar to OpenAI).

    Args:
        item: Dictionary with conversation data

    Returns:
        Dictionary in HF format
    """
    # HF format is similar to OpenAI
    return to_openai_format(item)


def to_simple_format(
    item: Dict[str, Any],
    assistant_key: str = "assistant"
) -> Dict[str, Any]:
    """
    Convert item to simple user/assistant format.

    Args:
        item: Dictionary with conversation data
        assistant_key: Key to use for assistant ("assistant" or "EzrA")

    Returns:
        Dictionary in simple format
    """
    if "messages" in item:
        messages = item["messages"]
        user_text = messages[0]["content"] if len(messages) > 0 else ""
        assistant_text = messages[1]["content"] if len(messages) > 1 else ""
    else:
        user_text = item.get("user", "")
        assistant_text = item.get("EzrA", item.get("assistant", ""))

    return {
        "user": user_text,
        assistant_key: assistant_text
    }


def convert_format(
    input_file: str,
    output_file: Optional[str] = None,
    target_format: str = "messages",
    assistant_key: str = "assistant",
    verbose: bool = True
) -> Optional[str]:
    """
    Convert JSONL file between different formats.

    Args:
        input_file: Path to input JSONL file
        output_file: Path to output file (default: input_{format}.jsonl)
        target_format: Target format ("messages", "simple", "openai", "hf")
        assistant_key: Key for assistant in simple format ("assistant" or "EzrA")
        verbose: Print progress

    Returns:
        Path to output file, or None if error
    """
    if not output_file:
        output_file = input_file.replace('.jsonl', f'_{target_format}.jsonl')

    if not os.path.exists(input_file):
        if verbose:
            print(f"❌ Error: {input_file} not found.")
        return None

    if verbose:
        print(f"🔄 Converting {input_file} to {target_format} format...")

    count = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                data = json.loads(line.strip())

                if target_format in ("messages", "openai"):
                    new_data = to_openai_format(data)
                elif target_format == "hf":
                    new_data = to_hf_format(data)
                elif target_format == "simple":
                    new_data = to_simple_format(data, assistant_key=assistant_key)
                else:
                    if verbose:
                        print(f"❌ Unknown format: {target_format}")
                    return None

                outfile.write(json.dumps(new_data, ensure_ascii=False) + "\n")
                count += 1

            except Exception as e:
                if verbose:
                    print(f"⚠️  Error: {e}")
                continue

    if verbose:
        print(f"\n✅ Conversion Complete!")
        print(f"   - Converted: {count} examples")
        print(f"   - Output: {output_file}")

    return output_file


def batch_convert(
    input_files: list,
    output_dir: str,
    target_format: str = "messages",
    verbose: bool = True
) -> list:
    """
    Convert multiple files to a target format.

    Args:
        input_files: List of input file paths
        output_dir: Directory for output files
        target_format: Target format
        verbose: Print progress

    Returns:
        List of output file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = []

    for input_file in input_files:
        filename = os.path.basename(input_file)
        output_file = os.path.join(output_dir, filename.replace('.jsonl', f'_{target_format}.jsonl'))
        result = convert_format(input_file, output_file, target_format, verbose=verbose)
        if result:
            output_files.append(result)

    return output_files
