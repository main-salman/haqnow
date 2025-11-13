#!/usr/bin/env python3
"""
Test script for virus scanning service
Tests ClamAV integration and file scanning functionality
"""
import sys
import io
from app.services.virus_scanning_service import virus_scanning_service

# EICAR test virus signature (standard harmless test file)
EICAR_TEST_VIRUS = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'

def test_service_availability():
    """Test if ClamAV service is available"""
    print("=" * 60)
    print("TEST 1: Service Availability")
    print("=" * 60)
    
    status = virus_scanning_service.get_status()
    print(f"Virus Scanning Available: {status['available']}")
    print(f"Scanner: {status.get('scanner', 'N/A')}")
    
    if status['available']:
        version = status.get('version', 'Unknown')
        print(f"ClamAV Version: {version}")
        print("✅ PASS: Virus scanning service is available")
        return True
    else:
        print("❌ FAIL: Virus scanning service is NOT available")
        print("   Make sure ClamAV daemon is running:")
        print("   sudo systemctl start clamav-daemon")
        return False

def test_clean_file():
    """Test scanning a clean file"""
    print("\n" + "=" * 60)
    print("TEST 2: Clean File Scanning")
    print("=" * 60)
    
    clean_content = b"This is a clean test file with no viruses."
    is_safe, virus_name = virus_scanning_service.scan_file_content(
        clean_content, 
        "clean_test.txt"
    )
    
    print(f"File Content: {clean_content.decode()}")
    print(f"Is Safe: {is_safe}")
    print(f"Virus Name: {virus_name}")
    
    if is_safe and virus_name is None:
        print("✅ PASS: Clean file correctly identified as safe")
        return True
    else:
        print("❌ FAIL: Clean file incorrectly flagged")
        return False

def test_infected_file():
    """Test scanning EICAR test virus"""
    print("\n" + "=" * 60)
    print("TEST 3: Infected File Detection (EICAR Test)")
    print("=" * 60)
    
    print("Note: EICAR is a standard harmless test virus signature")
    print(f"Test Content: {EICAR_TEST_VIRUS[:50]}...")
    
    is_safe, virus_name = virus_scanning_service.scan_file_content(
        EICAR_TEST_VIRUS,
        "eicar_test.txt"
    )
    
    print(f"Is Safe: {is_safe}")
    print(f"Detected Virus: {virus_name}")
    
    if not is_safe and virus_name:
        print("✅ PASS: EICAR test virus correctly detected")
        return True
    else:
        print("❌ FAIL: EICAR test virus not detected")
        print("   This may indicate virus definitions need updating:")
        print("   sudo freshclam")
        return False

def test_large_file():
    """Test scanning a larger file"""
    print("\n" + "=" * 60)
    print("TEST 4: Large File Performance")
    print("=" * 60)
    
    # Create a 1MB clean file
    large_content = b"Clean content. " * 70000  # ~1MB
    
    import time
    start_time = time.time()
    
    is_safe, virus_name = virus_scanning_service.scan_file_content(
        large_content,
        "large_test.bin"
    )
    
    scan_time = time.time() - start_time
    
    print(f"File Size: {len(large_content) / 1024 / 1024:.2f} MB")
    print(f"Scan Time: {scan_time:.3f} seconds")
    print(f"Is Safe: {is_safe}")
    
    if is_safe and scan_time < 10:
        print(f"✅ PASS: Large file scanned successfully in {scan_time:.3f}s")
        return True
    else:
        print(f"❌ FAIL: Large file scan issue (time: {scan_time:.3f}s)")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "VIRUS SCANNING SERVICE TEST SUITE" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    tests = [
        test_service_availability,
        test_clean_file,
        test_infected_file,
        test_large_file
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Virus scanning is working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED - Check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

