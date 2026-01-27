"""
Main GUI Window for NMR Spectra Simulator
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from typing import Optional, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmr_simulator import NMRSimulator, Molecule, Spectrum
from sdbs_import import SDBSParser


class NMRSimulatorGUI:
    """Main GUI application for the NMR Spectra Simulator."""
    
    def __init__(self):
        """Initialize the main GUI application."""
        self.root = tk.Tk()
        self.root.title("NMR Spectra Simulator with SDBS Import")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.simulator = NMRSimulator()
        self.parser = SDBSParser()
        
        self.current_molecule: Optional[Molecule] = None
        self.current_spectra: List[Spectrum] = []
        
        self._setup_ui()
        self._setup_menu()
        
        # Initialize with demo data
        self._load_demo_data()
    
    def _setup_ui(self):
        """Set up the main user interface."""
        # Create main paned window
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for controls
        self.left_frame = ttk.Frame(self.main_paned, width=300)
        self.main_paned.add(self.left_frame, weight=1)
        
        # Right panel for spectrum display
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=3)
        
        self._setup_left_panel()
        self._setup_right_panel()
    
    def _setup_left_panel(self):
        """Set up the left control panel."""
        # Molecule input section
        molecule_frame = ttk.LabelFrame(self.left_frame, text="Molecule Input", padding=10)
        molecule_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Input field
        ttk.Label(molecule_frame, text="Molecule:").pack(anchor=tk.W, pady=(10, 0))
        self.molecule_entry = ttk.Entry(molecule_frame, width=30)
        self.molecule_entry.pack(fill=tk.X, pady=5)
        self.molecule_entry.insert(0, "Ethanol")  # Default
        
        # SDBS search section
        sdbs_frame = ttk.LabelFrame(self.left_frame, text="SDBS Database", padding=10)
        sdbs_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(sdbs_frame, text="Load Demo Data", 
                  command=self._load_demo_data).pack(fill=tk.X, pady=2)
        
        # Simulation parameters
        sim_frame = ttk.LabelFrame(self.left_frame, text="Simulation Parameters", padding=10)
        sim_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Field strength
        ttk.Label(sim_frame, text="Field Strength (MHz):").pack(anchor=tk.W)
        self.field_strength_var = tk.StringVar(value="400")
        field_strength_combo = ttk.Combobox(sim_frame, textvariable=self.field_strength_var,
                                           values=["200", "300", "400", "500", "600", "800"],
                                           state="readonly", width=10)
        field_strength_combo.pack(anchor=tk.W, pady=2)
        
        # Nucleus type
        ttk.Label(sim_frame, text="Nucleus:").pack(anchor=tk.W, pady=(10, 0))
        self.nucleus_var = tk.StringVar(value="1H")
        nucleus_frame = ttk.Frame(sim_frame)
        nucleus_frame.pack(fill=tk.X, pady=2)
        
        ttk.Radiobutton(nucleus_frame, text="1H", 
                       variable=self.nucleus_var, value="1H").pack(side=tk.LEFT)
        ttk.Radiobutton(nucleus_frame, text="13C", 
                       variable=self.nucleus_var, value="13C").pack(side=tk.LEFT, padx=(10, 0))
        
        # Status section
        status_frame = ttk.LabelFrame(self.left_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_text = tk.Text(status_frame, height=8, width=30)
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, 
                                        command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Make status text read-only
        self.status_text.configure(state=tk.DISABLED)
    
    def _setup_right_panel(self):
        """Set up the right panel with spectrum viewer."""
        # Simple text display for now
        self.spectrum_display = tk.Text(self.right_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(self.right_frame, orient=tk.VERTICAL, 
                                 command=self.spectrum_display.yview)
        self.spectrum_display.configure(yscrollcommand=scrollbar.set)
        
        self.spectrum_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _log_message(self, message: str):
        """Add a message to the status log."""
        self.status_text.configure(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def _load_demo_data(self, compound_name: str = None):
        """Load demo NMR data for testing."""
        if compound_name is None:
            compound_name = self.molecule_entry.get().strip() or "Ethanol"
        
        self._log_message(f"Loading demo data for: {compound_name}")
        
        try:
            # Create demo molecule and spectra
            self.current_molecule, self.current_spectra = self.parser.create_demo_molecule(compound_name)
            
            # Display spectra information
            self.spectrum_display.delete(1.0, tk.END)
            
            for spectrum in self.current_spectra:
                spectrum_info = f"\n{spectrum.nucleus} NMR Spectrum\n"
                spectrum_info += "=" * 40 + "\n"
                
                spectrum.generate_spectrum_data()
                for i, peak in enumerate(spectrum.peaks):
                    spectrum_info += f"Peak {i+1}: {peak.chemical_shift:.2f} ppm "
                    spectrum_info += f"({peak.multiplicity}, {peak.integration:.0f}H)\n"
                
                spectrum_info += "\n"
                self.spectrum_display.insert(tk.END, spectrum_info)
            
            self._log_message(f"Loaded {len(self.current_spectra)} spectra")
            
        except Exception as e:
            self._log_message(f"Error loading demo data: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load demo data:\n{str(e)}")
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """NMR Spectra Simulator with SDBS Import
        
Version 1.0.0

A Python-based application for simulating NMR spectra.

Features:
• 1H and 13C NMR spectrum simulation
• Interactive spectrum visualization
• Peak analysis capabilities

Developed for educational and research purposes."""
        
        messagebox.showinfo("About NMR Simulator", about_text)
    
    def run(self):
        """Start the GUI application."""
        self._log_message("NMR Spectra Simulator started")
        self._log_message("Load demo data to begin")
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    try:
        app = NMRSimulatorGUI()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
