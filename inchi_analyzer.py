#!/usr/bin/env python3
"""
Simple InChI analyzer for NMR predictions without RDKit dependency.
Provides basic structural information for teaching purposes.
"""

import re
from typing import Dict, List, Tuple, Optional

class SimpleInChIAnalyzer:
    """
    Basic InChI analyzer that works without RDKit.
    Provides simple structural information for NMR teaching.
    """
    
    def __init__(self, inchi: str):
        """Initialize with InChI string."""
        self.inchi = inchi
        self.formula = self._extract_formula()
        self.connectivity = self._extract_connectivity()
        self.h_layer = self._extract_h_layer()
    
    def _extract_formula(self) -> str:
        """Extract molecular formula from InChI."""
        # InChI format: InChI=1S/C9H9N/...
        match = re.search(r'InChI=1S/([^/]+)', self.inchi)
        return match.group(1) if match else ""
    
    def _extract_connectivity(self) -> str:
        """Extract connectivity layer from InChI."""
        # Look for connectivity after formula
        match = re.search(r'InChI=1S/[^/]+/([^/]+)', self.inchi)
        return match.group(1) if match else ""
    
    def _extract_h_layer(self) -> str:
        """Extract hydrogen layer from InChI."""
        # Look for /h layer
        match = re.search(r'/h([^/]+)', self.inchi)
        return match.group(1) if match else ""
    
    def count_carbons(self) -> int:
        """Count carbon atoms."""
        match = re.search(r'C(\d+)', self.formula)
        return int(match.group(1)) if match else 0
    
    def count_hydrogens(self) -> int:
        """Count hydrogen atoms."""
        match = re.search(r'H(\d+)', self.formula)
        return int(match.group(1)) if match else 0
    
    def is_aromatic(self) -> bool:
        """Simple check for aromatic character."""
        # Look for aromatic patterns in connectivity
        # This is a very basic heuristic
        if not self.connectivity:
            return False
        
        # Look for cyclic patterns that might be aromatic
        # Numbers that appear multiple times might indicate rings
        numbers = re.findall(r'\d+', self.connectivity)
        unique_numbers = set(numbers)
        
        # If we have repeated numbers and the formula suggests aromatic compounds
        repeated = len(numbers) > len(unique_numbers)
        has_nitrogen = 'N' in self.formula
        
        return repeated and (has_nitrogen or self.count_carbons() >= 6)
    
    def predict_aromatic_protons(self) -> int:
        """Predict number of aromatic protons."""
        if not self.is_aromatic():
            return 0
        
        # Very basic prediction based on formula
        # This is educational - real prediction needs full structure
        total_h = self.count_hydrogens()
        total_c = self.count_carbons()
        
        if 'N' in self.formula and total_c == 9:  # Like indole/quinoline
            return 4  # Rough estimate for substituted aromatic system
        elif total_c >= 6:  # Benzene derivatives
            substituents = total_c - 6
            return max(0, 5 - substituents)  # 5H for monosubstituted benzene
        
        return 0
    
    def predict_assignments(self, peaks: List[Dict]) -> List[Dict]:
        """
        Add structural assignments to peaks based on chemical shifts.
        This is a simple heuristic for teaching purposes.
        """
        enhanced_peaks = []
        
        for peak in peaks:
            shift = peak['shift']
            enhanced_peak = peak.copy()
            
            # Add assignment based on chemical shift ranges
            if shift > 7.0:
                enhanced_peak['region'] = 'aromatic'
                enhanced_peak['description'] = 'Aromatic H'
            elif 6.0 <= shift <= 7.0:
                enhanced_peak['region'] = 'vinyl/aromatic'
                enhanced_peak['description'] = 'Vinyl or aromatic H'
            elif 3.0 <= shift <= 5.0:
                enhanced_peak['region'] = 'alpha'
                enhanced_peak['description'] = 'H α to heteroatom'
            elif 2.0 <= shift <= 3.0:
                enhanced_peak['region'] = 'aliphatic'
                enhanced_peak['description'] = 'Aliphatic CH₂/CH₃'
            elif 1.0 <= shift <= 2.0:
                enhanced_peak['region'] = 'alkyl'
                enhanced_peak['description'] = 'Alkyl CH₃'
            else:
                enhanced_peak['region'] = 'upfield'
                enhanced_peak['description'] = 'Shielded H'
            
            enhanced_peaks.append(enhanced_peak)
        
        return enhanced_peaks
    
    def get_compound_info(self) -> Dict:
        """Get basic compound information."""
        return {
            'formula': self.formula,
            'carbons': self.count_carbons(),
            'hydrogens': self.count_hydrogens(),
            'aromatic': self.is_aromatic(),
            'predicted_aromatic_h': self.predict_aromatic_protons()
        }

def analyze_inchi(inchi: str) -> Optional[SimpleInChIAnalyzer]:
    """Create analyzer from InChI string."""
    try:
        if inchi and inchi.startswith('InChI='):
            return SimpleInChIAnalyzer(inchi)
    except Exception as e:
        print(f"Error analyzing InChI: {e}")
    return None

if __name__ == "__main__":
    # Test with indole InChI
    test_inchi = "InChI=1S/C9H9N/c1-7-6-10-9-5-3-2-4-8(7)9/h2-6,10H,1H3"
    
    analyzer = analyze_inchi(test_inchi)
    if analyzer:
        info = analyzer.get_compound_info()
        print("Compound Analysis:")
        print(f"Formula: {info['formula']}")
        print(f"Carbons: {info['carbons']}")
        print(f"Hydrogens: {info['hydrogens']}")
        print(f"Aromatic: {info['aromatic']}")
        print(f"Predicted aromatic H: {info['predicted_aromatic_h']}")
    else:
        print("Failed to analyze InChI")
