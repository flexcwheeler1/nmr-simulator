#!/usr/bin/env python3
"""
Enhanced SDBS Integration for NMR Simulator

Integrates direct SDBS retrieval with the existing NMR simulator GUI.
Provides both real SDBS access (when working) and enhanced demo data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from direct_sdbs_retriever import DirectSDBSRetriever
from typing import Dict, List, Optional
import json

class EnhancedSDBSIntegration:
    """
    Enhanced SDBS integration with fallback to realistic demo data.
    """
    
    def __init__(self):
        self.retriever = DirectSDBSRetriever()
        self.demo_database = self._create_enhanced_demo_database()
    
    def search_compound_by_name(self, compound_name: str) -> List[Dict]:
        """
        Search for compounds by name with SDBS integration.
        
        Args:
            compound_name: Name of the compound to search for
            
        Returns:
            List of compound dictionaries with NMR data
        """
        # First try to find in demo database by name
        demo_results = []
        for compound_id, data in self.demo_database.items():
            if compound_name.lower() in data.get('name', '').lower():
                demo_results.append({
                    'sdbsno': compound_id,
                    'name': data['name'],
                    'formula': data['formula'],
                    'molecular_weight': data.get('molecular_weight', 0),
                    'source': 'demo',
                    'nmr_data': data.get('nmr_data', {})
                })
        
        return demo_results
    
    def get_compound_by_id(self, sdbsno: str, try_real: bool = False) -> Optional[Dict]:
        """
        Get compound data by SDBS number.
        
        Args:
            sdbsno: SDBS compound number
            try_real: Whether to attempt real SDBS retrieval
            
        Returns:
            Compound data dictionary or None
        """
        # Try real SDBS first if requested
        if try_real:
            try:
                print(f"Attempting real SDBS retrieval for #{sdbsno}...")
                real_data = self.retriever.get_compound_data(sdbsno)
                if real_data and real_data.get('name', 'Unknown') != 'Unknown':
                    real_data['source'] = 'real_sdbs'
                    return real_data
            except Exception as e:
                print(f"Real SDBS retrieval failed: {e}")
        
        # Fallback to demo database
        if sdbsno in self.demo_database:
            demo_data = self.demo_database[sdbsno].copy()
            demo_data['sdbsno'] = sdbsno
            demo_data['source'] = 'demo'
            return demo_data
        
        return None
    
    def _create_enhanced_demo_database(self) -> Dict:
        """Create enhanced demo database with realistic NMR data."""
        return {
            # Benzene
            "1": {
                "name": "Benzene",
                "formula": "C6H6",
                "molecular_weight": 78.11,
                "cas_number": "71-43-2",
                "nmr_data": {
                    "1H": {
                        "solvent": "CDCl3",
                        "frequency": "400 MHz",
                        "peaks": [
                            {"shift": 7.36, "multiplicity": "s", "integration": 6, "coupling": [], "assignment": "Ar-H"}
                        ]
                    },
                    "13C": {
                        "solvent": "CDCl3", 
                        "frequency": "100 MHz",
                        "peaks": [
                            {"shift": 128.4, "multiplicity": "s", "integration": 1, "assignment": "Ar-C"}
                        ]
                    }
                }
            },
            
            # Ethanol
            "10": {
                "name": "Ethanol",
                "formula": "C2H6O",
                "molecular_weight": 46.07,
                "cas_number": "64-17-5",
                "nmr_data": {
                    "1H": {
                        "solvent": "CDCl3",
                        "frequency": "400 MHz",
                        "peaks": [
                            {"shift": 3.65, "multiplicity": "q", "integration": 2, "coupling": [7.0], "assignment": "OCH2"},
                            {"shift": 1.25, "multiplicity": "t", "integration": 3, "coupling": [7.0], "assignment": "CH3"},
                            {"shift": 2.61, "multiplicity": "s", "integration": 1, "coupling": [], "assignment": "OH"}
                        ]
                    },
                    "13C": {
                        "solvent": "CDCl3",
                        "frequency": "100 MHz", 
                        "peaks": [
                            {"shift": 63.4, "multiplicity": "s", "integration": 1, "assignment": "OCH2"},
                            {"shift": 18.1, "multiplicity": "s", "integration": 1, "assignment": "CH3"}
                        ]
                    }
                }
            },
            
            # Indole  
            "1839": {
                "name": "Indole",
                "formula": "C8H7N", 
                "molecular_weight": 117.15,
                "cas_number": "120-72-9",
                "nmr_data": {
                    "1H": {
                        "solvent": "DMSO-d6",
                        "frequency": "400 MHz",
                        "peaks": [
                            {"shift": 11.08, "multiplicity": "s", "integration": 1, "coupling": [], "assignment": "NH"},
                            {"shift": 7.54, "multiplicity": "d", "integration": 1, "coupling": [7.8], "assignment": "H-4"},
                            {"shift": 7.34, "multiplicity": "d", "integration": 1, "coupling": [8.1], "assignment": "H-7"},
                            {"shift": 7.15, "multiplicity": "t", "integration": 1, "coupling": [2.8], "assignment": "H-2"},
                            {"shift": 7.04, "multiplicity": "t", "integration": 1, "coupling": [7.5], "assignment": "H-6"},
                            {"shift": 6.98, "multiplicity": "t", "integration": 1, "coupling": [7.5], "assignment": "H-5"},
                            {"shift": 6.38, "multiplicity": "m", "integration": 1, "coupling": [], "assignment": "H-3"}
                        ]
                    },
                    "13C": {
                        "solvent": "DMSO-d6",
                        "frequency": "100 MHz",
                        "peaks": [
                            {"shift": 136.1, "multiplicity": "s", "integration": 1, "assignment": "C-7a"},
                            {"shift": 127.2, "multiplicity": "s", "integration": 1, "assignment": "C-2"},
                            {"shift": 124.4, "multiplicity": "s", "integration": 1, "assignment": "C-3a"},
                            {"shift": 121.6, "multiplicity": "s", "integration": 1, "assignment": "C-6"},
                            {"shift": 120.9, "multiplicity": "s", "integration": 1, "assignment": "C-4"},
                            {"shift": 119.4, "multiplicity": "s", "integration": 1, "assignment": "C-5"},
                            {"shift": 111.8, "multiplicity": "s", "integration": 1, "assignment": "C-7"},
                            {"shift": 101.8, "multiplicity": "s", "integration": 1, "assignment": "C-3"}
                        ]
                    }
                }
            },
            
            # Acetone
            "100": {
                "name": "Acetone",
                "formula": "C3H6O",
                "molecular_weight": 58.08,
                "cas_number": "67-64-1", 
                "nmr_data": {
                    "1H": {
                        "solvent": "CDCl3",
                        "frequency": "400 MHz",
                        "peaks": [
                            {"shift": 2.17, "multiplicity": "s", "integration": 6, "coupling": [], "assignment": "CH3"}
                        ]
                    },
                    "13C": {
                        "solvent": "CDCl3",
                        "frequency": "100 MHz",
                        "peaks": [
                            {"shift": 207.1, "multiplicity": "s", "integration": 1, "assignment": "C=O"},
                            {"shift": 29.8, "multiplicity": "s", "integration": 1, "assignment": "CH3"}
                        ]
                    }
                }
            },
            
            # Toluene
            "1000": {
                "name": "Toluene", 
                "formula": "C7H8",
                "molecular_weight": 92.14,
                "cas_number": "108-88-3",
                "nmr_data": {
                    "1H": {
                        "solvent": "CDCl3",
                        "frequency": "400 MHz",
                        "peaks": [
                            {"shift": 7.25, "multiplicity": "m", "integration": 5, "coupling": [], "assignment": "Ar-H"},
                            {"shift": 2.34, "multiplicity": "s", "integration": 3, "coupling": [], "assignment": "CH3"}
                        ]
                    },
                    "13C": {
                        "solvent": "CDCl3",
                        "frequency": "100 MHz",
                        "peaks": [
                            {"shift": 137.9, "multiplicity": "s", "integration": 1, "assignment": "C-1"},
                            {"shift": 129.2, "multiplicity": "s", "integration": 1, "assignment": "C-3,5"},
                            {"shift": 128.3, "multiplicity": "s", "integration": 1, "assignment": "C-4"},
                            {"shift": 125.6, "multiplicity": "s", "integration": 1, "assignment": "C-2,6"},
                            {"shift": 21.4, "multiplicity": "s", "integration": 1, "assignment": "CH3"}
                        ]
                    }
                }
            }
        }

def test_enhanced_integration():
    """Test the enhanced SDBS integration."""
    integration = EnhancedSDBSIntegration()
    
    print("=== Testing Enhanced SDBS Integration ===\n")
    
    # Test search by name
    print("1. Testing search by compound name:")
    results = integration.search_compound_by_name("indole")
    for result in results:
        print(f"   Found: {result['name']} (SDBS #{result['sdbsno']})")
    
    print("\n2. Testing compound retrieval by ID:")
    compound = integration.get_compound_by_id("1839", try_real=False)
    if compound:
        print(f"   Compound: {compound['name']}")
        print(f"   Formula: {compound['formula']}")
        if 'nmr_data' in compound and '1H' in compound['nmr_data']:
            h1_peaks = len(compound['nmr_data']['1H']['peaks'])
            print(f"   1H NMR: {h1_peaks} peaks")

if __name__ == "__main__":
    test_enhanced_integration()
