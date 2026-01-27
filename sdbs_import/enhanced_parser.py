"""
Enhanced SDBS Parser with Real Web Integration

Provides parsing functionality for SDBS data with both demo and real web scraping capabilities.
"""

import sys
import os
from typing import List, Dict, Optional, Tuple
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmr_simulator import Molecule, Spectrum, Peak
from nmr_simulator.molecule import Atom
from .enhanced_scraper import SDBSScraper


class EnhancedSDBSParser:
    """
    Enhanced parser for SDBS NMR data with real web integration.
    """
    
    def __init__(self):
        """
        Initialize the SDBS parser with real SDBS web integration.
        """
        self.scraper = SDBSScraper()
        
        # Multiplicity mapping
        self.multiplicity_map = {
            's': 'singlet',
            'd': 'doublet', 
            't': 'triplet',
            'q': 'quartet',
            'm': 'multiplet',
            'dd': 'doublet of doublets',
            'dt': 'doublet of triplets'
        }
    
    def search_compounds(self, compound_name: str, max_results: int = 10) -> List[Dict]:
        """
        Search for compounds in SDBS database.
        
        Args:
            compound_name: Name of the compound to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionaries with compound information
        """
        return self.scraper.search_compounds(compound_name, max_results)
    
    def retrieve_by_id(self, sdbs_id: str) -> Tuple[Optional[Molecule], List[Spectrum]]:
        """
        Retrieve a specific SDBS entry by database ID.
        
        Args:
            sdbs_id: SDBS database ID (e.g., 'HSP-49-06001')
            
        Returns:
            Tuple of (Molecule, List of Spectrum objects) or (None, [])
        """
        try:
            # Try to use the compound ID to get NMR data
            return self.parse_compound_from_sdbs(sdbs_id, f"SDBS Entry {sdbs_id}")
            
        except Exception as e:
            print(f"Error retrieving SDBS ID {sdbs_id}: {e}")
            return None, []
    
    def parse_compound_from_sdbs(self, compound_id: str, compound_name: str = "") -> Tuple[Molecule, List[Spectrum]]:
        """
        Parse compound data from SDBS and create Molecule and Spectrum objects.
        
        Args:
            compound_id: SDBS compound identifier
            compound_name: Name of the compound (optional)
            
        Returns:
            Tuple of (Molecule, List of Spectrum objects)
        """
        # Get NMR data from SDBS
        nmr_data = self.scraper.get_nmr_data(compound_id)
        
        # Create molecule (simplified - in reality would parse full structure)
        molecule_name = compound_name or f"Compound_{compound_id}"
        molecule = Molecule(identifier=molecule_name, molecule_type="name")
        molecule.name = molecule_name
        
        # Add dummy atoms (in real implementation, would parse structure)
        from nmr_simulator.molecule import Atom
        molecule.add_atom(Atom(element="C", position=1))
        molecule.add_atom(Atom(element="H", position=1))
        
        # Create spectra from the data
        spectra = []
        
        # Process 1H NMR data
        if "1H" in nmr_data and nmr_data["1H"]:
            h_spectrum = self._create_spectrum_from_data(nmr_data["1H"], "1H", molecule_name)
            spectra.append(h_spectrum)
        
        # Process 13C NMR data  
        if "13C" in nmr_data and nmr_data["13C"]:
            c_spectrum = self._create_spectrum_from_data(nmr_data["13C"], "13C", molecule_name)
            spectra.append(c_spectrum)
        
        return molecule, spectra
    
    def _create_spectrum_from_data(self, peak_data: List[Dict], nucleus: str, compound_name: str = "") -> Spectrum:
        """
        Create a Spectrum object from parsed peak data.
        
        Args:
            peak_data: List of peak dictionaries
            nucleus: Nucleus type ('1H' or '13C')
            compound_name: Name of the compound
            
        Returns:
            Spectrum object
        """
        # Set appropriate PPM range based on nucleus
        if nucleus == "1H":
            ppm_range = (12.0, 0.0)
        elif nucleus == "13C":
            ppm_range = (220.0, 0.0)
        else:
            ppm_range = (15.0, 0.0)
        
        spectrum = Spectrum(
            nucleus=nucleus,
            field_strength=400.0  # Default field strength
        )
        
        # Set PPM range after creation
        spectrum.ppm_range = ppm_range
        
        # Set title
        spectrum.title = f"{nucleus} NMR Spectrum - {compound_name}" if compound_name else f"{nucleus} NMR Spectrum"
        
        # Add peaks to spectrum
        for peak_info in peak_data:
            chemical_shift = peak_info.get("shift", 0.0)
            multiplicity = peak_info.get("multiplicity", "s")
            integration = peak_info.get("integration", 1.0)
            coupling_constants = peak_info.get("coupling", [])
            is_solvent = peak_info.get("is_solvent", False)
            
            # Create peak with realistic intensity and width
            intensity = float(integration) * 0.8 + 0.2  # Normalize intensity
            width = 0.02 if nucleus == "1H" else 0.5  # Typical peak widths
            
            peak = Peak(
                chemical_shift=float(chemical_shift),
                intensity=intensity,
                width=width,
                multiplicity=multiplicity,
                integration=float(integration),
                coupling_constants=coupling_constants if coupling_constants else [],
                is_solvent=is_solvent
            )
            
            spectrum.add_peak(peak)
        
        return spectrum
    
    def create_demo_molecule(self, compound_name: str, solvent: str = "CDCl3") -> Tuple[Molecule, List[Spectrum]]:
        """
        Create demo molecule and spectra for testing with solvent signals.
        
        Args:
            compound_name: Name of the compound
            solvent: NMR solvent (CDCl3, DMSO-d6, D2O, etc.)
            
        Returns:
            Tuple of (Molecule, List of Spectrum objects)
        """
        # Define solvent signals for common NMR solvents
        solvent_signals = {
            "CDCl3": {
                "1H": [{"shift": 7.26, "multiplicity": "s", "integration": 0.2, "coupling": [], "is_solvent": True}],
                "13C": [{"shift": 77.16, "multiplicity": "t", "integration": 0.3, "coupling": [32.0], "is_solvent": True}]
            },
            "DMSO-d6": {
                "1H": [{"shift": 2.50, "multiplicity": "quint", "integration": 0.1, "coupling": [1.9], "is_solvent": True}],
                "13C": [{"shift": 39.52, "multiplicity": "sept", "integration": 0.2, "coupling": [1.3], "is_solvent": True}]
            },
            "D2O": {
                "1H": [{"shift": 4.79, "multiplicity": "s", "integration": 0.5, "coupling": [], "is_solvent": True}],
                "13C": []
            },
            "CD3OD": {
                "1H": [
                    {"shift": 3.31, "multiplicity": "quint", "integration": 0.1, "coupling": [1.1], "is_solvent": True},
                    {"shift": 4.87, "multiplicity": "s", "integration": 0.3, "coupling": [], "is_solvent": True}  # HOD
                ],
                "13C": [{"shift": 49.00, "multiplicity": "sept", "integration": 0.2, "coupling": [21.4], "is_solvent": True}]
            }
        }
        
        demo_data = {
            "ethanol": {
                "1H": [
                    {"shift": 1.25, "multiplicity": "t", "integration": 3, "coupling": [7.0]},   # CH3
                    {"shift": 3.70, "multiplicity": "q", "integration": 2, "coupling": [7.0]},   # OCH2
                    {"shift": 2.61, "multiplicity": "s", "integration": 1, "coupling": []}       # OH (broad)
                ],
                "13C": [
                    {"shift": 18.1, "multiplicity": "s", "integration": 1},  # CH3
                    {"shift": 58.4, "multiplicity": "s", "integration": 1}   # OCH2
                ]
            },
            "acetone": {
                "1H": [
                    {"shift": 2.17, "multiplicity": "s", "integration": 6, "coupling": []}
                ],
                "13C": [
                    {"shift": 29.8, "multiplicity": "s", "integration": 2},
                    {"shift": 207.1, "multiplicity": "s", "integration": 1}
                ]
            },
            "benzene": {
                "1H": [
                    {"shift": 7.36, "multiplicity": "s", "integration": 6, "coupling": []}
                ],
                "13C": [
                    {"shift": 128.4, "multiplicity": "s", "integration": 6}
                ]
            },
            "methanol": {
                "1H": [
                    {"shift": 3.34, "multiplicity": "s", "integration": 3, "coupling": []},
                    {"shift": 4.87, "multiplicity": "s", "integration": 1, "coupling": []}
                ],
                "13C": [
                    {"shift": 49.0, "multiplicity": "s", "integration": 1}
                ]
            },
            "toluene": {
                "1H": [
                    {"shift": 2.34, "multiplicity": "s", "integration": 3, "coupling": []},
                    {"shift": 7.17, "multiplicity": "m", "integration": 2, "coupling": []},
                    {"shift": 7.26, "multiplicity": "m", "integration": 3, "coupling": []}
                ],
                "13C": [
                    {"shift": 21.4, "multiplicity": "s", "integration": 1},
                    {"shift": 125.3, "multiplicity": "s", "integration": 1},
                    {"shift": 128.1, "multiplicity": "s", "integration": 2},
                    {"shift": 129.2, "multiplicity": "s", "integration": 2},
                    {"shift": 137.7, "multiplicity": "s", "integration": 1}
                ]
            },
            "indole": {
                "1H": [
                    {"shift": 6.52, "multiplicity": "m", "integration": 1, "coupling": []},  # H-3
                    {"shift": 7.08, "multiplicity": "t", "integration": 1, "coupling": [7.8]},  # H-5
                    {"shift": 7.16, "multiplicity": "t", "integration": 1, "coupling": [7.8]},  # H-6
                    {"shift": 7.21, "multiplicity": "d", "integration": 1, "coupling": [3.0]},  # H-2
                    {"shift": 7.38, "multiplicity": "d", "integration": 1, "coupling": [8.1]},  # H-7
                    {"shift": 7.64, "multiplicity": "d", "integration": 1, "coupling": [7.8]},  # H-4
                    {"shift": 8.14, "multiplicity": "s", "integration": 1, "coupling": []}   # NH
                ],
                "13C": [
                    {"shift": 102.1, "multiplicity": "s", "integration": 1},  # C-3
                    {"shift": 111.2, "multiplicity": "s", "integration": 1},  # C-7
                    {"shift": 119.7, "multiplicity": "s", "integration": 1},  # C-4
                    {"shift": 120.9, "multiplicity": "s", "integration": 1},  # C-5
                    {"shift": 122.1, "multiplicity": "s", "integration": 1},  # C-6
                    {"shift": 124.3, "multiplicity": "s", "integration": 1},  # C-2
                    {"shift": 127.9, "multiplicity": "s", "integration": 1},  # C-3a
                    {"shift": 136.1, "multiplicity": "s", "integration": 1}   # C-7a
                ]
            },
            "pyridine": {
                "1H": [
                    {"shift": 7.23, "multiplicity": "t", "integration": 2, "coupling": [7.7]}, # H-3,5
                    {"shift": 7.67, "multiplicity": "t", "integration": 1, "coupling": [7.7]}, # H-4
                    {"shift": 8.60, "multiplicity": "d", "integration": 2, "coupling": [4.8]}  # H-2,6
                ],
                "13C": [
                    {"shift": 123.8, "multiplicity": "s", "integration": 2}, # C-3,5
                    {"shift": 135.9, "multiplicity": "s", "integration": 1}, # C-4
                    {"shift": 149.9, "multiplicity": "s", "integration": 2}  # C-2,6
                ]
            },
            "phenol": {
                "1H": [
                    {"shift": 4.73, "multiplicity": "s", "integration": 1, "coupling": []},   # OH
                    {"shift": 6.78, "multiplicity": "d", "integration": 2, "coupling": [8.8]}, # H-2,6
                    {"shift": 6.93, "multiplicity": "t", "integration": 1, "coupling": [7.3]}, # H-4
                    {"shift": 7.20, "multiplicity": "t", "integration": 2, "coupling": [7.8]}  # H-3,5
                ],
                "13C": [
                    {"shift": 115.6, "multiplicity": "s", "integration": 2}, # C-2,6
                    {"shift": 120.8, "multiplicity": "s", "integration": 1}, # C-4
                    {"shift": 129.5, "multiplicity": "s", "integration": 2}, # C-3,5
                    {"shift": 155.3, "multiplicity": "s", "integration": 1}  # C-1
                ]
            }
        }
        
        # Get data for the compound
        compound_key = compound_name.lower().strip()
        nmr_data = demo_data.get(compound_key, demo_data["ethanol"])  # Default to ethanol
        
        # Create molecule
        molecule = Molecule(identifier=compound_name, molecule_type="name")
        molecule.name = compound_name
        
        # Add some basic atoms (simplified for demo purposes)
        from nmr_simulator.molecule import Atom
        molecule.add_atom(Atom(element="C", position=1))
        molecule.add_atom(Atom(element="H", position=1))
        
        # Create spectra
        spectra = []
        
        if "1H" in nmr_data:
            # Get compound peaks
            compound_peaks = nmr_data["1H"].copy()
            
            # Add solvent signals if available
            if solvent in solvent_signals and "1H" in solvent_signals[solvent]:
                compound_peaks.extend(solvent_signals[solvent]["1H"])
            
            h_spectrum = self._create_spectrum_from_data(compound_peaks, "1H", compound_name)
            h_spectrum.solvent = solvent
            spectra.append(h_spectrum)
        
        if "13C" in nmr_data:
            # Get compound peaks
            compound_peaks = nmr_data["13C"].copy()
            
            # Add solvent signals if available
            if solvent in solvent_signals and "13C" in solvent_signals[solvent]:
                compound_peaks.extend(solvent_signals[solvent]["13C"])
            
            c_spectrum = self._create_spectrum_from_data(compound_peaks, "13C", compound_name)
            c_spectrum.solvent = solvent
            spectra.append(c_spectrum)
        
        return molecule, spectra
    
    def export_to_nmr_format(self, spectrum: Spectrum, format_type: str = "simple") -> str:
        """
        Export spectrum data to standard NMR format.
        
        Args:
            spectrum: Spectrum object to export
            format_type: Type of format ('simple', 'detailed', 'jcamp')
            
        Returns:
            Formatted string representation
        """
        if format_type == "simple":
            return self._export_simple_format(spectrum)
        elif format_type == "detailed":
            return self._export_detailed_format(spectrum)
        elif format_type == "jcamp":
            return self._export_jcamp_format(spectrum)
        else:
            return self._export_simple_format(spectrum)
    
    def _export_simple_format(self, spectrum: Spectrum) -> str:
        """Export in simple text format."""
        output = f"{spectrum.nucleus} NMR ({spectrum.field_strength} MHz):\n"
        
        for i, peak in enumerate(spectrum.peaks, 1):
            mult_text = self.multiplicity_map.get(peak.multiplicity, peak.multiplicity)
            
            if peak.coupling_constants:
                coupling_text = f", J = {', '.join(f'{j:.1f}' for j in peak.coupling_constants)} Hz"
            else:
                coupling_text = ""
            
            output += f"δ {peak.chemical_shift:.2f} ({mult_text}, {peak.integration:.0f}H{coupling_text})\n"
        
        return output
    
    def _export_detailed_format(self, spectrum: Spectrum) -> str:
        """Export in detailed format with additional information."""
        output = f"{spectrum.nucleus} NMR Spectrum\n"
        output += "=" * 40 + "\n"
        output += f"Field Strength: {spectrum.field_strength} MHz\n"
        output += f"Number of Peaks: {len(spectrum.peaks)}\n"
        output += f"PPM Range: {spectrum.ppm_range[0]:.1f} - {spectrum.ppm_range[1]:.1f}\n\n"
        output += "Peak Analysis:\n"
        output += "-" * 40 + "\n"
        
        for i, peak in enumerate(spectrum.peaks, 1):
            mult_text = self.multiplicity_map.get(peak.multiplicity, peak.multiplicity)
            
            output += f"Peak {i}:\n"
            output += f"  Chemical Shift: {peak.chemical_shift:.2f} ppm\n"
            output += f"  Multiplicity: {mult_text} ({peak.multiplicity})\n"
            output += f"  Integration: {peak.integration:.1f}H\n"
            output += f"  Intensity: {peak.intensity:.3f}\n"
            output += f"  Width: {peak.width:.3f} ppm\n"
            
            if peak.coupling_constants:
                output += f"  Coupling Constants: {', '.join(f'{j:.1f} Hz' for j in peak.coupling_constants)}\n"
            
            output += "\n"
        
        return output
    
    def _export_jcamp_format(self, spectrum: Spectrum) -> str:
        """Export in simplified JCAMP-DX format."""
        output = "##TITLE= NMR Spectrum\n"
        output += "##JCAMP-DX= 5.00\n"
        output += f"##DATA TYPE= {spectrum.nucleus} NMR SPECTRUM\n"
        output += f"##OBSERVE FREQUENCY= {spectrum.field_strength}\n"
        output += "##OBSERVE NUCLEUS= ^1H\n" if spectrum.nucleus == "1H" else "##OBSERVE NUCLEUS= ^13C\n"
        output += "##UNITS= PPM\n"
        output += "##PEAK TABLE= (XY..XY)\n"
        
        for peak in spectrum.peaks:
            output += f"{peak.chemical_shift:.3f},{peak.intensity:.3f}\n"
        
        output += "##END=\n"
        return output
    
    def test_connection(self) -> bool:
        """Test connection to SDBS website."""
        return self.scraper.test_connection()


# For backwards compatibility, create an alias
SDBSParser = EnhancedSDBSParser
