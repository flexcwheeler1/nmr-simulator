#!/usr/bin/env python3
"""
NMR Data Input Module

Simple interface for pasting real NMR data from literature or databases.
Supports standard NMR data formats.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
import logging
from typing import List, Dict, Optional

# Import molecular analysis
try:
    from molecular_analysis import molecular_analyzer
    MOLECULAR_ANALYSIS_AVAILABLE = True
except ImportError:
    MOLECULAR_ANALYSIS_AVAILABLE = False
    molecular_analyzer = None

from typing import List, Dict, Tuple, Optional
import json

class NMRDataParser:
    """Parse NMR data from text input."""
    
    def __init__(self):
        self.multiplicity_map = {
            's': 'singlet', 'S': 'singlet',
            'd': 'doublet', 'D': 'doublet', 
            't': 'triplet', 'T': 'triplet',
            'q': 'quartet', 'Q': 'quartet',
            'm': 'multiplet', 'M': 'multiplet',
            'dd': 'doublet of doublets',
            'dt': 'doublet of triplets',
            'td': 'triplet of doublets',
            'br': 'broad', 'bs': 'broad singlet'
        }
    
    def parse_nmr_text(self, text: str, nucleus: str = "1H") -> List[Dict]:
        """
        Parse NMR data from text input.
        
        Supports formats like:
        - 7.36 (s, 5H)
        - 7.36 (s, 5H, Ar-H)
        - δ 7.36 (s, 5H)
        - 1.25 (t, J = 7.0 Hz, 3H)
        - Tabulated format: 136.25 363 1 (shift intensity peak#)
        - Hz ppm Int format: 2903.20 7.265 70
        - Assignment format: A 7.6 (assignment shift)
        """
        peaks = []
        multiplet_centers = {}  # Store main signal assignments
        
        # Clean the text
        text = text.strip()
        if not text:
            return peaks
        
        # Check if this looks like assignment data (contains letters A-Z)
        has_assignments = bool(re.search(r'^[A-Z]\s+\d+\.?\d*', text, re.MULTILINE))
        
        # Split by lines and/or semicolons
        lines = re.split(r'[;\n]', text)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Remove common prefixes
            line = re.sub(r'^(δ|delta)\s*', '', line, flags=re.IGNORECASE)
            line = re.sub(r'^1H\s*NMR.*?:', '', line, flags=re.IGNORECASE)
            line = re.sub(r'^13C\s*NMR.*?:', '', line, flags=re.IGNORECASE)
            
            # Try assignment format (Assign. Shift(ppm))
            assign_match = re.match(r'([A-Z])\s+(\d+\.?\d*)', line)
            if assign_match:
                try:
                    assignment = assign_match.group(1)
                    shift = float(assign_match.group(2))
                    
                    # Store multiplet center for later reference
                    multiplet_centers[assignment] = shift
                    
                    # Default values for assignment format
                    multiplicity = "m"  # Default to multiplet for teaching
                    integration = 1  # Will be adjusted based on typical aromatic vs aliphatic
                    intensity = 100  # Standard intensity
                    
                    # Heuristic integration based on chemical shift regions
                    if shift > 7.0:  # Aromatic region
                        integration = 1  # Typically 1H per aromatic signal
                        multiplicity = "m"  # Complex aromatic splitting
                        width = 0.003  # Narrow aromatic signals (1.2 Hz at 400 MHz)
                    elif shift > 6.0:  # Lower aromatic or NH region
                        integration = 1
                        multiplicity = "s" if shift > 7.5 else "m"  # NH often singlet, others multiplet
                        width = 0.008 if shift > 7.5 else 0.003  # NH broader (3.2 Hz), aromatic narrow
                    elif shift > 3.0:  # CH2/CH3 near electronegative atoms
                        integration = 2
                        multiplicity = "q"  # Often quartets or triplets
                        width = 0.002  # Sharp aliphatic signals (0.8 Hz)
                    elif shift > 1.0:  # Alkyl region
                        integration = 3
                        multiplicity = "t"  # Often triplets
                        width = 0.002  # Sharp aliphatic signals
                    else:  # Very upfield
                        integration = 1
                        multiplicity = "s"
                        width = 0.002
                    
                    peak = {
                        'shift': shift,
                        'multiplicity': multiplicity,
                        'integration': integration,
                        'coupling': [],
                        'intensity': intensity * integration * 10,  # Scale by integration
                        'assignment': assignment,
                        'is_multiplet_center': True,
                        'width_hz': width * 400,  # Convert to Hz for display
                        'linewidth': width  # Store in ppm for Peak object
                    }
                    peaks.append(peak)
                    continue
                    
                except (ValueError, AttributeError):
                    pass
                    if 6.5 <= shift <= 8.5:  # Aromatic region
                        integration = 1  # Usually 1H per aromatic signal
                    elif 2.0 <= shift <= 4.0:  # Aliphatic region
                        integration = 3  # Often CH3 groups
                    else:
                        integration = 1
                    
                    peak = {
                        'shift': shift,
                        'multiplicity': multiplicity,
                        'integration': integration,
                        'coupling': [],
                        'intensity': intensity,
                        'assignment': assignment
                    }
                    peaks.append(peak)
                    continue
                    
                except (ValueError, AttributeError):
                    pass
            
            # Try tabulated format - determine which format based on value ranges
            three_number_match = re.match(r'(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+)', line)
            if three_number_match:
                try:
                    val1 = float(three_number_match.group(1))
                    val2 = float(three_number_match.group(2))
                    val3 = float(three_number_match.group(3))
                    
                    # Determine format based on value ranges
                    # If val1 > 50 and val2 < 20, likely Hz ppm Int format
                    # If val1 < 20 and val2 > 50, likely shift intensity peak# format
                    
                    if val1 > 50 and val2 < 20:
                        # Format: Hz ppm Int (like 2903.20 7.265 70)
                        hz_value = val1
                        shift = val2
                        intensity = val3
                    elif val1 < 50 and val2 > 30:
                        # Format: shift intensity peak# (like 7.265 70 1)
                        shift = val1
                        intensity = val2
                        peak_num = val3
                    else:
                        # Default: assume shift intensity peak# format
                        shift = val1
                        intensity = val2
                        peak_num = val3
                    
                    # For 13C, assume singlets; for 1H, use appropriate values
                    if nucleus == "13C":
                        multiplicity = "s"
                        integration = 1
                        # For 13C, normalize intensity to a reasonable range
                        intensity = max(100, intensity)  # Ensure minimum intensity of 100
                    else:
                        multiplicity = "s"  # Default, can be updated
                        # Scale intensity for integration (normalize to reasonable range)
                        integration = max(1, round(intensity / 100)) if intensity > 10 else 1
                    
                    peak = {
                        'shift': shift,
                        'multiplicity': multiplicity,
                        'integration': integration,
                        'coupling': [],
                        'intensity': intensity
                    }
                    peaks.append(peak)
                    continue
                    
                except (ValueError, AttributeError):
                    pass
            
            # Parse parenthetical format (traditional)
            peak_matches = re.finditer(
                r'(\d+\.?\d*)\s*\(([^)]+)\)',
                line
            )
            
            for match in peak_matches:
                try:
                    shift = float(match.group(1))
                    details = match.group(2)
                    
                    # Parse multiplicity and integration
                    multiplicity = "s"
                    integration = 1
                    coupling = []
                    
                    # Look for multiplicity
                    mult_match = re.search(r'([a-zA-Z]+)', details)
                    if mult_match:
                        mult_text = mult_match.group(1).lower()
                        if mult_text in self.multiplicity_map:
                            multiplicity = mult_text
                    
                    # Look for integration (number followed by H)
                    int_match = re.search(r'(\d+)H', details)
                    if int_match:
                        integration = int(int_match.group(1))
                    
                    # Look for coupling constants
                    j_matches = re.finditer(r'J\s*=?\s*(\d+\.?\d*)', details, re.IGNORECASE)
                    for j_match in j_matches:
                        coupling.append(float(j_match.group(1)))
                    
                    # Look for explicit linewidth specification
                    linewidth = None
                    width_hz = None
                    
                    # Pattern: lw=15 Hz, linewidth=25 Hz, lw=0.025 ppm
                    lw_match = re.search(r'l(?:ine)?w(?:idth)?\s*=?\s*(\d+\.?\d*)\s*(Hz|ppm)?', details, re.IGNORECASE)
                    if lw_match:
                        lw_value = float(lw_match.group(1))
                        lw_unit = lw_match.group(2)
                        
                        if lw_unit and lw_unit.lower() == 'hz':
                            width_hz = lw_value
                            linewidth = lw_value / 400.0  # Convert to ppm assuming 400 MHz
                        elif lw_unit and lw_unit.lower() == 'ppm':
                            linewidth = lw_value
                            width_hz = lw_value * 400.0  # Convert to Hz assuming 400 MHz
                        else:
                            # No unit specified - assume Hz for reasonable values, ppm for small values
                            if lw_value > 1.0:
                                width_hz = lw_value
                                linewidth = lw_value / 400.0
                            else:
                                linewidth = lw_value
                                width_hz = lw_value * 400.0
                    
                    # If no explicit linewidth, apply automatic width based on multiplicity and shift
                    if linewidth is None:
                        # Check for broad multiplicity indicators
                        is_broad = any(broad_code in multiplicity.lower() for broad_code in ['br', 'broad'])
                        
                        if is_broad:
                            # Broad signals get 3x wider
                            if shift > 7.0:  # Aromatic/NH region
                                linewidth = 0.015  # 6 Hz at 400 MHz
                            else:  # Aliphatic region
                                linewidth = 0.006  # 2.4 Hz at 400 MHz
                        else:
                            # Normal automatic width assignment
                            if shift > 7.0:  # Aromatic region
                                linewidth = 0.003  # 1.2 Hz at 400 MHz
                            elif shift > 3.0:  # Mid-range
                                linewidth = 0.002  # 0.8 Hz at 400 MHz
                            else:  # Aliphatic
                                linewidth = 0.002  # 0.8 Hz at 400 MHz
                        
                        width_hz = linewidth * 400.0  # Convert to Hz for storage
                    
                    peak = {
                        'shift': shift,
                        'multiplicity': multiplicity,
                        'integration': integration,
                        'coupling': coupling,
                        'linewidth': linewidth,  # Store linewidth in ppm
                        'width_hz': width_hz,    # Store linewidth in Hz for display
                        'intensity': 100         # Default intensity
                    }
                    peaks.append(peak)
                    
                except (ValueError, AttributeError):
                    continue
        
        return peaks
    
    def enhance_peaks_with_structure(self, peaks: List[Dict], inchi: str, nucleus: str) -> List[Dict]:
        """Enhance peak data with structural information from InChI."""
        if not inchi or not MOLECULAR_ANALYSIS_AVAILABLE:
            return peaks
        
        try:
            enhanced_peaks = molecular_analyzer.enhance_peak_data(peaks, inchi, nucleus)
            return enhanced_peaks
        except Exception as e:
            logging.error(f"Error enhancing peaks with structure: {e}")
            return peaks

class NMRDataInputDialog:
    """Dialog for inputting NMR data manually."""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.parser = NMRDataParser()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Input Real NMR Data")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Compound name
        ttk.Label(main_frame, text="Compound Name (optional):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=40)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        self.name_entry.insert(0, "Unknown Compound")  # Default value
        
        # Nucleus selection
        ttk.Label(main_frame, text="Nucleus:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.nucleus_var = tk.StringVar(value="1H")
        nucleus_frame = ttk.Frame(main_frame)
        nucleus_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Radiobutton(nucleus_frame, text="1H NMR", variable=self.nucleus_var, value="1H").pack(side=tk.LEFT)
        ttk.Radiobutton(nucleus_frame, text="13C NMR", variable=self.nucleus_var, value="13C").pack(side=tk.LEFT, padx=(20, 0))
        
        # InChI input
        ttk.Label(main_frame, text="InChI (optional):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.inchi_entry = ttk.Entry(main_frame, width=60)
        self.inchi_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Solvent selection
        ttk.Label(main_frame, text="Solvent:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.solvent_var = tk.StringVar(value="CDCl3")
        solvent_combo = ttk.Combobox(main_frame, textvariable=self.solvent_var, width=15)
        solvent_combo['values'] = ('CDCl3', 'DMSO-d6', 'CD3OD', 'D2O', 'C6D6', 'CD3CN', 'Acetone-d6')
        solvent_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Instructions
        instructions = ttk.Label(main_frame, text="""
📋 Paste NMR data in any of these formats:
• Standard: 7.36 (s, 5H)  •  With coupling: 1.25 (t, J = 7.0 Hz, 3H)  
• Broad signals: 8.45 (br s, 1H)  •  Custom width: 8.45 (s, 1H, lw=20 Hz)
• With assignment: 3.70 (q, J = 7.0 Hz, 2H, CH2)  •  Assignment: A 7.6
• Tabulated: 136.25 363 1  •  Delta notation: δ 2.17 (s, 6H)

🎛️ Peak Width Control (for broad NH, OH signals):
• Add 'br' for broad: 8.45 (br s, 1H)  •  Specify Hz: 8.45 (s, 1H, lw=25 Hz)
• Or edit widths later in Tools → Show Peak List (double-click Width column)""", justify=tk.LEFT)
        instructions.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Text area for NMR data
        ttk.Label(main_frame, text="NMR Data:").grid(row=5, column=0, sticky=(tk.W, tk.N), pady=5)
        self.text_area = scrolledtext.ScrolledText(main_frame, width=60, height=15, wrap=tk.WORD)
        self.text_area.grid(row=5, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Parse & Preview", command=self._preview_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load Data", command=self._load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.LEFT, padx=5)
        
        # Example button
        ttk.Button(button_frame, text="Load Example", command=self._load_example).pack(side=tk.LEFT, padx=20)
        
        # Preview area
        ttk.Label(main_frame, text="Preview:").grid(row=7, column=0, sticky=(tk.W, tk.N), pady=5)
        self.preview_area = scrolledtext.ScrolledText(main_frame, width=60, height=8, wrap=tk.WORD)
        self.preview_area.grid(row=7, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
    def _load_example(self):
        """Load example NMR data."""
        nucleus = self.nucleus_var.get()
        
        if nucleus == "1H":
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, "Indole")
            self.solvent_var.set("DMSO-d6")
            example_data = """6.52 (m, 1H, H-3)
7.08 (t, J = 7.8 Hz, 1H, H-5)
7.16 (t, J = 7.8 Hz, 1H, H-6)
7.21 (d, J = 3.0 Hz, 1H, H-2)
7.38 (d, J = 8.1 Hz, 1H, H-7)
7.64 (d, J = 7.8 Hz, 1H, H-4)
11.14 (s, 1H, NH)"""
        else:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, "Indole")
            self.solvent_var.set("DMSO-d6")
            example_data = """136.1 900 1
127.9 800 2
124.3 750 3
122.1 600 4
120.9 650 5
119.7 700 6
111.2 850 7
102.1 500 8"""
        
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, example_data)
        self._preview_data()
        
    def _preview_data(self):
        """Preview the parsed data."""
        text = self.text_area.get(1.0, tk.END)
        nucleus = self.nucleus_var.get()
        
        peaks = self.parser.parse_nmr_text(text, nucleus)
        
        self.preview_area.delete(1.0, tk.END)
        
        if peaks:
            preview_text = f"Parsed {len(peaks)} peaks:\n\n"
            for i, peak in enumerate(peaks, 1):
                # Show appropriate nucleus symbol
                nucleus_symbol = "H" if nucleus == "1H" else "C"
                
                # Show assignment if available
                assignment_text = f" [{peak['assignment']}]" if peak.get('assignment') else ""
                
                preview_text += f"Peak {i}: δ {peak['shift']:.2f} ({peak['multiplicity']}, {peak['integration']}{nucleus_symbol}{assignment_text}"
                if peak['coupling']:
                    coupling_str = ", ".join(f"{j:.1f}" for j in peak['coupling'])
                    preview_text += f", J = {coupling_str} Hz"
                preview_text += ")\n"
            self.preview_area.insert(1.0, preview_text)
        else:
            self.preview_area.insert(1.0, "No peaks found. Please check the format.")
    
    def _load_data(self):
        """Load the data and close dialog."""
        compound_name = self.name_entry.get().strip()
        if not compound_name:
            messagebox.showwarning("Missing Information", "Please enter a compound name.")
            return
        
        text = self.text_area.get(1.0, tk.END)
        nucleus = self.nucleus_var.get()
        solvent = self.solvent_var.get()
        inchi = self.inchi_entry.get().strip()
        
        peaks = self.parser.parse_nmr_text(text, nucleus)
        
        if not peaks:
            messagebox.showwarning("No Data", "No valid NMR peaks found. Please check the format.")
            return
        
        # Enhance peaks with structural information if InChI is provided
        if inchi:
            try:
                enhanced_peaks = self.parser.enhance_peaks_with_structure(peaks, inchi, nucleus)
                if enhanced_peaks:
                    peaks = enhanced_peaks
                    messagebox.showinfo("Structural Analysis", 
                                      f"Enhanced {len(peaks)} peaks with structural predictions from InChI.")
            except Exception as e:
                messagebox.showwarning("Structural Analysis Warning", 
                                     f"Could not enhance with structural data: {str(e)}")
        
        self.result = {
            'name': compound_name,
            'nucleus': nucleus,
            'solvent': solvent,
            'inchi': inchi,
            'peaks': peaks
        }
        
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.dialog.destroy()

def show_nmr_input_dialog(parent):
    """Show the NMR data input dialog and return the result."""
    dialog = NMRDataInputDialog(parent)
    parent.wait_window(dialog.dialog)
    return dialog.result

if __name__ == "__main__":
    # Test the parser
    parser = NMRDataParser()
    
    test_data = """7.36 (s, 5H)
1.25 (t, J = 7.0 Hz, 3H)
3.70 (q, J = 7.0 Hz, 2H)"""
    
    peaks = parser.parse_nmr_text(test_data)
    print("Parsed peaks:")
    for peak in peaks:
        print(f"δ {peak['shift']:.2f} ({peak['multiplicity']}, {peak['integration']}H)")
