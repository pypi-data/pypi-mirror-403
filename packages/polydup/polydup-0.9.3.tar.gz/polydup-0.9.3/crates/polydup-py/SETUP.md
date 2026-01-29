# PolyDup Python Bindings Setup Guide

This guide covers building, testing, and publishing the Python bindings for PolyDup.

## Prerequisites

- **Rust**: Install via [rustup](https://rustup.rs/)
- **Python**: 3.8 or higher
- **Maturin**: Install via `pip install maturin`

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin
pip install maturin
```

## Development Build

Build and install the Python module in development mode:

```bash
cd crates/polydup-py

# Debug build (fast compilation, slower runtime)
maturin develop

# Release build (slow compilation, fast runtime)
maturin develop --release
```

This installs the `polydup` module in your current Python environment, allowing you to import it immediately.

## Testing

Run the test suite:

```bash
python test.py
```

Expected output:
```
============================================================
PolyDup Python Bindings Test Suite
============================================================

=== Test 5: Version ===
✓ PolyDup version: 0.1.0
Version test passed

=== Test 1: Basic Scan ===
✓ Scanned 4 files
✓ Analyzed 76 functions
✓ Found 57 duplicates
✓ Duration: 34ms
✓ Total tokens: 12345
✓ Unique hashes: 234
...
All tests passed!
```

## Manual Testing

```python
# In Python REPL or script
import polydup

# Check version
print(polydup.version())  # "0.1.0"

# Scan a directory
report = polydup.find_duplicates(['./src'], min_block_size=30)
print(f"Found {len(report.duplicates)} duplicates")

# Access report data
for dup in report.duplicates:
    print(f"{dup.file1} ↔️ {dup.file2} ({dup.similarity * 100:.1f}%)")
```

## Building Distribution Wheels

Build wheels for distribution:

```bash
# Build for current platform
maturin build --release

# Output: target/wheels/polydup-0.1.0-cp312-cp312-macosx_11_0_arm64.whl
```

For multi-platform builds, use GitHub Actions or cross-compilation:

```bash
# Build for multiple Python versions (requires pyenv or similar)
maturin build --release --interpreter python3.8 python3.9 python3.10 python3.11 python3.12
```

## Publishing to PyPI

1. Build release wheels:
   ```bash
   maturin build --release
   ```

2. Publish to PyPI:
   ```bash
   maturin publish --username __token__ --password <your-pypi-token>
   ```

3. Or publish to TestPyPI first:
   ```bash
   maturin publish --repository testpypi --username __token__ --password <your-token>
   ```

## Performance Optimization

### GIL Release Verification

The Python bindings use `py.allow_threads()` to release the GIL during scanning. Verify this works:

```python
import polydup
import concurrent.futures
import time

def scan(path):
    return polydup.find_duplicates([path])

# These should run in parallel
start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(scan, f'./path{i}') for i in range(4)]
    results = [f.result() for f in futures]
elapsed = time.time() - start

print(f"Scanned 4 paths in {elapsed:.2f}s (parallel)")
```

If the GIL is properly released, you should see near-linear speedup with CPU cores.

## Troubleshooting

### Build Errors

**Error**: `maturin: command not found`
- **Fix**: Install maturin: `pip install maturin`

**Error**: `error: linker 'cc' not found`
- **Fix**: Install C compiler:
  - macOS: `xcode-select --install`
  - Linux: `sudo apt-get install build-essential`

**Error**: `pyo3` version mismatch
- **Fix**: Clean build: `cargo clean && maturin develop --release`

### Runtime Errors

**Error**: `ImportError: No module named 'polydup'`
- **Fix**: Run `maturin develop` first to install the module

**Error**: `RuntimeError: Failed to create scanner`
- **Fix**: Ensure polydup-core dependencies are up to date: `cargo update -p polydup-core`

### Performance Issues

**Slow scanning**:
- Use `--release` flag: `maturin develop --release`
- Verify Rayon is using multiple cores: Check CPU usage during scan
- Ensure large min_block_size (e.g., 50) for better performance

**GIL not released**:
- Verify `py.allow_threads()` is called in [lib.rs](src/lib.rs#L176)
- Test with concurrent.futures as shown above

## Development Workflow

1. Edit [src/lib.rs](src/lib.rs)
2. Rebuild: `maturin develop --release`
3. Test: `python test.py`
4. Repeat

For faster iteration during development, use debug builds:
```bash
maturin develop  # ~1s rebuild vs ~10s for --release
```

Switch to release builds for performance testing.

## Architecture Notes

### Zero-Copy FFI

The Python bindings pass **file paths** to Rust, not file contents. This avoids:
- Python string → Rust string copies
- Memory overhead for large codebases
- GIL contention during I/O

Rust handles all file I/O internally.

### Type Conversions

- `dupe_core::Report` → `PyClass Report`: Deep clone of results
- `dupe_core::DuplicateMatch` → `PyClass DuplicateMatch`: Field-by-field copy
- Hash values: `u64` → `String` (hex format for JSON compatibility)

### GIL Release Pattern

```rust
let report = py.allow_threads(|| {
    scanner.scan(path_bufs)  // CPU-intensive, no Python access
})?;
```

This releases the GIL for the entire scan operation, allowing:
- Other Python threads to run
- Rayon to use all CPU cores
- True parallel processing

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Python Wheels

on: [push, pull_request]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable

      - name: Install maturin
        run: pip install maturin

      - name: Build wheel
        run: |
          cd crates/polydup-py
          maturin build --release

      - name: Test
        run: |
          cd crates/polydup-py
          maturin develop --release
          python test.py
```

## References

- [PyO3 Documentation](https://pyo3.rs/)
- [Maturin Documentation](https://www.maturin.rs/)
- [PolyDup Architecture](../../docs/architecture-research.md)
- [polydup-core API](../polydup-core/src/lib.rs)
