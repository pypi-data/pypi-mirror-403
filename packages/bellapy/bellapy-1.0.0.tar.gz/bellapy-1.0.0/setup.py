#!/usr/bin/env python3
"""
bellapy: ML Data Toolkit
The data processing library you wish existed.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else __doc__

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="bellapy",
    version="1.0.0",
    description="ML data toolkit - 29 features for dataset processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Chiggy",
    author_email="",
    url="https://github.com/JuiceB0xC0de/bellapy",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "openai>=1.0.0",
        "tiktoken>=0.5.0",
        "click>=8.0.0",
    ],
    extras_require={
        "training": [
            "modal>=0.63.0",
            "transformers>=4.30.0",
            "torch>=2.0.0",
            "peft>=0.5.0",
            "trl>=0.7.0",
            "datasets>=2.14.0",
            "accelerate>=0.20.0",
            "bitsandbytes>=0.41.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "export": [
            "pandas>=2.0.0",
            "pyarrow>=14.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bellapy=bellapy.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="machine-learning ml data-processing llm dataset bellapy",
)
