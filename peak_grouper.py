#!/usr/bin/env python3
"""
NMR Peak Grouping and Multiplicity Analysis

This module provides intelligent peak grouping to convert individual multiplet lines
into proper NMR multiplets with correct multiplicity and J-coupling information.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import re

class PeakGrouper:
    """Intelligent peak grouping for NMR multiplets."""
    
    def __init__(self):
        """Initialize the peak grouper."""
        self.coupling_tolerance = 0.1  # Hz tolerance for identifying coupling patterns
        self.grouping_window = 0.5     # ppm window for grouping peaks
        
    def analyze_peaks(self, peaks: List[Dict], assignment_data: Optional[List[Dict]] = None, 
                     aromatic_window=0.05, aliphatic_window=0.1) -> List[Dict]:
        """
        Analyze and group peaks into proper multiplets.
        
        Args:
            peaks: List of individual peak data
            assignment_data: Optional assignment data from SDBS
            aromatic_window: Grouping window for aromatic region (ppm)
            aliphatic_window: Grouping window for aliphatic region (ppm)
            
        Returns:
            List of grouped peaks with multiplicity information
        """
        if not peaks:
            return peaks
            
        # Sort peaks by chemical shift
        sorted_peaks = sorted(peaks, key=lambda p: p.get('shift', 0), reverse=True)
        
        # Calculate total intensity for relative integration scaling
        total_intensity = sum(p.get('intensity', 100) for p in sorted_peaks)
        
        # Group peaks by proximity with custom windows
        groups = self._group_nearby_peaks(sorted_peaks, aromatic_window, aliphatic_window)
        
        # Analyze each group for multiplicity
        analyzed_groups = []
        for group in groups:
            analyzed_group = self._analyze_group_multiplicity(group)
            
            # Calculate relative integration based on total spectrum intensity
            analyzed_group['integration'] = self._calculate_relative_integration(
                analyzed_group, total_intensity)
            
            # Try to match with assignment data if available
            if assignment_data:
                analyzed_group = self._match_with_assignments(analyzed_group, assignment_data)
            
            analyzed_groups.append(analyzed_group)
        
        return analyzed_groups
    
    def _group_nearby_peaks(self, peaks: List[Dict], aromatic_window=0.05, aliphatic_window=0.1) -> List[List[Dict]]:
        """Group peaks that are close in chemical shift."""
        if not peaks:
            return []
        
        groups = []
        current_group = [peaks[0]]
        
        for i in range(1, len(peaks)):
            current_peak = peaks[i]
            last_peak = current_group[-1]
            
            # Calculate distance in ppm
            distance = abs(current_peak.get('shift', 0) - last_peak.get('shift', 0))
            
            # Use configurable grouping windows
            shift = current_peak.get('shift', 0)
            if shift > 7.0:  # Aromatic region
                window = aromatic_window
            elif shift > 3.0:  # Mid-range
                window = (aromatic_window + aliphatic_window) / 2
            else:  # Aliphatic
                window = aliphatic_window
            
            if distance <= window:
                current_group.append(current_peak)
            else:
                # Start new group
                groups.append(current_group)
                current_group = [current_peak]
        
        # Add the last group
        groups.append(current_group)
        
        return groups
    
    def _analyze_group_multiplicity(self, group: List[Dict]) -> Dict:
        """Analyze a group of peaks to determine multiplicity and coupling."""
        if len(group) == 1:
            # Single peak - likely a singlet
            peak = group[0].copy()
            peak['multiplicity'] = 's'
            peak['coupling'] = []
            peak['integration'] = self._estimate_integration(group)
            return peak
        
        # Multiple peaks - analyze splitting pattern
        shifts = [p.get('shift', 0) for p in group]
        intensities = [p.get('intensity', 100) for p in group]
        
        # Calculate center of multiplet - use geometric mean to preserve original position
        center_shift = (max(shifts) + min(shifts)) / 2  # Geometric center
        # weighted_center = sum(s * i for s, i in zip(shifts, intensities)) / sum(intensities)  # Intensity-weighted
        
        # Analyze splitting pattern
        multiplicity, coupling_constants = self._determine_multiplicity(shifts, intensities)
        
        # Create grouped peak
        grouped_peak = {
            'shift': center_shift,  # Use geometric center to preserve position
            'multiplicity': multiplicity,
            'coupling': coupling_constants,
            'integration': self._estimate_integration(group),
            'intensity': sum(intensities),  # Total intensity
            'linewidth': self._estimate_linewidth(group),
            'original_peaks': len(group)  # Track how many peaks were grouped
        }
        
        return grouped_peak
    
    def _determine_multiplicity(self, shifts: List[float], intensities: List[float]) -> Tuple[str, List[float]]:
        """Determine multiplicity and coupling constants from peak pattern."""
        n_peaks = len(shifts)
        
        if n_peaks == 1:
            return 's', []
        elif n_peaks == 2:
            # Doublet
            j_value = abs(shifts[0] - shifts[1]) * 400  # Convert to Hz
            return 'd', [j_value]
        elif n_peaks == 3:
            # Could be triplet or doublet of doublets
            if self._is_triplet_pattern(intensities):
                # Calculate J from outer peaks
                j_value = abs(shifts[0] - shifts[2]) * 400 / 2  # Divide by 2 for triplet
                return 't', [j_value]
            else:
                # Doublet of doublets
                j_values = self._analyze_dd_pattern(shifts)
                return 'dd', j_values
        elif n_peaks == 4:
            # Could be quartet OR doublet of doublets
            if self._is_quartet_pattern(intensities):
                j_value = abs(shifts[0] - shifts[3]) * 400 / 3  # Divide by 3 for quartet
                return 'q', [j_value]
            else:
                # More likely doublet of doublets for 4 peaks with uneven intensity
                j_values = self._analyze_dd_pattern(shifts)
                return 'dd', j_values
        elif n_peaks == 5:
            # Could be quintet or doublet of triplets
            if self._is_quintet_pattern(intensities):
                j_value = abs(shifts[0] - shifts[4]) * 400 / 4
                return 'quin', [j_value]
            else:
                # Doublet of triplets
                j_values = self._analyze_complex_pattern(shifts, intensities)
                return 'dt', j_values
        elif n_peaks == 6:
            # Could be doublet of triplets, triplet of doublets, or sextet
            if self._is_sextet_pattern(intensities):
                j_value = abs(shifts[0] - shifts[5]) * 400 / 5
                return 'sext', [j_value]
            else:
                # Complex multiplet - try to identify pattern
                j_values = self._analyze_complex_pattern(shifts, intensities)
                pattern = self._identify_complex_pattern(n_peaks, intensities)
                return pattern, j_values
        elif n_peaks == 7:
            # Likely doublet of triplets (2x3=6 but sometimes 7 due to overlap)
            j_values = self._analyze_complex_pattern(shifts, intensities)
            return 'dt', j_values
        elif n_peaks == 8:
            # Could be doublet of quartets
            j_values = self._analyze_complex_pattern(shifts, intensities)
            return 'dq', j_values
        else:
            # Complex multiplet
            return 'm', []
    
    def _is_triplet_pattern(self, intensities: List[float]) -> bool:
        """Check if intensity pattern matches a triplet (1:2:1)."""
        if len(intensities) != 3:
            return False
        
        # Normalize intensities
        max_int = max(intensities)
        norm_int = [i / max_int for i in intensities]
        
        # Check for 1:2:1 pattern (with some tolerance)
        return (abs(norm_int[1] - 1.0) < 0.3 and  # Middle peak should be highest
                abs(norm_int[0] - norm_int[2]) < 0.3 and  # Outer peaks similar
                norm_int[0] < 0.8 and norm_int[2] < 0.8)  # Outer peaks smaller
    
    def _is_quartet_pattern(self, intensities: List[float]) -> bool:
        """Check if intensity pattern matches a quartet (1:3:3:1)."""
        if len(intensities) != 4:
            return False
        
        # Normalize intensities
        max_int = max(intensities)
        norm_int = [i / max_int for i in intensities]
        
        # Sort to check pattern
        sorted_int = sorted(norm_int)
        
        # For a true quartet: outer peaks ~25% of max, inner peaks ~75-100% of max
        # Very strict criteria since most 4-peak patterns in aromatic regions are dd
        return (sorted_int[0] < 0.4 and sorted_int[1] < 0.4 and  # Two small peaks
                sorted_int[2] > 0.7 and sorted_int[3] > 0.7 and  # Two large peaks
                abs(sorted_int[0] - sorted_int[1]) < 0.2 and     # Small peaks similar
                abs(sorted_int[2] - sorted_int[3]) < 0.2)        # Large peaks similar
    
    def _is_quintet_pattern(self, intensities: List[float]) -> bool:
        """Check if intensity pattern matches a quintet (1:4:6:4:1)."""
        if len(intensities) != 5:
            return False
        
        # Normalize intensities
        max_int = max(intensities)
        norm_int = [i / max_int for i in intensities]
        
        # Check for quintet pattern - middle peak highest, symmetric
        return (norm_int[2] > 0.8 and  # Middle peak highest
                abs(norm_int[0] - norm_int[4]) < 0.3 and  # Outer peaks similar
                abs(norm_int[1] - norm_int[3]) < 0.3)     # Inner peaks similar
    
    def _is_sextet_pattern(self, intensities: List[float]) -> bool:
        """Check if intensity pattern matches a sextet (1:5:10:10:5:1)."""
        if len(intensities) != 6:
            return False
        
        # Normalize intensities
        max_int = max(intensities)
        norm_int = [i / max_int for i in intensities]
        
        # Check for sextet pattern - two middle peaks highest, symmetric
        return (max(norm_int[2], norm_int[3]) > 0.8 and  # Middle peaks highest
                abs(norm_int[0] - norm_int[5]) < 0.3 and  # Outer peaks similar
                abs(norm_int[1] - norm_int[4]) < 0.3 and  # Second peaks similar
                abs(norm_int[2] - norm_int[3]) < 0.3)     # Center peaks similar
    
    def _identify_complex_pattern(self, n_peaks: int, intensities: List[float]) -> str:
        """Identify complex multiplicity patterns."""
        if n_peaks == 6:
            # Could be dt or td
            return 'dt'  # Default to doublet of triplets
        elif n_peaks == 8:
            return 'dq'  # Doublet of quartets
        elif n_peaks >= 9:
            return 'm'   # Too complex, just call it multiplet
        else:
            return 'm'
    
    def _analyze_complex_pattern(self, shifts: List[float], intensities: List[float]) -> List[float]:
        """Analyze complex coupling patterns for dt, dq, etc."""
        if len(shifts) < 3:
            return []
        
        # Convert to Hz
        shifts_hz = [s * 400 for s in shifts]
        
        # Look for repeating separations that indicate coupling constants
        separations = []
        for i in range(len(shifts_hz)-1):
            separations.append(abs(shifts_hz[i+1] - shifts_hz[i]))
        
        # Group similar separations
        unique_separations = []
        tolerance = 2.0  # Hz tolerance
        
        for sep in separations:
            found_group = False
            for existing in unique_separations:
                if abs(sep - existing) < tolerance:
                    found_group = True
                    break
            if not found_group:
                unique_separations.append(sep)
        
        # Return up to 3 most significant coupling constants
        return sorted(unique_separations)[:3]
    
    def _analyze_dd_pattern(self, shifts: List[float]) -> List[float]:
        """Analyze doublet of doublets pattern for 3 or 4 peaks."""
        if len(shifts) == 3:
            # For 3 peaks dd, calculate both coupling constants
            shifts_hz = [s * 400 for s in shifts]
            j1 = abs(shifts_hz[1] - shifts_hz[0])
            j2 = abs(shifts_hz[2] - shifts_hz[1])
            return [j1, j2]
        elif len(shifts) == 4:
            # For 4 peaks dd, analyze the pattern more carefully
            shifts_hz = [s * 400 for s in shifts]
            # Calculate possible coupling constants
            separations = []
            for i in range(len(shifts_hz)-1):
                separations.append(abs(shifts_hz[i+1] - shifts_hz[i]))
            
            # Look for two distinct coupling constants
            j_values = []
            if len(set(separations)) <= 2:  # Should have 1-2 distinct values
                unique_js = list(set([round(j, 1) for j in separations]))
                j_values = unique_js[:2]  # Take up to 2 coupling constants
            
            return j_values if j_values else [separations[0], separations[-1]]
        else:
            return []
    
    def _estimate_integration(self, group: List[Dict]) -> float:
        """Estimate integration from peak intensities using relative scaling."""
        total_intensity = sum(p.get('intensity', 100) for p in group)
        
        # Use a more realistic scaling based on typical NMR intensity ranges:
        # - Very large peaks (>15000) likely 3-6H (aromatics, methyl groups)
        # - Medium peaks (5000-15000) likely 2-3H 
        # - Small peaks (<5000) likely 1H
        
        if total_intensity > 20000:
            estimated = round(total_intensity / 7000)  # Scale down large intensities
        elif total_intensity > 5000:
            estimated = round(total_intensity / 5000)  # Medium intensities
        elif total_intensity > 1000:
            estimated = round(total_intensity / 2000)  # Smaller peaks
        else:
            estimated = 1.0  # Minimum 1H
        
        # Ensure reasonable bounds
        estimated = max(1.0, min(12.0, estimated))  # Between 1H and 12H
        return float(estimated)
    
    def _estimate_linewidth(self, group: List[Dict]) -> float:
        """Estimate appropriate linewidth for the grouped peak."""
        # Get chemical shift range
        shifts = [p.get('shift', 0) for p in group]
        shift_range = max(shifts) - min(shifts)
        
        # Base linewidth on chemical shift region - much smaller values for visible multiplets
        center_shift = sum(shifts) / len(shifts)
        
        if center_shift > 8.0:  # NH region
            return 0.003  # 1.2 Hz at 400 MHz - narrow for sharp multiplets
        elif center_shift > 7.0:  # Aromatic
            return 0.002  # 0.8 Hz at 400 MHz - very narrow for aromatic multiplets
        else:  # Aliphatic
            return 0.003  # 1.2 Hz at 400 MHz - narrow for clear splitting
    
    def _calculate_relative_integration(self, group: Dict, total_intensity: float) -> str:
        """Calculate realistic integration values based on peak intensities."""
        group_intensity = group.get('intensity', 100)
        
        # Base relative integration on comparison to total intensity
        # Assume typical NMR spectrum represents 10-20 protons total
        typical_total_protons = 15
        
        # Calculate relative proportion
        intensity_fraction = group_intensity / total_intensity if total_intensity > 0 else 0.1
        estimated_protons = intensity_fraction * typical_total_protons
        
        # Round to whole number integration values only (1H, 2H, 3H, etc.)
        if estimated_protons < 0.7:
            return "1H"  # Minimum 1H
        elif estimated_protons < 1.5:
            return "1H"
        elif estimated_protons < 2.5:
            return "2H"
        elif estimated_protons < 3.5:
            return "3H"
        elif estimated_protons < 4.5:
            return "4H"
        elif estimated_protons < 5.5:
            return "5H"
        elif estimated_protons < 6.5:
            return "6H"
        elif estimated_protons < 8:
            return "7H"
        elif estimated_protons < 10:
            return "9H"
        else:
            return f"{int(round(estimated_protons))}H"
    
    def _match_with_assignments(self, grouped_peak: Dict, assignment_data: List[Dict]) -> Dict:
        """Match grouped peak with assignment data."""
        peak_shift = grouped_peak.get('shift', 0)
        
        # Find closest assignment
        closest_assignment = None
        min_distance = float('inf')
        
        for assignment in assignment_data:
            if 'shift' in assignment:
                distance = abs(assignment['shift'] - peak_shift)
                if distance < min_distance and distance < 0.5:  # Within 0.5 ppm
                    min_distance = distance
                    closest_assignment = assignment
        
        # Add assignment information if found
        if closest_assignment:
            if 'assignment' in closest_assignment:
                grouped_peak['assignment'] = closest_assignment['assignment']
            if 'multiplicity' in closest_assignment and closest_assignment['multiplicity'] != 'm':
                # Use assignment multiplicity if it's specific
                grouped_peak['multiplicity'] = closest_assignment['multiplicity']
        
        return grouped_peak

def create_peak_grouping_dialog(parent, peaks, assignment_data=None):
    """Create a dialog for peak grouping configuration."""
    import tkinter as tk
    from tkinter import ttk
    
    dialog = tk.Toplevel(parent)
    dialog.title("🔗 Peak Grouping & Multiplicity Analysis")
    dialog.geometry("900x800")  # Larger window
    dialog.transient(parent)
    dialog.grab_set()
    
    # Create main frame
    main_frame = ttk.Frame(dialog, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Instructions
    ttk.Label(main_frame, text="Intelligent Peak Grouping", 
             font=("Arial", 14, "bold")).pack(pady=5)
    
    instructions = ttk.Label(main_frame, text="""
This tool will analyze your individual multiplet lines and group them into proper NMR peaks:
• Groups nearby peaks based on chemical shift proximity
• Determines multiplicity (s, d, t, q, dd, m) from splitting patterns
• Calculates J-coupling constants from peak separations  
• Estimates proper integration values
• Preserves original intensity information""", justify=tk.LEFT)
    instructions.pack(pady=10, padx=10, fill=tk.X)
    
    # Settings frame
    settings_frame = ttk.LabelFrame(main_frame, text="Grouping Settings", padding=10)
    settings_frame.pack(fill=tk.X, pady=10)
    
    # Grouping window setting
    ttk.Label(settings_frame, text="Grouping window (ppm):").grid(row=0, column=0, sticky=tk.W)
    window_var = tk.StringVar(value="0.5")
    window_entry = ttk.Entry(settings_frame, textvariable=window_var, width=10)
    window_entry.grid(row=0, column=1, padx=5)
    ttk.Label(settings_frame, text="(peaks within this range will be grouped)").grid(row=0, column=2, sticky=tk.W)
    
    # Coupling tolerance
    ttk.Label(settings_frame, text="Coupling tolerance (Hz):").grid(row=1, column=0, sticky=tk.W)
    coupling_var = tk.StringVar(value="0.1")
    coupling_entry = ttk.Entry(settings_frame, textvariable=coupling_var, width=10)
    coupling_entry.grid(row=1, column=1, padx=5)
    ttk.Label(settings_frame, text="(tolerance for coupling pattern recognition)").grid(row=1, column=2, sticky=tk.W)
    
    # Preview frame
    preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
    preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Create preview text widget
    preview_text = tk.Text(preview_frame, height=15, wrap=tk.WORD)
    preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=preview_text.yview)
    preview_text.configure(yscrollcommand=preview_scrollbar.set)
    
    preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Result storage
    result = {'grouped_peaks': None, 'apply': False}
    
    def update_preview():
        """Update the preview with current settings."""
        try:
            grouper = PeakGrouper()
            
            # Get parameters from the dialog
            aromatic_window = 0.05  # Default tight grouping for aromatic
            aliphatic_window = 0.1  # Default wider grouping for aliphatic
            
            try:
                # Try to get from window_var if it exists
                window_val = float(window_var.get())
                aromatic_window = window_val * 0.5  # Half for aromatic
                aliphatic_window = window_val  # Full for aliphatic
            except:
                pass  # Use defaults
            
            grouped_peaks = grouper.analyze_peaks(peaks, assignment_data, aromatic_window, aliphatic_window)
            
            # Generate preview text
            preview_content = f"Peak Grouping Analysis ({len(peaks)} → {len(grouped_peaks)} peaks)\n"
            preview_content += "=" * 60 + "\n\n"
            
            for i, peak in enumerate(grouped_peaks, 1):
                preview_content += f"Peak {i}: δ {peak['shift']:.3f} ppm\n"
                preview_content += f"  Multiplicity: {peak['multiplicity']}\n"
                preview_content += f"  Integration: {peak['integration']}\n"  # Already formatted as string
                preview_content += f"  Intensity: {peak['intensity']:.0f}\n"
                
                if peak['coupling']:
                    j_values = ", ".join(f"{j:.1f}" for j in peak['coupling'])
                    preview_content += f"  J-coupling: {j_values} Hz\n"
                
                if 'original_peaks' in peak:
                    preview_content += f"  (Grouped from {peak['original_peaks']} lines)\n"
                
                if 'assignment' in peak:
                    preview_content += f"  Assignment: {peak['assignment']}\n"
                
                preview_content += "\n"
            
            preview_text.delete(1.0, tk.END)
            preview_text.insert(tk.END, preview_content)
            
            # Store result
            result['grouped_peaks'] = grouped_peaks
            
        except Exception as e:
            preview_text.delete(1.0, tk.END)
            preview_text.insert(tk.END, f"Error in analysis: {e}")
    
    # Update preview initially
    update_preview()
    
    # Bind updates to setting changes
    try:
        window_var.trace('w', lambda *args: update_preview())
        coupling_var.trace('w', lambda *args: update_preview())
    except:
        pass  # Variables may not exist in simplified version
    
    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=10)
    
    def apply_grouping():
        """Apply the grouped peaks and close dialog."""
        result['apply'] = True
        result['grouped_peaks'] = result.get('grouped_peaks', [])
        dialog.destroy()
    
    def cancel_grouping():
        """Cancel grouping and close dialog."""
        result['apply'] = False
        dialog.destroy()
    
    # Create buttons with better styling
    apply_btn = ttk.Button(button_frame, text="✅ Apply Grouping", command=apply_grouping)
    apply_btn.pack(side=tk.LEFT, padx=5)
    
    cancel_btn = ttk.Button(button_frame, text="❌ Cancel", command=cancel_grouping)
    cancel_btn.pack(side=tk.LEFT, padx=5)
    
    refresh_btn = ttk.Button(button_frame, text="🔄 Refresh Preview", command=update_preview)
    refresh_btn.pack(side=tk.LEFT, padx=5)
    
    # Wait for dialog to close
    dialog.wait_window()
    
    return result

if __name__ == "__main__":
    # Test data
    test_peaks = [
        {'shift': 7.265, 'intensity': 70, 'peak_num': 1},
        {'shift': 7.263, 'intensity': 102, 'peak_num': 2},
        {'shift': 7.261, 'intensity': 89, 'peak_num': 3},
        {'shift': 7.259, 'intensity': 75, 'peak_num': 4},
        {'shift': 2.31, 'intensity': 300, 'peak_num': 5},
        {'shift': 1.25, 'intensity': 150, 'peak_num': 6},
        {'shift': 1.24, 'intensity': 150, 'peak_num': 7},
    ]
    
    grouper = PeakGrouper()
    result = grouper.analyze_peaks(test_peaks)
    
    print("Grouped Peaks:")
    for i, peak in enumerate(result, 1):
        print(f"Peak {i}: δ {peak['shift']:.3f} ({peak['multiplicity']}) - {peak['integration']:.1f}H")
        if peak['coupling']:
            print(f"  J = {', '.join(f'{j:.1f}' for j in peak['coupling'])} Hz")
