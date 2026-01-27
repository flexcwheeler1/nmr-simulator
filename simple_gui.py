"""
Simple NMR Simulator GUI - Working Version
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_gui():
    """Create and run a simple NMR simulator GUI."""
    # Import here to avoid circular imports
    from nmr_simulator import NMRSimulator, Molecule
    from sdbs_import import SDBSParser
    
    root = tk.Tk()
    root.title("NMR Spectra Simulator")
    root.geometry("800x600")
    
    # Initialize components
    simulator = NMRSimulator()
    parser = SDBSParser()
    
    # Create UI
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Input section
    input_frame = ttk.LabelFrame(main_frame, text="Molecule Input", padding=10)
    input_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(input_frame, text="Compound Name:").pack(anchor=tk.W)
    compound_entry = ttk.Entry(input_frame, width=30)
    compound_entry.pack(fill=tk.X, pady=5)
    compound_entry.insert(0, "Ethanol")
    
    # Results display
    results_frame = ttk.LabelFrame(main_frame, text="NMR Data", padding=10)
    results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    results_text = tk.Text(results_frame, wrap=tk.WORD)
    scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_text.yview)
    results_text.configure(yscrollcommand=scrollbar.set)
    
    results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Status
    status_var = tk.StringVar(value="Ready")
    status_label = ttk.Label(main_frame, textvariable=status_var)
    status_label.pack(anchor=tk.W)
    
    def load_demo_data():
        """Load demo NMR data."""
        try:
            compound_name = compound_entry.get().strip() or "Ethanol"
            status_var.set(f"Loading data for {compound_name}...")
            root.update_idletasks()
            
            # Create demo molecule and spectra
            molecule, spectra = parser.create_demo_molecule(compound_name)
            
            # Display results
            results_text.delete(1.0, tk.END)
            results_text.insert(tk.END, f"Compound: {compound_name}\n")
            results_text.insert(tk.END, "=" * 50 + "\n\n")
            
            for spectrum in spectra:
                spectrum.generate_spectrum_data()
                results_text.insert(tk.END, f"{spectrum.nucleus} NMR Spectrum:\n")
                results_text.insert(tk.END, "-" * 30 + "\n")
                
                for i, peak in enumerate(spectrum.peaks, 1):
                    results_text.insert(tk.END, 
                        f"Peak {i}: δ {peak.chemical_shift:.2f} ppm "
                        f"({peak.multiplicity}, {peak.integration:.0f}H)\n")
                
                results_text.insert(tk.END, "\n")
            
            status_var.set(f"Loaded {len(spectra)} spectra for {compound_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data:\n{str(e)}")
            status_var.set("Error loading data")
    
    # Load button
    load_button = ttk.Button(input_frame, text="Load Demo Data", command=load_demo_data)
    load_button.pack(pady=5)
    
    # Load initial data
    load_demo_data()
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    create_gui()
