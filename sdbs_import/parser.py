"""
SDBS Data Parser

This module provides functionality to parse and convert SDBS data into formats
suitable for NMR simulation.
"""

import re
import sys
import os
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmr_simulator.molecule import Molecule, Atom
from nmr_simulator.spectrum import Spectrum, Peak


class SDBSParser:
    """
    Parser for SDBS (Spectral Database for Organic Compounds) data.
    
    Converts raw SDBS data into Molecule and Spectrum objects for simulation.
    """
    
    def __init__(self):
        """Initialize the SDBS parser."""
        self.multiplicity_map = {
            's': 'singlet',
            'd': 'doublet',
            't': 'triplet',
            'q': 'quartet',
            'qui': 'quintet',
            'sex': 'sextet',
            'sep': 'septet',
            'oct': 'octet',
            'm': 'multiplet',
            'br': 'broad',
            'dd': 'doublet of doublets',
            'dt': 'doublet of triplets',
            'td': 'triplet of doublets',
            'dq': 'doublet of quartets',
            'qd': 'quartet of doublets',
            'tt': 'triplet of triplets',
            'ddd': 'doublet of doublet of doublets',
            'ddt': 'doublet of doublet of triplets',
            'dtd': 'doublet of triplet of doublets',
            'tdd': 'triplet of doublet of doublets',
            'dddd': 'doublet of doublet of doublet of doublets',
            'app': 'apparent',
            'vt': 'virtual triplet',
            'vd': 'virtual doublet',
            'vs': 'virtual singlet'
        }
    
    def parse_sdbs_data(self, sdbs_data: Dict, compound_name: str = "") -> Tuple[Molecule, List[Spectrum]]:
        """
        Parse SDBS data and create Molecule and Spectrum objects.
        
        Args:
            sdbs_data: Raw SDBS data dictionary
            compound_name: Name of the compound
            
        Returns:
            Tuple of (Molecule object, List of Spectrum objects)
        """
        # Create molecule object
        molecule = Molecule(identifier=compound_name, molecule_type="name")
        molecule.name = compound_name
        
        spectra = []
        
        # Parse H1 NMR data
        if 'h1_nmr' in sdbs_data and sdbs_data['h1_nmr']:
            h1_spectrum = self._parse_h1_nmr(sdbs_data['h1_nmr'], sdbs_data.get('conditions', {}))
            h1_spectrum.title = f"1H NMR Spectrum of {compound_name}"
            spectra.append(h1_spectrum)
            
            # Add H atoms to molecule with chemical shifts
            self._add_atoms_from_spectrum(molecule, h1_spectrum, 'H')
        
        # Parse C13 NMR data
        if 'c13_nmr' in sdbs_data and sdbs_data['c13_nmr']:
            c13_spectrum = self._parse_c13_nmr(sdbs_data['c13_nmr'], sdbs_data.get('conditions', {}))
            c13_spectrum.title = f"13C NMR Spectrum of {compound_name}"
            spectra.append(c13_spectrum)
            
            # Add C atoms to molecule with chemical shifts
            self._add_atoms_from_spectrum(molecule, c13_spectrum, 'C')
        
        return molecule, spectra
    
    def _parse_h1_nmr(self, h1_data: List[Dict], conditions: Dict) -> Spectrum:
        """
        Parse 1H NMR data into a Spectrum object.
        
        Args:
            h1_data: List of H1 NMR peak data
            conditions: Measurement conditions
            
        Returns:
            Spectrum object for 1H NMR
        """
        field_strength = conditions.get('field_strength', 400.0)
        spectrum = Spectrum(nucleus='1H', field_strength=field_strength)
        
        for peak_data in h1_data:
            peak = self._create_peak_from_data(peak_data, field_strength)
            spectrum.add_peak(peak)
        
        return spectrum
    
    def _parse_c13_nmr(self, c13_data: List[Dict], conditions: Dict) -> Spectrum:
        """
        Parse 13C NMR data into a Spectrum object.
        
        Args:
            c13_data: List of C13 NMR peak data
            conditions: Measurement conditions
            
        Returns:
            Spectrum object for 13C NMR
        """
        field_strength = conditions.get('field_strength', 400.0)
        spectrum = Spectrum(nucleus='13C', field_strength=field_strength)
        
        for peak_data in c13_data:
            peak = self._create_peak_from_data(peak_data, field_strength)
            spectrum.add_peak(peak)
        
        return spectrum
    
    def _create_peak_from_data(self, peak_data: Dict, field_strength: float) -> Peak:
        """
        Create a Peak object from SDBS peak data.
        
        Args:
            peak_data: Dictionary containing peak information
            field_strength: NMR field strength in MHz
            
        Returns:
            Peak object
        """
        chemical_shift = peak_data.get('chemical_shift', 0.0)
        multiplicity = peak_data.get('multiplicity', 's')
        integration = peak_data.get('integration', 1.0)
        description = peak_data.get('description', '')
        
        # Extract coupling constants from description
        coupling_constants = self._extract_coupling_constants(description)
        
        # Estimate peak intensity based on integration
        intensity = integration if integration else 1.0
        
        # Estimate peak width (narrower for 13C, broader for 1H)
        if 'C' in description or chemical_shift > 50:  # Likely 13C
            width = 0.5  # Broader peaks for 13C
        else:  # Likely 1H
            width = 0.01  # Narrower peaks for 1H
        
        return Peak(
            chemical_shift=chemical_shift,
            intensity=intensity,
            width=width,
            multiplicity=multiplicity,
            integration=integration,
            coupling_constants=coupling_constants
        )
    
    def _extract_coupling_constants(self, description: str) -> Optional[List[float]]:
        """
        Extract coupling constants from peak description.
        
        Args:
            description: Peak description string
            
        Returns:
            List of coupling constants in Hz, or None if none found
        """
        # Look for patterns like "J = 7.2 Hz" or "J 7.2"
        j_pattern = r'J\s*=?\s*(\d+\.?\d*)\s*Hz?'
        matches = re.findall(j_pattern, description, re.IGNORECASE)
        
        if matches:
            try:
                return [float(match) for match in matches]
            except ValueError:
                pass
        
        return None
    
    def _add_atoms_from_spectrum(self, molecule: Molecule, spectrum: Spectrum, element: str) -> None:
        """
        Add atoms to molecule based on spectrum peaks.
        
        Args:
            molecule: Molecule object to modify
            spectrum: Spectrum containing peak data
            element: Element type ('H' or 'C')
        """
        for i, peak in enumerate(spectrum.peaks):
            atom = Atom(
                element=element,
                position=len(molecule.atoms) + 1,
                chemical_shift=peak.chemical_shift,
                multiplicity=peak.multiplicity,
                coupling_constants=peak.coupling_constants,
                integration=peak.integration
            )
            molecule.add_atom(atom)
    
    def create_demo_molecule(self, compound_name: str = "Ethanol") -> Tuple[Molecule, List[Spectrum]]:
        """
        Create a demo molecule with realistic NMR data for testing.
        
        Args:
            compound_name: Name of the demo compound
            
        Returns:
            Tuple of (Molecule object, List of Spectrum objects)
        """
        demo_data = self._get_demo_data(compound_name)
        return self.parse_sdbs_data(demo_data, compound_name)
    
    def _get_demo_data(self, compound_name: str) -> Dict:
        """
        Get demo SDBS data for common compounds.
        
        Args:
            compound_name: Name of the compound
            
        Returns:
            Dictionary with demo NMR data
        """
        demo_compounds = {
            'Ethanol': {
                'h1_nmr': [
                    {
                        'chemical_shift': 1.25,
                        'description': 't, 3H, J = 7.2 Hz',
                        'multiplicity': 't',
                        'integration': 3.0
                    },
                    {
                        'chemical_shift': 3.69,
                        'description': 'q, 2H, J = 7.2 Hz',
                        'multiplicity': 'q',
                        'integration': 2.0
                    },
                    {
                        'chemical_shift': 5.32,
                        'description': 'br s, 1H',
                        'multiplicity': 's',
                        'integration': 1.0
                    }
                ],
                'c13_nmr': [
                    {
                        'chemical_shift': 18.3,
                        'description': 'CH3',
                        'multiplicity': 's',
                        'integration': 1.0
                    },
                    {
                        'chemical_shift': 58.2,
                        'description': 'CH2',
                        'multiplicity': 's',
                        'integration': 1.0
                    }
                ],
                'conditions': {
                    'solvent': 'CDCl3',
                    'field_strength': 400
                }
            },
            'Acetone': {
                'h1_nmr': [
                    {
                        'chemical_shift': 2.17,
                        'description': 's, 6H',
                        'multiplicity': 's',
                        'integration': 6.0
                    }
                ],
                'c13_nmr': [
                    {
                        'chemical_shift': 29.8,
                        'description': 'CH3',
                        'multiplicity': 's',
                        'integration': 2.0
                    },
                    {
                        'chemical_shift': 206.7,
                        'description': 'C=O',
                        'multiplicity': 's',
                        'integration': 1.0
                    }
                ],
                'conditions': {
                    'solvent': 'CDCl3',
                    'field_strength': 400
                }
            },
            'Benzene': {
                'h1_nmr': [
                    {
                        'chemical_shift': 7.36,
                        'description': 's, 6H',
                        'multiplicity': 's',
                        'integration': 6.0
                    }
                ],
                'c13_nmr': [
                    {
                        'chemical_shift': 128.4,
                        'description': 'CH',
                        'multiplicity': 's',
                        'integration': 6.0
                    }
                ],
                'conditions': {
                    'solvent': 'CDCl3',
                    'field_strength': 400
                }
            }
        }
        
        return demo_compounds.get(compound_name, demo_compounds['Ethanol'])
    
    def validate_chemical_shifts(self, spectrum: Spectrum) -> List[str]:
        """
        Validate chemical shifts against expected ranges.
        
        Args:
            spectrum: Spectrum to validate
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        for i, peak in enumerate(spectrum.peaks):
            shift = peak.chemical_shift
            
            if spectrum.nucleus == '1H':
                if shift < -5 or shift > 20:
                    warnings.append(f"Peak {i+1}: Unusual 1H chemical shift ({shift:.2f} ppm)")
            elif spectrum.nucleus == '13C':
                if shift < -20 or shift > 250:
                    warnings.append(f"Peak {i+1}: Unusual 13C chemical shift ({shift:.2f} ppm)")
        
        return warnings
    
    def export_to_nmr_format(self, spectrum: Spectrum, format_type: str = 'simple') -> str:
        """
        Export spectrum data in standard NMR format.
        
        Args:
            spectrum: Spectrum to export
            format_type: Export format ('simple', 'detailed')
            
        Returns:
            Formatted string with NMR data
        """
        if format_type == 'simple':
            lines = []
            lines.append(f"{spectrum.nucleus} NMR ({spectrum.field_strength} MHz):")
            
            for peak in spectrum.peaks:
                line = f"δ {peak.chemical_shift:.2f} ({peak.multiplicity}"
                if peak.integration and peak.integration != 1.0:
                    line += f", {peak.integration:.0f}H"
                if peak.coupling_constants:
                    j_values = ", ".join(f"J = {j:.1f} Hz" for j in peak.coupling_constants)
                    line += f", {j_values}"
                line += ")"
                lines.append(line)
            
            return "\n".join(lines)
        
        else:  # detailed format
            lines = []
            lines.append(f"=== {spectrum.nucleus} NMR Spectrum ===")
            lines.append(f"Field Strength: {spectrum.field_strength} MHz")
            lines.append(f"Number of Peaks: {len(spectrum.peaks)}")
            lines.append("")
            
            for i, peak in enumerate(spectrum.peaks, 1):
                lines.append(f"Peak {i}:")
                lines.append(f"  Chemical Shift: {peak.chemical_shift:.3f} ppm")
                lines.append(f"  Intensity: {peak.intensity:.2f}")
                lines.append(f"  Multiplicity: {peak.multiplicity}")
                lines.append(f"  Integration: {peak.integration:.1f}")
                if peak.coupling_constants:
                    lines.append(f"  Coupling Constants: {peak.coupling_constants} Hz")
                lines.append("")
            
            return "\n".join(lines)
