"""Cost estimation and token budgeting for API calls"""

import json
from typing import Dict, Optional


def estimate_api_cost(
    input_file: str,
    model: str = "gpt-4o",
    operation: str = "completion",
    verbose: bool = True
) -> Dict:
    """
    Estimate API costs for dataset processing.

    Args:
        input_file: Input JSONL
        model: Model name for pricing
        operation: "completion" or "embedding"
        verbose: Print report

    Returns:
        Cost estimation dict
    """
    # Pricing (as of Jan 2026, per 1M tokens)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "text-embedding-3-small": {"input": 0.02, "output": 0},
        "text-embedding-3-large": {"input": 0.13, "output": 0},
    }

    if model not in PRICING:
        model = "gpt-4o"  # default

    pricing = PRICING[model]

    # Count tokens
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
    except:
        encoding = None

    total_input_tokens = 0
    total_output_tokens = 0
    examples = 0

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                examples += 1

                # Get content
                if "messages" in data:
                    for msg in data["messages"]:
                        content = msg.get("content", "")
                        if encoding:
                            tokens = len(encoding.encode(content))
                        else:
                            tokens = len(content) // 4  # rough estimate

                        if msg.get("role") == "user":
                            total_input_tokens += tokens
                        else:
                            total_output_tokens += tokens
                else:
                    user = data.get("user", "")
                    assistant = data.get("assistant", data.get("EzrA", ""))

                    if encoding:
                        total_input_tokens += len(encoding.encode(user))
                        total_output_tokens += len(encoding.encode(assistant))
                    else:
                        total_input_tokens += len(user) // 4
                        total_output_tokens += len(assistant) // 4

            except:
                continue

    # Calculate costs
    input_cost = (total_input_tokens / 1_000_000) * pricing["input"]
    output_cost = (total_output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    report = {
        "model": model,
        "examples": examples,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": total_cost,
    }

    if verbose:
        print(f"\n💰 Cost Estimation: {input_file}")
        print(f"   Model: {model}")
        print(f"   Examples: {examples:,}")
        print(f"   Input tokens: {total_input_tokens:,}")
        print(f"   Output tokens: {total_output_tokens:,}")
        print(f"   Total tokens: {report['total_tokens']:,}")
        print(f"\n   Estimated cost:")
        print(f"     Input: ${input_cost:.4f}")
        print(f"     Output: ${output_cost:.4f}")
        print(f"     TOTAL: ${total_cost:.4f}")

    return report


def budget_samples(
    input_file: str,
    max_budget_usd: float,
    model: str = "gpt-4o",
    verbose: bool = True
) -> int:
    """
    Calculate how many examples you can process within budget.

    Args:
        input_file: Input JSONL
        max_budget_usd: Maximum budget in USD
        model: Model for pricing
        verbose: Print report

    Returns:
        Number of examples affordable
    """
    # Estimate full cost
    full_report = estimate_api_cost(input_file, model, verbose=False)

    if full_report["total_cost_usd"] == 0:
        return full_report["examples"]

    # Calculate affordable examples
    ratio = max_budget_usd / full_report["total_cost_usd"]
    affordable = int(full_report["examples"] * ratio)

    if verbose:
        print(f"\n💵 Budget Analysis")
        print(f"   Budget: ${max_budget_usd:.2f}")
        print(f"   Full dataset cost: ${full_report['total_cost_usd']:.4f}")
        print(f"   Full dataset size: {full_report['examples']:,} examples")
        print(f"\n   ✅ You can process: {affordable:,} examples")
        print(f"   ({ratio*100:.1f}% of dataset)")

    return affordable
