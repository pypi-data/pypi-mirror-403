"""
Data processing module for bellapy

Complete ML data toolkit:
- Dataset deduplication, merging, splitting
- PII scrubbing and text cleaning
- Format conversion (OpenAI, HuggingFace, CSV, Parquet)
- Sampling (random, stratified)
- Filtering (length, pattern, quality, custom)
- Validation and quality checks
- Batch processing for large datasets
- Cost estimation for API calls
- Dataset comparison and diffing
- Data augmentation
- Prompt templates and few-shot builders
"""

# Core processors
from bellapy.data.processors import deduplicate, merge_files, get_stats, split_dataset

# Cleaning
from bellapy.data.cleaning import scrub_pii, normalize_text, count_tokens, sanitize_content, clean_dataset

# Formats
from bellapy.data.formats import convert_format, to_openai_format, to_hf_format, to_simple_format

# Sampling
from bellapy.data.sampling import sample_dataset, stratified_sample

# Filtering
from bellapy.data.filters import filter_by_length, filter_by_pattern, filter_by_quality, filter_custom

# Validation
from bellapy.data.validation import validate_format, check_duplicates_detailed

# Batch processing
from bellapy.data.batch import process_in_batches, chunk_dataset

# Cost estimation
from bellapy.data.cost import estimate_api_cost, budget_samples

# Dataset comparison
from bellapy.data.diff import compare_datasets, extract_diff

# Export
from bellapy.data.export import to_csv, to_parquet, to_txt

# Augmentation
from bellapy.data.augmentation import paraphrase_with_gpt, balance_dataset

# Prompts
from bellapy.data.prompts import build_few_shot_prompt, PromptTemplate, select_few_shot_examples

__all__ = [
    # Processors
    "deduplicate", "merge_files", "get_stats", "split_dataset",
    # Cleaning
    "scrub_pii", "normalize_text", "count_tokens", "sanitize_content", "clean_dataset",
    # Formats
    "convert_format", "to_openai_format", "to_hf_format", "to_simple_format",
    # Sampling
    "sample_dataset", "stratified_sample",
    # Filtering
    "filter_by_length", "filter_by_pattern", "filter_by_quality", "filter_custom",
    # Validation
    "validate_format", "check_duplicates_detailed",
    # Batch
    "process_in_batches", "chunk_dataset",
    # Cost
    "estimate_api_cost", "budget_samples",
    # Diff
    "compare_datasets", "extract_diff",
    # Export
    "to_csv", "to_parquet", "to_txt",
    # Augmentation
    "paraphrase_with_gpt", "balance_dataset",
    # Prompts
    "build_few_shot_prompt", "PromptTemplate", "select_few_shot_examples",
]
