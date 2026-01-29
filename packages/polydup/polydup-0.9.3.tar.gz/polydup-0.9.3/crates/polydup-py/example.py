#!/usr/bin/env python3
"""
Quick example demonstrating PolyDup Python bindings usage
"""

import polydup
import json

def main():
    print("PolyDup Python Bindings Example")
    print("=" * 50)

    # Check version
    print(f"\nVersion: {polydup.version()}")

    # Scan the dupe-core crate
    print("\nScanning dupe-core crate...")
    report = polydup.find_duplicates(
        paths=['../dupe-core/src'],
        min_block_size=30,
        threshold=0.85
    )

    # Display results
    print(f"\n📊 Scan Results:")
    print(f"  Files scanned: {report.files_scanned}")
    print(f"  Functions analyzed: {report.functions_analyzed}")
    print(f"  Duplicates found: {len(report.duplicates)}")
    print(f"  Duration: {report.stats.duration_ms}ms")
    print(f"  Total tokens: {report.stats.total_tokens}")
    print(f"  Unique hashes: {report.stats.unique_hashes}")

    # Show duplicates if found
    if report.duplicates:
        print(f"\nFirst 5 duplicates:")
        for i, dup in enumerate(report.duplicates[:5], 1):
            print(f"\n  {i}. {dup.file1}:{dup.start_line1}")
            print(f"     ↔️ {dup.file2}:{dup.start_line2}")
            print(f"     Similarity: {dup.similarity * 100:.1f}%")
            print(f"     Length: {dup.length} tokens")
    else:
        print("\n✨ No duplicates found!")

    # Convert to dict and show JSON
    print("\n📄 JSON output (first 500 chars):")

    # Manually construct dict from report attributes
    report_dict = {
        'files_scanned': report.files_scanned,
        'functions_analyzed': report.functions_analyzed,
        'duplicates': [
            {
                'file1': d.file1,
                'file2': d.file2,
                'start_line1': d.start_line1,
                'start_line2': d.start_line2,
                'length': d.length,
                'similarity': d.similarity,
                'hash': d.hash
            }
            for d in report.duplicates[:5]  # First 5 only
        ],
        'stats': {
            'total_lines': report.stats.total_lines,
            'total_tokens': report.stats.total_tokens,
            'unique_hashes': report.stats.unique_hashes,
            'duration_ms': report.stats.duration_ms
        }
    }

    json_str = json.dumps(report_dict, indent=2)
    print(json_str[:500] + "..." if len(json_str) > 500 else json_str)

    print("\n✅ Example complete!")

if __name__ == '__main__':
    main()
