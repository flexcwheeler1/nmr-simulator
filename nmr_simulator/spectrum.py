"""
NMR Spectrum data structures and utilities.

This module provides classes for representing and manipulating NMR spectra data.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field


@dataclass
class Peak:
    """Represents a single peak in an NMR spectrum."""
    chemical_shift: float  # ppm
    intensity: float  # relative intensity
    width: float = 0.01  # peak width in ppm
    multiplicity: str = 's'  # s, d, t, q, m, etc.
    integration: float = 1.0  # relative integration
    coupling_constants: List[float] = field(default_factory=list)  # J values in Hz
    is_solvent: bool = False  # Whether this is a solvent peak


class Spectrum:
    """
    Represents an NMR spectrum with peaks and measurement parameters.
    """
    
    def __init__(self, nucleus: str = '1H', field_strength: float = 400.0):
        """
        Initialize an NMR spectrum.
        
        Args:
            nucleus: Nucleus type ('1H', '13C', etc.)
            field_strength: Magnetic field strength in MHz
        """
        self.nucleus = nucleus
        self.field_strength = field_strength  # MHz
        self.peaks: List[Peak] = []
        self.ppm_range: Tuple[float, float] = (0.0, 12.0)  # Default range
        self.data_points: Optional[np.ndarray] = None
        self.ppm_axis: Optional[np.ndarray] = None
        self.title: str = f"{nucleus} NMR Spectrum"
        
        # Set default ranges based on nucleus
        if nucleus == '1H':
            self.ppm_range = (0.0, 12.0)
        elif nucleus == '13C':
            self.ppm_range = (0.0, 220.0)
    
    @property
    def spectrum_data(self) -> Optional[np.ndarray]:
        """Alias for data_points to maintain compatibility."""
        return self.data_points
    
    @spectrum_data.setter
    def spectrum_data(self, value: Optional[np.ndarray]) -> None:
        """Setter for spectrum_data property."""
        self.data_points = value
    
    def add_peak(self, peak: Peak) -> None:
        """Add a peak to the spectrum."""
        self.peaks.append(peak)
    
    def add_peak_simple(self, chemical_shift: float, intensity: float = 1.0, 
                       width: float = 0.01, multiplicity: str = 's') -> None:
        """
        Add a peak with simple parameters.
        
        Args:
            chemical_shift: Chemical shift in ppm
            intensity: Peak intensity (relative)
            width: Peak width in ppm
            multiplicity: Peak multiplicity
        """
        peak = Peak(
            chemical_shift=chemical_shift,
            intensity=intensity,
            width=width,
            multiplicity=multiplicity
        )
        self.add_peak(peak)
    
    def generate_spectrum_data(self, resolution: int = 8192, noise_level: float = 0.0) -> None:
        """
        Generate the full spectrum data from individual peaks.
        
        Args:
            resolution: Number of data points in the spectrum (default 8192, can go up to 65536)
            noise_level: Noise level as fraction (0.0 = no noise, 0.1 = 10% noise)
        """
        # Create ppm axis in NMR convention: high field -> low field (descending ppm)
        # Use ppm_range[1] down to ppm_range[0] so axis[0] is highest ppm
        self.ppm_axis = np.linspace(self.ppm_range[1], self.ppm_range[0], resolution)
        self.data_points = np.zeros(resolution)
        
        # Add each peak to the spectrum
        for peak in self.peaks:
            self._add_peak_to_spectrum(peak)
        
        # Add noise if requested
        if noise_level > 0.0:
            self._add_noise(noise_level)
    
    def _add_peak_to_spectrum(self, peak: Peak) -> None:
        """Add a single peak to the spectrum data."""
        if self.ppm_axis is None or self.data_points is None:
            return
        
        if peak.multiplicity == 's':  # Singlet
            self._add_lorentzian(peak.chemical_shift, peak.intensity, peak.width)
        elif peak.multiplicity == 'd':  # Doublet
            if peak.coupling_constants and len(peak.coupling_constants) > 0:
                j = peak.coupling_constants[0]
                j_ppm = j / self.field_strength  # Convert Hz to ppm
                self._add_lorentzian(peak.chemical_shift - j_ppm/2, peak.intensity/2, peak.width)
                self._add_lorentzian(peak.chemical_shift + j_ppm/2, peak.intensity/2, peak.width)
            else:
                # Default doublet with 7 Hz coupling
                j_ppm = 7.0 / self.field_strength
                self._add_lorentzian(peak.chemical_shift - j_ppm/2, peak.intensity/2, peak.width)
                self._add_lorentzian(peak.chemical_shift + j_ppm/2, peak.intensity/2, peak.width)
        elif peak.multiplicity == 't':  # Triplet
            if peak.coupling_constants and len(peak.coupling_constants) > 0:
                j = peak.coupling_constants[0]
                j_ppm = j / self.field_strength
                self._add_lorentzian(peak.chemical_shift - j_ppm, peak.intensity/4, peak.width)
                self._add_lorentzian(peak.chemical_shift, peak.intensity/2, peak.width)
                self._add_lorentzian(peak.chemical_shift + j_ppm, peak.intensity/4, peak.width)
            else:
                # Default triplet with 7 Hz coupling
                j_ppm = 7.0 / self.field_strength
                self._add_lorentzian(peak.chemical_shift - j_ppm, peak.intensity/4, peak.width)
                self._add_lorentzian(peak.chemical_shift, peak.intensity/2, peak.width)
                self._add_lorentzian(peak.chemical_shift + j_ppm, peak.intensity/4, peak.width)
        elif peak.multiplicity == 'q':  # Quartet
            if peak.coupling_constants and len(peak.coupling_constants) > 0:
                j = peak.coupling_constants[0]
                j_ppm = j / self.field_strength
                # 1:3:3:1 pattern
                self._add_lorentzian(peak.chemical_shift - 3*j_ppm/2, peak.intensity/8, peak.width)
                self._add_lorentzian(peak.chemical_shift - j_ppm/2, peak.intensity*3/8, peak.width)
                self._add_lorentzian(peak.chemical_shift + j_ppm/2, peak.intensity*3/8, peak.width)
                self._add_lorentzian(peak.chemical_shift + 3*j_ppm/2, peak.intensity/8, peak.width)
            else:
                j_ppm = 7.0 / self.field_strength
                self._add_lorentzian(peak.chemical_shift - 3*j_ppm/2, peak.intensity/8, peak.width)
                self._add_lorentzian(peak.chemical_shift - j_ppm/2, peak.intensity*3/8, peak.width)
                self._add_lorentzian(peak.chemical_shift + j_ppm/2, peak.intensity*3/8, peak.width)
                self._add_lorentzian(peak.chemical_shift + 3*j_ppm/2, peak.intensity/8, peak.width)
        elif peak.multiplicity == 'dd':  # Doublet of doublets
            if peak.coupling_constants and len(peak.coupling_constants) >= 2:
                j1, j2 = peak.coupling_constants[0], peak.coupling_constants[1]
                j1_ppm, j2_ppm = j1 / self.field_strength, j2 / self.field_strength
                # 4 peaks for dd
                self._add_lorentzian(peak.chemical_shift - j1_ppm/2 - j2_ppm/2, peak.intensity/4, peak.width)
                self._add_lorentzian(peak.chemical_shift - j1_ppm/2 + j2_ppm/2, peak.intensity/4, peak.width)
                self._add_lorentzian(peak.chemical_shift + j1_ppm/2 - j2_ppm/2, peak.intensity/4, peak.width)
                self._add_lorentzian(peak.chemical_shift + j1_ppm/2 + j2_ppm/2, peak.intensity/4, peak.width)
            else:
                # Default dd with 7 and 3 Hz
                j1_ppm, j2_ppm = 7.0 / self.field_strength, 3.0 / self.field_strength
                self._add_lorentzian(peak.chemical_shift - j1_ppm/2 - j2_ppm/2, peak.intensity/4, peak.width)
                self._add_lorentzian(peak.chemical_shift - j1_ppm/2 + j2_ppm/2, peak.intensity/4, peak.width)
                self._add_lorentzian(peak.chemical_shift + j1_ppm/2 - j2_ppm/2, peak.intensity/4, peak.width)
                self._add_lorentzian(peak.chemical_shift + j1_ppm/2 + j2_ppm/2, peak.intensity/4, peak.width)
        elif peak.multiplicity == 'dt':  # Doublet of triplets
            if peak.coupling_constants and len(peak.coupling_constants) >= 2:
                j1, j2 = peak.coupling_constants[0], peak.coupling_constants[1]
                j1_ppm, j2_ppm = j1 / self.field_strength, j2 / self.field_strength
                # 6 peaks for dt (doublet first, then triplet splitting)
                for d_offset in [-j1_ppm/2, j1_ppm/2]:
                    self._add_lorentzian(peak.chemical_shift + d_offset - j2_ppm, peak.intensity/12, peak.width)
                    self._add_lorentzian(peak.chemical_shift + d_offset, peak.intensity/6, peak.width)
                    self._add_lorentzian(peak.chemical_shift + d_offset + j2_ppm, peak.intensity/12, peak.width)
            else:
                # Default dt with 7 and 3 Hz
                j1_ppm, j2_ppm = 7.0 / self.field_strength, 3.0 / self.field_strength
                for d_offset in [-j1_ppm/2, j1_ppm/2]:
                    self._add_lorentzian(peak.chemical_shift + d_offset - j2_ppm, peak.intensity/12, peak.width)
                    self._add_lorentzian(peak.chemical_shift + d_offset, peak.intensity/6, peak.width)
                    self._add_lorentzian(peak.chemical_shift + d_offset + j2_ppm, peak.intensity/12, peak.width)
        else:  # Default to singlet for other multiplicities (m, etc.)
            self._add_lorentzian(peak.chemical_shift, peak.intensity, peak.width)
    
    def _add_lorentzian(self, center: float, intensity: float, width: float) -> None:
        """Add a Lorentzian peak shape to the spectrum."""
        if self.ppm_axis is None or self.data_points is None:
            return
        
        # Lorentzian line shape
        gamma = width / 2
        lorentzian = intensity * (gamma**2) / ((self.ppm_axis - center)**2 + gamma**2)
        self.data_points += lorentzian
    
    def _add_noise(self, noise_level: float) -> None:
        """Add realistic FID-derived noise to the spectrum."""
        if self.data_points is None:
            return
        
        # Get the maximum intensity for scaling noise
        max_intensity = np.max(self.data_points)
        
        # Generate Gaussian noise that fluctuates around zero (realistic FID noise)
        # This noise can be both positive and negative
        noise = np.random.normal(0, max_intensity * noise_level, len(self.data_points))
        
        # Add noise to the spectrum (no constraint to positive values)
        self.data_points += noise
    
    def plot_spectrum(self, ax: Optional[plt.Axes] = None, **kwargs) -> plt.Axes:
        """
        Plot the NMR spectrum.
        
        Args:
            ax: Matplotlib axes to plot on (creates new if None)
            **kwargs: Additional plotting arguments
            
        Returns:
            Matplotlib axes object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 6))
        
        if self.data_points is None or self.ppm_axis is None:
            self.generate_spectrum_data()
        
        # Plot the spectrum (inverted x-axis for NMR convention)
        ax.plot(self.ppm_axis, self.data_points, **kwargs)
        ax.set_xlim(self.ppm_range[1], self.ppm_range[0])  # Inverted x-axis
        ax.set_xlabel('Chemical Shift (ppm)')
        ax.set_ylabel('Intensity')
        ax.set_title(self.title)
        ax.grid(True, alpha=0.3)
        
        # Add peak labels
        for peak in self.peaks:
            if peak.intensity > 0.1:  # Only label significant peaks
                ax.annotate(f'{peak.chemical_shift:.2f}', 
                           xy=(peak.chemical_shift, peak.intensity),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.7)
        
        return ax
    
    def get_peak_list(self) -> List[Dict]:
        """
        Get a list of peaks with their properties.
        
        Returns:
            List of dictionaries containing peak information
        """
        peak_list = []
        for i, peak in enumerate(self.peaks):
            peak_dict = {
                'peak_id': i + 1,
                'chemical_shift': peak.chemical_shift,
                'intensity': peak.intensity,
                'width': peak.width,
                'multiplicity': peak.multiplicity,
                'integration': peak.integration
            }
            if peak.coupling_constants:
                peak_dict['coupling_constants'] = peak.coupling_constants
            peak_list.append(peak_dict)
        return peak_list
    
    def export_data(self, filename: str, format: str = 'csv') -> None:
        """
        Export spectrum data to file.
        
        Args:
            filename: Output filename
            format: Export format ('csv', 'txt')
        """
        if self.data_points is None or self.ppm_axis is None:
            self.generate_spectrum_data()
        
        if format.lower() == 'csv':
            np.savetxt(filename, np.column_stack([self.ppm_axis, self.data_points]),
                      delimiter=',', header='Chemical_Shift_ppm,Intensity')
        elif format.lower() == 'txt':
            np.savetxt(filename, np.column_stack([self.ppm_axis, self.data_points]),
                      delimiter='\t', header='Chemical_Shift_ppm\tIntensity')
    
    def clear_peaks(self) -> None:
        """Remove all peaks from the spectrum."""
        self.peaks.clear()
        self.data_points = None
        self.ppm_axis = None
    
    def __str__(self) -> str:
        """String representation of the spectrum."""
        return f"{self.nucleus} NMR Spectrum ({self.field_strength} MHz) - {len(self.peaks)} peaks"
    
    def __repr__(self) -> str:
        """Detailed representation of the spectrum."""
        return f"Spectrum(nucleus='{self.nucleus}', field_strength={self.field_strength}, peaks={len(self.peaks)})"
