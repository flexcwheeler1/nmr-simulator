#!/usr/bin/env python3
"""
Debug script to test parsing of specific NMR data formats.
This helps identify why certain peaks like 7.57 ppm might be missing.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nmr_data_input import NMRDataParser

def test_missing_peaks():
    """Test parsing to find missing 7.57 peak."""
    parser = NMRDataParser()
    
    # Test different formats that might contain 7.57
    test_cases = [
        # Assignment format
        "A 7.6\nB 7.57\nC 2.3",
        
        # Standard format
        "7.60 (m, 1H)\n7.57 (m, 1H)\n2.30 (s, 3H)",
        
        # Tabulated format  
        "7.60 100 1\n7.57 85 2\n2.30 300 3",
        
        # Mixed format
        "A 7.6\n7.57 (s, 1H)\n2.30 (s, 3H)",
        
        # Your actual data format (example)
        """7.265 70 1
7.263 102 2  
7.260 79 3
7.57 85 4
7.245 114 5"""
    ]
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n=== Test Case {i} ===")
        print(f"Input: {repr(test_data)}")
        
        peaks = parser.parse_nmr_text(test_data, "1H")
        print(f"Parsed {len(peaks)} peaks:")
        
        for peak in peaks:
            shift = peak['shift']
            print(f"  δ {shift:.3f} ppm")
            
            # Check if we found the missing 7.57 signal
            if 7.56 <= shift <= 7.58:
                print(f"  ✅ Found 7.57 region signal!")
        
        # Check specifically for 7.57
        found_757 = any(7.56 <= p['shift'] <= 7.58 for p in peaks)
        if not found_757:
            print(f"  ❌ Missing 7.57 region signal")

def test_assignment_parsing():
    """Test assignment format specifically."""
    parser = NMRDataParser()
    
    # Test the assignment format you mentioned
    assignment_data = """A 7.6
B 7.57  
C 2.3
D 6.85"""
    
    print("\n=== Assignment Format Test ===")
    print(f"Input:\n{assignment_data}")
    
    peaks = parser.parse_nmr_text(assignment_data, "1H")
    print(f"\nParsed {len(peaks)} peaks:")
    
    for peak in peaks:
        assignment = peak.get('assignment', 'None')
        print(f"  {assignment}: δ {peak['shift']:.3f} ppm ({peak['multiplicity']}, {peak['integration']}H)")

if __name__ == "__main__":
    print("🔍 Debugging Missing NMR Peaks")
    print("=" * 40)
    
    test_missing_peaks()
    test_assignment_parsing()
    
    print("\n" + "=" * 40)
    print("🎯 Debug complete. Check output above for missing signals.")
