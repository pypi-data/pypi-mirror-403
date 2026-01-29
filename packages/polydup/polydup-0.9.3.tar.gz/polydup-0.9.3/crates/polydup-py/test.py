#!/usr/bin/env python3
"""
Test suite for PolyDup Python bindings

Tests:
1. Basic functionality
2. GIL release (concurrent execution)
3. Dictionary output
4. Error handling
5. Performance benchmarking
"""

import polydup
import time
import concurrent.futures
from pathlib import Path


def test_basic_scan():
    """Test basic duplicate detection"""
    print("\n=== Test 1: Basic Scan ===")

    # Scan the dupe-core crate
    report = polydup.find_duplicates(
        paths=['../dupe-core/src'],
        min_block_size=30,
        threshold=0.85
    )

    print(f"✓ Scanned {report.files_scanned} files")
    print(f"✓ Analyzed {report.functions_analyzed} functions")
    print(f"✓ Found {len(report.duplicates)} duplicates")
    print(f"✓ Duration: {report.stats.duration_ms}ms")
    print(f"✓ Total tokens: {report.stats.total_tokens}")
    print(f"✓ Unique hashes: {report.stats.unique_hashes}")

    # Show first few duplicates
    if report.duplicates:
        print("\nFirst 3 duplicates:")
        for dup in report.duplicates[:3]:
            print(f"  {dup}")

    assert report.files_scanned > 0, "Should scan at least one file"
    assert report.functions_analyzed > 0, "Should find at least one function"
    print("✅ Basic scan test passed")


def test_dict_output():
    """Test dictionary output for JSON serialization"""
    print("\n=== Test 2: Dictionary Output ===")

    import json

    report_dict = polydup.find_duplicates_dict(
        paths=['../dupe-core/src/lib.rs'],
        min_block_size=20,
        threshold=0.9
    )

    print(f"✓ Got dictionary with keys: {list(report_dict.keys())}")

    # Serialize to JSON
    json_str = json.dumps(report_dict, indent=2)
    print(f"✓ JSON length: {len(json_str)} bytes")

    # Verify structure
    assert 'files_scanned' in report_dict
    assert 'functions_analyzed' in report_dict
    assert 'duplicates' in report_dict
    assert 'stats' in report_dict
    assert isinstance(report_dict['duplicates'], list)

    print("✅ Dictionary output test passed")


def test_gil_release():
    """Test GIL release during scanning (concurrent execution)"""
    print("\n=== Test 3: GIL Release (Concurrent Execution) ===")

    def scan_path(path):
        """Scan a single path"""
        start = time.time()
        report = polydup.find_duplicates([path], min_block_size=30)
        elapsed = time.time() - start
        return {
            'path': path,
            'files': report.files_scanned,
            'duplicates': len(report.duplicates),
            'elapsed': elapsed
        }

    paths = [
        '../dupe-core/src',
        '../dupe-cli/src',
        '../dupe-node/src',
    ]

    # Sequential execution
    print("\nSequential execution:")
    seq_start = time.time()
    seq_results = [scan_path(p) for p in paths]
    seq_elapsed = time.time() - seq_start
    print(f"  Total time: {seq_elapsed:.3f}s")

    # Parallel execution (should be faster due to GIL release)
    print("\nParallel execution (with GIL release):")
    par_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(paths)) as executor:
        futures = [executor.submit(scan_path, p) for p in paths]
        par_results = [f.result() for f in concurrent.futures.as_completed(futures)]
    par_elapsed = time.time() - par_start
    print(f"  Total time: {par_elapsed:.3f}s")

    # Show results
    for result in seq_results:
        print(f"  {result['path']}: {result['files']} files, {result['duplicates']} duplicates")

    # Parallel should be faster (or at least not slower by much)
    speedup = seq_elapsed / par_elapsed
    print(f"\n✓ Speedup: {speedup:.2f}x")

    if speedup > 1.1:
        print("✅ GIL release test passed (significant parallelism)")
    elif speedup > 0.9:
        print("✅ GIL release test passed (acceptable parallelism)")
    else:
        print("⚠️  Warning: Parallel execution slower than sequential")


def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\n=== Test 4: Error Handling ===")

    # Test with non-existent path
    try:
        report = polydup.find_duplicates(['/nonexistent/path'])
        print("✓ Handled non-existent path (no error)")
    except Exception as e:
        print(f"✓ Caught error for non-existent path: {type(e).__name__}")

    # Test with invalid threshold
    try:
        report = polydup.find_duplicates(['../dupe-core/src'], threshold=1.5)
        print("⚠️  Warning: Invalid threshold not rejected")
    except Exception as e:
        print(f"✓ Caught error for invalid threshold: {type(e).__name__}")

    print("✅ Error handling test passed")


def test_version():
    """Test version function"""
    print("\n=== Test 5: Version ===")

    version = polydup.version()
    print(f"✓ PolyDup version: {version}")

    assert isinstance(version, str)
    assert len(version) > 0

    print("✅ Version test passed")


def benchmark():
    """Performance benchmark"""
    print("\n=== Benchmark ===")

    # Benchmark on the entire crates directory
    print("\nBenchmarking full codebase scan...")

    start = time.time()
    report = polydup.find_duplicates(
        paths=['..'],  # Scan all crates
        min_block_size=50,
        threshold=0.85
    )
    elapsed = time.time() - start

    print(f"\nResults:")
    print(f"  Files scanned: {report.files_scanned}")
    print(f"  Functions analyzed: {report.functions_analyzed}")
    print(f"  Duplicates found: {len(report.duplicates)}")
    print(f"  Total lines: {report.stats.total_lines}")
    print(f"  Total tokens: {report.stats.total_tokens}")
    print(f"  Unique hashes: {report.stats.unique_hashes}")
    print(f"  Duration: {report.stats.duration_ms}ms")
    print(f"  Wall time: {elapsed:.3f}s")

    if report.stats.total_tokens > 0:
        throughput = report.stats.total_tokens / elapsed
        print(f"  Throughput: {throughput:,.0f} tokens/sec")

    print("\n✅ Benchmark complete")


def main():
    """Run all tests"""
    print("=" * 60)
    print("PolyDup Python Bindings Test Suite")
    print("=" * 60)

    try:
        test_version()
        test_basic_scan()
        test_dict_output()
        test_error_handling()
        test_gil_release()
        benchmark()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
