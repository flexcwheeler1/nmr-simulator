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
            field_strength=400.0
        )
        spectrum.title = f"1H NMR of {compound_name} (Demo)"
        
        # Add some demo peaks based on compound name
        name_lower = compound_name.lower()
        
        if "ethanol" in name_lower:
            # Ethanol: CH3CH2OH
            spectrum.add_peak(Peak(chemical_shift=1.25, intensity=3.0, multiplicity="t", coupling_constants=[7.0]))  # CH3
            spectrum.add_peak(Peak(chemical_shift=3.70, intensity=2.0, multiplicity="q", coupling_constants=[7.0]))  # CH2
            spectrum.add_peak(Peak(chemical_shift=2.61, intensity=1.0, multiplicity="s"))  # OH
            
        elif "methanol" in name_lower:
            # Methanol: CH3OH
            spectrum.add_peak(Peak(chemical_shift=3.34, intensity=3.0, multiplicity="s"))  # CH3
            spectrum.add_peak(Peak(chemical_shift=4.87, intensity=1.0, multiplicity="s"))  # OH
            
        elif "benzene" in name_lower:
            # Benzene: aromatic
            spectrum.add_peak(Peak(chemical_shift=7.37, intensity=6.0, multiplicity="s"))  # Aromatic H
            
        elif "toluene" in name_lower:
            # Toluene: CH3-benzene
            spectrum.add_peak(Peak(chemical_shift=2.35, intensity=3.0, multiplicity="s"))  # CH3
            spectrum.add_peak(Peak(chemical_shift=7.20, intensity=5.0, multiplicity="m"))  # Aromatic H
            
        elif "acetone" in name_lower:
            # Acetone: (CH3)2CO
            spectrum.add_peak(Peak(chemical_shift=2.17, intensity=6.0, multiplicity="s"))  # CH3
            
        elif "phenol" in name_lower:
            # Phenol
            spectrum.add_peak(Peak(chemical_shift=6.80, intensity=3.0, multiplicity="m"))  # Aromatic H
            spectrum.add_peak(Peak(chemical_shift=7.25, intensity=2.0, multiplicity="m"))  # Aromatic H
            spectrum.add_peak(Peak(chemical_shift=5.20, intensity=1.0, multiplicity="s"))  # OH
            
        elif "aniline" in name_lower:
            # Aniline
            spectrum.add_peak(Peak(chemical_shift=6.65, intensity=3.0, multiplicity="m"))  # Aromatic H
            spectrum.add_peak(Peak(chemical_shift=7.15, intensity=2.0, multiplicity="m"))  # Aromatic H
            spectrum.add_peak(Peak(chemical_shift=3.65, intensity=2.0, multiplicity="s"))  # NH2
            
        elif "chloroform" in name_lower:
            # Chloroform: CHCl3
            spectrum.add_peak(Peak(chemical_shift=7.26, intensity=1.0, multiplicity="s"))  # CHCl3
            
        elif "hexane" in name_lower or "alkane" in name_lower:
            # Alkane pattern
            spectrum.add_peak(Peak(chemical_shift=0.88, intensity=6.0, multiplicity="t", coupling_constants=[7.0]))  # CH3
            spectrum.add_peak(Peak(chemical_shift=1.30, intensity=8.0, multiplicity="m"))  # CH2
            
        elif "acid" in name_lower:
            # Carboxylic acid
            spectrum.add_peak(Peak(chemical_shift=11.5, intensity=1.0, multiplicity="s"))  # COOH
            spectrum.add_peak(Peak(chemical_shift=2.35, intensity=2.0, multiplicity="t"))  # CH2-COOH
            spectrum.add_peak(Peak(chemical_shift=1.15, intensity=3.0, multiplicity="t"))  # CH3
            
        else:
            # Generic aromatic/aliphatic mixture
            spectrum.add_peak(Peak(chemical_shift=7.2, intensity=2.0, multiplicity="m"))  # Aromatic
            spectrum.add_peak(Peak(chemical_shift=2.5, intensity=2.0, multiplicity="t"))  # CH2
            spectrum.add_peak(Peak(chemical_shift=1.2, intensity=3.0, multiplicity="t"))  # CH3
        
        return spectrum
    
    def _generate_demo_c13_spectrum(self, compound_name: str) -> Spectrum:
        """Generate a demo 13C NMR spectrum."""
        spectrum = Spectrum(
            nucleus="13C",
            field_strength=100.0
        )
        spectrum.title = f"13C NMR of {compound_name} (Demo)"
        
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
        output += f"Field Strength: {spectrum.field_strength} MHz\n\n"
        
        output += "Peak List:\n"
        output += "Chemical Shift (ppm) | Intensity | Multiplicity | Coupling (Hz)\n"
        output += "-" * 60 + "\n"
        
        for peak in spectrum.peaks:
            coupling_str = f"{peak.coupling_constants[0]:.1f}" if peak.coupling_constants else "N/A"
            output += f"{peak.chemical_shift:8.2f} | {peak.intensity:8.2f} | {peak.multiplicity:10s} | {coupling_str:>10s}\n"
        
        return output
