# PolyDup Python Documentation

Python extension module for duplicate code detection.

## Overview

The `polydup` package provides Python bindings to the PolyDup core library via PyO3, enabling high-performance duplicate detection in Python projects.

## Installation

```bash
# pip
pip install polydup

# uv (faster)
uv pip install polydup

# pipx (isolated)
pipx install polydup
```

## Requirements

- Python 3.8, 3.9, 3.10, 3.11, or 3.12
- Supported platforms:
  - macOS (x64, ARM64)
  - Linux (x64)
  - Windows (x64)

## API Reference

### `find_duplicates(paths, min_block_size=10, similarity_threshold=0.9)`

Scans directories for duplicate code.

**Parameters:**

- `paths` (List[str]): List of directory paths to scan
- `min_block_size` (int): Minimum lines per code block (default: 10)
- `similarity_threshold` (float): Similarity threshold 0.0-1.0 (default: 0.9)

**Returns:** List[Dict] of duplicate matches

```python
{
    'file1': str,           # First file path
    'file2': str,           # Second file path
    'start_line1': int,     # Starting line in file1
    'start_line2': int,     # Starting line in file2
    'length': int,          # Number of lines
    'similarity': float,    # Similarity score (0.0-1.0)
    'hash': int            # Hash value for deduplication
}
```

**Example:**

```python
import polydup

duplicates = polydup.find_duplicates(
    paths=['src/', 'tests/'],
    min_block_size=10,
    similarity_threshold=0.85
)

print(f"Found {len(duplicates)} duplicates")

for dup in duplicates:
    print(f"{dup['file1']}:{dup['start_line1']} <-> {dup['file2']}:{dup['start_line2']}")
    print(f"Similarity: {dup['similarity']*100:.1f}%")
    print(f"Length: {dup['length']} lines\n")
```

### `version()`

Returns the package version string.

```python
import polydup

print(polydup.version())  # "0.1.2"
```

## Usage Examples

### Basic Scanning

```python
import polydup

# Scan with defaults
duplicates = polydup.find_duplicates(['./src'])
print(f"Found {len(duplicates)} duplicates")
```

### Custom Configuration

```python
# Strict matching: 95% similarity, 20+ line blocks
strict_dups = polydup.find_duplicates(
    paths=['./src'],
    min_block_size=20,
    similarity_threshold=0.95
)

# Lenient matching: 70% similarity, 5+ line blocks
lenient_dups = polydup.find_duplicates(
    paths=['./src'],
    min_block_size=5,
    similarity_threshold=0.70
)
```

### Multiple Directories

```python
duplicates = polydup.find_duplicates(
    paths=['./src', './lib', './tests'],
    min_block_size=10,
    similarity_threshold=0.85
)
```

### JSON Export

```python
import json
import polydup
from datetime import datetime

duplicates = polydup.find_duplicates(['./src'])

report = {
    'scanned_at': datetime.now().isoformat(),
    'duplicate_count': len(duplicates),
    'duplicates': duplicates
}

with open('duplicates.json', 'w') as f:
    json.dump(report, f, indent=2)
```

### Pandas DataFrame

```python
import pandas as pd
import polydup

duplicates = polydup.find_duplicates(['./src'])

df = pd.DataFrame(duplicates)
print(df[['file1', 'file2', 'similarity', 'length']].head())

# Group by similarity
print(df.groupby(pd.cut(df['similarity'], bins=5)).size())
```

### CLI Script

```python
#!/usr/bin/env python3
import sys
import polydup

def main():
    if len(sys.argv) < 2:
        print("Usage: check_duplicates.py <directory>")
        sys.exit(1)

    duplicates = polydup.find_duplicates(
        paths=[sys.argv[1]],
        min_block_size=10,
        similarity_threshold=0.90
    )

    if duplicates:
        print(f"Error: Found {len(duplicates)} duplicates")
        for dup in duplicates[:5]:  # Show first 5
            print(f"  {dup['file1']}:{dup['start_line1']} <-> "
                  f"{dup['file2']}:{dup['start_line2']}")
        sys.exit(1)

    print("No duplicates detected")

if __name__ == '__main__':
    main()
```

### Pre-commit Hook

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: check-duplicates
        name: Check for duplicate code
        entry: python -c "import polydup, sys; sys.exit(1 if polydup.find_duplicates(['src/']) else 0)"
        language: python
        pass_filenames: false
```

### Django Management Command

```python
# myapp/management/commands/check_duplicates.py
from django.core.management.base import BaseCommand
import polydup

class Command(BaseCommand):
    help = 'Check for duplicate code in the project'

    def add_arguments(self, parser):
        parser.add_argument('--threshold', type=float, default=0.9)
        parser.add_argument('--min-size', type=int, default=10)

    def handle(self, *args, **options):
        duplicates = polydup.find_duplicates(
            paths=['myapp/'],
            min_block_size=options['min_size'],
            similarity_threshold=options['threshold']
        )

        if duplicates:
            self.stdout.write(
                self.style.WARNING(f'Found {len(duplicates)} duplicates')
            )
            for dup in duplicates:
                self.stdout.write(
                    f"  {dup['file1']}:{dup['start_line1']} <-> "
                    f"{dup['file2']}:{dup['start_line2']}"
                )
        else:
            self.stdout.write(self.style.SUCCESS('No duplicates found'))
```

## Performance

The Python binding releases the GIL during scanning for true parallelism:

- **Startup**: <20ms initialization
- **Throughput**: ~400 files/second on modern hardware
- **Memory**: O(n) where n = total lines of code
- **CPU**: Automatic parallelization across cores

Typical scan times:

- 100 files: ~250ms
- 1000 files: ~2.5 seconds
- 10000 files: ~25 seconds

## Error Handling

```python
import polydup

try:
    duplicates = polydup.find_duplicates(['./src'])
except FileNotFoundError:
    print("Directory not found")
except ValueError as e:
    print(f"Invalid parameter: {e}")
except Exception as e:
    print(f"Scan failed: {e}")
```

## Type Hints

The package includes type stubs for static analysis:

```python
from typing import List, Dict

import polydup

def scan_project(paths: List[str]) -> List[Dict[str, any]]:
    return polydup.find_duplicates(paths)
```

## Building from Source

### Prerequisites

- Python 3.8-3.12
- Rust 1.70+
- maturin

### Build Steps

```bash
git clone https://github.com/wiesnerbernard/polydup.git
cd polydup/crates/polydup-py

# Install maturin
pip install maturin

# Build and install in development mode
maturin develop

# Or build wheel
maturin build --release

# Run tests
python -m pytest
```

## Troubleshooting

### ImportError: No module named 'polydup'

Ensure the package is installed:

```bash
pip install polydup
```

### Incompatible Python version

Check supported versions (3.8-3.12):

```bash
python --version
```

### Wheel not available for platform

The package includes prebuilt wheels for common platforms. If your platform isn't supported, you'll need Rust and maturin installed to build from source.

### Segmentation fault or crash

This may indicate a bug in the native code. Please report with:

1. Python version (`python --version`)
2. Platform (OS, architecture)
3. Minimal reproduction case

## Contributing

See the main [README](../../../README.md) for contribution guidelines.

## License

MIT OR Apache-2.0
