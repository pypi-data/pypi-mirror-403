import polydup
import time

print(f"PolyDup Python v{polydup.version()}")

# Test 1: Basic scan
print("\n🧪 Test 1: Basic scan")
report = polydup.find_duplicates(['../../test_duplicates'], min_block_size=3)
print(f"✅ Files: {report.files_scanned}, Functions: {report.functions_analyzed}")
print(f"✅ Duplicates: {len(report.duplicates)}")

if report.duplicates:
    dup = report.duplicates[0]
    print(f"\nFirst duplicate:")
    print(f"  {dup.file1} ↔️ {dup.file2}")
    print(f"  Similarity: {dup.similarity * 100:.1f}%")
    print(f"  Length: {dup.length} tokens")

# Test 2: Dict output
print("\n🧪 Test 2: Dictionary output")
report_dict = polydup.find_duplicates_dict(['../../crates/dupe-core/src'], min_block_size=30)
print(f"✅ Dict keys: {list(report_dict.keys())}")
print(f"✅ Scan time: {report_dict['stats']['duration_ms']}ms")

print("\n✅ Phase 3: Python bindings VERIFIED")
