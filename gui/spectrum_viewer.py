"""
Spectrum Viewer Widget

This module provides a matplotlib-based widget for displaying NMR spectra.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmr_simulator.spectrum import Spectrum


class SpectrumViewer(ttk.Frame):
    """
    A widget for displaying and interacting with NMR spectra.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the spectrum viewer.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments
        """
        super().__init__(parent, **kwargs)
        
        self.spectra: List[Spectrum] = []
        self.current_spectrum: Optional[Spectrum] = None
        
        self._setup_ui()
        self._setup_plot()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Spectrum selection
        ttk.Label(self.control_frame, text="Spectrum:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.spectrum_var = tk.StringVar()
        self.spectrum_combo = ttk.Combobox(self.control_frame, textvariable=self.spectrum_var, 
                                          state="readonly", width=30)
        self.spectrum_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.spectrum_combo.bind('<<ComboboxSelected>>', self._on_spectrum_changed)
        
        # Plot controls
        self.show_peaks_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.control_frame, text="Show Peak Labels", 
                       variable=self.show_peaks_var, 
                       command=self._update_plot).pack(side=tk.LEFT, padx=(10, 5))
        
        self.show_grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.control_frame, text="Show Grid", 
                       variable=self.show_grid_var, 
                       command=self._update_plot).pack(side=tk.LEFT, padx=(5, 5))
        
        # Zoom controls
        zoom_frame = ttk.LabelFrame(self.control_frame, text="Zoom", padding=5)
        zoom_frame.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Button(zoom_frame, text="Reset", command=self._reset_zoom).pack(side=tk.LEFT, padx=1)
        ttk.Button(zoom_frame, text="Aromatic", command=self._zoom_aromatic).pack(side=tk.LEFT, padx=1)
        ttk.Button(zoom_frame, text="Aliphatic", command=self._zoom_aliphatic).pack(side=tk.LEFT, padx=1)
        
        # Display options for multiplicity
        self.show_multiplicity_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.control_frame, text="Show Multiplicity", 
                       variable=self.show_multiplicity_var, 
                       command=self._update_plot).pack(side=tk.LEFT, padx=(10, 5))
        
        # Export button
        ttk.Button(self.control_frame, text="Export Plot", 
                  command=self._export_plot).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Plot frame
        self.plot_frame = ttk.Frame(self.main_frame)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _setup_plot(self):
        """Set up the matplotlib plot."""
        # Create figure and axis
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Create toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        
        # Initial empty plot
        self._setup_empty_plot()
    
    def _setup_empty_plot(self):
        """Set up an empty plot with proper styling."""
        self.ax.clear()
        self.ax.set_xlim(12, 0)  # NMR convention: high field to low field
        self.ax.set_ylim(0, 1)
        self.ax.set_xlabel('Chemical Shift (ppm)')
        self.ax.set_ylabel('Intensity')
        self.ax.set_title('NMR Spectrum - No Data Loaded')
        self.ax.grid(True, alpha=0.3)
        
        # Add some helpful text
        self.ax.text(6, 0.5, 'Load a spectrum to view data', 
                    ha='center', va='center', fontsize=14, alpha=0.6)
        
        self.canvas.draw()
    
    def add_spectrum(self, spectrum: Spectrum):
        """
        Add a spectrum to the viewer.
        
        Args:
            spectrum: Spectrum object to add
        """
        self.spectra.append(spectrum)
        self._update_spectrum_list()
        
        # If this is the first spectrum, select it
        if len(self.spectra) == 1:
            self.spectrum_var.set(str(spectrum))
            self.current_spectrum = spectrum
            self._update_plot()
    
    def clear_spectra(self):
        """Clear all spectra from the viewer."""
        self.spectra.clear()
        self.current_spectrum = None
        self._update_spectrum_list()
        self._setup_empty_plot()
    
    def _update_spectrum_list(self):
        """Update the spectrum selection combobox."""
        spectrum_names = [str(spectrum) for spectrum in self.spectra]
        self.spectrum_combo['values'] = spectrum_names
        
        if not spectrum_names:
            self.spectrum_var.set('')
    
    def _on_spectrum_changed(self, event=None):
        """Handle spectrum selection change."""
        selected_name = self.spectrum_var.get()
        
        # Find the selected spectrum
        for spectrum in self.spectra:
            if str(spectrum) == selected_name:
                self.current_spectrum = spectrum
                self._update_plot()
                break
    
    def _update_plot(self):
        """Update the plot with the current spectrum."""
        if not self.current_spectrum:
            self._setup_empty_plot()
            return
        
        # Clear the plot
        self.ax.clear()
        
        # Generate spectrum data if not already done
        if self.current_spectrum.data_points is None:
            self.current_spectrum.generate_spectrum_data()
        
        # Plot the spectrum
        if (self.current_spectrum.ppm_axis is not None and 
            self.current_spectrum.data_points is not None):
            
            self.ax.plot(self.current_spectrum.ppm_axis, 
                        self.current_spectrum.data_points, 
                        'b-', linewidth=1.0)
        
        # Set up the plot appearance
        self.ax.set_xlim(self.current_spectrum.ppm_range[1], 
                        self.current_spectrum.ppm_range[0])  # Inverted for NMR
        
        # Auto-scale y-axis with some padding
        if self.current_spectrum.data_points is not None:
            y_max = np.max(self.current_spectrum.data_points)
            self.ax.set_ylim(-0.05 * y_max, 1.1 * y_max)
        
        self.ax.set_xlabel('Chemical Shift (ppm)', fontsize=12)
        self.ax.set_ylabel('Intensity', fontsize=12)
        self.ax.set_title(self.current_spectrum.title, fontsize=14)
        
        # Grid
        if self.show_grid_var.get():
            self.ax.grid(True, alpha=0.3)
        
        # Peak labels
        if self.show_peaks_var.get():
            self._add_peak_labels()
            
        # Enhanced multiplicity display
        if hasattr(self, 'show_multiplicity_var') and self.show_multiplicity_var.get():
            self._add_multiplicity_display()
        
        # Refresh canvas
        self.canvas.draw()
    
    def _add_peak_labels(self):
        """Add labels for significant peaks."""
        if not self.current_spectrum or not self.current_spectrum.peaks:
            return
        
        for peak in self.current_spectrum.peaks:
            if peak.intensity > 0.1:  # Only label significant peaks
                # Find the y-coordinate for the label
                y_pos = peak.intensity * 1.05  # Slightly above the peak
                
                # Create label text
                label_text = f'{peak.chemical_shift:.2f}'
                if peak.multiplicity != 's':
                    label_text += f' ({peak.multiplicity})'
                
                self.ax.annotate(label_text, 
                               xy=(peak.chemical_shift, peak.intensity),
                               xytext=(peak.chemical_shift, y_pos),
                               ha='center', va='bottom',
                               fontsize=8, alpha=0.8,
                               arrowprops=dict(arrowstyle='->', alpha=0.5, lw=0.5))
    
    def _export_plot(self):
        """Export the current plot to a file."""
        if not self.current_spectrum:
            messagebox.showwarning("No Data", "No spectrum to export.")
            return
        
        from tkinter import filedialog
        
        # Ask for filename
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf"),
                ("SVG files", "*.svg"),
                ("All files", "*.*")
            ],
            title="Export Spectrum Plot"
        )
        
        if filename:
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Plot exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export plot:\n{str(e)}")
    
    def zoom_to_region(self, ppm_min: float, ppm_max: float):
        """
        Zoom to a specific ppm region.
        
        Args:
            ppm_min: Minimum ppm value
            ppm_max: Maximum ppm value
        """
        if self.current_spectrum:
            self.ax.set_xlim(ppm_max, ppm_min)  # Inverted for NMR
            self.canvas.draw()
    
    def reset_zoom(self):
        """Reset zoom to show full spectrum."""
        if self.current_spectrum:
            self.ax.set_xlim(self.current_spectrum.ppm_range[1], 
                            self.current_spectrum.ppm_range[0])
            self.canvas.draw()
    
    def get_current_spectrum(self) -> Optional[Spectrum]:
        """
        Get the currently displayed spectrum.
        
        Returns:
            Current Spectrum object or None
        """
        return self.current_spectrum
    
    def _reset_zoom(self):
        """Reset zoom to show full spectrum range."""
        if self.current_spectrum:
            self.ax.set_xlim(self.current_spectrum.ppm_range[1], 
                            self.current_spectrum.ppm_range[0])
            if self.current_spectrum.data_points is not None:
                y_max = np.max(self.current_spectrum.data_points)
                self.ax.set_ylim(-0.05 * y_max, 1.1 * y_max)
            self.canvas.draw()
    
    def _zoom_aromatic(self):
        """Zoom to aromatic region (6-9 ppm for 1H, 100-160 ppm for 13C)."""
        if not self.current_spectrum:
            return
            
        if self.current_spectrum.nucleus == '1H':
            self.ax.set_xlim(9, 6)
        elif self.current_spectrum.nucleus == '13C':
            self.ax.set_xlim(160, 100)
        
        self._auto_scale_y()
        self.canvas.draw()
    
    def _zoom_aliphatic(self):
        """Zoom to aliphatic region (0-4 ppm for 1H, 0-80 ppm for 13C)."""
        if not self.current_spectrum:
            return
            
        if self.current_spectrum.nucleus == '1H':
            self.ax.set_xlim(4, 0)
        elif self.current_spectrum.nucleus == '13C':
            self.ax.set_xlim(80, 0)
            
        self._auto_scale_y()
        self.canvas.draw()
    
    def _auto_scale_y(self):
        """Auto-scale Y axis for current X range."""
        if not self.current_spectrum or self.current_spectrum.data_points is None:
            return
            
        # Get current x limits
        x_min, x_max = self.ax.get_xlim()
        
        # Find data points in current range
        ppm_axis = self.current_spectrum.ppm_axis
        data_points = self.current_spectrum.data_points
        
        if ppm_axis is not None:
            # Note: x_min > x_max for NMR (inverted axis)
            mask = (ppm_axis <= x_min) & (ppm_axis >= x_max)
            if np.any(mask):
                y_max = np.max(data_points[mask])
                self.ax.set_ylim(-0.05 * y_max, 1.1 * y_max)
    
    def _add_multiplicity_display(self):
        """Add enhanced multiplicity display for peaks."""
        if not self.current_spectrum or not self.current_spectrum.peaks:
            return
            
        # Multiplicity symbols and descriptions
        mult_symbols = {
            's': 'singlet',
            'd': 'doublet', 
            't': 'triplet',
            'q': 'quartet',
            'p': 'pentet',
            'h': 'hextet',
            'm': 'multiplet',
            'dd': 'doublet of doublets',
            'dt': 'doublet of triplets',
            'td': 'triplet of doublets'
        }
        
        for peak in self.current_spectrum.peaks:
            if peak.intensity > 0.05:  # Show for significant peaks
                y_pos = peak.intensity * 1.15
                
                # Create detailed label
                mult_desc = mult_symbols.get(peak.multiplicity, peak.multiplicity)
                
                if peak.coupling_constants:
                    j_values = ', '.join([f'{j:.1f}' for j in peak.coupling_constants])
                    label = f'{peak.chemical_shift:.2f} ppm\n{mult_desc}\nJ = {j_values} Hz'
                else:
                    label = f'{peak.chemical_shift:.2f} ppm\n{mult_desc}'
                
                # Add a styled text box
                bbox_props = dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7)
                self.ax.text(peak.chemical_shift, y_pos, label,
                           ha='center', va='bottom', fontsize=8,
                           bbox=bbox_props)
