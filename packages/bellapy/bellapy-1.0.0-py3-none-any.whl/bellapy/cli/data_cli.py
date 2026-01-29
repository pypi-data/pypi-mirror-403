"""Data processing CLI commands"""

import click
from bellapy.data import (
    deduplicate,
    merge_files,
    get_stats,
    split_dataset,
    convert_format,
    clean_dataset,
)


@click.group()
def data():
    """Data processing commands"""
    pass


@data.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
def dedupe(input_file, output, quiet):
    """Remove duplicate entries from a dataset"""
    deduplicate(input_file, output, verbose=not quiet)


@data.command()
@click.argument('output_file', type=click.Path())
@click.argument('input_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--no-dedupe', is_flag=True, help='Skip deduplication during merge')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
def merge(output_file, input_files, no_dedupe, quiet):
    """Merge multiple JSONL files"""
    merge_files(output_file, list(input_files), dedupe=not no_dedupe, verbose=not quiet)


@data.command()
@click.argument('input_file', type=click.Path(exists=True))
def stats(input_file):
    """Show dataset statistics"""
    get_stats(input_file, verbose=True)


@data.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--ratio', '-r', type=float, default=0.9, help='Training data ratio (default: 0.9)')
@click.option('--shuffle/--no-shuffle', default=True, help='Shuffle before splitting')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
def split(input_file, ratio, shuffle, quiet):
    """Split dataset into train/test sets"""
    split_dataset(input_file, train_ratio=ratio, shuffle=shuffle, verbose=not quiet)


@data.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', 'target_format',
              type=click.Choice(['messages', 'simple', 'openai', 'hf']),
              default='messages', help='Target format')
@click.option('--assistant-key', default='assistant', help='Key for assistant in simple format')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
def convert(input_file, output, target_format, assistant_key, quiet):
    """Convert dataset between formats"""
    convert_format(input_file, output, target_format, assistant_key, verbose=not quiet)


@data.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
@click.option('--no-pii', is_flag=True, help='Skip PII scrubbing')
@click.option('--no-sanitize', is_flag=True, help='Skip content sanitization')
@click.option('--no-normalize', is_flag=True, help='Skip text normalization')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
def clean(input_file, output, no_pii, no_sanitize, no_normalize, quiet):
    """Clean dataset with PII scrubbing and sanitization"""
    clean_dataset(
        input_file,
        output,
        scrub_pii_enabled=not no_pii,
        sanitize=not no_sanitize,
        normalize=not no_normalize,
        verbose=not quiet
    )


if __name__ == "__main__":
    data()
