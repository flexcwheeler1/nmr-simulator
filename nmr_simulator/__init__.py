"""
NMR Simulator Package

A comprehensive package for simulating NMR spectra with SDBS database integration.
"""

__version__ = "1.0.0"
__author__ = "NMR Simulator Team"

from .simulator import NMRSimulator
from .molecule import Molecule
from .spectrum import Spectrum, Peak

__all__ = ['NMRSimulator', 'Molecule', 'Spectrum', 'Peak']
