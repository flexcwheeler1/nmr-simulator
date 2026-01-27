#!/usr/bin/env python3
"""
Non-Destructive Peak Grouper for NMR Spectra

This module groups peaks visually without replacing original data.
All individual peaks are preserved with added grouping metadata.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class PeakGroup:
    """Represents a group of peaks with shared assignment and integration."""
    group_id: int
    assignment: str  # A, B, C, etc.
    center_shift: float
    integration: int
    multiplicity: str
    coupling_constants: List[float]
    peak_indices: List[int]  # Indices of original peaks in this group
    
class NonDestructiveGrouper:
    """Groups peaks while preserving all original data."""
    
    def __init__(self):
        self.groups: List[PeakGroup] = []
        self.next_assignment = ord('A')
    
    def group_peaks_by_proximity(self, peaks: List[Dict], 
                                tolerance_ppm: float = 0.1) -> Tuple[List[Dict], List[PeakGroup]]:
        """
        Group peaks by chemical shift proximity while preserving all original peaks.
        
        Args:
            peaks: List of original peak dictionaries
            tolerance_ppm: Maximum distance between peaks in the same group
            
        Returns:
            Tuple of (annotated_peaks, groups) where annotated_peaks have group metadata
        """
        if not peaks:
            return [], []
        
        # Sort peaks by chemical shift
        sorted_peaks = sorted(enumerate(peaks), key=lambda x: x[1].get('shift', 0))
        
        # Create a copy of peaks with group annotations
        annotated_peaks = [peak.copy() for peak in peaks]
        groups = []
        
        # Group peaks by proximity
        current_group_indices = []
        current_group_shifts = []
        group_id = 0
        
        for i, (original_idx, peak) in enumerate(sorted_peaks):
            shift = peak.get('shift', 0)
            
            # Check if this peak belongs to current group
            if (current_group_shifts and 
                abs(shift - current_group_shifts[-1]) > tolerance_ppm):
                # Start new group
                if current_group_indices:
                    group = self._create_group(group_id, current_group_indices, 
                                             current_group_shifts, peaks)
                    groups.append(group)
                    self._annotate_peaks_in_group(annotated_peaks, group)
                    group_id += 1
                
                current_group_indices = []
                current_group_shifts = []
            
            # Add peak to current group
            current_group_indices.append(original_idx)
            current_group_shifts.append(shift)
        
        # Handle last group
        if current_group_indices:
            group = self._create_group(group_id, current_group_indices, 
                                     current_group_shifts, peaks)
            groups.append(group)
            self._annotate_peaks_in_group(annotated_peaks, group)
        
        return annotated_peaks, groups
    
    def _create_group(self, group_id: int, peak_indices: List[int], 
                     shifts: List[float], original_peaks: List[Dict]) -> PeakGroup:
        """Create a PeakGroup from a set of peak indices."""
        # Calculate group properties
        center_shift = (min(shifts) + max(shifts)) / 2  # Geometric center
        
        # Get intensities for this group
        intensities = [original_peaks[idx].get('intensity', 100) for idx in peak_indices]
        total_intensity = sum(intensities)
        
        # Estimate integration (rough estimate based on intensity)
        integration = max(1, round(total_intensity / 500))  # Adjust scaling as needed
        
        # Determine multiplicity based on number of peaks
        multiplicity, coupling = self._analyze_multiplicity(shifts, intensities)
        
        # Generate assignment letter
        assignment = chr(self.next_assignment)
        self.next_assignment += 1
        
        return PeakGroup(
            group_id=group_id,
            assignment=assignment,
            center_shift=center_shift,
            integration=integration,
            multiplicity=multiplicity,
            coupling_constants=coupling,
            peak_indices=peak_indices
        )
    
    def _analyze_multiplicity(self, shifts: List[float], intensities: List[float]) -> Tuple[str, List[float]]:
        """Analyze multiplicity pattern for a group of peaks."""
        n_peaks = len(shifts)
        
        if n_peaks == 1:
            return 's', []
        elif n_peaks == 2:
            # Doublet
            j_value = abs(shifts[0] - shifts[1]) * 400  # Convert to Hz (assuming 400 MHz)
            return 'd', [j_value]
        elif n_peaks == 3:
            # Check if it's a triplet (1:2:1) or doublet of doublets
            if self._is_triplet_pattern(intensities):
                j_value = abs(shifts[0] - shifts[2]) * 400 / 2
                return 't', [j_value]
            else:
                # Doublet of doublets
                j1 = abs(shifts[0] - shifts[1]) * 400
                j2 = abs(shifts[1] - shifts[2]) * 400
                return 'dd', [j1, j2]
        elif n_peaks == 4:
            # Could be quartet or doublet of doublets
            if self._is_quartet_pattern(intensities):
                j_value = abs(shifts[0] - shifts[3]) * 400 / 3
                return 'q', [j_value]
            else:
                # Complex doublet of doublets
                j1 = abs(shifts[0] - shifts[1]) * 400
                j2 = abs(shifts[2] - shifts[3]) * 400
                return 'dd', [j1, j2]
        else:
            # Complex multiplet
            return 'm', []
    
    def _is_triplet_pattern(self, intensities: List[float]) -> bool:
        """Check if intensity pattern matches triplet (1:2:1)."""
        if len(intensities) != 3:
            return False
        
        # Normalize intensities
        max_int = max(intensities)
        norm_int = [i / max_int for i in intensities]
        
        # Check for 1:2:1 pattern (with tolerance)
        return (abs(norm_int[1] - 1.0) < 0.3 and  # Middle peak highest
                abs(norm_int[0] - norm_int[2]) < 0.3 and  # Outer peaks similar
                norm_int[0] < 0.8 and norm_int[2] < 0.8)  # Outer peaks smaller
    
    def _is_quartet_pattern(self, intensities: List[float]) -> bool:
        """Check if intensity pattern matches quartet (1:3:3:1)."""
        if len(intensities) != 4:
            return False
        
        # Normalize intensities
        max_int = max(intensities)
        norm_int = [i / max_int for i in intensities]
        
        # Sort to check pattern
        sorted_int = sorted(norm_int)
        
        # For quartet: outer peaks smaller, inner peaks larger
        return (sorted_int[0] < 0.4 and sorted_int[1] < 0.4 and
                sorted_int[2] > 0.7 and sorted_int[3] > 0.7)
    
    def _annotate_peaks_in_group(self, annotated_peaks: List[Dict], group: PeakGroup):
        """Add group metadata to original peaks."""
        for peak_idx in group.peak_indices:
            annotated_peaks[peak_idx].update({
                'group_id': group.group_id,
                'group_assignment': group.assignment,
                'group_center': group.center_shift,
                'group_integration': group.integration,
                'group_multiplicity': group.multiplicity,
                'group_coupling': group.coupling_constants,
                'is_group_center': peak_idx == group.peak_indices[len(group.peak_indices)//2]  # Mark middle peak
            })
    
    def get_group_summary(self, groups: List[PeakGroup]) -> str:
        """Generate a summary of all groups for display."""
        summary = "Peak Groups:\n"
        summary += "=" * 50 + "\n"
        
        for group in groups:
            coupling_str = ""
            if group.coupling_constants:
                coupling_str = f", J = {', '.join(f'{j:.1f}' for j in group.coupling_constants)} Hz"
            
            summary += (f"{group.assignment}: {group.center_shift:.2f} ppm "
                       f"({group.multiplicity}{coupling_str}, {group.integration}H, "
                       f"{len(group.peak_indices)} peaks)\n")
        
        return summary
    
    def reset_assignments(self):
        """Reset assignment letters to start from 'A' again."""
        self.next_assignment = ord('A')
        self.groups = []

if __name__ == "__main__":
    # Test with sample data
    test_peaks = [
        {'shift': 8.932, 'intensity': 657},
        {'shift': 8.927, 'intensity': 664},
        {'shift': 8.921, 'intensity': 671},
        {'shift': 8.917, 'intensity': 659},
        {'shift': 7.567, 'intensity': 603},
        {'shift': 7.564, 'intensity': 594},
    ]
    
    grouper = NonDestructiveGrouper()
    annotated_peaks, groups = grouper.group_peaks_by_proximity(test_peaks, tolerance_ppm=0.05)
    
    print("Original peaks:", len(test_peaks))
    print("Annotated peaks:", len(annotated_peaks))
    print("Groups:", len(groups))
    print(grouper.get_group_summary(groups))
