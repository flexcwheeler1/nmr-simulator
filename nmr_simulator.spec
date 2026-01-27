"""
NMR Spectra Simulator - PyInstaller Specification File

This spec file defines how to build the standalone executable.
"""

# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath('main.py'))

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=[
        (os.path.join(current_dir, 'nmr_simulator'), 'nmr_simulator/'),
        (os.path.join(current_dir, 'visual_multiplet_grouper.py'), '.'),
        (os.path.join(current_dir, 'non_destructive_grouper.py'), '.'),
        (os.path.join(current_dir, 'nmr_data_input.py'), '.'),
        (os.path.join(current_dir, 'help_dialog.py'), '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'numpy',
        'scipy',
        'pandas',
        'requests',
        'beautifulsoup4',
        'bs4',
        'lxml',
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NMR-Spectra-Simulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
