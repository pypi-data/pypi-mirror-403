"""Prompt templates and few-shot example builders"""

from typing import List, Dict, Optional


def build_few_shot_prompt(
    examples: List[Dict[str, str]],
    query: str,
    instruction: Optional[str] = None,
    format_template: str = "User: {user}\nAssistant: {assistant}\n"
) -> str:
    """
    Build few-shot prompt from examples.

    Args:
        examples: List of dicts with 'user' and 'assistant' keys
        query: The actual query
        instruction: Optional instruction at the top
        format_template: Template for each example

    Returns:
        Complete prompt string

    Example:
        examples = [
            {"user": "What is 2+2?", "assistant": "4"},
            {"user": "What is 3+3?", "assistant": "6"}
        ]
        prompt = build_few_shot_prompt(examples, "What is 5+5?")
    """
    parts = []

    if instruction:
        parts.append(instruction)
        parts.append("")

    # Add examples
    for ex in examples:
        parts.append(format_template.format(user=ex.get("user", ""), assistant=ex.get("assistant", "")))

    # Add query
    parts.append(f"User: {query}")
    parts.append("Assistant:")

    return "\n".join(parts)


class PromptTemplate:
    """Common prompt templates for ML tasks"""

    @staticmethod
    def classification(text: str, labels: List[str]) -> str:
        """Classification prompt"""
        labels_str = ", ".join(labels)
        return f"""Classify the following text into one of these categories: {labels_str}

Text: {text}

Category:"""

    @staticmethod
    def summarization(text: str, max_words: int = 50) -> str:
        """Summarization prompt"""
        return f"""Summarize the following text in {max_words} words or less:

{text}

Summary:"""

    @staticmethod
    def qa(context: str, question: str) -> str:
        """Question answering prompt"""
        return f"""Answer the question based on the context below.

Context: {context}

Question: {question}

Answer:"""

    @staticmethod
    def chat(system_message: str, conversation_history: List[Dict[str, str]], user_message: str) -> List[Dict[str, str]]:
        """Chat prompt with history"""
        messages = [{"role": "system", "content": system_message}]

        # Add history
        for turn in conversation_history:
            messages.append({"role": "user", "content": turn.get("user", "")})
            messages.append({"role": "assistant", "content": turn.get("assistant", "")})

        # Add current message
        messages.append({"role": "user", "content": user_message})

        return messages

    @staticmethod
    def extraction(text: str, entity_types: List[str]) -> str:
        """Entity extraction prompt"""
        types_str = ", ".join(entity_types)
        return f"""Extract the following entities from the text: {types_str}

Text: {text}

Entities:"""

    @staticmethod
    def rewrite(text: str, style: str) -> str:
        """Rewriting prompt"""
        return f"""Rewrite the following text in a {style} style:

Original: {text}

Rewritten:"""


def select_few_shot_examples(
    dataset_file: str,
    query: str,
    n_examples: int = 3,
    method: str = "random"
) -> List[Dict[str, str]]:
    """
    Select few-shot examples from dataset.

    Args:
        dataset_file: JSONL dataset
        query: Query to find similar examples for
        n_examples: Number of examples
        method: "random", "similar" (requires embeddings), or "diverse"

    Returns:
        List of example dicts
    """
    import json
    import random

    examples = []

    with open(dataset_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line.strip())

                if "messages" in data:
                    user = data["messages"][0].get("content", "")
                    assistant = data["messages"][1].get("content", "")
                else:
                    user = data.get("user", "")
                    assistant = data.get("assistant", data.get("EzrA", ""))

                examples.append({"user": user, "assistant": assistant})

            except:
                continue

    # Select based on method
    if method == "random":
        return random.sample(examples, min(n_examples, len(examples)))

    elif method == "diverse":
        # Simple diversity: pick from different length buckets
        short = [ex for ex in examples if len(ex.get("assistant", "")) < 50]
        medium = [ex for ex in examples if 50 <= len(ex.get("assistant", "")) < 200]
        long = [ex for ex in examples if len(ex.get("assistant", "")) >= 200]

        selected = []
        buckets = [b for b in [short, medium, long] if b]

        while len(selected) < n_examples and buckets:
            for bucket in buckets:
                if bucket and len(selected) < n_examples:
                    selected.append(random.choice(bucket))

        return selected[:n_examples]

    else:  # "similar" would require embeddings
        return random.sample(examples, min(n_examples, len(examples)))
