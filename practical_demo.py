#!/usr/bin/env python3
"""
Practical Demo: How to Use Data Merging to Avoid Missing Peaks

This script demonstrates the exact workflow to solve the issue where
peaks at 7.6 ppm disappeared when switching from assignment to multiplet data.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def show_practical_demo():
    """Show the step-by-step solution for the missing peaks issue."""
    
    demo_window = tk.Tk()
    demo_window.title("🎓 Practical Demo: Data Merging Solution")
    demo_window.geometry("800x700")
    
    # Create scrollable text widget
    frame = ttk.Frame(demo_window)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    text_widget = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 11))
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)
    
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Demo content
    demo_content = """🎯 PROBLEM SOLVED: Missing 7.6 ppm Peaks
========================================

❌ THE ISSUE YOU EXPERIENCED:
When you switched from assignment data to multiplet data, peaks at 7.6 ppm disappeared.

Assignment Data:        Multiplet Data:
A 7.6                  7.265 70 1
B 7.57                 7.263 102 2
                       7.261 89 3
                       (no 7.6 ppm peaks!)

✅ THE SOLUTION: Data Merging System

🔧 HOW TO USE THE DATA MERGING DIALOG:

1️⃣ LOAD YOUR FIRST DATASET:
   • Run: python enhanced_gui.py
   • Click 'Paste Real Data'
   • Enter your assignment data:
     A 7.6
     B 7.57
   • Click 'Load Data'

2️⃣ ADD YOUR SECOND DATASET:
   • Click 'Paste Real Data' again
   • Enter your multiplet data:
     7.265 70 1
     7.263 102 2
     7.261 89 3
     7.259 75 4
   • Click 'Load Data'

3️⃣ USE THE DATA MERGING DIALOG:
   📋 The system will show:
   "This will replace existing data. Choose action:"
   
   🔘 Replace: Remove old peaks, use only new data
   🔘 Add: Keep old peaks, add new peaks (RECOMMENDED)
   🔘 Cancel: Don't load new data
   
   ✅ SELECT "Add" to keep both datasets!

4️⃣ VERIFY YOUR PEAKS:
   • Go to Tools → Show Peak List
   • You should see BOTH:
     - Assignment peaks at 7.6 and 7.57 ppm
     - Multiplet peaks at 7.265, 7.263, 7.261, 7.259 ppm

🎨 VISUAL DISPLAY OPTIONS:

To see all your data clearly:
✓ Show Labels: See chemical shifts
✓ Show Assignments: See A, B letters
✓ Show Fine Structure: See multiplet patterns

🔍 WHAT EACH OPTION DOES:

📊 Replace Mode:
- Removes ALL existing peaks
- Loads ONLY the new data
- Use when starting over

📈 Add Mode (RECOMMENDED):
- Keeps ALL existing peaks
- Adds the new peaks
- Perfect for combining datasets

❌ Cancel Mode:
- Keeps existing data unchanged
- Doesn't load new data
- Use if you made a mistake

💡 PRO TIP: Combining Different Data Types

You can mix and match any formats:

Step 1 - Load assignments:
A 7.6
B 7.57

Step 2 - Add detailed multiplets (choose "Add"):
7.25 (d, J = 8.0 Hz, 2H)
7.15 (t, J = 8.0 Hz, 1H)

Step 3 - Add more experimental data (choose "Add"):
2.31 200 12
1.26 300 15

Result: Complete spectrum with all peaks!

📋 EXAMPLE WORKFLOW - COMPLETE AROMATIC COMPOUND:

Dataset 1 (Assignments):
A 7.6
B 7.57
C 2.3
D 1.2

Dataset 2 (Detailed Multiplets - Choose "Add"):
7.25 (d, J = 8.0 Hz, 2H, ortho-H)
7.15 (t, J = 8.0 Hz, 1H, para-H)
2.31 (s, 3H, CH3)
1.26 (t, J = 7.1 Hz, 3H, CH3)

Dataset 3 (More Experimental Data - Choose "Add"):
7.265 70 20
7.263 102 21
7.261 89 22

Final Result: 
- Assignment letters A, B, C, D
- Detailed J-coupling information
- Experimental peak fine structure
- ALL peaks preserved!

🔬 CHECKING YOUR RESULTS:

After each "Add" operation:
1. Go to Tools → Show Peak List
2. Verify all expected peaks are present
3. Check chemical shift ranges
4. Look for any missing regions

📊 Peak List Should Show:
Chemical Shift | Assignment | Multiplicity | Integration
7.600         | A          | m           | Auto
7.570         | B          | m           | Auto
7.265         | Auto       | m           | 70
7.263         | Auto       | m           | 102
(etc.)

⚡ QUICK TROUBLESHOOTING:

Missing peaks? 
→ You probably chose "Replace" instead of "Add"
→ Reload your first dataset, then use "Add" for subsequent ones

Duplicate peaks?
→ Check Tools → Show Peak List for overlapping chemical shifts
→ The system handles reasonable duplicates automatically

Wrong format?
→ Check the multiplet guide (multiplet_guide.py) for format examples

🎯 KEY TAKEAWAY:
The "Add" option in the data merging dialog is your friend!
It solves the missing peaks issue by preserving existing data.

🚀 TRY IT NOW:
Close this demo and practice with your real data using the "Add" workflow!
"""
    
    text_widget.insert(tk.END, demo_content)
    text_widget.config(state=tk.DISABLED)
    
    # Add buttons
    button_frame = ttk.Frame(demo_window)
    button_frame.pack(fill=tk.X, padx=10, pady=5)
    
    ttk.Button(
        button_frame, 
        text="🚀 Start Enhanced GUI",
        command=lambda: [demo_window.destroy(), start_enhanced_gui()]
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        button_frame, 
        text="📖 View Multiplet Guide",
        command=lambda: os.system("python multiplet_guide.py")
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        button_frame, 
        text="❌ Close Demo",
        command=demo_window.destroy
    ).pack(side=tk.RIGHT, padx=5)
    
    demo_window.mainloop()

def start_enhanced_gui():
    """Start the enhanced GUI for hands-on practice."""
    try:
        os.system("python enhanced_gui.py")
    except Exception as e:
        messagebox.showerror("Error", f"Could not start enhanced GUI: {e}")

if __name__ == "__main__":
    show_practical_demo()
