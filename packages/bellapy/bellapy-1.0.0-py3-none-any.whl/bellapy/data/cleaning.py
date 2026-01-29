"""Text cleaning and PII scrubbing utilities"""

import re
import json
from typing import Tuple, Dict, Optional
from collections import defaultdict

# PII Patterns for scrubbing
PII_PATTERNS = {
    'email': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    'phone': (r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]'),
    'ssn': (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    'credit_card': (r'\b(?:\d[ -]*?){13,16}\b', '[CREDIT_CARD]'),
    'ip_address': (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),
    'url': (r'https?://[^\s]+|www\.[^\s]+', '[URL]'),
    'api_key': (r'(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key)[:\s]+["\']?([a-zA-Z0-9]{32,})["\']?', '[API_KEY]'),
    'private_key': (r'-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----', '[PRIVATE_KEY]'),
    'password': (r'(?i)(?:password|passwd|pwd)[:\s=]+["\']?([^"\'\s]{8,})["\']?', '[PASSWORD]'),
    'zip_code': (r'\b\d{5}(?:-\d{4})?\b', '[ZIP]'),
    'mac_address': (r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b', '[MAC_ADDR]'),
}


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: Input text
        model: Model name for encoding

    Returns:
        Number of tokens
    """
    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model)
        except:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        # Fallback: rough estimate (4 chars = 1 token)
        return len(text) // 4


def normalize_text(text: str) -> str:
    """
    Normalize text by removing control characters and invisible unicode.

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    if not isinstance(text, str):
        return text

    # Remove zero-width characters and other invisible unicode
    cleaned = re.sub(r'[\u200b-\u200d\ufeff]', '', text)

    # Remove control characters except newline and tab
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\t')

    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()

    return cleaned


def scrub_pii(
    text: str,
    stats_counter: Optional[Dict] = None
) -> Tuple[str, Dict[str, int]]:
    """
    Scrub PII from text and track what was replaced.

    Args:
        text: Input text containing potential PII
        stats_counter: Optional dict to accumulate stats across multiple calls

    Returns:
        Tuple of (cleaned_text, replacements_dict)
    """
    if not isinstance(text, str):
        return text, {}

    cleaned = text
    replacements = defaultdict(int)

    # Order matters: more specific/longer patterns first
    for pii_type, (pattern, replacement) in PII_PATTERNS.items():
        try:
            matches = re.findall(pattern, cleaned, flags=re.IGNORECASE if pii_type != 'url' else 0)
            if matches:
                replacements[pii_type] = len(matches)
                if stats_counter is not None:
                    stats_counter[pii_type] += len(matches)
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE if pii_type != 'url' else 0)
        except Exception as e:
            print(f"⚠️  Error scrubbing {pii_type}: {e}")

    return cleaned, dict(replacements)


def sanitize_content(text: str) -> str:
    """
    Sanitize text by removing self-dialogue patterns, limiting emojis, and cleaning spam.

    Args:
        text: Input text

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # 1. Remove self-dialogue patterns (assistant: , ezra:, etc.)
    text = re.sub(r'(?i)\b(assistant|ezra|user|friend|cat)\s*[:\-]\s*', '', text)

    # 2. Limit emojis to 2 max per response
    emojis = re.findall(r'[^\x00-\x7F]+', text)
    if len(emojis) > 2:
        for extra in emojis[2:]:
            text = text.replace(extra, '', 1)

    # 3. Remove common repetitive spam
    text = re.sub(r'[\{\}\[\]\|\<\>\/\\]{3,}', '', text)
    text = re.sub(r'[\.\:\;\!\?]{4,}', '.', text)  # Collapse .... into .

    # 4. Strip whitespace
    text = text.strip()

    return text


def clean_dataset(
    input_file: str,
    output_file: Optional[str] = None,
    scrub_pii_enabled: bool = True,
    sanitize: bool = True,
    normalize: bool = True,
    verbose: bool = True
) -> Optional[str]:
    """
    Clean an entire dataset with PII scrubbing, sanitization, and normalization.

    Args:
        input_file: Path to input JSONL file
        output_file: Path to output file (default: input_CLEANED.jsonl)
        scrub_pii_enabled: Enable PII scrubbing
        sanitize: Enable content sanitization
        normalize: Enable text normalization
        verbose: Print progress

    Returns:
        Path to output file, or None if error
    """
    import os

    if not output_file:
        output_file = input_file.replace('.jsonl', '_CLEANED.jsonl')

    if not os.path.exists(input_file):
        if verbose:
            print(f"❌ Error: {input_file} not found.")
        return None

    if verbose:
        print(f"🧹 Cleaning {input_file}...")

    count = 0
    removed = 0
    pii_stats = defaultdict(int)

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:
            try:
                data = json.loads(line)

                # Handle different formats
                if "messages" in data:
                    messages = data.get("messages", [])
                    if len(messages) < 2:
                        removed += 1
                        continue

                    user_content = messages[0]["content"]
                    assistant_content = messages[1]["content"]

                    # Clean assistant content
                    if normalize:
                        assistant_content = normalize_text(assistant_content)
                    if scrub_pii_enabled:
                        assistant_content, _ = scrub_pii(assistant_content, pii_stats)
                    if sanitize:
                        assistant_content = sanitize_content(assistant_content)

                    if not assistant_content or len(assistant_content) < 2:
                        removed += 1
                        continue

                    messages[1]["content"] = assistant_content
                    messages[0]["content"] = user_content.strip()

                else:
                    # Handle simple format
                    user_content = data.get("user", "")
                    assistant_content = data.get("EzrA", data.get("assistant", ""))

                    # Clean assistant content
                    if normalize:
                        assistant_content = normalize_text(assistant_content)
                    if scrub_pii_enabled:
                        assistant_content, _ = scrub_pii(assistant_content, pii_stats)
                    if sanitize:
                        assistant_content = sanitize_content(assistant_content)

                    if not assistant_content or len(assistant_content) < 2:
                        removed += 1
                        continue

                    data["user"] = user_content.strip()
                    if "EzrA" in data:
                        data["EzrA"] = assistant_content
                    else:
                        data["assistant"] = assistant_content

                outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
                count += 1

            except Exception as e:
                if verbose:
                    print(f"⚠️  Error: {e}")
                removed += 1

    if verbose:
        print(f"\n✅ Cleaning Complete!")
        print(f"   - Cleaned: {count}")
        print(f"   - Removed (spam/empty): {removed}")
        if scrub_pii_enabled and pii_stats:
            print(f"   - PII scrubbed:")
            for pii_type, count in pii_stats.items():
                print(f"     • {pii_type}: {count}")
        print(f"   - Output: {output_file}")

    return output_file
