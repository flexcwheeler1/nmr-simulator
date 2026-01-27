#!/usr/bin/env python3
"""
Enhanced NMR Peak Width Control Demo

This script demonstrates various ways to control peak widths, especially for broad signals like NH.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def show_peak_width_guide():
    """Show comprehensive guide for controlling peak widths."""
    
    demo_window = tk.Tk()
    demo_window.title("🎛️ Peak Width Control Guide")
    demo_window.geometry("900x700")
    
    # Create scrollable text widget
    frame = ttk.Frame(demo_window)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    text_widget = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 11))
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)
    
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Guide content
    guide_content = """🎛️ PEAK WIDTH CONTROL FOR NMR SIGNALS
==========================================

For broad signals like NH, OH, and exchangeable protons, you can control peak width using several methods:

📋 METHOD 1: BROAD MULTIPLICITY CODES (Easiest)
──────────────────────────────────────────────

Use standard multiplicity codes that indicate broad signals:

Examples:
8.45 (br s, 1H)          # Broad singlet (NH)
10.2 (br, 1H)            # General broad signal
5.67 (bs, 1H)            # Broad singlet (alternative)
4.12 (br d, 1H)          # Broad doublet

Supported broad codes:
• br = broad signal (automatically wider)
• bs = broad singlet
• bd = broad doublet
• bt = broad triplet

🎯 METHOD 2: EXPLICIT LINEWIDTH IN HZ
────────────────────────────────────────

Specify the linewidth directly in Hz after J-coupling:

Examples:
8.45 (s, 1H, lw=15 Hz)           # 15 Hz linewidth (broad NH)
10.2 (s, 1H, linewidth=25 Hz)   # 25 Hz linewidth (very broad)
7.23 (d, J=8.0 Hz, 1H, lw=3 Hz) # Sharp aromatic (3 Hz)
3.45 (s, 3H, lw=1 Hz)            # Very sharp singlet

📐 METHOD 3: LINEWIDTH IN PPM
────────────────────────────────

For field-independent specification:

Examples:
8.45 (s, 1H, lw=0.025 ppm)      # 10 Hz at 400 MHz, 15 Hz at 600 MHz
7.23 (d, J=8.0 Hz, 1H, lw=0.008 ppm)  # Sharp signal
10.2 (br s, 1H, lw=0.05 ppm)    # Very broad signal

⚡ METHOD 4: COMBINED APPROACH (Recommended)
──────────────────────────────────────────────

Combine multiplicity with explicit width:

Examples:
8.45 (br s, 1H, lw=20 Hz)       # Broad singlet, 20 Hz width
10.2 (br, 1H, lw=30 Hz)         # Very broad, 30 Hz width
4.12 (br d, J=6 Hz, 1H, lw=12 Hz)  # Broad doublet with specified width

🧪 TYPICAL NH SIGNAL EXAMPLES
─────────────────────────────────

For different types of NH signals:

Primary amide NH2:
6.2 (br s, 2H, lw=25 Hz)        # Broad, often exchanges
5.8 (br s, 2H)                  # Alternative without explicit width

Secondary amide NH:
8.45 (br s, 1H, lw=15 Hz)       # Moderately broad
7.89 (br d, J=6 Hz, 1H, lw=18 Hz)  # NH coupled to adjacent CH

Aromatic NH (pyrrole, indole):
10.2 (br s, 1H, lw=8 Hz)        # Less broad, often visible
8.67 (br s, 1H)                 # Standard broad treatment

Hydrogen-bonded NH:
12.3 (br s, 1H, lw=40 Hz)       # Very broad, exchanging rapidly

🔬 COMPLETE COMPOUND EXAMPLE
──────────────────────────────────

Acetanilide (N-phenylacetamide):

7.52 (d, J=8.0 Hz, 2H)          # ortho-H (sharp)
7.31 (t, J=8.0 Hz, 2H)          # meta-H (sharp)  
7.09 (t, J=8.0 Hz, 1H)          # para-H (sharp)
8.45 (br s, 1H, lw=18 Hz)       # NH (broad)
2.15 (s, 3H)                    # CH3 (sharp)

💡 AUTOMATIC WIDTH ASSIGNMENT
────────────────────────────────────

The system automatically assigns widths based on chemical shift and multiplicity:

Chemical Shift Regions:
• 0-3 ppm:    Sharp (0.8 Hz)    - Alkyl CH, CH2, CH3
• 3-7 ppm:    Medium (1.2 Hz)   - OCH, NCH, etc.
• 7-8 ppm:    Sharp (1.2 Hz)    - Aromatic CH
• 8-15 ppm:   Broad (3-8 Hz)    - NH, OH, CHO

Multiplicity-Based:
• s, d, t, q: Normal width
• br, bs:     2-3x wider automatically
• m:          Slightly broader for complex multiplets

🎨 VISUAL APPEARANCE
───────────────────────

Different linewidths create different peak shapes:

Linewidth (Hz) | Appearance     | Typical For
1-2 Hz        | Sharp, tall    | CH3, sharp aromatic
3-5 Hz        | Normal         | Most CH signals
8-15 Hz       | Broad          | NH in amides
20-40 Hz      | Very broad     | Exchanging OH, NH
50+ Hz        | Baseline hump  | Very fast exchange

🚀 QUICK START EXAMPLES
─────────────────────────

Copy these examples into your simulator:

Example 1 - Simple NH specification:
7.23 (d, J=8.0 Hz, 2H)
8.45 (br s, 1H)                 # Auto-broad NH
2.15 (s, 3H)

Example 2 - Explicit NH width:
7.23 (d, J=8.0 Hz, 2H)
8.45 (br s, 1H, lw=20 Hz)       # 20 Hz broad NH
2.15 (s, 3H)

Example 3 - Mixed sharp and broad:
7.52 (d, J=8.0 Hz, 2H, lw=2 Hz)     # Very sharp aromatic
8.45 (br s, 1H, lw=25 Hz)           # Broad NH
3.67 (s, 3H, lw=1 Hz)               # Sharp methyl

⚙️ SYSTEM BEHAVIOR
─────────────────────

When you specify:
• "br" multiplicity → Automatically 3x wider than normal
• "lw=X Hz" → Explicit width in Hz
• "lw=X ppm" → Explicit width in ppm
• No specification → Automatic based on chemical shift region

🎯 TROUBLESHOOTING
─────────────────────

Peak too sharp?
→ Add "br" to multiplicity or "lw=XX Hz"

Peak too broad?
→ Use explicit "lw=2 Hz" for sharper signals

NH not visible?
→ Check if linewidth is too broad (>50 Hz)
→ Try reducing to 10-25 Hz range

Wrong integration?
→ Broad signals may appear smaller due to spreading
→ Intensity is preserved, just distributed over wider range

✨ PRO TIPS
──────────────

1. Start with "br s" for NH signals - system handles width automatically
2. For very specific needs, use explicit "lw=XX Hz"
3. Consider your spectrometer frequency - higher field = Hz values scale
4. Use chemical shift to guide width: aromatic sharp, NH broad
5. Test different widths to match your experimental data

==========================================
🎛️ Ready to control your peak widths like a pro!
"""
    
    text_widget.insert(tk.END, guide_content)
    text_widget.config(state=tk.DISABLED)
    
    # Add buttons
    button_frame = ttk.Frame(demo_window)
    button_frame.pack(fill=tk.X, padx=10, pady=5)
    
    ttk.Button(
        button_frame, 
        text="🧪 Test Examples",
        command=lambda: test_width_examples()
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        button_frame, 
        text="🚀 Start Simulator",
        command=lambda: [demo_window.destroy(), start_simulator()]
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        button_frame, 
        text="❌ Close",
        command=demo_window.destroy
    ).pack(side=tk.RIGHT, padx=5)
    
    demo_window.mainloop()

def test_width_examples():
    """Create a test window with example data ready to copy."""
    test_window = tk.Toplevel()
    test_window.title("🧪 Peak Width Test Examples")
    test_window.geometry("600x500")
    
    # Create text area with examples
    frame = ttk.Frame(test_window)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(frame, text="Copy these examples into your simulator:").pack(anchor=tk.W, pady=5)
    
    examples_text = scrolledtext.ScrolledText(frame, width=70, height=25, wrap=tk.WORD)
    examples_text.pack(fill=tk.BOTH, expand=True)
    
    examples = """# Example 1: Acetanilide with automatic broad NH
7.52 (d, J=8.0 Hz, 2H)
7.31 (t, J=8.0 Hz, 2H)
7.09 (t, J=8.0 Hz, 1H)
8.45 (br s, 1H)
2.15 (s, 3H)

# Example 2: Acetanilide with explicit NH width
7.52 (d, J=8.0 Hz, 2H)
7.31 (t, J=8.0 Hz, 2H)
7.09 (t, J=8.0 Hz, 1H)
8.45 (br s, 1H, lw=18 Hz)
2.15 (s, 3H)

# Example 3: Mixed linewidths
7.52 (d, J=8.0 Hz, 2H, lw=2 Hz)
8.45 (br s, 1H, lw=25 Hz)
3.67 (s, 3H, lw=1 Hz)

# Example 4: Primary amide
7.23 (d, J=8.0 Hz, 2H)
6.2 (br s, 2H, lw=30 Hz)
2.31 (s, 3H)

# Example 5: Hydrogen-bonded NH
7.89 (d, J=8.0 Hz, 1H)
12.3 (br s, 1H, lw=40 Hz)
7.45 (t, J=8.0 Hz, 1H)

# Example 6: Using ppm linewidth
8.45 (br s, 1H, lw=0.025 ppm)
7.23 (d, J=8.0 Hz, 2H, lw=0.005 ppm)
"""
    
    examples_text.insert(tk.END, examples)
    
    ttk.Button(frame, text="Close", command=test_window.destroy).pack(pady=5)

def start_simulator():
    """Start the enhanced GUI."""
    try:
        os.system("python enhanced_gui.py")
    except Exception as e:
        print(f"Could not start enhanced GUI: {e}")

if __name__ == "__main__":
    show_peak_width_guide()
