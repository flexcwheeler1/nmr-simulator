"""
Molecule representation for NMR simulation.

This module provides classes and functions for representing molecular structures
and their NMR-relevant properties.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Atom:
    """Represents an atom in a molecule with NMR-relevant properties."""
    element: str
    position: int
    chemical_shift: Optional[float] = None
    multiplicity: Optional[str] = None  # s, d, t, q, m, etc.
    coupling_constants: Optional[List[float]] = None
    integration: Optional[float] = None


class Molecule:
    """
    Represents a molecule for NMR simulation.
    
    Can be initialized from molecular formula, SMILES string, or manual atom specification.
    """
    
    def __init__(self, identifier: str = "", molecule_type: str = "formula"):
        """
        Initialize a molecule.
        
        Args:
            identifier: Molecular formula, SMILES string, or molecule name
            molecule_type: Type of identifier ("formula", "smiles", "name")
        """
        self.identifier = identifier
        self.molecule_type = molecule_type
        self.atoms: List[Atom] = []
        self.name: Optional[str] = None
        self.molecular_weight: Optional[float] = None
        
        if identifier:
            self._parse_identifier()
    
    def _parse_identifier(self) -> None:
        """Parse the molecule identifier and extract basic information."""
        if self.molecule_type == "formula":
            self._parse_molecular_formula()
        elif self.molecule_type == "smiles":
            self._parse_smiles()
        elif self.molecule_type == "name":
            self.name = self.identifier
    
    def _parse_molecular_formula(self) -> None:
        """Parse a molecular formula like C6H12O6."""
        # Simple regex to extract element counts
        pattern = r'([A-Z][a-z]?)(\d*)'
        matches = re.findall(pattern, self.identifier)
        
        atom_id = 1
        for element, count_str in matches:
            count = int(count_str) if count_str else 1
            for _ in range(count):
                self.atoms.append(Atom(element=element, position=atom_id))
                atom_id += 1
    
    def _parse_smiles(self) -> None:
        """Parse a SMILES string (simplified implementation)."""
        # This is a very basic implementation
        # In a real application, you'd use a chemistry library like RDKit
        self.name = f"SMILES: {self.identifier}"
    
    def add_atom(self, atom: Atom) -> None:
        """Add an atom to the molecule."""
        self.atoms.append(atom)
    
    def get_atoms_by_element(self, element: str) -> List[Atom]:
        """Get all atoms of a specific element."""
        return [atom for atom in self.atoms if atom.element == element]
    
    def get_proton_count(self) -> int:
        """Get the total number of protons (H atoms)."""
        return len(self.get_atoms_by_element('H'))
    
    def get_carbon_count(self) -> int:
        """Get the total number of carbons."""
        return len(self.get_atoms_by_element('C'))
    
    def set_chemical_shifts(self, shifts: Dict[int, float]) -> None:
        """
        Set chemical shifts for atoms by position.
        
        Args:
            shifts: Dictionary mapping atom position to chemical shift (ppm)
        """
        for atom in self.atoms:
            if atom.position in shifts:
                atom.chemical_shift = shifts[atom.position]
    
    def get_chemical_shifts(self, element: str) -> List[Tuple[int, float]]:
        """
        Get chemical shifts for atoms of a specific element.
        
        Args:
            element: Element symbol (e.g., 'H', 'C')
            
        Returns:
            List of (position, chemical_shift) tuples
        """
        shifts = []
        for atom in self.atoms:
            if atom.element == element and atom.chemical_shift is not None:
                shifts.append((atom.position, atom.chemical_shift))
        return shifts
    
    def __str__(self) -> str:
        """String representation of the molecule."""
        if self.name:
            return f"Molecule: {self.name} ({self.identifier})"
        return f"Molecule: {self.identifier}"
    
    def __repr__(self) -> str:
        """Detailed representation of the molecule."""
        return f"Molecule(identifier='{self.identifier}', type='{self.molecule_type}', atoms={len(self.atoms)})"
