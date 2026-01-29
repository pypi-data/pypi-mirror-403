# Installation Guide

## Quick Install

```bash
cd /Users/chiggy/bellapy
pip install -e .
```

## Verify Installation

```bash
# Check version
bellapy --version

# View help
bellapy --help

# Test data commands
bellapy data --help
```

## Test It Out

```bash
# Create a test dataset
echo '{"user": "Hello", "assistant": "Hi there!"}' > test.jsonl
echo '{"user": "How are you?", "assistant": "I am doing well"}' >> test.jsonl
echo '{"user": "Hello", "assistant": "Hi there!"}' >> test.jsonl  # duplicate

# View stats
bellapy data stats test.jsonl

# Deduplicate
bellapy data dedupe test.jsonl

# Clean up
rm test.jsonl test_UNIQUE.jsonl
```

## Installation Options

### Standard Installation
```bash
pip install -e .
```
Installs core dependencies: rich, pyyaml, openai, tiktoken, click

### With Training Dependencies
```bash
pip install -e ".[training]"
```
Adds: modal, transformers, torch, peft, trl, datasets, accelerate, bitsandbytes

### Development Installation
```bash
pip install -e ".[dev]"
```
Adds testing and linting tools: pytest, black, ruff, mypy

### All Features
```bash
pip install -e ".[training,dev]"
```

## Uninstall

```bash
pip uninstall bellapy
```

## Troubleshooting

### Command not found: bellapy
Make sure the package is installed:
```bash
pip list | grep bellapy
```

If not installed, run:
```bash
cd /Users/chiggy/bellapy && pip install -e .
```

### ImportError
Make sure you're in the right environment:
```bash
which python
pip list
```

### Permission errors
Use `--user` flag:
```bash
pip install --user -e .
```

## Next Steps

1. Read the [README.md](README.md) for usage examples
2. Run `bellapy --help` to see available commands
3. Try cleaning a real dataset: `bellapy data clean your_data.jsonl`
