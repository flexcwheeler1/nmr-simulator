"""
Enhanced NMR Simulator GUI with Spectrum Plotting and Real Data Input

This version includes:
- Interactive matplotlib spectrum plots
- Graphics export functionality  
- Multiple compound support
- Real NMR data paste functionality
- Non-destructive peak grouping
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from nmr_data_input import show_nmr_input_dialog
import numpy as np
import requests
from bs4 import BeautifulSoup
import sys
import os
import threading
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmr_simulator import NMRSimulator, Molecule, Spectrum
from nmr_simulator.spectrum import Peak
from non_destructive_grouper import NonDestructiveGrouper
from visual_multiplet_grouper import VisualMultipletGrouper
from csv_importer import load_csv_database, load_json_database


class EnhancedNMRGUI:
    """Enhanced NMR Simulator with full spectrum visualization and real data input."""
    
    def __init__(self):
        """Initialize the enhanced GUI."""
        self.root = tk.Tk()
        self.root.title("NMR Spectra Simulator")
        self.root.geometry("1400x900")
        
        # Initialize components
        self.simulator = NMRSimulator()
        self.non_destructive_grouper = NonDestructiveGrouper()  # New grouper
        self.visual_grouper = VisualMultipletGrouper(use_numbers_for_1H=True)  # Visual grouper
        
        # Data storage
        self.current_spectra = []
        self.current_molecule = None
        self.updating_plot = False  # Prevent recursive updates
        
        # Create UI
        self._setup_ui()
        self._setup_menu()
        
        # Initialize with empty plot - NO DEMO DATA
        self._setup_empty_plot()
    
    def _setup_ui(self):
        """Set up the main user interface."""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for controls
        left_panel = ttk.Frame(main_container, width=350)
        main_container.add(left_panel, weight=1)
        
        # Right panel for spectrum display
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=3)
        
        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)
    
    def _setup_left_panel(self, parent):
        """Set up the left control panel."""
        # Compound input section
        input_frame = ttk.LabelFrame(parent, text="Compound Input", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Compound Name:").pack(anchor=tk.W)
        self.compound_entry = ttk.Entry(input_frame, width=30)
        self.compound_entry.pack(fill=tk.X, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="📋 Paste Real NMR Data", 
                  command=self._paste_real_data).pack(fill=tk.X, pady=2)
        
        ttk.Button(button_frame, text="🔄 Clear All Data", 
                  command=self._clear_all_data).pack(fill=tk.X, pady=2)
        
        # Simulation parameters
        params_frame = ttk.LabelFrame(parent, text="NMR Parameters", padding=10)
        params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Field strength
        ttk.Label(params_frame, text="Field Strength (MHz):").pack(anchor=tk.W)
        self.field_var = tk.StringVar(value="400")
        field_combo = ttk.Combobox(params_frame, textvariable=self.field_var,
                                  values=["200", "300", "400", "500", "600", "800"],
                                  state="readonly", width=15)
        field_combo.pack(anchor=tk.W, pady=(0, 10))
        
        # Nucleus selection
        ttk.Label(params_frame, text="Nucleus Type:").pack(anchor=tk.W)
        self.nucleus_var = tk.StringVar(value="1H")
        nucleus_frame = ttk.Frame(params_frame)
        nucleus_frame.pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Radiobutton(nucleus_frame, text="1H", variable=self.nucleus_var, 
                       value="1H", command=self._update_plot).pack(side=tk.LEFT)
        ttk.Radiobutton(nucleus_frame, text="13C", variable=self.nucleus_var, 
                       value="13C", command=self._update_plot).pack(side=tk.LEFT, padx=(10, 0))
        
        # Display options
        display_frame = ttk.Frame(params_frame)
        display_frame.pack(anchor=tk.W, pady=(5, 10))
        
        self.show_integrals_var = tk.BooleanVar(value=False)  # Default disabled
        ttk.Checkbutton(display_frame, text="Show Integrals", 
                       variable=self.show_integrals_var,
                       command=self._update_plot).pack(side=tk.LEFT)
        
        self.show_labels_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="Show Chemical Shifts", 
                       variable=self.show_labels_var,
                       command=self._update_plot).pack(side=tk.LEFT, padx=(15, 0))
        
        self.show_assignments_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="Show Assignments (A-Z)", 
                       variable=self.show_assignments_var,
                       command=self._update_plot).pack(side=tk.LEFT, padx=(15, 0))
        
        self.show_fine_structure_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(display_frame, text="Show Fine Structure", 
                       variable=self.show_fine_structure_var,
                       command=self._update_plot).pack(side=tk.LEFT, padx=(15, 0))
        
        # Noise and resolution controls
        noise_frame = ttk.LabelFrame(params_frame, text="Spectrum Quality", padding=5)
        noise_frame.pack(fill=tk.X, pady=(10, 5))
        
        # Noise level
        ttk.Label(noise_frame, text="Noise Level:").pack(anchor=tk.W)
        self.noise_var = tk.DoubleVar(value=0.0)
        noise_scale = ttk.Scale(noise_frame, from_=0.0, to=0.1, 
                               variable=self.noise_var, orient=tk.HORIZONTAL,
                               command=lambda x: self._update_plot())
        noise_scale.pack(fill=tk.X, pady=(0, 5))
        
        # Noise level display
        self.noise_label = ttk.Label(noise_frame, text="0.0%")
        self.noise_label.pack(anchor=tk.W)
        
        # Data points - set default to 32768 (32k)
        ttk.Label(noise_frame, text="Resolution (Data Points):").pack(anchor=tk.W, pady=(10, 0))
        self.resolution_var = tk.StringVar(value="32768")
        resolution_combo = ttk.Combobox(noise_frame, textvariable=self.resolution_var,
                                       values=["2048", "4096", "8192", "16384", "32768", "65536"],
                                       state="readonly", width=15)
        resolution_combo.pack(anchor=tk.W, pady=(0, 5))
        resolution_combo.bind('<<ComboboxSelected>>', lambda e: self._update_plot())
        
        # Update noise label when scale changes
        def update_noise_label(value):
            percentage = float(value) * 100
            self.noise_label.config(text=f"{percentage:.1f}%")
            self._update_plot()
        
        noise_scale.config(command=update_noise_label)
        
        # Export options
        export_frame = ttk.LabelFrame(parent, text="Export Options", padding=10)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Export Plot (PNG)", 
                  command=self._export_plot).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="Export Data (CSV)", 
                  command=self._export_data).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="Export Bruker Format", 
                  command=self._export_bruker).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="Export JCAMP-DX", 
                  command=self._export_jcamp).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="Export NMR Report", 
                  command=self._export_report).pack(fill=tk.X, pady=2)
        
        # Status log
        log_frame = ttk.LabelFrame(parent, text="Status Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL,
                                     command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.configure(state=tk.DISABLED)
    
    def _setup_right_panel(self, parent):
        """Set up the right panel with matplotlib spectrum viewer."""
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Create toolbar
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Spectrum info panel
        info_frame = ttk.LabelFrame(parent, text="Spectrum Information", padding=10)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        self.info_text = tk.Text(info_frame, height=4, wrap=tk.WORD)
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL,
                                      command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initialize empty plot
        self._setup_empty_plot()
    
    def _setup_empty_plot(self):
        """Set up an empty spectrum plot."""
        self.ax.clear()
        self.ax.set_xlim(12, 0)  # NMR convention
        self.ax.set_ylim(0, 1)
        self.ax.set_xlabel('Chemical Shift (ppm)', fontsize=12)
        self.ax.set_ylabel('Intensity', fontsize=12)
        self.ax.set_title('NMR Spectrum - Load Data to View', fontsize=14)
        self.ax.grid(True, alpha=0.3)
        self.ax.text(6, 0.5, 'Load a compound to view spectrum', 
                    ha='center', va='center', fontsize=16, alpha=0.6)
        self.canvas.draw()
    
    def _setup_empty_plot(self):
        """Set up empty plot with proper NMR axes."""
        self.ax.clear()
        self.ax.set_xlim(12, 0)  # NMR convention: high field left, low field right
        self.ax.set_ylim(0, 1)
        self.ax.set_xlabel('Chemical Shift (ppm)', fontsize=12)
        self.ax.set_ylabel('Intensity', fontsize=12)
        self.ax.set_title('NMR Spectra Simulator', fontsize=14)
        self.ax.grid(True, alpha=0.3)
        self.ax.text(6, 0.5, 'Enter compound name and paste real NMR data', 
                    ha='center', va='center', fontsize=14, alpha=0.7)
        self.canvas.draw()
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Real NMR Data...", command=self._paste_real_data)
        file_menu.add_separator()
        file_menu.add_command(label="Clear Current Data", command=self._clear_data)
        file_menu.add_separator()
        file_menu.add_command(label="Import from NMRBank (CSV/JSON)...", command=self._import_nmrbank_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Export Plot...", command=self._export_plot)
        file_menu.add_command(label="Export Data...", command=self._export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Peak List Editor (Edit Widths)", command=self._show_peak_list)
        tools_menu.add_separator()
        tools_menu.add_command(label="📊 Visual Multiplet Grouping (Teaching Mode)", command=self._visual_multiplet_grouping)
        tools_menu.add_command(label="Group Multiplet Lines", command=self._group_peaks)
        tools_menu.add_command(label="Simple Line Grouping", command=self._simple_group_peaks)
        tools_menu.add_command(label="Non-Destructive Grouping (Preserve All Peaks)", command=self._non_destructive_group_peaks)
        tools_menu.add_command(label="Analyze Peak Patterns", command=self._analyze_peak_patterns)
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear Log", command=self._clear_log)
        tools_menu.add_command(label="Reset Zoom", command=self._reset_zoom)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self._show_help)
        help_menu.add_command(label="About", command=self._show_about)

    def _import_nmrbank_dialog(self):
        """Import compounds from an external CSV/JSON (e.g., NMRBank) and load spectra."""
        try:
            filepath = filedialog.askopenfilename(
                title="Select NMRBank CSV or JSON",
                filetypes=[
                    ("CSV Files", "*.csv"),
                    ("JSON / JSONL Files", "*.json;*.jsonl"),
                    ("All Files", "*.*"),
                ]
            )
            if not filepath:
                return

            self._log(f"Opening compound browser: {os.path.basename(filepath)}")
            self._show_compound_browser(filepath)
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {e}")
            self._log(f"Import error: {e}")
    
    def _show_compound_browser(self, filepath):
        """Show a scrollable browser to explore and load compounds from a database file."""
        browser = tk.Toplevel(self.root)
        browser.title(f"NMRBank Browser - {os.path.basename(filepath)}")
        browser.geometry("800x600")
        
        # Top search bar
        search_frame = ttk.Frame(browser)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        max_var = tk.StringVar(value="100")
        ttk.Label(search_frame, text="Max:").pack(side=tk.LEFT, padx=(10, 5))
        ttk.Entry(search_frame, textvariable=max_var, width=6).pack(side=tk.LEFT, padx=(0, 5))
        
        # Results list with details
        list_frame = ttk.Frame(browser)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview for better display
        columns = ("name", "nuclei", "peaks")
        tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", selectmode="browse")
        tree.heading("#0", text="")
        tree.column("#0", width=0, stretch=False)
        tree.heading("name", text="Compound Name")
        tree.column("name", width=450)
        tree.heading("nuclei", text="Nuclei")
        tree.column("nuclei", width=100)
        tree.heading("peaks", text="Peaks")
        tree.column("peaks", width=80)
        
        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store compounds data
        compounds_data = []
        
        def load_compounds(query=None):
            """Load compounds with optional filter."""
            tree.delete(*tree.get_children())
            compounds_data.clear()
            
            try:
                max_records = int(max_var.get())
            except ValueError:
                max_records = 100
            
            self._log(f"Loading database: {os.path.basename(filepath)} (filter='{query or 'all'}', max={max_records})")
            browser.update()
            
            try:
                if filepath.lower().endswith(".csv"):
                    results = load_csv_database(filepath, name_query=query, max_records=max_records)
                else:
                    results = load_json_database(filepath, name_query=query, max_records=max_records)
                
                for compound in results:
                    name = compound.get("name") or "Unknown"
                    nuclei = ", ".join(compound.get("nmr_data", {}).keys())
                    total_peaks = sum(len(d.get("peaks", [])) for d in compound.get("nmr_data", {}).values())
                    
                    tree.insert("", tk.END, values=(name, nuclei, total_peaks))
                    compounds_data.append(compound)
                
                self._log(f"Loaded {len(results)} compounds")
                if not results:
                    messagebox.showinfo("No Results", "No compounds found. Try a different search term or increase max records.", parent=browser)
                    
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load compounds: {e}", parent=browser)
                self._log(f"Load error: {e}")
        
        def on_search(*args):
            query = search_var.get().strip()
            load_compounds(query if query else None)
        
        def on_load():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a compound to load.", parent=browser)
                return
            
            idx = tree.index(selection[0])
            if 0 <= idx < len(compounds_data):
                compound = compounds_data[idx]
                browser.destroy()
                self._load_compound_record(compound)
        
        def on_double_click(event):
            on_load()
        
        # Buttons
        btn_frame = ttk.Frame(browser)
        btn_frame.pack(fill=tk.X, padx=10, pady=8)
        
        ttk.Button(btn_frame, text="Search", command=on_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load Selected", command=on_load).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Close", command=browser.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Bind events
        search_entry.bind("<Return>", on_search)
        tree.bind("<Double-1>", on_double_click)
        
        # Initial load - show first 100 compounds
        browser.after(100, lambda: load_compounds(None))
        
        browser.transient(self.root)
        browser.focus_set()

    def _select_compound_dialog(self, compounds):
        """Simple selection dialog returning the chosen compound dict or None."""
        top = tk.Toplevel(self.root)
        top.title("Select Compound")
        top.geometry("500x400")
        ttk.Label(top, text="Select a compound:").pack(anchor=tk.W, padx=10, pady=5)

        frame = ttk.Frame(top)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        lb = tk.Listbox(frame)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        for idx, c in enumerate(compounds):
            name = c.get("name") or "Unknown"
            nuclei = ", ".join(c.get("nmr_data", {}).keys())
            lb.insert(tk.END, f"{name}  [{nuclei}]")

        selection = {"value": None}

        def on_ok():
            sel = lb.curselection()
            if not sel:
                return
            selection["value"] = compounds[sel[0]]
            top.destroy()

        def on_cancel():
            selection["value"] = None
            top.destroy()

        btns = ttk.Frame(top)
        btns.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(btns, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btns, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)

        top.transient(self.root)
        top.grab_set()
        self.root.wait_window(top)
        return selection["value"]

    def _load_compound_record(self, compound: dict):
        """Load a parsed compound record (from CSV/JSON importer) into the GUI."""
        name = compound.get("name") or "Unknown"
        nmr = compound.get("nmr_data", {})

        # Prefer 1H if available
        nucleus = "1H" if "1H" in nmr else ("13C" if "13C" in nmr else None)
        if not nucleus:
            self._log("Selected compound has no parsable NMR data.")
            messagebox.showwarning("No NMR", "Selected compound has no NMR data.")
            return

        spec_info = nmr[nucleus]
        peaks = spec_info.get("peaks", [])
        if not peaks:
            messagebox.showwarning("No Peaks", f"No peaks found for {nucleus}.")
            return

        # Create molecule and spectrum
        molecule = Molecule(identifier=name, molecule_type="name")
        molecule.name = name

        spectrum = Spectrum(nucleus=nucleus, field_strength=400.0)
        self._log(f"Loading {nucleus} data for {name}: {len(peaks)} peaks")

        for i, peak_data in enumerate(peaks):
            # Determine linewidth in ppm (default ~0.5 Hz at 400 MHz)
            if 'linewidth' in peak_data:
                width_ppm = peak_data['linewidth']
            else:
                width_ppm = 0.5 / 400.0

            intensity = peak_data.get('intensity', 100)
            multiplicity = peak_data.get('multiplicity', 's')
            coupling = peak_data.get('coupling', [])
            integration = peak_data.get('integration', 1)

            try:
                shift = float(peak_data['shift'])
            except Exception:
                continue

            p = Peak(
                chemical_shift=shift,
                intensity=intensity,
                width=width_ppm,
                multiplicity=multiplicity,
                coupling_constants=coupling,
                integration=integration,
            )
            spectrum.add_peak(p)

        # Set as current
        self.current_molecule = molecule
        self.current_spectra = [spectrum]
        self.nucleus_var.set(nucleus)
        self._log(f"Set nucleus selection to {nucleus}")

        # Update plot and info
        self._update_plot()
        self._update_info_display()
    
    def _log(self, message):
        """Add a message to the status log."""
        self.log_text.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def _clear_all_data(self):
        """Clear all loaded data and reset the interface."""
        # Clear data
        self.current_spectra = []
        self.current_molecule = None
        
        # Reset compound name
        self.compound_entry.delete(0, tk.END)
        
        # Clear plot
        self._setup_empty_plot()
        
        # Clear log
        self._clear_log()
        
        self._log("All data cleared. Ready for new input.")
        messagebox.showinfo("Data Cleared", "All data has been cleared. You can now paste new NMR data.")
    
    def _paste_real_data(self):
        """Open dialog to paste real NMR data."""
        self._log("Opening real NMR data input dialog...")
        
        result = show_nmr_input_dialog(self.root)
        
        if result:
            # Create a molecule and spectrum from the pasted data
            from nmr_simulator.molecule import Molecule, Atom
            from nmr_simulator.spectrum import Spectrum, Peak
            
            # Analyze InChI if provided
            inchi_info = None
            if result.get('inchi'):
                try:
                    from inchi_analyzer import analyze_inchi
                    analyzer = analyze_inchi(result['inchi'])
                    if analyzer:
                        inchi_info = analyzer.get_compound_info()
                        # Enhance peaks with structural information
                        result['peaks'] = analyzer.predict_assignments(result['peaks'])
                        self._log(f"InChI analysis: {inchi_info['formula']} - {inchi_info['carbons']}C, {inchi_info['hydrogens']}H")
                except ImportError:
                    self._log("InChI analyzer not available")
                except Exception as e:
                    self._log(f"InChI analysis error: {e}")
            
            # Create molecule
            molecule = Molecule(identifier=result['name'], molecule_type="name")
            molecule.name = result['name']
            
            # Store InChI if provided
            if result.get('inchi'):
                molecule.inchi = result['inchi']
                self._log(f"Stored InChI: {result['inchi'][:50]}..." if len(result['inchi']) > 50 else f"Stored InChI: {result['inchi']}")
            
            # Store InChI analysis results
            if inchi_info:
                molecule.inchi_info = inchi_info
            
            # Add dummy atoms
            molecule.add_atom(Atom(element="C", position=1))
            molecule.add_atom(Atom(element="H", position=1))
            
            # Handle multiple datasets - ask user what to do if data already exists
            if self.current_spectra and self.current_molecule:
                choice = messagebox.askyesnocancel(
                    "Data Already Loaded",
                    f"You already have data for '{self.current_molecule.name}'.\n\n"
                    f"• Yes: Replace existing data\n"
                    f"• No: Add peaks to existing spectrum\n" 
                    f"• Cancel: Keep current data unchanged",
                    title="Data Loading Options"
                )
                
                if choice is None:  # Cancel
                    self._log("Data loading cancelled - keeping existing data")
                    return
                elif choice is False:  # No = Add to existing
                    self._log("Adding peaks to existing spectrum...")
                    # Find existing spectrum with same nucleus
                    existing_spectrum = None
                    for spec in self.current_spectra:
                        if spec.nucleus == result['nucleus']:
                            existing_spectrum = spec
                            break
                    
                    if existing_spectrum:
                        # Add new peaks to existing spectrum
                        peak_count_before = len(existing_spectrum.peaks)
                        for i, peak_data in enumerate(result['peaks']):
                            # Use custom linewidth if provided
                            if 'linewidth' in peak_data:
                                width_ppm = peak_data['linewidth']
                                width_hz = peak_data.get('width_hz', width_ppm * 400)
                            else:
                                width_hz = 0.5
                                width_ppm = width_hz / 400.0
                            
                            peak = Peak(
                                chemical_shift=peak_data['shift'],
                                intensity=peak_data['intensity'],
                                width=width_ppm,
                                multiplicity=peak_data['multiplicity'],
                                coupling_constants=peak_data['coupling'],
                                integration=peak_data['integration']
                            )
                            existing_spectrum.add_peak(peak)
                            self._log(f"Added peak {peak_count_before + i + 1}: δ {peak_data['shift']:.3f}")
                        
                        # Update display
                        self._log(f"Total peaks now: {len(existing_spectrum.peaks)}")
                        self.root.after(100, self._update_plot)
                        return
                    else:
                        self._log(f"No existing {result['nucleus']} spectrum found, creating new one")
                # choice is True = Replace (continue with normal flow)
                else:
                    self._log("Replacing existing data with new dataset")
            
            # Create spectrum with correct constructor
            spectrum = Spectrum(
                nucleus=result['nucleus'],
                field_strength=400.0  # Default 400 MHz
            )
            
            # Add peaks from parsed data
            self._log(f"Adding {len(result['peaks'])} peaks to spectrum...")
            for i, peak_data in enumerate(result['peaks']):
                # Use custom linewidth if provided, otherwise default to 0.5 Hz
                if 'linewidth' in peak_data:
                    width_ppm = peak_data['linewidth']
                    width_hz = peak_data.get('width_hz', width_ppm * 400)
                else:
                    # Convert 0.5 Hz linewidth to ppm (linewidth in Hz / field strength in MHz)
                    width_hz = 0.5  # 0.5 Hz linewidth
                    width_ppm = width_hz / 400.0  # Convert to ppm (assuming 400 MHz)
                
                peak = Peak(
                    chemical_shift=peak_data['shift'],
                    intensity=peak_data['intensity'],  # Use actual intensity from data
                    width=width_ppm,  # Use custom or default width
                    multiplicity=peak_data['multiplicity'],
                    coupling_constants=peak_data['coupling'],
                    integration=peak_data['integration']
                )
                spectrum.add_peak(peak)
                self._log(f"Added peak {i+1}: δ {peak_data['shift']:.3f} (intensity: {peak_data['intensity']}, width: {width_hz:.1f} Hz)")
            
            # Set as current data
            self.current_molecule = molecule
            self.current_spectra = [spectrum]
            
            # Update GUI nucleus selection to match the loaded data
            self.nucleus_var.set(result['nucleus'])
            self._log(f"Set nucleus selection to {result['nucleus']}")
            
            # Update display
            self._log("Updating plot...")
            
            # Small delay to ensure data is ready
            self.root.after(100, lambda: self._delayed_update(result, spectrum))
        else:
            self._log("Real data input cancelled")
            
    def _delayed_update(self, result, spectrum):
        """Delayed update to ensure spectrum data is ready."""
        self._log("Performing delayed update...")
        self._update_plot()
        self._update_info_display()
        
        # Log final spectrum state
        if hasattr(spectrum, 'spectrum_data') and spectrum.spectrum_data is not None:
            self._log(f"Final spectrum check: {len(spectrum.spectrum_data)} data points ready")
        else:
            self._log("Warning: spectrum_data still not ready after delay")
            
        self._log(f"Loaded real NMR data for {result['name']}: {len(result['peaks'])} peaks ({result['nucleus']} NMR)")
        self._log(f"Spectrum has {len(spectrum.peaks)} peaks total")
        
    def _paste_real_data_complete(self):
        """Complete the paste real data process."""
        pass
        
    def _paste_real_data_cancelled(self):
        """Handle cancelled paste real data."""
        self._log("Real data input cancelled")
    
    def _search_compound(self):
        """Search for compounds in SDBS database - REAL DATA ONLY."""
        compound_name = self.compound_entry.get().strip()
        if not compound_name:
            messagebox.showwarning("Input Required", "Please enter a compound name to search.")
            return
        
        self._log(f"Searching SDBS for: {compound_name}")
        
        # Run SDBS search in a separate thread to avoid blocking UI
        search_thread = threading.Thread(target=self._perform_sdbs_search, args=(compound_name,))
        search_thread.daemon = True
        search_thread.start()
    
    def _perform_sdbs_search(self, compound_name):
        """Perform actual SDBS search."""
        try:
            self.root.after(0, self._log, "Connecting to SDBS database...")
            
            # Perform the search
            results = self.parser.search_compounds(compound_name, max_results=10)
            
            # Update UI in main thread
            self.root.after(0, self._update_search_results, results)
            
            if results:
                self.root.after(0, self._log, f"Found {len(results)} compounds from SDBS database")
            else:
                self.root.after(0, self._log, f"No SDBS data found for '{compound_name}'")
            
        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            self.root.after(0, self._log, error_msg)
            print(f"Detailed error: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_search_results(self, results):
        """Update the search results listbox."""
        self.results_listbox.delete(0, tk.END)
        
        for result in results:
            if isinstance(result, dict):
                # Real search result format
                display_text = f"{result['name']} ({result['id']}) - {result['formula']}"
                if result['mw'] > 0:
                    display_text += f" MW: {result['mw']:.1f}"
            else:
                # Fallback for string results
                display_text = str(result)
            
            self.results_listbox.insert(tk.END, display_text)
    
    def _on_result_select(self, event):
        """Handle selection of a search result."""
        selection = self.results_listbox.curselection()
        if selection:
            selected_text = self.results_listbox.get(selection[0])
            
            # Extract compound name from the display text
            if '(' in selected_text:
                compound_name = selected_text.split(' (')[0]  # Extract base name
            else:
                compound_name = selected_text
            
            self.compound_entry.delete(0, tk.END)
            self.compound_entry.insert(0, compound_name)
            
            # Try to load real SDBS data if available
            try:
                # Extract SDBS ID if available
                self._log(f"Selected text: '{selected_text}'")
                if '(' in selected_text and ')' in selected_text:
                    id_part = selected_text.split('(')[1].split(')')[0]
                    self._log(f"Extracted ID part: '{id_part}'")
                    if id_part.startswith('HSP-'):
                        # This is an SDBS ID, try to get real data
                        self._log(f"Attempting to load SDBS data for ID: {id_part}")
                        molecule, spectra = self.parser.parse_compound_from_sdbs(id_part, compound_name)
                        if spectra:
                            self.current_molecule = molecule
                            self.current_spectra = spectra
                            self._update_plot()
                            self._update_info_display()
                            self._log(f"Loaded real SDBS data for {compound_name}")
                            return
                        else:
                            self._log(f"No spectra returned for SDBS ID: {id_part}")
                    else:
                        self._log(f"ID part does not start with HSP-: '{id_part}'")
                else:
                    self._log(f"No parentheses found in selected text")
                
                # No SDBS data found
                self._log(f"No SDBS data available for {compound_name}")
                
            except Exception as e:
                self._log(f"Error loading compound data: {e}")
                import traceback
                self._log(f"Traceback: {traceback.format_exc()}")
    
    def _update_spectrum_display(self):
        """Update the spectrum display with current data."""
        if self.current_spectra:
            # Display the first spectrum by default
            spectrum = self.current_spectra[0]
            self._plot_spectrum(spectrum)
            self._update_info_display()
        else:
            self._setup_empty_plot()
    
    def _update_plot(self):
        """Update the spectrum plot."""
        if self.updating_plot:
            self._log("Plot update already in progress, skipping")
            return
            
        self.updating_plot = True
        try:
            self._log("_update_plot called")
            if not self.current_spectra:
                self._log("No current_spectra found, setting up empty plot")
                self._setup_empty_plot()
                return
            
            nucleus = self.nucleus_var.get()
            field_strength = float(self.field_var.get())
            self._log(f"Looking for spectrum with nucleus: {nucleus}")
            
            # Find the spectrum for the selected nucleus
            spectrum = None
            for i, spec in enumerate(self.current_spectra):
                self._log(f"Spectrum {i}: nucleus={spec.nucleus}")
                if spec.nucleus == nucleus:
                    spectrum = spec
                    break
            
            if not spectrum:
                self._log(f"No spectrum found for nucleus {nucleus}")
                self._setup_empty_plot()
                self.ax.text(6, 0.5, f'No {nucleus} NMR data available', 
                            ha='center', va='center', fontsize=16, alpha=0.6)
                self.canvas.draw()
                return
            
            self._log(f"Found spectrum with {len(spectrum.peaks)} peaks")
            # Update field strength
            spectrum.field_strength = field_strength
            
            # Generate spectrum data with noise and resolution
            self._log("Generating spectrum data...")
            resolution = int(self.resolution_var.get())
            noise_level = self.noise_var.get()
            spectrum.generate_spectrum_data(resolution=resolution, noise_level=noise_level)
        finally:
            self.updating_plot = False
        
        # Clear and plot
        self.ax.clear()
        self._log("Axis cleared")
        
        if spectrum.ppm_axis is not None and spectrum.spectrum_data is not None:
            self._log(f"Plotting spectrum: PPM range {min(spectrum.ppm_axis):.2f} to {max(spectrum.ppm_axis):.2f}")
            self._log(f"Intensity range: {min(spectrum.spectrum_data):.2e} to {max(spectrum.spectrum_data):.2e}")
            
            # Plot the spectrum
            self.ax.plot(spectrum.ppm_axis, spectrum.spectrum_data, 'b-', linewidth=1.5)
            self._log(f"Plotted {len(spectrum.ppm_axis)} data points")
            
            # Check if any data is visible in the plot range
            visible_data = spectrum.spectrum_data[
                (spectrum.ppm_axis >= spectrum.ppm_range[0]) & 
                (spectrum.ppm_axis <= spectrum.ppm_range[1])
            ]
            if len(visible_data) > 0:
                self._log(f"Visible data range: {np.min(visible_data):.2e} to {np.max(visible_data):.2e}")
            else:
                self._log("No visible data in PPM range!")
            
            # Force axis to redraw
            self.ax.relim()
            self.ax.autoscale_view()
            
            # Add peak markers and labels with smart positioning
            labeled_positions = []  # Track label positions to avoid overlap
            self._current_shift_positions = []  # Reset shift positions for this plot update
            self._shift_counter = 0  # Reset shift counter for alternating heights
            
            for i, peak in enumerate(spectrum.peaks):
                # Find peak position in data
                peak_idx = np.argmin(np.abs(spectrum.ppm_axis - peak.chemical_shift))
                peak_y = spectrum.spectrum_data[peak_idx]
                
                # Determine if this is a multiplet center, visual group center, or fine structure
                is_multiplet_center = (hasattr(peak, 'integration') and 
                                     peak.integration is not None and peak.integration > 0.5)
                is_visual_center = getattr(peak, 'is_visual_center', False)
                is_assignment = hasattr(peak, 'integration') and hasattr(peak, 'multiplicity')
                
                # When using visual grouping, ONLY show assignments on visual centers
                has_visual_groups = any(hasattr(p, 'visual_group_id') and p.visual_group_id >= 0 for p in spectrum.peaks)
                if has_visual_groups:
                    should_show_assignment = is_visual_center  # Only visual centers
                else:
                    should_show_assignment = is_visual_center or is_multiplet_center  # Fallback to old logic
                
                # Show assignment labels (visual assignments or auto-generated)
                if (self.show_assignments_var.get() and should_show_assignment and 
                    hasattr(peak, 'integration') and peak.integration is not None and peak.integration >= 1):
                    
                    # Skip if this peak has a visual assignment but isn't a visual center
                    # This prevents duplicates when visual grouping is active
                    if (has_visual_groups and 
                        hasattr(peak, 'visual_assignment') and 
                        peak.visual_assignment and 
                        not is_visual_center):
                        continue
                    
                    # Use visual assignment if available, otherwise auto-generate
                    if hasattr(peak, 'visual_assignment') and peak.visual_assignment:
                        assignment_letter = peak.visual_assignment
                    elif hasattr(peak, 'assignment') and peak.assignment:
                        assignment_letter = peak.assignment
                    else:
                        # Fallback: auto-generate assignment
                        assignment_letter = chr(65 + (i % 26))  # A, B, C, etc.
                    
                    # Position assignment at top of plot area with smart spacing
                    y_min, y_max = self.ax.get_ylim()
                    
                    # Smart horizontal positioning to avoid overlap
                    base_x = peak.chemical_shift
                    final_x = base_x
                    
                    # Check for conflicts with existing labels
                    min_distance = 4.0 if spectrum.nucleus == '13C' else 0.15  # Larger spacing for 13C
                    for labeled_x in labeled_positions:
                        if abs(final_x - labeled_x) < min_distance:
                            # Offset to avoid overlap
                            if final_x > labeled_x:
                                final_x = labeled_x + min_distance
                            else:
                                final_x = labeled_x - min_distance
                    
                    labeled_positions.append(final_x)
                    label_y = y_max * 0.95  # 95% of max height
                    
                    # Draw connecting line from peak to label if offset
                    if abs(final_x - base_x) > 0.01:
                        self.ax.plot([base_x, final_x], [peak_y, label_y], 
                                   'r--', linewidth=1, alpha=0.7)
                    
                    self.ax.annotate(f'{assignment_letter}', 
                                   xy=(final_x, label_y),
                                   xytext=(0, 0), textcoords='offset points',
                                   ha='center', va='center', 
                                   fontsize=14, fontweight='bold', color='black',
                                   bbox=dict(boxstyle='circle,pad=0.3', facecolor='white', 
                                           edgecolor='black', linewidth=2, alpha=0.9))
                
                # Show chemical shift labels ONLY for group centers and at top
                if (self.show_labels_var.get() and should_show_assignment):
                    # Skip if this peak has a visual assignment but isn't a visual center
                    # This prevents duplicates when visual grouping is active
                    if (has_visual_groups and 
                        hasattr(peak, 'visual_assignment') and 
                        peak.visual_assignment and 
                        not is_visual_center):
                        continue
                    # Show shift with alternating heights and tilted text for better visibility
                    y_min, y_max = self.ax.get_ylim()
                    
                    # Alternate between two height levels for better visibility
                    if not hasattr(self, '_shift_counter'):
                        self._shift_counter = 0
                    
                    # Use alternating heights: high and low positions
                    if self._shift_counter % 2 == 0:
                        shift_y = y_max * 0.85  # Higher position
                    else:
                        shift_y = y_max * 0.75  # Lower position
                    
                    self._shift_counter += 1
                    
                    # Apply spacing for shift labels to prevent overlap
                    base_x = peak.chemical_shift
                    final_shift_x = base_x
                    
                    # Check for conflicts with OTHER shift labels only
                    # Build list of shift positions from previous peaks in this loop
                    if not hasattr(self, '_current_shift_positions'):
                        self._current_shift_positions = []
                    
                    # Adjust minimum distance based on nucleus type
                    if spectrum.nucleus == '13C':
                        min_distance = 2.5  # Reduced spacing due to alternating heights
                    else:
                        min_distance = 0.12  # Smaller spacing for 1H (narrower ppm range)
                    
                    for existing_shift_x in self._current_shift_positions:
                        if abs(final_shift_x - existing_shift_x) < min_distance:
                            # Offset to avoid overlap
                            if final_shift_x > existing_shift_x:
                                final_shift_x = existing_shift_x + min_distance
                            else:
                                final_shift_x = existing_shift_x - min_distance
                    
                    # Add this position to the list
                    self._current_shift_positions.append(final_shift_x)
                    
                    # Draw connecting line if significantly offset
                    if abs(final_shift_x - base_x) > 0.02:  # Only if significantly offset
                        self.ax.plot([base_x, final_shift_x], [peak_y, shift_y], 
                                   'gray', linestyle=':', linewidth=1, alpha=0.6)
                    
                    # Format chemical shift based on nucleus type
                    if spectrum.nucleus == '13C':
                        shift_text = f'{peak.chemical_shift:.1f}'  # 1 decimal for 13C
                        rotation = 25 if self._shift_counter % 2 == 1 else 0  # Tilt alternating labels
                    else:
                        shift_text = f'{peak.chemical_shift:.2f}'  # 2 decimals for 1H and others
                        rotation = 0  # No rotation for 1H
                    
                    self.ax.annotate(shift_text, 
                                   xy=(final_shift_x, shift_y),
                                   xytext=(0, 0), textcoords='offset points',
                                   ha='center', va='center', 
                                   fontsize=9, color='black', fontweight='bold',
                                   rotation=rotation,  # Tilt alternating labels
                                   bbox=dict(boxstyle='round,pad=0.2', facecolor='lightyellow', 
                                           edgecolor='gray', linewidth=1, alpha=0.8))
                
                # Show fine structure (individual lines) if checkbox is checked
                if (self.show_fine_structure_var.get() and not is_multiplet_center):
                    # Mark fine structure lines with small markers
                    self.ax.plot(peak.chemical_shift, peak_y, 'r.', markersize=3)
                
                # Show integrals BELOW the PPM scale for main signals only
                if (self.show_integrals_var.get() and 
                    spectrum.nucleus == '1H' and 
                    should_show_assignment and  # Use same logic as assignments
                    hasattr(peak, 'integration') and peak.integration is not None):
                    
                    # Get current axis limits to place integrals below
                    y_min, y_max = self.ax.get_ylim()
                    integral_y = y_min + (y_max - y_min) * 0.05  # 5% up from bottom
                    
                    # Draw a small line to represent integration below the spectrum
                    integral_width = 0.02
                    self.ax.plot([peak.chemical_shift - integral_width, peak.chemical_shift + integral_width], 
                               [integral_y, integral_y], 'r-', linewidth=3)
                    
                    # Add integration value below the line
                    self.ax.annotate(f'{peak.integration:.0f}H', 
                                   xy=(peak.chemical_shift, integral_y),
                                   xytext=(0, -10), textcoords='offset points',  # Below the line
                                   ha='center', va='top', 
                                   fontsize=8, color='red', fontweight='bold')
        else:
            self._log("Warning: spectrum.ppm_axis or spectrum.spectrum_data is None!")
        
        # Set up plot appearance
        self.ax.set_xlim(spectrum.ppm_range[1], spectrum.ppm_range[0])  # Inverted for NMR
        
        if spectrum.spectrum_data is not None:
            y_max = np.max(spectrum.spectrum_data)
            y_min = np.min(spectrum.spectrum_data)
            self._log(f"Setting y-axis limits: min={y_min:.2e}, max={y_max:.2e}")
            self.ax.set_ylim(-0.05 * y_max, 1.2 * y_max)
            self._log(f"Y-axis limits set to: {self.ax.get_ylim()}")
        else:
            self.ax.set_ylim(0, 1)
            self._log("No spectrum data, using default y-limits (0, 1)")
        
        self._log(f"X-axis limits: {self.ax.get_xlim()}")
        
        self.ax.set_xlabel('Chemical Shift (ppm)', fontsize=12)
        self.ax.set_ylabel('Intensity', fontsize=12)
        self.ax.set_title(f'{spectrum.nucleus} NMR Spectrum - {self.compound_entry.get()} ({field_strength} MHz)', 
                         fontsize=14)
        self.ax.grid(True, alpha=0.3)
        
        # Refresh canvas with forced updates
        self._log("Drawing canvas...")
        self.canvas.draw()
        self.canvas.flush_events()  # Force immediate drawing
        
        # Multiple attempts to force GUI refresh
        self.root.update_idletasks()  # Force GUI update
        self.root.update()  # Force complete GUI update
        
        # Force figure refresh
        self.figure.canvas.draw_idle()
        
        # Additional canvas refresh
        try:
            self.canvas.get_tk_widget().update()
        except:
            pass
            
        self._log("Canvas drawn and GUI updated")
    
    def _update_info_display(self):
        """Update the spectrum information display."""
        if not self.current_spectra:
            return
        
        nucleus = self.nucleus_var.get()
        spectrum = None
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            return
        
        # Generate detailed peak information
        info_text = f"{spectrum.nucleus} NMR Spectrum Information:\n"
        info_text += f"Field Strength: {spectrum.field_strength} MHz\n"
        info_text += f"Number of Peaks: {len(spectrum.peaks)}\n"
        
        # Add compound name and InChI if available
        if self.current_molecule:
            info_text += f"Compound: {getattr(self.current_molecule, 'name', 'Unknown')}\n"
            
            # Show InChI analysis results if available
            if hasattr(self.current_molecule, 'inchi_info') and self.current_molecule.inchi_info:
                inchi_info = self.current_molecule.inchi_info
                info_text += f"Formula: {inchi_info['formula']}\n"
                info_text += f"Aromatic: {'Yes' if inchi_info['aromatic'] else 'No'}\n"
                if inchi_info['aromatic']:
                    info_text += f"Predicted aromatic H: {inchi_info['predicted_aromatic_h']}\n"
            
            if hasattr(self.current_molecule, 'inchi') and self.current_molecule.inchi:
                inchi_display = self.current_molecule.inchi[:60] + "..." if len(self.current_molecule.inchi) > 60 else self.current_molecule.inchi
                info_text += f"InChI: {inchi_display}\n"
        
        info_text += "\n"
        
        for i, peak in enumerate(spectrum.peaks, 1):
            info_text += f"Peak {i}: δ {peak.chemical_shift:.2f} ppm "
            info_text += f"({peak.multiplicity}, {peak.integration:.0f}H)\n"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info_text)
    
    def _export_plot(self):
        """Export the current plot as an image."""
        if not self.current_spectra:
            messagebox.showwarning("No Data", "No spectrum to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf"),
                ("SVG files", "*.svg"),
                ("EPS files", "*.eps"),
                ("All files", "*.*")
            ],
            title="Export Spectrum Plot"
        )
        
        if filename:
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight', 
                                   facecolor='white', edgecolor='none')
                self._log(f"Plot exported to: {filename}")
                messagebox.showinfo("Export Successful", f"Plot saved as:\n{filename}")
            except Exception as e:
                self._log(f"Export error: {str(e)}")
                messagebox.showerror("Export Error", f"Failed to export plot:\n{str(e)}")
    
    def _export_data(self):
        """Export spectrum data as CSV."""
        nucleus = self.nucleus_var.get()
        spectrum = None
        
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            messagebox.showwarning("No Data", f"No {nucleus} NMR data to export.")
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
                spectrum.export_data(filename, "csv" if filename.endswith(".csv") else "txt")
                self._log(f"Data exported to: {filename}")
                messagebox.showinfo("Export Successful", f"Data saved as:\n{filename}")
            except Exception as e:
                self._log(f"Export error: {str(e)}")
                messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")
    
    def _export_report(self):
        """Export a complete NMR report."""
        if not self.current_spectra:
            messagebox.showwarning("No Data", "No spectrum data to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ],
            title="Export NMR Report"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(f"NMR Spectroscopy Report\n")
                    f.write(f"=" * 50 + "\n\n")
                    f.write(f"Compound: {self.compound_entry.get()}\n")
                    f.write(f"Field Strength: {self.field_var.get()} MHz\n\n")
                    
                    for spectrum in self.current_spectra:
                        report_text = self.parser.export_to_nmr_format(spectrum, "detailed")
                        f.write(report_text + "\n\n")
                
                self._log(f"Report exported to: {filename}")
                messagebox.showinfo("Export Successful", f"Report saved as:\n{filename}")
            except Exception as e:
                self._log(f"Export error: {str(e)}")
                messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")
    
    def _export_bruker(self):
        """Export spectrum in Bruker format for TopSpin compatibility."""
        nucleus = self.nucleus_var.get()
        spectrum = None
        
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            messagebox.showwarning("No Data", f"No {nucleus} NMR data to export.")
            return
        
        # Choose directory for Bruker folder structure
        directory = filedialog.askdirectory(title="Select Directory for Bruker Export")
        
        if directory:
            try:
                self._create_bruker_export(spectrum, directory)
                self._log(f"Bruker format exported to: {directory}")
                messagebox.showinfo("Export Successful", 
                                  f"Bruker format saved to:\n{directory}\n\n"
                                  f"Ready for import into TopSpin!")
            except Exception as e:
                self._log(f"Bruker export error: {str(e)}")
                messagebox.showerror("Export Error", f"Failed to export Bruker format:\n{str(e)}")
    
    def _export_jcamp(self):
        """Export spectrum in JCAMP-DX format."""
        nucleus = self.nucleus_var.get()
        spectrum = None
        
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            messagebox.showwarning("No Data", f"No {nucleus} NMR data to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".jdx",
            filetypes=[
                ("JCAMP-DX files", "*.jdx"),
                ("JDF files", "*.jdf"),
                ("DX files", "*.dx"),
                ("All files", "*.*")
            ],
            title="Export JCAMP-DX Spectrum Data"
        )
        
        if filename:
            try:
                self._create_jcamp_export(spectrum, filename)
                self._log(f"JCAMP-DX format exported to: {filename}")
                messagebox.showinfo("Export Successful", f"JCAMP-DX data saved as:\n{filename}")
            except Exception as e:
                self._log(f"JCAMP-DX export error: {str(e)}")
                messagebox.showerror("Export Error", f"Failed to export JCAMP-DX format:\n{str(e)}")
    
    def _create_jcamp_export(self, spectrum, filename):
        """Create JCAMP-DX export with MestreNova compatibility."""
        import datetime
        
        with open(filename, 'w') as f:
            # JCAMP-DX Header - MestreNova compatible
            f.write("##TITLE= NMR Simulator Export\n")
            f.write("##JCAMP-DX= 5.01\n")
            f.write("##DATA TYPE= NMR SPECTRUM\n")
            f.write("##DATA CLASS= XYDATA\n")
            f.write("##ORIGIN= NMR Simulator\n")
            f.write("##OWNER= User\n")
            f.write(f"##DATE= {datetime.datetime.now().strftime('%Y/%m/%d')}\n")
            f.write(f"##TIME= {datetime.datetime.now().strftime('%H:%M:%S')}\n")
            f.write("\n")
            
            # Spectral Information
            f.write("##.OBSERVEFREQUENCY= {:.6f}\n".format(spectrum.field_strength))
            f.write("##.OBSERVENUCLEUS= ^{}\n".format(spectrum.nucleus))
            f.write("##SPECTROMETER/DATA SYSTEM= NMR Simulator\n")
            f.write("##.SOLVENTNAME= CDCl3\n")
            f.write("##XUNITS= PPM\n")
            f.write("##YUNITS= RELATIVE INTENSITY\n")
            f.write("##XLABEL= Chemical Shift\n")
            f.write("##YLABEL= Intensity\n")
            f.write("\n")
            
            # Critical fix for MestreNova: Use reversed PPM range ordering
            # MestreNova expects FIRSTX > LASTX for NMR (high field to low field)
            ppm_min = spectrum.ppm_range[0]  # Low field (left side)
            ppm_max = spectrum.ppm_range[1]  # High field (right side)
            
            f.write("##FIRSTX= {:.6f}\n".format(ppm_max))  # Start with high field
            f.write("##LASTX= {:.6f}\n".format(ppm_min))   # End with low field
            f.write("##MAXX= {:.6f}\n".format(ppm_max))
            f.write("##MINX= {:.6f}\n".format(ppm_min))
            f.write("##MAXY= {:.6f}\n".format(float(np.max(spectrum.data_points))))
            f.write("##MINY= {:.6f}\n".format(float(np.min(spectrum.data_points))))
            f.write("##NPOINTS= {}\n".format(len(spectrum.data_points)))
            # Negative DELTAX for decreasing PPM values (NMR convention)
            f.write("##DELTAX= {:.6f}\n".format(-(ppm_max - ppm_min) / (len(spectrum.data_points) - 1)))
            f.write("\n")
            
            # Acquisition Parameters
            f.write("##.PULSE SEQUENCE= zg30\n")
            f.write("##.NUMBER OF SCANS= 1\n")
            f.write("##.ACQUISITION TIME= 2.0\n")
            f.write("##.RELAXATION DELAY= 1.0\n")
            f.write("##.PULSE WIDTH= 30\n")
            f.write("##.TEMPERATURE= 298\n")
            f.write("##.FIELD= {:.1f}\n".format(spectrum.field_strength))
            f.write("##.SWEEP WIDTH= {:.2f}\n".format((ppm_max - ppm_min) * spectrum.field_strength))
            f.write("##.DIGITAL RESOLUTION= {:.3f}\n".format((ppm_max - ppm_min) * spectrum.field_strength / len(spectrum.data_points)))
            f.write("\n")
            
            # Processing Parameters
            f.write("##.PROCESSING= ft\n")
            f.write("##.LINE BROADENING= 0.3\n")
            f.write("##.ZERO FILLING= 0\n")
            f.write("##.BASELINE CORRECTION= polynomial\n")
            f.write("##.PHASE CORRECTION= manual\n")
            f.write("##.REFERENCING= TMS\n")
            f.write("\n")
            
            # Export Parameters
            f.write("##.EXPORT RESOLUTION= {}\n".format(int(self.resolution_var.get())))
            f.write("##.NOISE LEVEL= {:.1f}%\n".format(self.noise_var.get() * 100))
            f.write("\n")
            
            # Peak Table (if available)
            if hasattr(spectrum, 'peaks') and spectrum.peaks:
                f.write("##$PEAKTABLE= (XY..XY)\n")
                sorted_peaks = sorted(spectrum.peaks, key=lambda p: p.chemical_shift, reverse=True)
                for i, peak in enumerate(sorted_peaks):
                    # Find peak intensity in spectrum data
                    peak_idx = np.argmin(np.abs(spectrum.ppm_axis - peak.chemical_shift))
                    peak_intensity = spectrum.data_points[peak_idx]
                    f.write("({:.3f},{:.3f})".format(peak.chemical_shift, peak_intensity))
                    if i < len(sorted_peaks) - 1:
                        f.write(" ")
                f.write("\n\n")
            
            # XY Data - MestreNova compatible format
            f.write("##XYDATA= (X++(Y..Y))\n")
            
            # For MestreNova: Use reversed data order (high field to low field)
            # This matches the FIRSTX > LASTX and negative DELTAX convention
            reversed_ppm = spectrum.ppm_axis[::-1]      # Reverse PPM axis
            reversed_data = spectrum.data_points[::-1]  # Reverse intensity data
            
            # Write data in standard JCAMP format
            chunk_size = 10  # Data points per line
            for i in range(0, len(reversed_ppm), chunk_size):
                end_idx = min(i + chunk_size, len(reversed_ppm))
                
                # Start with X value for this chunk
                f.write("{:.6f}".format(reversed_ppm[i]))
                
                # Add Y values for this chunk
                for j in range(i, end_idx):
                    f.write(" {:.6f}".format(reversed_data[j]))
                f.write("\n")
            
            # JCAMP-DX Footer
            f.write("##END=\n")
    
    def _create_bruker_export(self, spectrum, base_directory):
        """Create Bruker-compatible folder structure and files."""
        import os
        import datetime
        import struct
        
        # Create Bruker folder structure
        experiment_name = f"{spectrum.nucleus}_simulated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        exp_dir = os.path.join(base_directory, experiment_name, "1")  # Add "1" experiment number
        pdata_dir = os.path.join(exp_dir, "pdata", "1")
        
        os.makedirs(pdata_dir, exist_ok=True)
        
        # Prepare spectrum data for Bruker format
        # CRITICAL FIX: Bruker expects data in reverse order (high field to low field)
        spectrum_data_reversed = spectrum.data_points[::-1]  # Reverse the data
        spectrum_data_scaled = spectrum_data_reversed * 1000000  # Scale to integer range
        
        # Create 1r file (real spectrum data) - binary format
        spectrum_file = os.path.join(pdata_dir, "1r")
        with open(spectrum_file, 'wb') as f:
            # Convert to 32-bit big-endian integers
            for value in spectrum_data_scaled:
                # Clamp to 32-bit integer range
                int_value = max(-2147483648, min(2147483647, int(value)))
                f.write(struct.pack('>i', int_value))
        
        # Create proc file (processing parameters) - required by TopSpin
        proc_file = os.path.join(pdata_dir, "proc")
        with open(proc_file, 'w') as f:
            f.write("##TITLE= Parameter file, TopSpin 4.1.4\n")
            f.write("##JCAMPDX= 5.0\n")
            f.write("##DATATYPE= Parameter Values\n")
            f.write("##NPOINTS= 1\n")
            f.write("##ORIGIN= Bruker BioSpin GmbH\n")
            f.write("##OWNER= nmrsu\n")
            f.write("##$ABSF1= 0\n")
            f.write("##$ABSF2= 0\n")
            f.write("##$ABSG= 0\n")
            f.write("##$ABSL= 0\n")
            f.write("##$ALPHA= 0\n")
            f.write("##$AQORDER= 0\n")
            f.write("##$ASSFAC= 0\n")
            f.write("##$ASSFACI= 0\n")
            f.write("##$ASSFACX= 0\n")
            f.write("##$ASSWID= 0\n")
            f.write("##$AUNMP= <proc_1d>\n")
            f.write("##$AZFE= 0.1\n")
            f.write("##$AZFW= 0.5\n")
            f.write("##$BCFW= 1\n")
            f.write("##$BC_mod= 0\n")
            f.write("##$BYTORDP= 1\n")  # Big endian
            f.write("##$COROFFS= 0\n")
            f.write("##$DATMOD= 1\n")
            f.write("##$DC= 1\n")
            f.write("##$DFILT= <>\n")
            f.write("##$DTYPP= 0\n")
            f.write("##$FCOR= 0.5\n")
            f.write("##$FTSIZE= 65536\n")
            f.write("##$FT_mod= 6\n")
            f.write("##$GAMMA= 1\n")
            f.write("##$GB= 0\n")
            f.write("##$INTBC= 1\n")
            f.write("##$INTSCL= 1\n")
            f.write("##$ISEN= 128\n")
            f.write("##$LB= 0.3\n")
            f.write("##$LEV0= 0\n")
            f.write("##$LPBIN= 0\n")
            f.write("##$MAXI= 10000\n")
            f.write("##$MC2= 0\n")
            f.write("##$MEAN= 0\n")
            f.write("##$ME_mod= 0\n")
            f.write("##$MI= 0\n")
            f.write("##$NCOEF= 0\n")
            f.write("##$NC_proc= -4\n")  # 32-bit integer
            f.write("##$NLEV= 6\n")
            f.write("##$NOISF1= 1\n")
            f.write("##$NOISF2= 1\n")
            f.write("##$NSP= 1\n")
            f.write(f"##$OFFSET= {spectrum.ppm_range[1]:.6f}\n")  # High field limit
            f.write("##$PC= 1\n")
            f.write("##$PHC0= 0\n")
            f.write("##$PHC1= 0\n")
            f.write("##$PH_mod= 1\n")
            f.write("##$PKNL= yes\n")
            f.write("##$PPARMOD= 0\n")
            f.write("##$PSCAL= 1\n")
            f.write("##$PSIGN= 0\n")
            f.write("##$REVERSE= no\n")
            f.write(f"##$SF= {spectrum.field_strength:.6f}\n")  # Spectrometer frequency
            f.write(f"##$SI= {len(spectrum.data_points)}\n")  # Size
            f.write("##$SIGF1= 1\n")
            f.write("##$SIGF2= 1\n")
            f.write("##$SINO= 400\n")
            f.write("##$SIOLD= 65536\n")
            f.write("##$SREGLST= <1H.CDCl3>\n")
            f.write("##$SSB= 0\n")
            f.write(f"##$SW_p= {(spectrum.ppm_range[1] - spectrum.ppm_range[0]) * spectrum.field_strength:.2f}\n")  # Sweep width in Hz
            f.write("##$SYMM= 0\n")
            f.write("##$S_DEV= 0\n")
            f.write("##$TDeff= 65536\n")
            f.write("##$TI= <>\n")
            f.write("##$TILT= no\n")
            f.write("##$TM1= 0.1\n")
            f.write("##$TM2= 0.9\n")
            f.write("##$TOPLEV= 0\n")
            f.write("##$USERP1= <user>\n")
            f.write("##$USERP2= <user>\n")
            f.write("##$USERP3= <user>\n")
            f.write("##$USERP4= <user>\n")
            f.write("##$USERP5= <user>\n")
            f.write("##$WDW= 1\n")
            f.write("##$XDIM= 8192\n")
            f.write("##$YMAX_p= 0\n")
            f.write("##$YMIN_p= 0\n")
            f.write("##END=\n")
        
        # Create procs file (processing parameters)
        procs_file = os.path.join(pdata_dir, "procs")
        with open(procs_file, 'w') as f:
            f.write("##TITLE= Parameter file, TopSpin 4.1.4\n")
            f.write("##JCAMPDX= 5.0\n")
            f.write("##DATATYPE= Parameter Values\n")
            f.write("##NPOINTS= 1\n")
            f.write("##ORIGIN= Bruker BioSpin GmbH\n")
            f.write("##OWNER= nmrsu\n")
            f.write("##$ABSF1= 0\n")
            f.write("##$ABSF2= 0\n")
            f.write("##$ABSG= 0\n")
            f.write("##$ABSL= 0\n")
            f.write("##$ALPHA= 0\n")
            f.write("##$AQORDER= 0\n")
            f.write("##$ASSFAC= 0\n")
            f.write("##$ASSFACI= 0\n")
            f.write("##$ASSFACX= 0\n")
            f.write("##$ASSWID= 0\n")
            f.write("##$AUNMP= <proc_1d>\n")
            f.write("##$AZFE= 0.1\n")
            f.write("##$AZFW= 0.5\n")
            f.write("##$BCFW= 1\n")
            f.write("##$BC_mod= 0\n")
            f.write("##$BYTORDP= 1\n")  # Big endian
            f.write("##$COROFFS= 0\n")
            f.write("##$DATMOD= 1\n")
            f.write("##$DC= 1\n")
            f.write("##$DFILT= <>\n")
            f.write("##$DTYPP= 0\n")
            f.write("##$FCOR= 0.5\n")
            f.write("##$FTSIZE= 65536\n")
            f.write("##$FT_mod= 6\n")
            f.write("##$GAMMA= 1\n")
            f.write("##$GB= 0\n")
            f.write("##$INTBC= 1\n")
            f.write("##$INTSCL= 1\n")
            f.write("##$ISEN= 128\n")
            f.write("##$LB= 0.3\n")
            f.write("##$LEV0= 0\n")
            f.write("##$LPBIN= 0\n")
            f.write("##$MAXI= 10000\n")
            f.write("##$MC2= 0\n")
            f.write("##$MEAN= 0\n")
            f.write("##$ME_mod= 0\n")
            f.write("##$MI= 0\n")
            f.write("##$NCOEF= 0\n")
            f.write("##$NC_proc= -4\n")  # 32-bit integer
            f.write("##$NLEV= 6\n")
            f.write("##$NOISF1= 1\n")
            f.write("##$NOISF2= 1\n")
            f.write("##$NSP= 1\n")
            f.write(f"##$OFFSET= {spectrum.ppm_range[1]:.6f}\n")  # High field limit
            f.write("##$PC= 1\n")
            f.write("##$PHC0= 0\n")
            f.write("##$PHC1= 0\n")
            f.write("##$PH_mod= 1\n")
            f.write("##$PKNL= yes\n")
            f.write("##$PPARMOD= 0\n")
            f.write("##$PSCAL= 1\n")
            f.write("##$PSIGN= 0\n")
            f.write("##$REVERSE= no\n")
            f.write(f"##$SF= {spectrum.field_strength:.6f}\n")  # Spectrometer frequency
            f.write(f"##$SI= {len(spectrum.data_points)}\n")  # Size
            f.write("##$SIGF1= 1\n")
            f.write("##$SIGF2= 1\n")
            f.write("##$SINO= 400\n")
            f.write("##$SIOLD= 65536\n")
            f.write("##$SREGLST= <1H.CDCl3>\n")
            f.write("##$SSB= 0\n")
            f.write("##$STSI= 0\n")
            f.write("##$STSR= 0\n")
            f.write(f"##$SW_p= {(spectrum.ppm_range[1] - spectrum.ppm_range[0]) * spectrum.field_strength:.2f}\n")  # Sweep width in Hz
            f.write("##$SYMM= 0\n")
            f.write("##$S_DEV= 0\n")
            f.write("##$TDeff= 0\n")
            f.write("##$TDoff= 0\n")
            f.write("##$TI= <>\n")
            f.write("##$TILT= no\n")
            f.write("##$TM1= 0.1\n")
            f.write("##$TM2= 0.9\n")
            f.write("##$TOPLEV= 0\n")
            f.write("##$USERP1= <user>\n")
            f.write("##$USERP2= <user>\n")
            f.write("##$USERP3= <user>\n")
            f.write("##$USERP4= <user>\n")
            f.write("##$USERP5= <user>\n")
            f.write("##$WDW= 1\n")
            f.write(f"##$XDIM= {len(spectrum.data_points)}\n")
            f.write("##$YMAX_p= 0\n")
            f.write("##$YMIN_p= 0\n")
            f.write("##END=\n")
        
        # Create acqus file (acquisition parameters) - this was missing!
        acqus_file = os.path.join(exp_dir, "acqus")
        with open(acqus_file, 'w') as f:
            f.write("##TITLE= Parameter file, TopSpin 4.1.4\n")
            f.write("##JCAMPDX= 5.0\n")
            f.write("##DATATYPE= Parameter Values\n")
            f.write("##NPOINTS= 1\n")
            f.write("##ORIGIN= Bruker BioSpin GmbH\n")
            f.write("##OWNER= nmrsu\n")
            f.write("##$AMP= (0..31)\n")
            f.write("100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100\n")
            f.write("100 100 100 100 100 100 100 100 100 100 100 100 100 100 100 100\n")
            f.write("##$AMPCOIL= (0..19)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$ANAVPT= -1\n")
            f.write("##$AQSEQ= 0\n")
            f.write("##$AQ_mod= 3\n")
            f.write("##$AUNM= <au_zg>\n")
            f.write("##$AUTOPOS= <>\n")
            f.write("##$BF1= 400.13\n")
            f.write("##$BF2= 400.13\n")
            f.write("##$BF3= 400.13\n")
            f.write("##$BF4= 400.13\n")
            f.write("##$BF5= 400.13\n")
            f.write("##$BF6= 400.13\n")
            f.write("##$BF7= 400.13\n")
            f.write("##$BF8= 400.13\n")
            f.write("##$BYTORDA= 1\n")
            f.write("##$CAGPARS= (0..11)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$CFRGN= 4\n")
            f.write("##$CHEMSTR= <none>\n")
            f.write("##$CNST= (0..63)\n")
            f.write("1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1\n")
            f.write("1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1\n")
            f.write("##$CPDPRG= (0..8)\n")
            f.write("<> <> <> <> <> <> <> <> <>\n")
            f.write("##$D= (0..63)\n")
            f.write("0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$DATE= 0\n")
            f.write("##$DBL= (0..7)\n")
            f.write("120 120 120 120 120 120 120 120\n")
            f.write("##$DBP= (0..7)\n")
            f.write("150 150 150 150 150 150 150 150\n")
            f.write("##$DBP07= 0\n")
            f.write("##$DBP47= 0\n")
            f.write("##$DBPNAM0= <>\n")
            f.write("##$DBPNAM1= <>\n")
            f.write("##$DBPNAM2= <>\n")
            f.write("##$DBPNAM3= <>\n")
            f.write("##$DBPNAM4= <>\n")
            f.write("##$DBPNAM5= <>\n")
            f.write("##$DBPNAM6= <>\n")
            f.write("##$DBPNAM7= <>\n")
            f.write("##$DBPOAL= (0..7)\n")
            f.write("0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5\n")
            f.write("##$DBPOFFS= (0..7)\n")
            f.write("0 0 0 0 0 0 0 0\n")
            f.write("##$DEPA= (0..7)\n")
            f.write("4.7 4.7 4.7 4.7 4.7 4.7 4.7 4.7\n")
            f.write("##$DERX= 0\n")
            f.write("##$DE= 6.5\n")
            f.write("##$DIGMOD= 1\n")
            f.write("##$DIGTYP= 8\n")
            f.write("##$DQDMODE= 0\n")
            f.write("##$DR= 22\n")
            f.write("##$DS= 2\n")
            f.write("##$DSPFIRM= 0\n")
            f.write("##$DSPFVS= 20\n")
            f.write("##$DTYPA= 0\n")
            f.write("##$EXP= <>\n")
            f.write("##$F1LIST= <>\n")
            f.write("##$F2LIST= <>\n")
            f.write("##$F3LIST= <>\n")
            f.write("##$FCUCHAN= (0..9)\n")
            f.write("0 1 2 3 0 0 0 0 0 0\n")
            f.write("##$FL1= 90\n")
            f.write("##$FL2= 90\n")
            f.write("##$FL3= 90\n")
            f.write("##$FL4= 90\n")
            f.write("##$FOV= 20\n")
            f.write("##$FQ1LIST= <>\n")
            f.write("##$FQ2LIST= <>\n")
            f.write("##$FQ3LIST= <>\n")
            f.write("##$FQ4LIST= <>\n")
            f.write("##$FQ5LIST= <>\n")
            f.write("##$FQ6LIST= <>\n")
            f.write("##$FQ7LIST= <>\n")
            f.write("##$FQ8LIST= <>\n")
            f.write("##$FRQLO3= 0\n")
            f.write("##$FRQLO3N= 0\n")
            f.write("##$FS= (0..7)\n")
            f.write("83 83 83 83 83 83 83 83\n")
            f.write("##$FTLPGN= 0\n")
            f.write("##$FW= 125000\n")
            f.write("##$FnMODE= 0\n")
            f.write("##$FnTYPE= 0\n")
            f.write("##$GPNAM= (0..31)\n")
            f.write("SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100\n")
            f.write("SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100\n")
            f.write("SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100\n")
            f.write("SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100 SINE.100\n")
            f.write("##$GPX= (0..31)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$GPY= (0..31)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$GPZ= (0..31)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$GRDPROG= <>\n")
            f.write("##$GRPDLY= -1\n")
            f.write("##$HDDUTY= 20\n")
            f.write("##$HDRATE= 1\n")
            f.write("##$HGAIN= (0..3)\n")
            f.write("0 0 0 0\n")
            f.write("##$HL1= 90\n")
            f.write("##$HL2= 90\n")
            f.write("##$HL3= 90\n")
            f.write("##$HL4= 90\n")
            f.write("##$HOLDER= 0\n")
            f.write("##$HPMOD= (0..7)\n")
            f.write("0 0 0 0 0 0 0 0\n")
            f.write("##$HPPRGN= 0\n")
            f.write("##$IN= (0..63)\n")
            f.write("0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001\n")
            f.write("0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001\n")
            f.write("0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001\n")
            f.write("0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001\n")
            f.write("##$INF= (0..7)\n")
            f.write("0.001 0.001 0.001 0.001 0.001 0.001 0.001 0.001\n")
            f.write("##$INP= (0..63)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$INSTRUM= <>\n")
            f.write("##$INTEGFAC= (0..63)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$L= (0..31)\n")
            f.write("1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1\n")
            f.write("##$LFILTER= 10\n")
            f.write("##$LGAIN= -10\n")
            f.write("##$LINPSTP= 0\n")
            f.write("##$LOCKED= no\n")
            f.write("##$LOCKFLD= 0\n")
            f.write("##$LOCKGN= 0\n")
            f.write("##$LOCKPOW= -20\n")
            f.write("##$LOCKPPM= 0\n")
            f.write("##$LOCNUC= <2H>\n")
            f.write("##$LOCPHAS= 0\n")
            f.write("##$LOCSHFT= no\n")
            f.write("##$LOCSW= 0\n")
            f.write("##$LTIME= 0.1\n")
            f.write("##$MASR= 4200\n")
            f.write("##$MASRLST= <>\n")
            f.write("##$MULEXPNO= (0..15)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$NBL= 1\n")
            f.write("##$NC= 0\n")
            f.write(f"##$NLOGCH= 1\n")
            f.write("##$NOVFLW= 0\n")
            f.write("##$NS= 1\n")
            f.write(f"##$NUC1= <{spectrum.nucleus}>\n")
            f.write("##$NUC2= <off>\n")
            f.write("##$NUC3= <off>\n")
            f.write("##$NUC4= <off>\n")
            f.write("##$NUC5= <off>\n")
            f.write("##$NUC6= <off>\n")
            f.write("##$NUC7= <off>\n")
            f.write("##$NUC8= <off>\n")
            f.write("##$NUCLEI= 0\n")
            f.write("##$NUCLEUS= <off>\n")
            f.write("##$O1= 0\n")
            f.write("##$O2= 0\n")
            f.write("##$O3= 0\n")
            f.write("##$O4= 0\n")
            f.write("##$O5= 0\n")
            f.write("##$O6= 0\n")
            f.write("##$O7= 0\n")
            f.write("##$O8= 0\n")
            f.write("##$OVERFLW= 0\n")
            f.write("##$P= (0..63)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$PACOIL= (0..15)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$PAPS= 0\n")
            f.write("##$PARMODE= 0\n")
            f.write("##$PCPD= (0..9)\n")
            f.write("0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$PEXSEL= (0..9)\n")
            f.write("1 1 1 1 1 1 1 1 1 1\n")
            f.write("##$PHCOR= (0..31)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$PHLIST= <>\n")
            f.write("##$PHP= 1\n")
            f.write("##$PH_ref= 0\n")
            f.write("##$PL= (0..63)\n")
            f.write("120 120 120 120 120 120 120 120 120 120 120 120 120 120 120 120\n")
            f.write("120 120 120 120 120 120 120 120 120 120 120 120 120 120 120 120\n")
            f.write("120 120 120 120 120 120 120 120 120 120 120 120 120 120 120 120\n")
            f.write("120 120 120 120 120 120 120 120 120 120 120 120 120 120 120 120\n")
            f.write("##$PLSTEP= 0.1\n")
            f.write("##$PLSTRT= -6\n")
            f.write("##$PLW= (0..63)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$POWMOD= 0\n")
            f.write("##$PQPHASE= 0\n")
            f.write("##$PQSCALE= 1\n")
            f.write("##$PR= 1\n")
            f.write("##$PRECHAN= (0..15)\n")
            f.write("-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1\n")
            f.write("##$PRGAIN= 0\n")
            f.write("##$PROBHD= <>\n")
            f.write("##$PROSOL= no\n")
            f.write("##$PULPROG= <zg30>\n")
            f.write("##$PW= 0\n")
            f.write("##$PYNM= <>\n")
            f.write("##$PYS= 0\n")
            f.write("##$QNP= 1\n")
            f.write("##$RD= 0\n")
            f.write("##$RECCHAN= (0..15)\n")
            f.write("0 1 2 3 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$RECPH= 0\n")
            f.write("##$RECPRE= (0..15)\n")
            f.write("-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1\n")
            f.write("##$RECPRFX= (0..15)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$RECSEL= (0..15)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$RG= 64\n")
            f.write("##$RO= 0\n")
            f.write("##$RSEL= (0..15)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$S= (0..7)\n")
            f.write("83 83 83 83 83 83 83 83\n")
            f.write("##$SELREC= (0..9)\n")
            f.write("0 0 0 0 0 0 0 0 0 0\n")
            f.write(f"##$SFO1= {spectrum.field_strength:.6f}\n")
            f.write("##$SFO2= 400.13\n")
            f.write("##$SFO3= 400.13\n")
            f.write("##$SFO4= 400.13\n")
            f.write("##$SFO5= 400.13\n")
            f.write("##$SFO6= 400.13\n")
            f.write("##$SFO7= 400.13\n")
            f.write("##$SFO8= 400.13\n")
            f.write("##$SOLVENT= <CDCl3>\n")
            f.write("##$SOLVOLD= <off>\n")
            f.write("##$SP= (0..31)\n")
            f.write("150 150 150 150 150 150 150 150 150 150 150 150 150 150 150 150\n")
            f.write("150 150 150 150 150 150 150 150 150 150 150 150 150 150 150 150\n")
            f.write("##$SP07= 0\n")
            f.write("##$SP47= 0\n")
            f.write("##$SPECTR= 0\n")
            f.write("##$SPINCNT= 0\n")
            f.write("##$SPNAM= (0..31)\n")
            f.write("<> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <> <>\n")
            f.write("##$SPOAL= (0..31)\n")
            f.write("0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5\n")
            f.write("0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5\n")
            f.write("##$SPOFFS= (0..31)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$SPPEX= (0..31)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$SPW= (0..63)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$SUBNAM= (0..9)\n")
            f.write("<> <> <> <> <> <> <> <> <> <>\n")
            f.write(f"##$SW= {(spectrum.ppm_range[1] - spectrum.ppm_range[0]) * spectrum.field_strength:.2f}\n")  # Sweep width in Hz
            f.write("##$SWIBOX= (0..19)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write(f"##$SW_h= {(spectrum.ppm_range[1] - spectrum.ppm_range[0]) * spectrum.field_strength:.2f}\n")
            f.write("##$TD= 65536\n")
            f.write("##$TD0= 1\n")
            f.write("##$TD_INDIRECT= (0..7)\n")
            f.write("0 0 0 0 0 0 0 0\n")
            f.write("##$TDav= 1\n")
            f.write("##$TE= 298\n")
            f.write("##$TE1= 300\n")
            f.write("##$TE2= 300\n")
            f.write("##$TE3= 300\n")
            f.write("##$TEG= 300\n")
            f.write("##$TL= (0..7)\n")
            f.write("120 120 120 120 120 120 120 120\n")
            f.write("##$TP= (0..7)\n")
            f.write("150 150 150 150 150 150 150 150\n")
            f.write("##$TP07= 0\n")
            f.write("##$TP47= 0\n")
            f.write("##$TPNAME0= <>\n")
            f.write("##$TPNAME1= <>\n")
            f.write("##$TPNAME2= <>\n")
            f.write("##$TPNAME3= <>\n")
            f.write("##$TPNAME4= <>\n")
            f.write("##$TPNAME5= <>\n")
            f.write("##$TPNAME6= <>\n")
            f.write("##$TPNAME7= <>\n")
            f.write("##$TPOAL= (0..7)\n")
            f.write("0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5\n")
            f.write("##$TPOFFS= (0..7)\n")
            f.write("0 0 0 0 0 0 0 0\n")
            f.write("##$TPW= (0..63)\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
            f.write("##$TUNHIN= 0\n")
            f.write("##$TUNHOUT= 0\n")
            f.write("##$TUNXOUT= 0\n")
            f.write("##$USERA1= <>\n")
            f.write("##$USERA2= <>\n")
            f.write("##$USERA3= <>\n")
            f.write("##$USERA4= <>\n")
            f.write("##$USERA5= <>\n")
            f.write("##$V9= 5\n")
            f.write("##$VALIST= <>\n")
            f.write("##$VCLIST= <>\n")
            f.write("##$VD= 0\n")
            f.write("##$VDLIST= <>\n")
            f.write("##$VENTMP= 300\n")
            f.write("##$VF= 0\n")
            f.write("##$VK= 0\n")
            f.write("##$VMWORK= 1.2e-06\n")
            f.write("##$VPLIST= <>\n")
            f.write("##$VTLIST= <>\n")
            f.write("##$WBST= 1024\n")
            f.write("##$WBSW= 4\n")
            f.write("##$XGAIN= (0..3)\n")
            f.write("0 0 0 0\n")
            f.write("##$XL= 0\n")
            f.write("##$YL= 0\n")
            f.write("##$YMAX_a= 0\n")
            f.write("##$YMIN_a= 0\n")
            f.write("##$ZGOPTNS= <>\n")
            f.write("##$ZL1= 120\n")
            f.write("##$ZL2= 120\n")
            f.write("##$ZL3= 120\n")
            f.write("##$ZL4= 120\n")
            f.write("##END=\n")
        
        # Create acqu file (without 's') - TopSpin specifically looks for this
        acqu_file = os.path.join(exp_dir, "acqu")
        with open(acqu_file, 'w') as f:
            # Copy the same content as acqus but with different header
            f.write("##TITLE= Parameter file, TopSpin 4.1.4\n")
            f.write("##JCAMPDX= 5.0\n")
            f.write("##DATATYPE= Parameter Values\n")
            f.write("##NPOINTS= 1\n")
            f.write("##ORIGIN= Bruker BioSpin GmbH\n")
            f.write("##OWNER= nmrsu\n")
            f.write(f"##$NUC1= <{spectrum.nucleus}>\n")
            f.write(f"##$SFO1= {spectrum.field_strength:.6f}\n")
            f.write(f"##$SW_h= {(spectrum.ppm_range[1] - spectrum.ppm_range[0]) * spectrum.field_strength:.2f}\n")
            f.write("##$TD= 65536\n")
            f.write("##$SOLVENT= <CDCl3>\n")
            f.write("##$NS= 1\n")
            f.write("##$TE= 298\n")
            f.write("##END=\n")
        
        # Create audita.txt (audit trail)
        audit_file = os.path.join(exp_dir, "audita.txt")
        with open(audit_file, 'w') as f:
            f.write("$$ Tue Aug 15 11:11:40 2025 +0200 (UT+2h)  nmrsu (LIN)\n")
            f.write("$$ /opt/topspin4.1.4/exp/stan/nmr/lists/pp/zg30\n")
            f.write("$$ process C:\\Bruker\\TopSpin4.1.4\\exp\\stan\\nmr\\py\\TopSpin_Atma\\acqu_par.py (C:\\Bruker\\TopSpin4.1.4\\python\\TopSpin_Atma\\acqu_par.py)\n")
            f.write("$$ Tue Aug 15 11:11:40 2025 +0200 (UT+2h)  nmrsu (LIN)\n")
            f.write("$$ NMR Simulator Export\n")
        
        # Create format.temp file (display format parameters)
        format_file = os.path.join(pdata_dir, "format.temp")
        with open(format_file, 'w') as f:
            f.write("##TITLE= Parameter file, TopSpin 4.1.4\n")
            f.write("##JCAMPDX= 5.0\n")
            f.write("##DATATYPE= Parameter Values\n")
            f.write("##NPOINTS= 1\n")
            f.write("##ORIGIN= Bruker BioSpin GmbH\n")
            f.write("##OWNER= nmrsu\n")
            f.write("##$ABSF1= 0\n")
            f.write("##$ABSF2= 0\n")
            f.write("##$ABSG= 0\n")
            f.write("##$ABSL= 0\n")
            f.write("##$BYTORDP= 1\n")
            f.write("##$DATMOD= 1\n")
            f.write("##$DTYPP= 0\n")
            f.write("##$LAYOUT= <+/1D_X32_Y32_Z32_A32_B32_C32_D32.xwp>\n")
            f.write("##$NC_proc= -4\n")
            f.write("##$PPARMOD= 0\n")
            f.write(f"##$SF= {spectrum.field_strength:.6f}\n")
            f.write(f"##$SI= {len(spectrum.data_points)}\n")
            f.write("##$XDIM= 8192\n")
            f.write("##END=\n")
        
        # Create outd file (output parameters)
        outd_file = os.path.join(pdata_dir, "outd")
        with open(outd_file, 'w') as f:
            f.write("##TITLE= Parameter file, TopSpin 4.1.4\n")
            f.write("##JCAMPDX= 5.0\n")
            f.write("##DATATYPE= Parameter Values\n")
            f.write("##NPOINTS= 1\n")
            f.write("##ORIGIN= Bruker BioSpin GmbH\n")
            f.write("##OWNER= nmrsu\n")
            f.write("##$CURPLOT= <>\n")
            f.write("##$CURPRIN= <>\n")
            f.write("##$DFORMAT= <normdp>\n")
            f.write("##$LAYOUT= <+/1D_X32_Y32_Z32_A32_B32_C32_D32.xwp>\n")
            f.write("##$LFORMAT= <normlp>\n")
            f.write("##$PFORMAT= <normpl>\n")
            f.write("##END=\n")
        
        self._log(f"✅ Bruker export completed successfully!")
        self._log(f"📁 Created: {experiment_name}")
        self._log(f"📂 Files: 1r, proc, procs, acqus, acqu, format.temp, outd, audita.txt")
        
        return experiment_name
    
    def _create_ascii_export(self, spectrum, filename):
        """Create ASCII export with proper formatting."""
        import datetime
        
        with open(filename, 'w') as f:
            # Header
            f.write(f"# NMR Simulator ASCII Export\n")
            f.write(f"# Nucleus: {spectrum.nucleus}\n")
            f.write(f"# Field Strength: {spectrum.field_strength} MHz\n")
            f.write(f"# Data Points: {len(spectrum.data_points)}\n")
            f.write(f"# PPM Range: {spectrum.ppm_range[0]:.3f} to {spectrum.ppm_range[1]:.3f}\n")
            f.write(f"# Resolution: {int(self.resolution_var.get())}\n")
            f.write(f"# Noise Level: {self.noise_var.get()*100:.1f}%\n")
            f.write(f"# Export Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("#\n")
            f.write("# Format: PPM<tab>Intensity\n")
            f.write("#\n")
            
            # Data
            for ppm, intensity in zip(spectrum.ppm_axis, spectrum.data_points):
                f.write(f"{ppm:.6f}\t{intensity:.6f}\n")
    
    def _show_peak_list(self):
        """Show editable peak list with width control."""
        if not self.current_spectra:
            messagebox.showinfo("No Data", "No spectra loaded.")
            return
        
        nucleus = self.nucleus_var.get()
        spectrum = None
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            messagebox.showinfo("No Data", f"No {nucleus} spectrum found.")
            return
        
        # Create peak list window
        peak_window = tk.Toplevel(self.root)
        peak_window.title(f"📊 {nucleus} NMR Peak Editor")
        peak_window.geometry("800x600")
        
        # Instructions frame
        info_frame = ttk.LabelFrame(peak_window, text="💡 Peak Editor", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        info_text = """Double-click any value to edit: Chemical Shift (ppm), Width (Hz), Multiplicity, Integration, or J-coupling.
Examples: Width 15-25 Hz for NH • Multiplicity: s, d, t, q, m, br s • Integration: 1H, 2H, 3H • J-coupling: 7.5, 8.2"""
        ttk.Label(info_frame, text=info_text, wraplength=750).pack()
        
        # Create treeview for editable peak list
        tree_frame = tk.Frame(peak_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview with columns
        columns = ("Peak", "δ (ppm)", "Width (Hz)", "Multiplicity", "Integration", "J-coupling")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        tree.heading("Peak", text="Peak")
        tree.heading("δ (ppm)", text="δ (ppm)")
        tree.heading("Width (Hz)", text="Width (Hz)")
        tree.heading("Multiplicity", text="Multiplicity")
        tree.heading("Integration", text="Integration")
        tree.heading("J-coupling", text="J-coupling (Hz)")
        
        tree.column("Peak", width=50, anchor=tk.CENTER)
        tree.column("δ (ppm)", width=90, anchor=tk.CENTER)
        tree.column("Width (Hz)", width=90, anchor=tk.CENTER)
        tree.column("Multiplicity", width=90, anchor=tk.CENTER)
        tree.column("Integration", width=90, anchor=tk.CENTER)
        tree.column("J-coupling", width=130, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar_tree = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_tree.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bulk operations frame - NEW FEATURE
        bulk_frame = ttk.LabelFrame(peak_window, text="🔧 Bulk Operations", padding=10)
        bulk_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Bulk linewidth modification
        bulk_linewidth_frame = ttk.Frame(bulk_frame)
        bulk_linewidth_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(bulk_linewidth_frame, text="Set ALL linewidths to:").pack(side=tk.LEFT, padx=(0, 5))
        
        bulk_linewidth_var = tk.StringVar(value="2.0")
        bulk_linewidth_entry = ttk.Entry(bulk_linewidth_frame, textvariable=bulk_linewidth_var, width=8)
        bulk_linewidth_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(bulk_linewidth_frame, text="Hz").pack(side=tk.LEFT, padx=(0, 10))
        
        def apply_bulk_linewidth():
            try:
                new_width_hz = float(bulk_linewidth_var.get())
                if new_width_hz <= 0 or new_width_hz > 100:
                    raise ValueError("Linewidth should be between 0.1-100 Hz")
                
                # Apply to all peaks
                new_width_ppm = new_width_hz / 400  # Convert Hz to ppm
                for peak in sorted_peaks:
                    peak.width = new_width_ppm
                
                # Update tree display
                for item_id, peak in peak_items.items():
                    tree.set(item_id, "Width (Hz)", f"{new_width_hz:.1f}")
                
                self._log(f"Applied linewidth {new_width_hz:.1f} Hz to all {len(sorted_peaks)} peaks")
                self.root.after(100, self._update_plot)
                
            except ValueError as e:
                messagebox.showerror("Invalid Input", f"Please enter a valid linewidth.\nError: {e}")
        
        ttk.Button(bulk_linewidth_frame, text="Apply to All Peaks", 
                  command=apply_bulk_linewidth).pack(side=tk.LEFT, padx=(0, 10))
        
        # Quick preset buttons for common linewidths
        presets_frame = ttk.Frame(bulk_linewidth_frame)
        presets_frame.pack(side=tk.LEFT)
        
        linewidth_presets = [("Sharp", "0.5"), ("Normal", "1.2"), ("Broad", "2.5"), ("Very Broad", "5.0")]
        for name, width in linewidth_presets:
            btn = ttk.Button(presets_frame, text=f"{name}\n{width} Hz", width=8,
                            command=lambda w=width: [bulk_linewidth_var.set(w), apply_bulk_linewidth()])
            btn.pack(side=tk.LEFT, padx=1)
        
        # Additional bulk operations
        bulk_other_frame = ttk.Frame(bulk_frame)
        bulk_other_frame.pack(fill=tk.X, pady=(5, 0))
        
        def reset_all_integrations():
            for peak in sorted_peaks:
                peak.integration = 1.0
            for item_id, peak in peak_items.items():
                tree.set(item_id, "Integration", "1.0H")
            self._log(f"Reset all integrations to 1.0H")
            self.root.after(100, self._update_plot)
        
        ttk.Button(bulk_other_frame, text="Reset All Integrations → 1H", 
                  command=reset_all_integrations).pack(side=tk.LEFT, padx=(0, 10))
        
        def sort_peaks_by_shift():
            # Re-populate tree with sorted peaks
            for item in tree.get_children():
                tree.delete(item)
            
            sorted_peaks_new = sorted(spectrum.peaks, key=lambda p: p.chemical_shift, reverse=True)
            peak_items.clear()
            
            for i, peak in enumerate(sorted_peaks_new, 1):
                j_values = ", ".join(f"{j:.1f}" for j in peak.coupling_constants) if peak.coupling_constants else "-"
                width_hz = peak.width * 400
                
                item = tree.insert("", tk.END, values=(
                    f"{i:2d}",
                    f"{peak.chemical_shift:.3f}",
                    f"{width_hz:.1f}",
                    peak.multiplicity,
                    f"{peak.integration:.1f}H",
                    j_values
                ))
                peak_items[item] = peak
                
            self._log("Peaks re-sorted by chemical shift")
        
        ttk.Button(bulk_other_frame, text="Sort by Chemical Shift", 
                  command=sort_peaks_by_shift).pack(side=tk.LEFT, padx=(0, 10))
        
        # Populate tree with peak data
        sorted_peaks = sorted(spectrum.peaks, key=lambda p: p.chemical_shift, reverse=True)
        peak_items = {}  # Store tree items for updating
        
        for i, peak in enumerate(sorted_peaks, 1):
            j_values = ", ".join(f"{j:.1f}" for j in peak.coupling_constants) if peak.coupling_constants else "-"
            width_hz = peak.width * 400  # Convert from ppm to Hz
            
            item = tree.insert("", tk.END, values=(
                f"{i:2d}",
                f"{peak.chemical_shift:.3f}",
                f"{width_hz:.1f}",
                peak.multiplicity,
                f"{peak.integration:.1f}H",
                j_values
            ))
            peak_items[item] = peak
        
        # Edit functionality for all values
        def on_double_click(event):
            """Handle double-click for editing any peak parameter."""
            item = tree.identify('item', event.x, event.y)
            column = tree.identify('column', event.x, event.y)
            
            if not item:
                return
                
            peak = peak_items[item]
            column_names = ["Peak", "δ (ppm)", "Width (Hz)", "Multiplicity", "Integration", "J-coupling"]
            col_index = int(column.replace('#', '')) - 1
            
            if col_index == 0:  # Peak number - not editable
                return
                
            # Create edit dialog
            edit_window = tk.Toplevel(peak_window)
            edit_window.title(f"Edit {column_names[col_index]}")
            edit_window.geometry("400x300")
            edit_window.grab_set()  # Modal dialog
            edit_window.transient(peak_window)
            
            ttk.Label(edit_window, text=f"Peak at δ {peak.chemical_shift:.3f} ppm", 
                     font=("Arial", 12, "bold")).pack(pady=10)
            
            if col_index == 1:  # Chemical Shift
                ttk.Label(edit_window, text="New chemical shift (ppm):").pack(pady=5)
                current_value = f"{peak.chemical_shift:.3f}"
                value_var = tk.StringVar(value=current_value)
                value_entry = ttk.Entry(edit_window, textvariable=value_var, justify=tk.CENTER)
                value_entry.pack(pady=5)
                
                # Quick presets for common regions
                presets_frame = ttk.Frame(edit_window)
                presets_frame.pack(pady=10)
                ttk.Label(presets_frame, text="Common regions:", font=("Arial", 9)).pack()
                preset_frame = ttk.Frame(presets_frame)
                preset_frame.pack()
                
                presets = [("Aromatic", "7.3"), ("NH", "8.5"), ("CHO", "9.8"), ("Alkyl", "2.5"), ("CH3", "1.2")]
                for name, value in presets:
                    btn = ttk.Button(preset_frame, text=f"{name}\n{value}", width=8,
                                   command=lambda v=value: value_var.set(v))
                    btn.pack(side=tk.LEFT, padx=2)
                
                def apply_edit():
                    try:
                        new_shift = float(value_var.get())
                        if new_shift < 0 or new_shift > 20:
                            raise ValueError("Chemical shift should be between 0-20 ppm")
                        peak.chemical_shift = new_shift
                        tree.set(item, "δ (ppm)", f"{new_shift:.3f}")
                        self.root.after(100, self._update_plot)
                        edit_window.destroy()
                    except ValueError as e:
                        messagebox.showerror("Invalid Input", f"Please enter a valid chemical shift.\nError: {e}")
            
            elif col_index == 2:  # Width (Hz)
                ttk.Label(edit_window, text="New linewidth (Hz):").pack(pady=5)
                current_width = peak.width * 400  # Convert to Hz
                value_var = tk.StringVar(value=f"{current_width:.1f}")
                value_entry = ttk.Entry(edit_window, textvariable=value_var, justify=tk.CENTER)
                value_entry.pack(pady=5)
                
                # Width presets
                presets_frame = ttk.Frame(edit_window)
                presets_frame.pack(pady=10)
                ttk.Label(presets_frame, text="Quick presets:", font=("Arial", 9)).pack()
                preset_frame = ttk.Frame(presets_frame)
                preset_frame.pack()
                
                presets = [("Sharp", 2), ("Normal", 5), ("Broad", 15), ("NH", 25), ("Very Broad", 40)]
                for name, hz_value in presets:
                    btn = ttk.Button(preset_frame, text=f"{name}\n({hz_value} Hz)", width=8,
                                   command=lambda v=hz_value: value_var.set(str(v)))
                    btn.pack(side=tk.LEFT, padx=2)
                
                def apply_edit():
                    try:
                        new_width_hz = float(value_var.get())
                        if new_width_hz <= 0:
                            raise ValueError("Width must be positive")
                        peak.width = new_width_hz / 400.0  # Convert to ppm
                        tree.set(item, "Width (Hz)", f"{new_width_hz:.1f}")
                        self.root.after(100, self._update_plot)
                        edit_window.destroy()
                    except ValueError as e:
                        messagebox.showerror("Invalid Input", f"Please enter a valid positive number.\nError: {e}")
            
            elif col_index == 3:  # Multiplicity
                ttk.Label(edit_window, text="New multiplicity:").pack(pady=5)
                value_var = tk.StringVar(value=peak.multiplicity)
                value_entry = ttk.Entry(edit_window, textvariable=value_var, justify=tk.CENTER)
                value_entry.pack(pady=5)
                
                # Multiplicity presets
                presets_frame = ttk.Frame(edit_window)
                presets_frame.pack(pady=10)
                ttk.Label(presets_frame, text="Common multiplicities:", font=("Arial", 9)).pack()
                preset_frame = ttk.Frame(presets_frame)
                preset_frame.pack()
                
                presets = [("s", "s"), ("d", "d"), ("t", "t"), ("q", "q"), ("m", "m"), ("br s", "br s")]
                for name, mult in presets:
                    btn = ttk.Button(preset_frame, text=name, width=6,
                                   command=lambda v=mult: value_var.set(v))
                    btn.pack(side=tk.LEFT, padx=2)
                
                def apply_edit():
                    try:
                        new_mult = value_var.get().strip()
                        if not new_mult:
                            raise ValueError("Multiplicity cannot be empty")
                        peak.multiplicity = new_mult
                        tree.set(item, "Multiplicity", new_mult)
                        self.root.after(100, self._update_plot)
                        edit_window.destroy()
                    except ValueError as e:
                        messagebox.showerror("Invalid Input", f"Please enter a valid multiplicity.\nError: {e}")
            
            elif col_index == 4:  # Integration
                ttk.Label(edit_window, text="New integration (number of H):").pack(pady=5)
                value_var = tk.StringVar(value=str(int(peak.integration)))
                value_entry = ttk.Entry(edit_window, textvariable=value_var, justify=tk.CENTER)
                value_entry.pack(pady=5)
                
                # Integration presets
                presets_frame = ttk.Frame(edit_window)
                presets_frame.pack(pady=10)
                ttk.Label(presets_frame, text="Common integrations:", font=("Arial", 9)).pack()
                preset_frame = ttk.Frame(presets_frame)
                preset_frame.pack()
                
                presets = [("1H", "1"), ("2H", "2"), ("3H", "3"), ("4H", "4"), ("5H", "5"), ("6H", "6")]
                for name, integ in presets:
                    btn = ttk.Button(preset_frame, text=name, width=6,
                                   command=lambda v=integ: value_var.set(v))
                    btn.pack(side=tk.LEFT, padx=2)
                
                def apply_edit():
                    try:
                        new_integ = float(value_var.get())
                        if new_integ <= 0:
                            raise ValueError("Integration must be positive")
                        peak.integration = new_integ
                        tree.set(item, "Integration", f"{new_integ:.1f}H")
                        self.root.after(100, self._update_plot)
                        edit_window.destroy()
                    except ValueError as e:
                        messagebox.showerror("Invalid Input", f"Please enter a valid positive number.\nError: {e}")
            
            elif col_index == 5:  # J-coupling
                ttk.Label(edit_window, text="J-coupling constants (Hz, comma-separated):").pack(pady=5)
                current_j = ", ".join(f"{j:.1f}" for j in peak.coupling_constants) if peak.coupling_constants else ""
                value_var = tk.StringVar(value=current_j)
                value_entry = ttk.Entry(edit_window, textvariable=value_var, justify=tk.CENTER)
                value_entry.pack(pady=5)
                
                ttk.Label(edit_window, text="Examples: 7.5  or  7.5, 1.2  or  8.0, 2.1, 0.5", 
                         font=("Arial", 9)).pack(pady=5)
                
                # J-coupling presets
                presets_frame = ttk.Frame(edit_window)
                presets_frame.pack(pady=10)
                ttk.Label(presets_frame, text="Common J-values:", font=("Arial", 9)).pack()
                preset_frame = ttk.Frame(presets_frame)
                preset_frame.pack()
                
                presets = [("Ortho", "7.5"), ("Meta", "2.0"), ("Triplet", "7.0"), ("Clear", "")]
                for name, j_val in presets:
                    btn = ttk.Button(preset_frame, text=name, width=8,
                                   command=lambda v=j_val: value_var.set(v))
                    btn.pack(side=tk.LEFT, padx=2)
                
                def apply_edit():
                    try:
                        j_text = value_var.get().strip()
                        if j_text:
                            # Parse comma-separated J values
                            j_values = [float(j.strip()) for j in j_text.split(',') if j.strip()]
                            peak.coupling_constants = j_values
                            j_display = ", ".join(f"{j:.1f}" for j in j_values)
                        else:
                            peak.coupling_constants = []
                            j_display = "-"
                        
                        tree.set(item, "J-coupling", j_display)
                        self.root.after(100, self._update_plot)
                        edit_window.destroy()
                    except ValueError as e:
                        messagebox.showerror("Invalid Input", f"Please enter valid J-coupling values.\nError: {e}")
            
            value_entry.select_range(0, tk.END)
            value_entry.focus()
            
            # Buttons
            btn_frame = ttk.Frame(edit_window)
            btn_frame.pack(pady=15)
            
            ttk.Button(btn_frame, text="Apply", command=apply_edit).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)
            
            # Bind Enter key
            value_entry.bind('<Return>', lambda e: apply_edit())
        
        tree.bind("<Double-1>", on_double_click)
        
        # Button frame
        btn_frame = ttk.Frame(peak_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Quick editing buttons
        ttk.Label(btn_frame, text="Quick adjustments:").pack(side=tk.LEFT, padx=5)
        
        def set_broad_nh():
            """Set all peaks above 8 ppm to broad NH width."""
            count = 0
            for item, peak in peak_items.items():
                if peak.chemical_shift > 8.0:
                    peak.width = 20.0 / 400.0  # 20 Hz
                    peak.multiplicity = "br s"  # Broad singlet
                    tree.set(item, "Width (Hz)", "20.0")
                    tree.set(item, "Multiplicity", "br s")
                    count += 1
            if count > 0:
                self.root.after(100, self._update_plot)
                messagebox.showinfo("Applied", f"Set {count} peaks > 8 ppm to broad NH (20 Hz, br s)")
        
        def normalize_aromatic():
            """Normalize aromatic peaks (7-8 ppm) to 1H integration."""
            count = 0
            for item, peak in peak_items.items():
                if 7.0 <= peak.chemical_shift <= 8.0:
                    peak.integration = 1.0
                    tree.set(item, "Integration", "1.0H")
                    count += 1
            if count > 0:
                self.root.after(100, self._update_plot)
                messagebox.showinfo("Applied", f"Set {count} aromatic peaks to 1H integration")
        
        def reset_widths():
            """Reset all widths to automatic values."""
            for item, peak in peak_items.items():
                # Automatic width based on chemical shift and multiplicity
                is_broad = 'br' in peak.multiplicity.lower()
                if is_broad:
                    auto_width = 15.0 if peak.chemical_shift > 7.0 else 8.0
                else:
                    auto_width = 3.0 if peak.chemical_shift > 7.0 else 2.0
                
                peak.width = auto_width / 400.0
                tree.set(item, "Width (Hz)", f"{auto_width:.1f}")
            
            self.root.after(100, self._update_plot)
            messagebox.showinfo("Reset", "All peak widths reset to automatic values")
        
        def add_new_peak():
            """Add a new peak to the spectrum."""
            add_window = tk.Toplevel(peak_window)
            add_window.title("Add New Peak")
            add_window.geometry("300x400")
            add_window.grab_set()
            add_window.transient(peak_window)
            
            ttk.Label(add_window, text="Add New Peak", font=("Arial", 12, "bold")).pack(pady=10)
            
            # Input fields
            fields = {}
            field_names = [
                ("Chemical Shift (ppm):", "7.25"),
                ("Multiplicity:", "s"),
                ("Integration (H):", "1"),
                ("Linewidth (Hz):", "3"),
                ("J-coupling (Hz):", "")
            ]
            
            for label, default in field_names:
                frame = ttk.Frame(add_window)
                frame.pack(fill=tk.X, padx=20, pady=5)
                ttk.Label(frame, text=label).pack(side=tk.LEFT)
                var = tk.StringVar(value=default)
                entry = ttk.Entry(frame, textvariable=var)
                entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                fields[label.split()[0].lower()] = var
            
            def add_peak():
                try:
                    from nmr_simulator.spectrum import Peak
                    
                    shift = float(fields['chemical'].get())
                    mult = fields['multiplicity'].get()
                    integ = float(fields['integration'].get())
                    width_hz = float(fields['linewidth'].get())
                    j_text = fields['j-coupling'].get().strip()
                    
                    # Parse J-coupling
                    j_values = [float(j.strip()) for j in j_text.split(',') if j.strip()] if j_text else []
                    
                    # Create new peak
                    new_peak = Peak(
                        chemical_shift=shift,
                        intensity=100,
                        width=width_hz / 400.0,  # Convert to ppm
                        multiplicity=mult,
                        coupling_constants=j_values,
                        integration=integ
                    )
                    
                    # Add to spectrum
                    spectrum.add_peak(new_peak)
                    
                    # Update tree
                    j_display = ", ".join(f"{j:.1f}" for j in j_values) if j_values else "-"
                    new_item = tree.insert("", tk.END, values=(
                        f"{len(spectrum.peaks):2d}",
                        f"{shift:.3f}",
                        f"{width_hz:.1f}",
                        mult,
                        f"{integ:.1f}H",
                        j_display
                    ))
                    peak_items[new_item] = new_peak
                    
                    # Update plot
                    self.root.after(100, self._update_plot)
                    add_window.destroy()
                    
                except ValueError as e:
                    messagebox.showerror("Invalid Input", f"Please check your input values.\nError: {e}")
            
            btn_frame_add = ttk.Frame(add_window)
            btn_frame_add.pack(pady=15)
            ttk.Button(btn_frame_add, text="Add Peak", command=add_peak).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame_add, text="Cancel", command=add_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Batch operation buttons
        ttk.Button(btn_frame, text="Broaden NH (>8 ppm)", command=set_broad_nh).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Normalize Aromatic", command=normalize_aromatic).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Reset Widths", command=reset_widths).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Add Peak", command=add_new_peak).pack(side=tk.LEFT, padx=2)
        
        # Close button
        ttk.Button(btn_frame, text="Close", command=peak_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _clear_data(self):
        """Clear all current data."""
        if self.current_spectra or self.current_molecule:
            result = messagebox.askyesno(
                "Clear Data",
                "Are you sure you want to clear all current NMR data?",
                icon='question'
            )
            if result:
                self.current_spectra = []
                self.current_molecule = None
                self._setup_empty_plot()
                self._update_info_display()
                self._log("All data cleared")
        else:
            messagebox.showinfo("No Data", "No data to clear.")
    
    def _clear_log(self):
        """Clear the status log."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _reset_zoom(self):
        """Reset plot zoom to default."""
        if self.current_spectra:
            self._update_plot()
    
    def _show_help(self):
        """Show comprehensive help dialog."""
        try:
            from help_dialog import show_help_dialog
            show_help_dialog(self.root)
        except ImportError:
            messagebox.showinfo("Help", 
                "Help features:\n\n"
                "• Show Integrals: Display integration curves\n"
                "• Show Labels: Display chemical shift values\n" 
                "• Show Assignments: Display letter assignments (A,B,C...)\n"
                "• Show Fine Structure: Display coupling patterns\n\n"
                "InChI: Provides structural analysis and enhanced predictions\n\n"
                "Data formats: Standard (7.36 (s, 5H)), Assignment (A 7.6), Tabulated")
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """Enhanced NMR Spectra Simulator v2.0

Features:
• Interactive spectrum visualization
• Real-time plot updates
• SDBS database search (demo mode)
• Multiple export formats (PNG, PDF, SVG, CSV)
• Professional NMR reports
• Peak labeling and analysis

Built with Python, matplotlib, and tkinter
For educational and research purposes"""
        
        messagebox.showinfo("About NMR Simulator", about_text)
    
    def _group_peaks(self):
        """Group individual multiplet lines into proper NMR peaks."""
        if not self.current_spectra:
            messagebox.showinfo("No Data", "No spectra loaded.")
            return
        
        nucleus = self.nucleus_var.get()
        spectrum = None
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            messagebox.showinfo("No Data", f"No {nucleus} spectrum found.")
            return
        
        # Convert current peaks to the format expected by the grouper
        peak_data = []
        for peak in spectrum.peaks:
            peak_data.append({
                'shift': peak.chemical_shift,
                'intensity': peak.intensity,
                'multiplicity': getattr(peak, 'multiplicity', 's'),
                'coupling': getattr(peak, 'coupling_constants', []),
                'integration': getattr(peak, 'integration', 1.0)
            })
        
        # Import and use the peak grouper
        try:
            from peak_grouper import create_peak_grouping_dialog
            
            # Check if we have assignment data
            assignment_data = None
            # You could add assignment data from your molecule if available
            
            result = create_peak_grouping_dialog(self.root, peak_data, assignment_data)
            
            if result['apply'] and result['grouped_peaks']:
                # Replace current spectrum with grouped peaks
                self._apply_grouped_peaks(spectrum, result['grouped_peaks'])
                self._log(f"Grouped {len(peak_data)} peaks into {len(result['grouped_peaks'])} multiplets")
                self.root.after(100, self._update_plot)
                
        except ImportError as e:
            messagebox.showerror("Import Error", f"Could not import peak grouper: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error in peak grouping: {e}")
    
    def _simple_group_peaks(self):
        """Simple grouping of nearby peaks without multiplicity assignment."""
        if not self.current_spectra:
            messagebox.showinfo("No Data", "No spectra loaded.")
            return
        
        nucleus = self.nucleus_var.get()
        spectrum = None
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            messagebox.showinfo("No Data", f"No {nucleus} spectrum found.")
            return
        
        # Convert current peaks to the format expected by the grouper
        peak_data = []
        for peak in spectrum.peaks:
            peak_data.append({
                'shift': peak.chemical_shift,
                'intensity': peak.intensity,
                'multiplicity': 's',  # Keep as singlets
                'coupling': [],
                'integration': getattr(peak, 'integration', 1.0)
            })
        
        # Simple proximity grouping without external dependencies
        tolerance_ppm = 0.1  # Group peaks within 0.1 ppm
        sorted_peaks = sorted(peak_data, key=lambda p: p.get('shift', 0), reverse=True)
        
        groups = []
        current_group = []
        
        for peak in sorted_peaks:
            if not current_group:
                current_group = [peak]
            else:
                # Check if peak is close enough to the last peak in current group
                last_shift = current_group[-1]['shift']
                if abs(peak['shift'] - last_shift) <= tolerance_ppm:
                    current_group.append(peak)
                else:
                    # Start new group
                    groups.append(current_group)
                    current_group = [peak]
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        # Convert groups to simple averaged peaks
        simple_peaks = []
        for group in groups:
            if len(group) == 1:
                # Single peak - keep as is
                simple_peaks.append(group[0])
            else:
                # Multiple peaks - average shift, sum intensity, keep as singlet
                avg_shift = sum(p['shift'] for p in group) / len(group)
                total_intensity = sum(p['intensity'] for p in group)
                simple_peaks.append({
                    'shift': avg_shift,
                    'intensity': total_intensity,
                    'multiplicity': 's',  # Always singlet for simple grouping
                    'coupling': [],
                    'integration': len(group),  # Number of grouped lines as integer
                    'linewidth': 0.003,  # Narrow linewidth
                    'original_peaks': len(group)
                })
        
        # Apply the simplified peaks
        self._apply_grouped_peaks(spectrum, simple_peaks)
        self._log(f"Simple grouping: {len(peak_data)} peaks → {len(simple_peaks)} groups")
        self.root.after(100, self._update_plot)
    
    def _non_destructive_group_peaks(self):
        """Non-destructive grouping that preserves all original peaks with group annotations."""
        if not self.current_spectra:
            messagebox.showinfo("No Data", "No spectra loaded.")
            return
        
        nucleus = self.nucleus_var.get()
        spectrum = None
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            messagebox.showinfo("No Data", f"No {nucleus} spectrum found.")
            return
        
        try:
            # Convert current peaks to the format expected by the non-destructive grouper
            peak_data = []
            for peak in spectrum.peaks:
                peak_data.append({
                    'shift': peak.chemical_shift,
                    'intensity': peak.intensity,
                    'linewidth': getattr(peak, 'linewidth', 0.003)
                })
            
            # Reset grouper assignments to start fresh
            self.non_destructive_grouper.reset_assignments()
            
            # Perform non-destructive grouping
            tolerance = 0.1  # Default tolerance in ppm
            annotated_peaks, groups = self.non_destructive_grouper.group_peaks_by_proximity(
                peak_data, tolerance_ppm=tolerance)
            
            # Apply the annotated peaks (preserves all original peaks)
            self._apply_non_destructive_groups(spectrum, annotated_peaks, groups)
            
            # Show grouping summary
            summary = self.non_destructive_grouper.get_group_summary(groups)
            self._log(f"Non-destructive grouping: {len(peak_data)} peaks preserved in {len(groups)} groups")
            self._log(summary)
            
            # Show detailed dialog with group information
            self._show_group_summary_dialog(groups, annotated_peaks)
            
            self.root.after(100, self._update_plot)
            
        except Exception as e:
            self._log(f"Error in non-destructive grouping: {e}")
            messagebox.showerror("Error", f"Error in non-destructive grouping: {e}")
    
    def _apply_non_destructive_groups(self, spectrum, annotated_peaks, groups):
        """Apply non-destructive grouping results to the spectrum."""
        from nmr_simulator.spectrum import Peak
        
        # Clear existing peaks
        spectrum.peaks.clear()
        
        # Add all annotated peaks (preserves original data)
        for peak_data in annotated_peaks:
            # Create peak with correct parameters only
            peak = Peak(
                chemical_shift=peak_data['shift'],
                intensity=peak_data['intensity'],
                width=peak_data.get('linewidth', 0.003),  # Use 'width' not 'linewidth'
                integration=peak_data.get('group_integration', 1),
                multiplicity=peak_data.get('group_multiplicity', 's'),
                coupling_constants=peak_data.get('group_coupling', [])
            )
            
            # Add group metadata as attributes (not constructor parameters)
            peak.group_id = peak_data.get('group_id', -1)
            peak.group_center = peak_data.get('group_center', peak_data['shift'])
            peak.is_group_center = peak_data.get('is_group_center', False)
            peak.assignment = peak_data.get('group_assignment', '')  # Add as attribute
            
            spectrum.peaks.append(peak)
    
    def _show_group_summary_dialog(self, groups, annotated_peaks):
        """Show a dialog with detailed group summary."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Peak Grouping Summary")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create text widget for summary
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap='word')
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        text_widget.pack(side='left', fill='both', expand=True)
        
        # Generate detailed summary
        summary = f"Peak Grouping Results:\n"
        summary += f"{'='*50}\n\n"
        summary += f"Total original peaks: {len(annotated_peaks)}\n"
        summary += f"Number of groups: {len(groups)}\n\n"
        
        summary += "Group Details:\n"
        for group in groups:
            coupling_str = ""
            if group.coupling_constants:
                coupling_str = f", J = {', '.join(f'{j:.1f}' for j in group.coupling_constants)} Hz"
            
            summary += (f"\n{group.assignment}: {group.center_shift:.3f} ppm "
                       f"({group.multiplicity}{coupling_str}, {group.integration}H)\n")
            summary += f"  Contains {len(group.peak_indices)} peaks: "
            
            # List individual peaks in this group
            group_shifts = []
            for peak_idx in group.peak_indices:
                group_shifts.append(f"{annotated_peaks[peak_idx]['shift']:.3f}")
            summary += ", ".join(group_shifts) + " ppm\n"
        
        text_widget.insert('1.0', summary)
        text_widget.config(state='disabled')
        
        # Add close button
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack()
        
        # Center dialog on parent
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def _visual_multiplet_grouping(self):
        """Create visual multiplet groups for teaching purposes."""
        if not self.current_spectra:
            messagebox.showinfo("No Data", "No spectra loaded.")
            return
        
        nucleus = self.nucleus_var.get()
        spectrum = None
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            messagebox.showinfo("No Data", f"No {nucleus} spectrum found.")
            return
        
        # Create tolerance dialog
        tolerance_dialog = tk.Toplevel(self.root)
        tolerance_dialog.title("Visual Multiplet Grouping Settings")
        tolerance_dialog.geometry("400x200")
        
        # Center the dialog
        tolerance_dialog.transient(self.root)
        tolerance_dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(tolerance_dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tolerance setting
        ttk.Label(main_frame, text="Detection Width (ppm):").pack(pady=(0, 5))
        tolerance_var = tk.DoubleVar(value=0.05)
        tolerance_spin = ttk.Spinbox(main_frame, from_=0.05, to=1.0, increment=0.05, 
                                   textvariable=tolerance_var, width=10)
        tolerance_spin.pack(pady=(0, 10))
        
        # Help text
        help_text = ("Adjust the detection width to control grouping sensitivity.\n"
                    "Smaller values create more separate groups.\n"
                    "Larger values merge more peaks into groups.")
        ttk.Label(main_frame, text=help_text, foreground="gray").pack(pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def apply_grouping():
            tolerance = tolerance_var.get()
            try:
                # Convert current peaks to the format expected by the visual grouper
                peak_data = []
                for peak in spectrum.peaks:
                    peak_data.append({
                        'shift': peak.chemical_shift,
                        'intensity': peak.intensity,
                        'linewidth': getattr(peak, 'width', 0.003)
                    })
                
                # Create visual groups with user-specified tolerance
                print(f"DEBUG: Before grouping - {len(peak_data)} peaks")
                annotated_peaks, visual_groups = self.visual_grouper.create_visual_groups(
                    peak_data, nucleus=nucleus, tolerance_ppm=tolerance)
                print(f"DEBUG: After grouping - {len(annotated_peaks)} annotated peaks")
                
                # Apply the visual grouping (preserves all peaks + adds visual group info)
                self._apply_visual_groups(spectrum, annotated_peaks, visual_groups)
                print(f"DEBUG: After applying - {len(spectrum.peaks)} final peaks")
                
                # Show visual grouping summary
                summary = self.visual_grouper.get_groups_summary(visual_groups)
                self._log(f"Visual multiplet grouping: {len(peak_data)} peaks organized into {len(visual_groups)} visual groups")
                self._log(summary)
                
                # Show editable group dialog
                tolerance_dialog.destroy()
                self._show_visual_groups_dialog(visual_groups, annotated_peaks, spectrum)
                
                self.root.after(100, self._update_plot)
                
            except Exception as e:
                self._log(f"Error in visual multiplet grouping: {e}")
                messagebox.showerror("Error", f"Error in visual multiplet grouping: {e}")
        
        def cancel():
            tolerance_dialog.destroy()
        
        ttk.Button(button_frame, text="Apply", command=apply_grouping).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT)
    
    def _apply_visual_groups(self, spectrum, annotated_peaks, visual_groups):
        """Apply visual grouping results to the spectrum - ONLY ADD METADATA, DON'T CREATE NEW PEAKS."""
        
        # DON'T clear existing peaks - just add metadata to them
        print(f"Original peaks before grouping: {len(spectrum.peaks)}")
        
        # Create a mapping from chemical shift to annotated peak data
        shift_to_annotation = {}
        for peak_data in annotated_peaks:
            shift = peak_data['shift']
            shift_to_annotation[shift] = peak_data
        
        # Add visual group metadata to existing peaks
        for i, peak in enumerate(spectrum.peaks):
            # Find matching annotated data by chemical shift (with small tolerance)
            matching_annotation = None
            for shift, annotation in shift_to_annotation.items():
                if abs(peak.chemical_shift - shift) < 0.001:  # 0.001 ppm tolerance
                    matching_annotation = annotation
                    break
            
            if matching_annotation:
                # Add visual group metadata as attributes to existing peak
                peak.visual_group_id = matching_annotation.get('visual_group_id', -1)
                peak.visual_assignment = matching_annotation.get('visual_assignment', '')
                peak.visual_center_shift = matching_annotation.get('visual_center_shift', peak.chemical_shift)
                peak.is_visual_center = matching_annotation.get('is_group_center', False)
                peak.group_size = matching_annotation.get('group_size', 1)
                
                # Debug output
                if peak.is_visual_center:
                    print(f"DEBUG: Visual center at {peak.chemical_shift:.3f} ppm, assignment: {peak.visual_assignment}")
                
                # Update integration for visual centers
                if peak.is_visual_center and matching_annotation.get('visual_integration'):
                    peak.integration = matching_annotation.get('visual_integration')
                    print(f"DEBUG: Set integration to {peak.integration} for center at {peak.chemical_shift:.3f}")
            else:
                # No visual group for this peak
                peak.visual_group_id = -1
                peak.visual_assignment = ''
                peak.is_visual_center = False
                peak.group_size = 1
        
        print(f"Peaks after grouping: {len(spectrum.peaks)} (should be same as before!)")
    
    def _show_visual_groups_dialog(self, visual_groups, annotated_peaks, spectrum):
        """Show an editable dialog for visual groups."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Visual Multiplet Groups - Teaching Mode")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Editable Multiplet Groups", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Groups frame with scrollbar
        groups_frame = ttk.Frame(main_frame)
        groups_frame.pack(fill='both', expand=True)
        
        # Canvas and scrollbar for scrolling
        canvas = tk.Canvas(groups_frame)
        scrollbar = ttk.Scrollbar(groups_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store entry widgets for editing
        entry_widgets = {}
        
        # Create editable entries for each group
        for i, group in enumerate(visual_groups):
            group_frame = ttk.LabelFrame(scrollable_frame, 
                                       text=f"Group {group.assignment}", padding=10)
            group_frame.pack(fill='x', pady=5)
            
            # Assignment
            assign_frame = ttk.Frame(group_frame)
            assign_frame.pack(fill='x', pady=2)
            ttk.Label(assign_frame, text="Assignment:", width=12).pack(side='left')
            assign_entry = ttk.Entry(assign_frame, width=10)
            assign_entry.insert(0, group.assignment)
            assign_entry.pack(side='left', padx=(5, 0))
            entry_widgets[f'assign_{i}'] = assign_entry
            
            # Center Shift
            shift_frame = ttk.Frame(group_frame)
            shift_frame.pack(fill='x', pady=2)
            ttk.Label(shift_frame, text="Center (ppm):", width=12).pack(side='left')
            shift_entry = ttk.Entry(shift_frame, width=10)
            shift_entry.insert(0, f"{group.center_shift:.3f}")
            shift_entry.pack(side='left', padx=(5, 0))
            entry_widgets[f'shift_{i}'] = shift_entry
            
            # Integration
            int_frame = ttk.Frame(group_frame)
            int_frame.pack(fill='x', pady=2)
            ttk.Label(int_frame, text="Integration:", width=12).pack(side='left')
            int_entry = ttk.Entry(int_frame, width=10)
            int_entry.insert(0, str(group.integration))
            int_entry.pack(side='left', padx=(5, 0))
            entry_widgets[f'int_{i}'] = int_entry
            
            # Multiplicity (read-only for now)
            mult_frame = ttk.Frame(group_frame)
            mult_frame.pack(fill='x', pady=2)
            ttk.Label(mult_frame, text="Multiplicity:", width=12).pack(side='left')
            mult_label = ttk.Label(mult_frame, text=group.multiplicity, 
                                 foreground='blue', font=('Arial', 10, 'bold'))
            mult_label.pack(side='left', padx=(5, 0))
            
            # Peak count info
            info_frame = ttk.Frame(group_frame)
            info_frame.pack(fill='x', pady=2)
            ttk.Label(info_frame, text="Peak count:", width=12).pack(side='left')
            ttk.Label(info_frame, text=f"{group.peak_count} peaks", 
                     foreground='gray').pack(side='left', padx=(5, 0))
            
            # Range info
            range_frame = ttk.Frame(group_frame)
            range_frame.pack(fill='x', pady=2)
            ttk.Label(range_frame, text="Range (ppm):", width=12).pack(side='left')
            ttk.Label(range_frame, text=f"{group.shift_range[1]:.3f} - {group.shift_range[0]:.3f}", 
                     foreground='gray').pack(side='left', padx=(5, 0))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        def apply_changes():
            """Apply user edits to the visual groups."""
            try:
                for i, group in enumerate(visual_groups):
                    # Get new values
                    new_assign = entry_widgets[f'assign_{i}'].get().strip()
                    new_shift = float(entry_widgets[f'shift_{i}'].get())
                    new_int = int(entry_widgets[f'int_{i}'].get())
                    
                    # Update group
                    group.assignment = new_assign
                    group.center_shift = new_shift
                    group.integration = new_int
                
                # Update annotated_peaks with new integration values from visual groups
                for peak_data in annotated_peaks:
                    if peak_data.get('is_group_center', False):
                        # Find matching visual group by center shift
                        for group in visual_groups:
                            if abs(peak_data['visual_center_shift'] - group.center_shift) < 0.001:
                                peak_data['visual_integration'] = group.integration
                                print(f"DEBUG: Updated annotated peak integration to {group.integration} for center at {group.center_shift:.3f}")
                                break
                
                # Update spectrum with new values
                self._apply_visual_groups(spectrum, annotated_peaks, visual_groups)
                self._update_plot()
                
                # Update log
                summary = self.visual_grouper.get_groups_summary(visual_groups)
                self._log("Visual groups updated:")
                self._log(summary)
                
                messagebox.showinfo("Success", "Visual groups updated successfully!")
                
            except ValueError as e:
                messagebox.showerror("Input Error", f"Invalid input: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Error applying changes: {e}")
        
        ttk.Button(button_frame, text="Apply Changes", command=apply_changes).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side='left', padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def _apply_grouped_peaks(self, spectrum, grouped_peaks):
        """Apply grouped peaks to the current spectrum."""
        from nmr_simulator.spectrum import Peak
        
        # Clear existing peaks
        spectrum.peaks.clear()
        
        # Add new grouped peaks
        for peak_data in grouped_peaks:
            try:
                # Parse integration value - handle both string and numeric formats
                integration_raw = peak_data.get('integration', 1.0)
                if isinstance(integration_raw, str):
                    integration_val = float(integration_raw.replace('H', ''))
                    integration_str = integration_raw
                else:
                    integration_val = float(integration_raw)
                    integration_str = f"{integration_val}H"
                
                # Ensure coupling constants is a list
                coupling = peak_data.get('coupling', [])
                if not isinstance(coupling, list):
                    coupling = []
                
                # Ensure linewidth is reasonable
                linewidth = peak_data.get('linewidth', 0.005)
                if linewidth <= 0:
                    linewidth = 0.005
                
                self._log(f"Creating peak: {peak_data['shift']:.3f} ppm, {peak_data.get('multiplicity', 's')}, {integration_str}, J={coupling}")
                
                peak = Peak(
                    chemical_shift=peak_data['shift'],
                    intensity=peak_data.get('intensity', 100),
                    width=linewidth,
                    multiplicity=peak_data.get('multiplicity', 's'),
                    coupling_constants=coupling,
                    integration=integration_val
                )
                spectrum.peaks.append(peak)
                self._log(f"✓ Added grouped peak: {peak_data['shift']:.2f} ppm, {peak_data.get('multiplicity', 's')}, {integration_str}")
            except Exception as e:
                self._log(f"❌ Error adding grouped peak: {e}")
                self._log(f"Peak data: {peak_data}")
                import traceback
                traceback.print_exc()
    
    def _analyze_peak_patterns(self):
        """Analyze peak patterns for multiplicity prediction."""
        if not self.current_spectra:
            messagebox.showinfo("No Data", "No spectra loaded.")
            return
        
        nucleus = self.nucleus_var.get()
        spectrum = None
        for spec in self.current_spectra:
            if spec.nucleus == nucleus:
                spectrum = spec
                break
        
        if not spectrum:
            messagebox.showinfo("No Data", f"No {nucleus} spectrum found.")
            return
        
        # Create analysis window
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("🔍 Peak Pattern Analysis")
        analysis_window.geometry("600x500")
        
        # Analysis text widget
        text_frame = tk.Frame(analysis_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Perform analysis
        analysis_text = self._generate_peak_analysis(spectrum)
        text_widget.insert(tk.END, analysis_text)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(analysis_window, text="Close", command=analysis_window.destroy).pack(pady=5)
    
    def _generate_peak_analysis(self, spectrum):
        """Generate peak pattern analysis text."""
        analysis = f"Peak Pattern Analysis ({spectrum.nucleus} NMR)\n"
        analysis += "=" * 50 + "\n\n"
        
        # Sort peaks by chemical shift
        sorted_peaks = sorted(spectrum.peaks, key=lambda p: p.chemical_shift, reverse=True)
        
        # Group peaks by proximity for analysis
        groups = []
        current_group = [sorted_peaks[0]] if sorted_peaks else []
        
        for i in range(1, len(sorted_peaks)):
            current_peak = sorted_peaks[i]
            last_peak = current_group[-1]
            
            distance = abs(current_peak.chemical_shift - last_peak.chemical_shift)
            
            if distance <= 0.5:  # Group peaks within 0.5 ppm
                current_group.append(current_peak)
            else:
                groups.append(current_group)
                current_group = [current_peak]
        
        if current_group:
            groups.append(current_group)
        
        # Analyze each group
        for i, group in enumerate(groups, 1):
            if len(group) == 1:
                peak = group[0]
                analysis += f"Peak {i}: δ {peak.chemical_shift:.3f} ppm (Single peak)\n"
                analysis += f"  Current: {peak.multiplicity}, {peak.integration:.1f}H\n"
                analysis += f"  Intensity: {peak.intensity:.0f}\n"
                analysis += f"  Suggestion: Likely singlet or unresolved multiplet\n\n"
            else:
                # Multiple peaks in group
                shifts = [p.chemical_shift for p in group]
                intensities = [p.intensity for p in group]
                center = sum(s * i for s, i in zip(shifts, intensities)) / sum(intensities)
                
                analysis += f"Peak Group {i}: δ {center:.3f} ppm ({len(group)} lines)\n"
                analysis += f"  Range: {min(shifts):.3f} - {max(shifts):.3f} ppm\n"
                analysis += f"  Total intensity: {sum(intensities):.0f}\n"
                
                # Suggest multiplicity based on pattern
                if len(group) == 2:
                    j_hz = abs(shifts[0] - shifts[1]) * 400
                    analysis += f"  Suggested: Doublet (J = {j_hz:.1f} Hz)\n"
                elif len(group) == 3:
                    # Check for triplet pattern
                    if self._is_triplet_like(intensities):
                        j_hz = abs(shifts[0] - shifts[2]) * 400 / 2
                        analysis += f"  Suggested: Triplet (J = {j_hz:.1f} Hz)\n"
                    else:
                        analysis += f"  Suggested: Doublet of doublets or complex multiplet\n"
                elif len(group) == 4:
                    if self._is_quartet_like(intensities):
                        j_hz = abs(shifts[0] - shifts[3]) * 400 / 3
                        analysis += f"  Suggested: Quartet (J = {j_hz:.1f} Hz)\n"
                    else:
                        analysis += f"  Suggested: Complex multiplet\n"
                else:
                    analysis += f"  Suggested: Complex multiplet (m)\n"
                
                analysis += f"  Recommendation: Use 'Group Multiplet Lines' tool\n\n"
        
        # Add suggestions
        analysis += "\n🔧 RECOMMENDATIONS:\n"
        analysis += "=" * 30 + "\n"
        analysis += "1. Use 'Tools → Group Multiplet Lines' to automatically group related peaks\n"
        analysis += "2. Use 'Tools → Peak List Editor' to manually adjust multiplicities\n"
        analysis += "3. Consider the chemical environment when assigning multiplicities\n"
        analysis += "4. Check integration ratios for consistency\n\n"
        
        return analysis
    
    def _is_triplet_like(self, intensities):
        """Check if intensity pattern resembles a triplet (1:2:1)."""
        if len(intensities) != 3:
            return False
        max_int = max(intensities)
        norm = [i / max_int for i in intensities]
        # Middle peak should be highest, outer peaks similar and smaller
        return norm[1] > 0.7 and abs(norm[0] - norm[2]) < 0.3 and max(norm[0], norm[2]) < 0.8
    
    def _is_quartet_like(self, intensities):
        """Check if intensity pattern resembles a quartet (1:3:3:1)."""
        if len(intensities) != 4:
            return False
        max_int = max(intensities)
        norm = [i / max_int for i in intensities]
        # Middle two peaks should be similar and high, outer peaks similar and lower
        return (abs(norm[1] - norm[2]) < 0.3 and norm[1] > 0.7 and norm[2] > 0.7 and
                abs(norm[0] - norm[3]) < 0.3 and max(norm[0], norm[3]) < 0.8)
    
    def run(self):
        """Start the GUI application."""
        self._log("Enhanced NMR Simulator started")
        self._log("Ready for compound analysis")
        self.root.mainloop()


def create_enhanced_gui():
    """Create and run the enhanced NMR GUI."""
    try:
        app = EnhancedNMRGUI()
        app.run()
    except Exception as e:
        print(f"Error starting enhanced GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    create_enhanced_gui()
