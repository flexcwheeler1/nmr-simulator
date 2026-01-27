"""
SDBS Scraper module for interfacing with the SDBS database.
"""

from typing import List, Dict, Any
import random


class SDBSScraper:
    """Scraper for SDBS (Spectral Database for Organic Compounds) database."""
    
    def __init__(self):
        """Initialize the SDBS scraper."""
        self.demo_compounds = [
            {"name": "Ethanol", "formula": "C2H6O"},
            {"name": "Methanol", "formula": "CH4O"},
            {"name": "Benzene", "formula": "C6H6"},
            {"name": "Toluene", "formula": "C7H8"},
            {"name": "Acetone", "formula": "C3H6O"},
            {"name": "Chloroform", "formula": "CHCl3"},
            {"name": "DMSO", "formula": "C2H6OS"},
            {"name": "Pyridine", "formula": "C5H5N"},
            {"name": "Aniline", "formula": "C6H7N"},
            {"name": "Phenol", "formula": "C6H6O"}
        ]
    
    def search_compound(self, compound_name: str) -> List[Dict[str, Any]]:
        """Search for a compound in the SDBS database."""
        # For demo purposes, return matching compounds from our demo list
        results = []
        for compound in self.demo_compounds:
            if compound_name.lower() in compound["name"].lower():
                results.append(compound)
        
        return results
    
    def get_random_compounds(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get random compounds for demo purposes."""
        return random.sample(self.demo_compounds, min(count, len(self.demo_compounds)))
    
    def get_compound_data(self, compound_id: str) -> Dict[str, Any]:
        """Get detailed data for a specific compound."""
        # For demo purposes, return mock data
        return {
            "id": compound_id,
            "name": "Demo Compound",
            "formula": "C6H6",
            "nmr_data": {
                "1H": [{"shift": 7.2, "intensity": 1.0, "multiplicity": "s"}],
                "13C": [{"shift": 128.0, "intensity": 1.0}]
            }
        }
