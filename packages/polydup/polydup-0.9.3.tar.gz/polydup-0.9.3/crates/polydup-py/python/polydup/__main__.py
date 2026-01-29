"""
polydup - Cross-language duplicate code detector

This package provides both:
1. Python library bindings for programmatic use
2. CLI tool for command-line usage

CLI usage (after pip install):
    polydup scan ./src
    polydup --help

Library usage:
    import polydup
    report = polydup.find_duplicates(['src/'], min_block_size=50, threshold=0.85)
    for dup in report.duplicates:
        print(f"{dup.file1} <-> {dup.file2}")
"""

import sys

from polydup._cli import main

if __name__ == "__main__":
    sys.exit(main())
