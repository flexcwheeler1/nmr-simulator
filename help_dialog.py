#!/usr/bin/env python3
"""
Help dialog explaining NMR simulator features.
"""

import tkinter as tk
from tkinter import ttk

def show_help_dialog(parent):
    """Show comprehensive help dialog."""
    
    help_window = tk.Toplevel(parent)
    help_window.title("NMR Simulator Help")
    help_window.geometry("700x600")
    help_window.transient(parent)
    
    # Create notebook for tabs
    notebook = ttk.Notebook(help_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Features tab
    features_frame = ttk.Frame(notebook)
    notebook.add(features_frame, text="Features")
    
    features_text = tk.Text(features_frame, wrap=tk.WORD, padx=10, pady=10)
    features_text.pack(fill=tk.BOTH, expand=True)
    
    features_content = """NMR SIMULATOR FEATURES

📊 DISPLAY OPTIONS:

• Show Integrals: Display integration curves above peaks
  - Helps determine relative numbers of protons
  - Essential for quantitative analysis

• Show Labels: Display chemical shift values above peaks  
  - Shows exact ppm values for each signal
  - Useful for precise measurements

• Show Assignments: Display letter assignments (A, B, C...)
  - Assigns letters to multiplet centers
  - Helps correlate signals with molecular structure
  - Teaching tool for structure assignment

• Show Fine Structure: Display detailed coupling patterns
  - Shows individual lines within multiplets
  - Reveals J-coupling information
  - Advanced analysis feature

🧪 InChI FUNCTIONALITY:

InChI (International Chemical Identifier) provides:
• Molecular formula analysis
• Aromatic character detection  
• Structural predictions for peak assignments
• Enhanced integration predictions
• Educational context for chemical shifts

📈 SPECTRUM TYPES:

• 1H NMR: Proton nuclear magnetic resonance
  - Range: 0-12 ppm typically
  - Shows hydrogen environments
  - Integration proportional to number of H

• 13C NMR: Carbon-13 nuclear magnetic resonance  
  - Range: 0-220 ppm typically
  - Shows carbon environments
  - Usually no integration (natural abundance)

🎯 TEACHING FEATURES:

• Variable linewidths for different signal types
• Assignment format for systematic analysis
• Real data input from experimental spectra
• Structural correlation tools"""

    features_text.insert(tk.END, features_content)
    features_text.config(state=tk.DISABLED)
    
    # Data formats tab
    formats_frame = ttk.Frame(notebook)
    notebook.add(formats_frame, text="Data Formats")
    
    formats_text = tk.Text(formats_frame, wrap=tk.WORD, padx=10, pady=10)
    formats_text.pack(fill=tk.BOTH, expand=True)
    
    formats_content = """SUPPORTED DATA FORMATS

📝 STANDARD FORMAT:
7.36 (s, 5H)
1.25 (t, J = 7.0 Hz, 3H)
3.70 (q, J = 7.0 Hz, 2H, CH2)

📋 TABULATED FORMAT:
7.265 70 1    (shift intensity peak#)
136.25 363 1  (for 13C data)

🔤 ASSIGNMENT FORMAT:
A 7.6    (assigns letter A to 7.6 ppm)
B 2.3    (assigns letter B to 2.3 ppm)
C 1.2    (assigns letter C to 1.2 ppm)

⚡ MIXED FORMAT:
A 7.6
7.57 (s, 1H)  
2.30 (s, 3H)

📊 Hz PPM INT FORMAT:
2903.20 7.265 70  (frequency ppm intensity)

💡 TIPS:
• Include InChI for enhanced analysis
• Use assignment format for teaching
• Combine formats as needed
• Check nucleus selection (1H vs 13C)"""

    formats_text.insert(tk.END, formats_content)
    formats_text.config(state=tk.DISABLED)
    
    # Troubleshooting tab
    trouble_frame = ttk.Frame(notebook)
    notebook.add(trouble_frame, text="Troubleshooting")
    
    trouble_text = tk.Text(trouble_frame, wrap=tk.WORD, padx=10, pady=10)
    trouble_text.pack(fill=tk.BOTH, expand=True)
    
    trouble_content = """TROUBLESHOOTING GUIDE

❌ MISSING PEAKS:
• Check data format - ensure proper spacing
• Verify chemical shift values are reasonable
• Try assignment format: A 7.57
• Check nucleus selection (1H vs 13C)

🔍 LOW INTENSITIES:
• For 13C: Use higher intensity values (>100)
• Check field strength setting  
• Verify data format interpretation

📊 NO SPECTRUM DISPLAY:
• Ensure peaks are parsed correctly
• Check preview in data input dialog
• Switch between 1H and 13C tabs
• Try "Load Example" button

🎯 INTEGRATION ISSUES:
• Provide InChI for accurate predictions
• Use standard format with explicit integration
• Check "Show Integrals" checkbox
• Consider structural assignments

⚙️ PERFORMANCE:
• Application may update plots multiple times
• This is normal during data loading
• Large datasets may take time to process

💡 GETTING HELP:
• Use "Load Example" for sample data
• Check log panel for detailed messages  
• Try different data formats
• Ensure compound name is provided"""

    trouble_text.insert(tk.END, trouble_content)
    trouble_text.config(state=tk.DISABLED)
    
    # Close button
    close_btn = ttk.Button(help_window, text="Close", command=help_window.destroy)
    close_btn.pack(pady=10)

if __name__ == "__main__":
    # Test the help dialog
    root = tk.Tk()
    root.withdraw()  # Hide main window
    show_help_dialog(root)
    root.mainloop()
