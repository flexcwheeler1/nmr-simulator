"""
Main NMR Simulator class.

This module provides the core simulation functionality for generating NMR spectra
from molecular structures and chemical shift data.
"""

import numpy as np
from typing import Dict, List, Optional, Union
from .molecule import Molecule, Atom
from .spectrum import Spectrum, Peak


class NMRSimulator:
    """
    Main NMR simulator class for generating realistic NMR spectra.
    """
    
    def __init__(self, field_strength: float = 400.0):
        """
        Initialize the NMR simulator.
        
        Args:
            field_strength: Magnetic field strength in MHz
        """
        self.field_strength = field_strength
        self.default_linewidth = 0.01  # Default peak width in ppm
        self.noise_level = 0.001  # Default noise level
        
        # Default chemical shift ranges for different functional groups
        self.default_shifts = {
            '1H': {
                'alkyl': (0.8, 2.5),
                'aromatic': (7.0, 8.5),
                'aldehyde': (9.5, 10.5),
                'alcohol': (1.0, 5.5),
                'carboxylic_acid': (10.5, 12.0),
                'alkene': (4.5, 6.5)
            },
            '13C': {
                'alkyl': (10.0, 50.0),
                'aromatic': (120.0, 160.0),
                'carbonyl': (160.0, 220.0),
                'alkene': (100.0, 150.0)
            }
        }
    
    def simulate_spectrum(self, molecule: Molecule, nucleus: str = '1H', 
                         use_sdbs_data: bool = True) -> Spectrum:
        """
        Simulate an NMR spectrum for a given molecule.
        
        Args:
            molecule: Molecule object to simulate
            nucleus: Nucleus type ('1H', '13C', etc.)
            use_sdbs_data: Whether to use SDBS chemical shift data if available
            
        Returns:
            Spectrum object containing the simulated spectrum
        """
        spectrum = Spectrum(nucleus=nucleus, field_strength=self.field_strength)
        spectrum.title = f"{nucleus} NMR Spectrum of {molecule.identifier}"
        
        # Get atoms of the specified nucleus
        target_atoms = molecule.get_atoms_by_element(nucleus.replace('1', '').replace('2', ''))
        
        if not target_atoms:
            # No atoms of this type found
            return spectrum
        
        # Generate peaks for each atom
        for atom in target_atoms:
            if atom.chemical_shift is not None:
                # Use provided chemical shift
                peak = self._create_peak_from_atom(atom)
                spectrum.add_peak(peak)
            elif use_sdbs_data:
                # Try to estimate chemical shift
                estimated_shift = self._estimate_chemical_shift(atom, nucleus)
                if estimated_shift is not None:
                    atom.chemical_shift = estimated_shift
                    peak = self._create_peak_from_atom(atom)
                    spectrum.add_peak(peak)
        
        # Generate the full spectrum data
        spectrum.generate_spectrum_data()
        
        # Add realistic noise
        if spectrum.data_points is not None:
            noise = np.random.normal(0, self.noise_level, len(spectrum.data_points))
            spectrum.data_points += noise
        
        return spectrum
    
    def _create_peak_from_atom(self, atom: Atom) -> Peak:
        """
        Create a Peak object from an Atom with chemical shift data.
        
        Args:
            atom: Atom object with chemical shift information
            
        Returns:
            Peak object
        """
        return Peak(
            chemical_shift=atom.chemical_shift or 0.0,
            intensity=atom.integration or 1.0,
            width=self.default_linewidth,
            multiplicity=atom.multiplicity or 's',
            coupling_constants=atom.coupling_constants,
            integration=atom.integration or 1.0
        )
    
    def _estimate_chemical_shift(self, atom: Atom, nucleus: str) -> Optional[float]:
        """
        Estimate chemical shift for an atom based on its environment.
        This is a simplified estimation - in practice, you'd use more sophisticated methods.
        
        Args:
            atom: Atom to estimate shift for
            nucleus: Nucleus type
            
        Returns:
            Estimated chemical shift in ppm, or None if cannot estimate
        """
        if nucleus not in self.default_shifts:
            return None
        
        element = atom.element
        if element not in ['H', 'C']:
            return None
        
        # Simple random selection from alkyl range as default
        # In a real implementation, this would analyze molecular environment
        shift_ranges = self.default_shifts[nucleus]
        alkyl_range = shift_ranges.get('alkyl', (0.0, 2.0))
        
        # Add some randomness to make it more realistic
        min_shift, max_shift = alkyl_range
        return np.random.uniform(min_shift, max_shift)
    
    def add_coupling(self, spectrum: Spectrum, atom1_pos: int, atom2_pos: int, 
                    j_value: float) -> None:
        """
        Add coupling between two atoms (simplified implementation).
        
        Args:
            spectrum: Spectrum to modify
            atom1_pos: Position of first atom
            atom2_pos: Position of second atom
            j_value: Coupling constant in Hz
        """
        # This is a simplified implementation
        # In practice, coupling patterns are more complex
        for peak in spectrum.peaks:
            if hasattr(peak, 'atom_position'):
                if peak.atom_position in [atom1_pos, atom2_pos]:
                    if peak.coupling_constants is None:
                        peak.coupling_constants = []
                    peak.coupling_constants.append(j_value)
                    
                    # Update multiplicity based on coupling
                    if peak.multiplicity == 's':
                        peak.multiplicity = 'd'
                    elif peak.multiplicity == 'd':
                        peak.multiplicity = 't'
    
    def simulate_multiple_spectra(self, molecules: List[Molecule], 
                                nucleus: str = '1H') -> List[Spectrum]:
        """
        Simulate spectra for multiple molecules.
        
        Args:
            molecules: List of Molecule objects
            nucleus: Nucleus type
            
        Returns:
            List of Spectrum objects
        """
        spectra = []
        for molecule in molecules:
            spectrum = self.simulate_spectrum(molecule, nucleus)
            spectra.append(spectrum)
        return spectra
    
    def compare_spectra(self, spectrum1: Spectrum, spectrum2: Spectrum) -> Dict:
        """
        Compare two spectra and return similarity metrics.
        
        Args:
            spectrum1: First spectrum
            spectrum2: Second spectrum
            
        Returns:
            Dictionary with comparison metrics
        """
        if (spectrum1.data_points is None or spectrum2.data_points is None or
            spectrum1.ppm_axis is None or spectrum2.ppm_axis is None):
            return {'error': 'Spectra not generated'}
        
        # Simple correlation coefficient
        correlation = np.corrcoef(spectrum1.data_points, spectrum2.data_points)[0, 1]
        
        # Peak count comparison
        peak_count_diff = abs(len(spectrum1.peaks) - len(spectrum2.peaks))
        
        return {
            'correlation': correlation,
            'peak_count_difference': peak_count_diff,
            'spectrum1_peaks': len(spectrum1.peaks),
            'spectrum2_peaks': len(spectrum2.peaks)
        }
    
    def set_field_strength(self, field_strength: float) -> None:
        """Set the magnetic field strength."""
        self.field_strength = field_strength
    
    def set_noise_level(self, noise_level: float) -> None:
        """Set the noise level for simulated spectra."""
        self.noise_level = noise_level
    
    def set_default_linewidth(self, linewidth: float) -> None:
        """Set the default line width for peaks."""
        self.default_linewidth = linewidth
