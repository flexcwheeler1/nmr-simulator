"""
SDBS Parser module for parsing NMR data from the SDBS database.
"""

from typing import List, Dict, Any, Tuple
import random
from nmr_simulator import Molecule, Spectrum, Peak


class SDBSParser:
    """Parser for SDBS (Spectral Database for Organic Compounds) data."""
    
    def __init__(self):
        """Initialize the SDBS parser."""
        pass
    
    def create_demo_molecule(self, compound_name: str) -> Tuple[Molecule, List[Spectrum]]:
        """Create a demo molecule with synthetic NMR data."""
        # Create a demo molecule
        molecule = Molecule(identifier=compound_name, molecule_type="name")
        
        # Generate demo spectra
        spectra = []
        
        # Generate 1H NMR spectrum
        h1_spectrum = self._generate_demo_h1_spectrum(compound_name)
        spectra.append(h1_spectrum)
        
        # Generate 13C NMR spectrum
        c13_spectrum = self._generate_demo_c13_spectrum(compound_name)
        spectra.append(c13_spectrum)
        
        return molecule, spectra
    
    def _generate_demo_h1_spectrum(self, compound_name: str) -> Spectrum:
        """Generate a demo 1H NMR spectrum."""
        spectrum = Spectrum(
            nucleus="1H",
            frequency=400.0,
            title=f"1H NMR of {compound_name} (Demo)"
        )
        
        # Add some demo peaks based on compound name
        if "ethanol" in compound_name.lower():
            # Ethanol peaks: triplet around 1.2 ppm (CH3), quartet around 3.7 ppm (CH2), singlet around 2.5 ppm (OH)
            spectrum.add_peak(Peak(chemical_shift=1.2, intensity=3.0, multiplicity="t", coupling=7.0))
            spectrum.add_peak(Peak(chemical_shift=3.7, intensity=2.0, multiplicity="q", coupling=7.0))
            spectrum.add_peak(Peak(chemical_shift=2.5, intensity=1.0, multiplicity="s"))
        elif "methanol" in compound_name.lower():
            # Methanol peaks
            spectrum.add_peak(Peak(chemical_shift=3.3, intensity=3.0, multiplicity="s"))
            spectrum.add_peak(Peak(chemical_shift=4.8, intensity=1.0, multiplicity="s"))
        else:
            # Generic aromatic compound peaks
            for i in range(3):
                shift = 7.0 + random.uniform(-1.0, 1.0)
                intensity = random.uniform(0.5, 2.0)
                spectrum.add_peak(Peak(chemical_shift=shift, intensity=intensity, multiplicity="m"))
        
        return spectrum
    
    def _generate_demo_c13_spectrum(self, compound_name: str) -> Spectrum:
        """Generate a demo 13C NMR spectrum."""
        spectrum = Spectrum(
            nucleus="13C",
            frequency=100.0,
            title=f"13C NMR of {compound_name} (Demo)"
        )
        
        # Add some demo peaks
        if "ethanol" in compound_name.lower():
            spectrum.add_peak(Peak(chemical_shift=18.0, intensity=1.0, multiplicity="q"))
            spectrum.add_peak(Peak(chemical_shift=58.0, intensity=1.0, multiplicity="t"))
        else:
            # Generic peaks
            for i in range(2, 5):
                shift = 20.0 + i * 30.0 + random.uniform(-10.0, 10.0)
                intensity = random.uniform(0.5, 1.0)
                spectrum.add_peak(Peak(chemical_shift=shift, intensity=intensity, multiplicity="s"))
        
        return spectrum
    
    def export_to_nmr_format(self, spectrum: Spectrum, format_type: str = "detailed") -> str:
        """Export spectrum data to NMR format."""
        output = f"Spectrum: {spectrum.title}\n"
        output += f"Nucleus: {spectrum.nucleus}\n"
        output += f"Frequency: {spectrum.frequency} MHz\n\n"
        
        output += "Peak List:\n"
        output += "Chemical Shift (ppm) | Intensity | Multiplicity | Coupling (Hz)\n"
        output += "-" * 60 + "\n"
        
        for peak in spectrum.peaks:
            coupling_str = f"{peak.coupling:.1f}" if peak.coupling else "N/A"
            output += f"{peak.chemical_shift:8.2f} | {peak.intensity:8.2f} | {peak.multiplicity:10s} | {coupling_str:>10s}\n"
        
        return output
