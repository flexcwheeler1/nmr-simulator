#!/usr/bin/env python3
"""
SDBS Compound Retrieval Tool

A simple tool to retrieve specific SDBS compounds with enhanced demo data.
Includes the ability to manually add compound data from SDBS URLs.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_sdbs_integration import EnhancedSDBSIntegration
import json

def manual_compound_entry():
    """Allow manual entry of compound data from SDBS URLs."""
    print("=== Manual SDBS Compound Entry ===")
    print("Enter compound data manually from SDBS URLs:")
    print("Example URLs:")
    print("- Compound view: https://sdbs.db.aist.go.jp/CompoundView.aspx?sdbsno=1839")
    print("- 1H NMR: https://sdbs.db.aist.go.jp/HNmrSpectralView.aspx?imgdir=hsp&fname=HSP47592&sdbsno=1839")
    print("- 13C NMR: https://sdbs.db.aist.go.jp/CNmrSpectralView.aspx?imgdir=cds&fname=CDS00452&sdbsno=1839")
    print()
    
    # Get basic compound info
    sdbsno = input("SDBS Number: ").strip()
    name = input("Compound Name: ").strip()
    formula = input("Molecular Formula: ").strip()
    mw = input("Molecular Weight: ").strip()
    
    try:
        mw = float(mw) if mw else 0
    except ValueError:
        mw = 0
    
    compound_data = {
        "name": name,
        "formula": formula,
        "molecular_weight": mw,
        "sdbsno": sdbsno,
        "source": "manual_entry",
        "nmr_data": {}
    }
    
    # Get 1H NMR data
    print("\n1H NMR Data (enter 'done' when finished):")
    h1_peaks = []
    while True:
        shift = input("Chemical shift (ppm) or 'done': ").strip()
        if shift.lower() == 'done':
            break
        
        try:
            shift = float(shift)
            mult = input("Multiplicity (s/d/t/q/m): ").strip()
            integration = input("Integration: ").strip()
            try:
                integration = int(integration)
            except ValueError:
                integration = 1
            
            h1_peaks.append({
                "shift": shift,
                "multiplicity": mult,
                "integration": integration,
                "coupling": [],
                "assignment": ""
            })
        except ValueError:
            print("Invalid chemical shift, skipping...")
    
    if h1_peaks:
        compound_data["nmr_data"]["1H"] = {
            "solvent": "CDCl3",
            "frequency": "400 MHz",
            "peaks": h1_peaks
        }
    
    # Get 13C NMR data
    print("\n13C NMR Data (enter 'done' when finished):")
    c13_peaks = []
    while True:
        shift = input("Chemical shift (ppm) or 'done': ").strip()
        if shift.lower() == 'done':
            break
        
        try:
            shift = float(shift)
            c13_peaks.append({
                "shift": shift,
                "multiplicity": "s",
                "integration": 1,
                "assignment": ""
            })
        except ValueError:
            print("Invalid chemical shift, skipping...")
    
    if c13_peaks:
        compound_data["nmr_data"]["13C"] = {
            "solvent": "CDCl3",
            "frequency": "100 MHz",
            "peaks": c13_peaks
        }
    
    # Save the compound data
    filename = f"manual_compound_{sdbsno}.json"
    with open(filename, 'w') as f:
        json.dump(compound_data, f, indent=2)
    
    print(f"\nCompound data saved to {filename}")
    print("You can now use this data in the NMR simulator!")
    
    return compound_data

def retrieve_compound_tool():
    """Interactive tool for retrieving compound data."""
    integration = EnhancedSDBSIntegration()
    
    print("=== SDBS Compound Retrieval Tool ===\n")
    print("Available options:")
    print("1. Search by compound name")
    print("2. Get compound by SDBS number (demo data)")
    print("3. Try real SDBS retrieval (experimental)")
    print("4. Manual compound entry")
    print("5. List available demo compounds")
    
    while True:
        choice = input("\nEnter choice (1-5) or 'quit': ").strip()
        
        if choice.lower() == 'quit':
            break
            
        elif choice == '1':
            name = input("Enter compound name: ").strip()
            results = integration.search_compound_by_name(name)
            if results:
                print(f"\nFound {len(results)} compounds:")
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result['name']} (SDBS #{result['sdbsno']})")
                    print(f"   Formula: {result['formula']}")
                    if 'nmr_data' in result:
                        nmr_count = len(result['nmr_data'].keys())
                        print(f"   NMR data: {nmr_count} nuclei")
            else:
                print("No compounds found with that name.")
        
        elif choice == '2':
            sdbsno = input("Enter SDBS number: ").strip()
            compound = integration.get_compound_by_id(sdbsno, try_real=False)
            if compound:
                print(f"\nCompound: {compound['name']}")
                print(f"Formula: {compound['formula']}")
                print(f"MW: {compound.get('molecular_weight', 'Unknown')}")
                print(f"Source: {compound.get('source', 'Unknown')}")
                
                if 'nmr_data' in compound:
                    for nucleus in compound['nmr_data']:
                        peaks = len(compound['nmr_data'][nucleus]['peaks'])
                        print(f"{nucleus} NMR: {peaks} peaks")
            else:
                print("Compound not found in demo database.")
        
        elif choice == '3':
            sdbsno = input("Enter SDBS number for real retrieval: ").strip()
            print("Attempting real SDBS retrieval (may fail due to website limitations)...")
            compound = integration.get_compound_by_id(sdbsno, try_real=True)
            if compound:
                print(f"Retrieved: {compound['name']} from {compound.get('source', 'unknown')}")
            else:
                print("Real SDBS retrieval failed, no demo data available.")
        
        elif choice == '4':
            manual_compound_entry()
        
        elif choice == '5':
            print("\nAvailable demo compounds:")
            for sdbsno, data in integration.demo_database.items():
                print(f"SDBS #{sdbsno}: {data['name']} ({data['formula']})")
        
        else:
            print("Invalid choice. Please enter 1-5 or 'quit'.")

if __name__ == "__main__":
    retrieve_compound_tool()
