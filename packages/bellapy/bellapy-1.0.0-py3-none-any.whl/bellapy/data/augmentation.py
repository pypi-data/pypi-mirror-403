"""Data augmentation utilities"""

import json
import os
from typing import Optional, List


def paraphrase_with_gpt(
    input_file: str,
    output_file: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
    variations: int = 1,
    verbose: bool = True
) -> Optional[str]:
    """
    Augment dataset by paraphrasing with GPT.

    Args:
        input_file: Input JSONL
        output_file: Output JSONL
        api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        model: Model to use
        variations: Paraphrases per example
        verbose: Print progress

    Returns:
        Output file path
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ Error: openai package required")
        print("   Install: pip install openai")
        return None

    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        return None

    if not output_file:
        output_file = input_file.replace('.jsonl', '_augmented.jsonl')

    client = OpenAI(api_key=api_key)

    count = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                data = json.loads(line.strip())

                # Get content
                if "messages" in data:
                    user = data["messages"][0].get("content", "")
                    assistant = data["messages"][1].get("content", "")
                else:
                    user = data.get("user", "")
                    assistant = data.get("assistant", data.get("EzrA", ""))

                # Write original
                outfile.write(line)
                count += 1

                # Generate paraphrases
                for _ in range(variations):
                    prompt = f"Paraphrase this conversation while preserving meaning:\nUser: {user}\nAssistant: {assistant}\n\nReturn ONLY the paraphrased conversation in the same format."

                    response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.8
                    )

                    paraphrased = response.choices[0].message.content

                    # Simple extraction (could be improved)
                    lines = paraphrased.strip().split('\n')
                    if len(lines) >= 2:
                        new_user = lines[0].replace("User:", "").strip()
                        new_assistant = lines[1].replace("Assistant:", "").strip()

                        new_data = {
                            "user": new_user,
                            "assistant": new_assistant
                        }

                        outfile.write(json.dumps(new_data, ensure_ascii=False) + "\n")
                        count += 1

                if verbose and count % 10 == 0:
                    print(f"Processed {count} examples...", end='\r')

            except Exception as e:
                if verbose:
                    print(f"\n⚠️  Error: {e}")

    if verbose:
        print(f"\n✅ Augmentation complete: {count} total examples")

    return output_file


def balance_dataset(
    input_file: str,
    output_file: Optional[str] = None,
    target_count: Optional[int] = None,
    strategy: str = "oversample",
    verbose: bool = True
) -> Optional[str]:
    """
    Balance dataset by category (length buckets).

    Args:
        input_file: Input JSONL
        output_file: Output JSONL
        target_count: Target count per bucket (None = max bucket size)
        strategy: "oversample" (duplicate) or "undersample" (remove)
        verbose: Print progress

    Returns:
        Output file path
    """
    import random

    if not output_file:
        output_file = input_file.replace('.jsonl', '_balanced.jsonl')

    # Categorize by length
    buckets = {"short": [], "medium": [], "long": []}

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())

                # Get assistant length
                if "messages" in data:
                    content = data["messages"][1].get("content", "")
                else:
                    content = data.get("assistant", data.get("EzrA", ""))

                length = len(content)

                if length < 50:
                    buckets["short"].append(line.strip())
                elif length < 200:
                    buckets["medium"].append(line.strip())
                else:
                    buckets["long"].append(line.strip())

            except:
                continue

    # Determine target
    if target_count is None:
        target_count = max(len(b) for b in buckets.values())

    # Balance
    balanced = []

    for bucket_name, examples in buckets.items():
        if strategy == "oversample":
            # Duplicate to reach target
            while len(examples) < target_count:
                examples.append(random.choice(examples))
            balanced.extend(examples[:target_count])

        else:  # undersample
            # Random sample to target
            if len(examples) > target_count:
                balanced.extend(random.sample(examples, target_count))
            else:
                balanced.extend(examples)

    random.shuffle(balanced)

    # Write
    with open(output_file, "w", encoding="utf-8") as f:
        for line in balanced:
            f.write(line + "\n")

    if verbose:
        print(f"✅ Dataset balanced: {output_file}")
        print(f"   Short: {len(buckets['short'])} → {target_count}")
        print(f"   Medium: {len(buckets['medium'])} → {target_count}")
        print(f"   Long: {len(buckets['long'])} → {target_count}")
        print(f"   Total: {len(balanced)}")

    return output_file
