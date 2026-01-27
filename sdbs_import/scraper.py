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
            # Aromatic heterocycles
            {"name": "Indole", "formula": "C8H7N", "category": "Heterocycle", "id": "SDBS001"},
            {"name": "Pyridine", "formula": "C5H5N", "category": "Heterocycle", "id": "SDBS002"},
            {"name": "Furan", "formula": "C4H4O", "category": "Heterocycle", "id": "SDBS003"},
            {"name": "Thiophene", "formula": "C4H4S", "category": "Heterocycle", "id": "SDBS004"},
            {"name": "Pyrrole", "formula": "C4H5N", "category": "Heterocycle", "id": "SDBS005"},
            {"name": "Imidazole", "formula": "C3H4N2", "category": "Heterocycle", "id": "SDBS006"},
            
            # Aromatics
            {"name": "Benzene", "formula": "C6H6", "category": "Aromatic", "id": "SDBS007"},
            {"name": "Toluene", "formula": "C7H8", "category": "Aromatic", "id": "SDBS008"},
            {"name": "Phenol", "formula": "C6H6O", "category": "Aromatic", "id": "SDBS009"},
            {"name": "Aniline", "formula": "C6H7N", "category": "Aromatic", "id": "SDBS010"},
            {"name": "Benzaldehyde", "formula": "C7H6O", "category": "Aromatic", "id": "SDBS011"},
            {"name": "Benzoic acid", "formula": "C7H6O2", "category": "Aromatic", "id": "SDBS012"},
            {"name": "Nitrobenzene", "formula": "C6H5NO2", "category": "Aromatic", "id": "SDBS013"},
            
            # Alcohols
            {"name": "Methanol", "formula": "CH4O", "category": "Alcohol", "id": "SDBS014"},
            {"name": "Ethanol", "formula": "C2H6O", "category": "Alcohol", "id": "SDBS015"},
            {"name": "2-Propanol", "formula": "C3H8O", "category": "Alcohol", "id": "SDBS016"},
            {"name": "1-Butanol", "formula": "C4H10O", "category": "Alcohol", "id": "SDBS017"},
            {"name": "tert-Butanol", "formula": "C4H10O", "category": "Alcohol", "id": "SDBS018"},
            {"name": "Benzyl alcohol", "formula": "C7H8O", "category": "Alcohol", "id": "SDBS019"},
            
            # Ketones
            {"name": "Acetone", "formula": "C3H6O", "category": "Ketone", "id": "SDBS020"},
            {"name": "2-Butanone", "formula": "C4H8O", "category": "Ketone", "id": "SDBS021"},
            {"name": "Cyclohexanone", "formula": "C6H10O", "category": "Ketone", "id": "SDBS022"},
            {"name": "Acetophenone", "formula": "C8H8O", "category": "Ketone", "id": "SDBS023"},
            
            # Carboxylic acids
            {"name": "Acetic acid", "formula": "C2H4O2", "category": "Carboxylic acid", "id": "SDBS024"},
            {"name": "Propionic acid", "formula": "C3H6O2", "category": "Carboxylic acid", "id": "SDBS025"},
            {"name": "Butyric acid", "formula": "C4H8O2", "category": "Carboxylic acid", "id": "SDBS026"},
            
            # Esters
            {"name": "Ethyl acetate", "formula": "C4H8O2", "category": "Ester", "id": "SDBS027"},
            {"name": "Methyl propanoate", "formula": "C4H8O2", "category": "Ester", "id": "SDBS028"},
            {"name": "Methyl benzoate", "formula": "C8H8O2", "category": "Ester", "id": "SDBS029"},
            
            # Ethers
            {"name": "Diethyl ether", "formula": "C4H10O", "category": "Ether", "id": "SDBS030"},
            {"name": "Tetrahydrofuran", "formula": "C4H8O", "category": "Ether", "id": "SDBS031"},
            {"name": "Dimethoxyethane", "formula": "C4H10O2", "category": "Ether", "id": "SDBS032"},
            
            # Halogenated compounds
            {"name": "Chloroform", "formula": "CHCl3", "category": "Halogenated", "id": "SDBS033"},
            {"name": "Dichloromethane", "formula": "CH2Cl2", "category": "Halogenated", "id": "SDBS034"},
            {"name": "Chlorobenzene", "formula": "C6H5Cl", "category": "Halogenated", "id": "SDBS035"},
            
            # Sulfur compounds
            {"name": "DMSO", "formula": "C2H6OS", "category": "Sulfur compound", "id": "SDBS036"},
            {"name": "Dimethyl sulfide", "formula": "C2H6S", "category": "Sulfur compound", "id": "SDBS037"},
            
            # Alkanes
            {"name": "n-Hexane", "formula": "C6H14", "category": "Alkane", "id": "SDBS038"},
            {"name": "Cyclohexane", "formula": "C6H12", "category": "Alkane", "id": "SDBS039"},
            {"name": "2-Methylpentane", "formula": "C6H14", "category": "Alkane", "id": "SDBS040"},
            
            # Alkenes
            {"name": "1-Hexene", "formula": "C6H12", "category": "Alkene", "id": "SDBS041"},
            {"name": "Cyclohexene", "formula": "C6H10", "category": "Alkene", "id": "SDBS042"},
            {"name": "Styrene", "formula": "C8H8", "category": "Alkene", "id": "SDBS043"}
        ]
    
    def search_compound(self, compound_name: str) -> List[Dict[str, Any]]:
        """Search for a compound in the SDBS database."""
        # For demo purposes, return matching compounds from our demo list
        results = []
        search_term = compound_name.lower()
        
        for compound in self.demo_compounds:
            # Search in name, formula, and category
            if (search_term in compound["name"].lower() or 
                search_term in compound["formula"].lower() or
                search_term in compound.get("category", "").lower()):
                results.append(compound)
        
        # If no exact matches, try partial matches
        if not results:
            for compound in self.demo_compounds:
                if any(search_term in field.lower() for field in [
                    compound["name"], 
                    compound["formula"], 
                    compound.get("category", "")
                ]):
                    results.append(compound)
        
        return results[:10]  # Limit to 10 results
    
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
