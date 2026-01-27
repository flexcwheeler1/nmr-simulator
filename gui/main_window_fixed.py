"""
Main GUI Window for NMR Spectra Simulator

This module provides the main application window with all controls and functionality.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
from typing import Optional, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmr_simulator import NMRSimulator, Molecule, Spectrum
from sdbs_import import SDBSScraper, SDBSParser
from .spectrum_viewer import SpectrumViewer


class NMRSimulatorGUI:
    """
    Main GUI application for the NMR Spectra Simulator.
    """
    
    def __init__(self):
        """Initialize the main GUI application."""
        self.root = tk.Tk()
        self.root.title("NMR Spectra Simulator with SDBS Import")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.simulator = NMRSimulator()
        self.scraper = SDBSScraper()
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
        
        # Input type selection
        ttk.Label(molecule_frame, text="Input Type:").pack(anchor=tk.W)
        self.input_type_var = tk.StringVar(value="name")
        
        input_type_frame = ttk.Frame(molecule_frame)
        input_type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(input_type_frame, text="Compound Name", 
                       variable=self.input_type_var, value="name").pack(anchor=tk.W)
        ttk.Radiobutton(input_type_frame, text="Molecular Formula", 
                       variable=self.input_type_var, value="formula").pack(anchor=tk.W)
        ttk.Radiobutton(input_type_frame, text="SMILES String", 
                       variable=self.input_type_var, value="smiles").pack(anchor=tk.W)
        
        # Input field
        ttk.Label(molecule_frame, text="Molecule:").pack(anchor=tk.W, pady=(10, 0))
        self.molecule_entry = ttk.Entry(molecule_frame, width=30)
        self.molecule_entry.pack(fill=tk.X, pady=5)
        self.molecule_entry.insert(0, "Ethanol")  # Default
        
        # SDBS search section
        sdbs_frame = ttk.LabelFrame(self.left_frame, text="SDBS Database", padding=10)
        sdbs_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(sdbs_frame, text="Search SDBS", 
                  command=self._search_sdbs).pack(fill=tk.X, pady=2)
        
        ttk.Button(sdbs_frame, text="Load Demo Data", 
                  command=self._load_demo_data).pack(fill=tk.X, pady=2)
        
        # Search results
        ttk.Label(sdbs_frame, text="Search Results:").pack(anchor=tk.W, pady=(10, 0))
        
        self.results_frame = ttk.Frame(sdbs_frame)
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.results_listbox = tk.Listbox(self.results_frame, height=6)
        self.results_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, 
                                              command=self.results_listbox.yview)
        self.results_listbox.configure(yscrollcommand=self.results_scrollbar.set)
        
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_listbox.bind('<Double-1>', self._on_result_double_click)
        
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
        field_strength_combo.bind('<<ComboboxSelected>>', self._on_field_strength_changed)
        
        # Nucleus type
        ttk.Label(sim_frame, text="Nucleus:").pack(anchor=tk.W, pady=(10, 0))
        self.nucleus_var = tk.StringVar(value="1H")
        nucleus_frame = ttk.Frame(sim_frame)
        nucleus_frame.pack(fill=tk.X, pady=2)
        
        ttk.Radiobutton(nucleus_frame, text="1H", 
                       variable=self.nucleus_var, value="1H").pack(side=tk.LEFT)
        ttk.Radiobutton(nucleus_frame, text="13C", 
                       variable=self.nucleus_var, value="13C").pack(side=tk.LEFT, padx=(10, 0))
        
        # Simulation controls
        control_frame = ttk.Frame(sim_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(control_frame, text="Simulate Spectrum", 
                  command=self._simulate_spectrum).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_frame, text="Clear All", 
                  command=self._clear_all).pack(side=tk.LEFT)
        
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
        # Spectrum viewer
        self.spectrum_viewer = SpectrumViewer(self.right_frame)
        self.spectrum_viewer.pack(fill=tk.BOTH, expand=True)
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Spectrum Data...", command=self._export_spectrum_data)
        file_menu.add_command(label="Export Plot...", command=self._export_plot)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Peak Analysis", command=self._show_peak_analysis)
        tools_menu.add_command(label="Compare Spectra", command=self._compare_spectra)
        
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
    
    def _search_sdbs(self):
        """Search the SDBS database for the entered compound."""
        compound_name = self.molecule_entry.get().strip()
        if not compound_name:
            messagebox.showwarning("No Input", "Please enter a compound name to search.")
            return
        
        self._log_message(f"Searching SDBS for: {compound_name}")
        
        try:
            # For demo purposes, use demo compounds
            results = self.scraper.get_random_compounds(5)
            
            # Clear previous results
            self.results_listbox.delete(0, tk.END)
            
            # Add results to listbox
            for result in results:
                display_text = f"{result['name']} ({result.get('formula', 'Unknown')})"
                self.results_listbox.insert(tk.END, display_text)
            
            if results:
                self._log_message(f"Found {len(results)} compounds")
            else:
                self._log_message("No compounds found")
                
        except Exception as e:
            self._log_message(f"Error searching SDBS: {str(e)}")
            messagebox.showerror("Search Error", f"Failed to search SDBS:\\n{str(e)}")
    
    def _on_result_double_click(self, event):
        """Handle double-click on search result."""
        selection = self.results_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.results_listbox.get(selection[0])
        compound_name = selected_text.split(' (')[0]  # Extract compound name
        
        self.molecule_entry.delete(0, tk.END)
        self.molecule_entry.insert(0, compound_name)
        
        self._log_message(f"Selected: {compound_name}")
        
        # Automatically load demo data for the selected compound
        self._load_demo_data()
    
    def _load_demo_data(self, compound_name: str = None):
        """Load demo NMR data for testing."""
        if compound_name is None:
            compound_name = self.molecule_entry.get().strip() or "Ethanol"
        
        self._log_message(f"Loading demo data for: {compound_name}")
        
        try:
            # Create demo molecule and spectra
            self.current_molecule, self.current_spectra = self.parser.create_demo_molecule(compound_name)
            
            # Clear previous spectra from viewer
            self.spectrum_viewer.clear_spectra()
            
            # Add spectra to viewer
            for spectrum in self.current_spectra:
                self.spectrum_viewer.add_spectrum(spectrum)
            
            self._log_message(f"Loaded {len(self.current_spectra)} spectra")
            
            # Update molecule entry if it was auto-selected
            if self.molecule_entry.get().strip() != compound_name:
                self.molecule_entry.delete(0, tk.END)
                self.molecule_entry.insert(0, compound_name)
            
        except Exception as e:
            self._log_message(f"Error loading demo data: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load demo data:\\n{str(e)}")
    
    def _simulate_spectrum(self):
        """Simulate NMR spectrum for the current molecule."""
        compound_name = self.molecule_entry.get().strip()
        if not compound_name:
            messagebox.showwarning("No Input", "Please enter a compound to simulate.")
            return
        
        input_type = self.input_type_var.get()
        nucleus = self.nucleus_var.get()
        field_strength = float(self.field_strength_var.get())
        
        self._log_message(f"Simulating {nucleus} NMR spectrum for: {compound_name}")
        
        try:
            # Update simulator settings
            self.simulator.set_field_strength(field_strength)
            
            # Create molecule
            molecule = Molecule(identifier=compound_name, molecule_type=input_type)
            
            # Simulate spectrum
            spectrum = self.simulator.simulate_spectrum(molecule, nucleus)
            spectrum.title = f"{nucleus} NMR of {compound_name} (Simulated)"
            
            # Add to viewer
            self.spectrum_viewer.add_spectrum(spectrum)
            
            self._log_message(f"Simulation complete - {len(spectrum.peaks)} peaks generated")
            
        except Exception as e:
            self._log_message(f"Simulation error: {str(e)}")
            messagebox.showerror("Simulation Error", f"Failed to simulate spectrum:\\n{str(e)}")
    
    def _on_field_strength_changed(self, event=None):
        """Handle field strength change."""
        field_strength = float(self.field_strength_var.get())
        self.simulator.set_field_strength(field_strength)
        self._log_message(f"Field strength set to {field_strength} MHz")
    
    def _clear_all(self):
        """Clear all data and reset the interface."""
        self.spectrum_viewer.clear_spectra()
        self.results_listbox.delete(0, tk.END)
        self.current_molecule = None
        self.current_spectra = []
        
        # Clear status log
        self.status_text.configure(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.configure(state=tk.DISABLED)
        
        self._log_message("Interface cleared")
    
    def _export_spectrum_data(self):
        """Export spectrum data to file."""
        current_spectrum = self.spectrum_viewer.get_current_spectrum()
        if not current_spectrum:
            messagebox.showwarning("No Data", "No spectrum to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ],
            title="Export Spectrum Data"
        )
        
        if filename:
            try:
                format_type = "csv" if filename.lower().endswith(".csv") else "txt"
                current_spectrum.export_data(filename, format_type)
                self._log_message(f"Data exported to {filename}")
                messagebox.showinfo("Success", f"Spectrum data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data:\\n{str(e)}")
    
    def _export_plot(self):
        """Export current plot."""
        self.spectrum_viewer._export_plot()
    
    def _show_peak_analysis(self):
        """Show peak analysis window."""
        current_spectrum = self.spectrum_viewer.get_current_spectrum()
        if not current_spectrum:
            messagebox.showwarning("No Data", "No spectrum loaded for analysis.")
            return
        
        # Create peak analysis window
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("Peak Analysis")
        analysis_window.geometry("600x400")
        
        # Create text widget for peak list
        text_frame = ttk.Frame(analysis_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Generate peak analysis
        analysis_text = self.parser.export_to_nmr_format(current_spectrum, "detailed")
        text_widget.insert(tk.END, analysis_text)
        text_widget.configure(state=tk.DISABLED)
    
    def _compare_spectra(self):
        """Show spectrum comparison (placeholder)."""
        messagebox.showinfo("Feature Coming Soon", "Spectrum comparison feature will be implemented in a future version.")
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """NMR Spectra Simulator with SDBS Import
        
Version 1.0.0

A Python-based application for simulating NMR spectra with integration to the SDBS (Spectral Database for Organic Compounds) database.

Features:
• 1H and 13C NMR spectrum simulation
• SDBS database integration
• Interactive spectrum visualization
• Peak analysis and export capabilities

Developed for educational and research purposes."""
        
        messagebox.showinfo("About NMR Simulator", about_text)
    
    def run(self):
        """Start the GUI application."""
        self._log_message("NMR Spectra Simulator started")
        self._log_message("Load demo data or search SDBS to begin")
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
