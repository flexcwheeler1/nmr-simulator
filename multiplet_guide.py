#!/usr/bin/env python3
"""
Complete Guide: How to Add Multiplet Information in NMR Simulator
"""

print("📖 COMPLETE GUIDE: Adding Multiplet Information")
print("=" * 60)

print("\n🎯 WHAT ARE MULTIPLETS?")
print("Multiplets show J-coupling patterns in NMR:")
print("• s = singlet (no coupling)")
print("• d = doublet (one coupling)")  
print("• t = triplet (equivalent coupling to 2H)")
print("• q = quartet (equivalent coupling to 3H)")
print("• m = multiplet (complex pattern)")

print("\n📝 METHOD 1: STANDARD FORMAT (Most Common)")
print("Format: chemical_shift (multiplicity, J-coupling, integration)")
print("\nExamples:")
print("7.36 (s, 5H)                    # Singlet, 5 protons")
print("1.25 (t, J = 7.0 Hz, 3H)        # Triplet, J=7.0 Hz, 3 protons")
print("3.70 (q, J = 7.0 Hz, 2H)        # Quartet, J=7.0 Hz, 2 protons")
print("7.24 (d, J = 8.2 Hz, 2H)        # Doublet, J=8.2 Hz, 2 protons")
print("2.31 (s, 3H)                    # Singlet, 3 protons")

print("\n📊 METHOD 2: ASSIGNMENT FORMAT (For Teaching)")
print("Format: Letter chemical_shift")
print("The simulator will assign appropriate multiplicities based on chemical shift:")
print("\nExamples:")
print("A 7.6      # Aromatic proton → multiplet")
print("B 7.57     # Aromatic proton → multiplet") 
print("C 2.3      # Aliphatic proton → singlet")
print("D 1.2      # Alkyl proton → triplet (typical)")

print("\n🔢 METHOD 3: TABULATED FORMAT (Experimental Data)")
print("Format: chemical_shift intensity peak_number")
print("Good for importing real experimental data:")
print("\nExamples:")
print("7.265 70 1     # δ 7.265 ppm, intensity 70")
print("7.263 102 2    # δ 7.263 ppm, intensity 102")
print("1.250 300 15   # δ 1.250 ppm, intensity 300")

print("\n⚡ METHOD 4: DETAILED FORMAT (Advanced)")
print("Include assignment and J-coupling:")
print("\nExamples:")
print("7.36 (s, 5H, Ar-H)              # With assignment")
print("1.25 (t, J = 7.0 Hz, 3H, CH3)   # With group assignment")
print("3.70 (q, J = 7.0 Hz, 2H, CH2)   # Quartet with assignment")

print("\n🎓 STEP-BY-STEP TUTORIAL:")
print("\n1️⃣ START THE SIMULATOR:")
print("   • Run: python enhanced_gui.py")
print("   • Click 'Paste Real Data' button")

print("\n2️⃣ CHOOSE YOUR INPUT METHOD:")
print("   Method A - Standard Format:")
print("   7.36 (s, 5H)")
print("   1.25 (t, J = 7.0 Hz, 3H)")
print("   3.70 (q, J = 7.0 Hz, 2H)")
print("   2.31 (s, 3H)")

print("\n   Method B - Mixed Format:")
print("   A 7.6")
print("   1.25 (t, J = 7.0 Hz, 3H)")
print("   2.31 (s, 3H)")

print("\n3️⃣ ENTER COMPOUND INFO:")
print("   • Compound Name: Your compound")
print("   • Nucleus: 1H NMR")
print("   • Solvent: CDCl3 (or appropriate)")
print("   • InChI: (optional for enhanced analysis)")

print("\n4️⃣ PASTE YOUR DATA:")
print("   Copy one of the examples above into the text area")

print("\n5️⃣ PREVIEW AND LOAD:")
print("   • Click 'Parse & Preview' to check")
print("   • Click 'Load Data' when satisfied")

print("\n💡 DISPLAY OPTIONS:")
print("✓ Show Integrals: See integration curves")
print("✓ Show Labels: See chemical shift values")
print("✓ Show Assignments: See letter assignments")
print("✓ Show Fine Structure: See J-coupling patterns")

print("\n🔬 EXAMPLE: ETHYL ACETATE")
print("Complete NMR data with multiplets:")
example = """4.12 (q, J = 7.1 Hz, 2H, OCH2)
2.09 (s, 3H, COCH3)
1.26 (t, J = 7.1 Hz, 3H, CH3)"""
print(example)

print("\n🧪 EXAMPLE: AROMATIC COMPOUND")
print("Mixed assignment and detailed format:")
example2 = """A 7.6
B 7.57
7.25 (d, J = 8.0 Hz, 2H, Ar-H)
7.15 (t, J = 8.0 Hz, 1H, Ar-H)
2.31 (s, 3H, CH3)"""
print(example2)

print("\n📋 MULTIPLICITY CODES:")
print("s  = singlet      | d  = doublet")
print("t  = triplet      | q  = quartet") 
print("qt = quintet      | sx = sextet")
print("sp = septet       | m  = multiplet")
print("dd = doublet of doublets")
print("dt = doublet of triplets")

print("\n🎯 COMMON J-COUPLING VALUES:")
print("Aromatic ortho:    6-10 Hz")
print("Aromatic meta:     1-3 Hz")
print("Aromatic para:     0-1 Hz")
print("Alkyl CH-CH3:      6-8 Hz")
print("Vinyl trans:       12-18 Hz")
print("Vinyl cis:         6-12 Hz")

print("\n✨ PRO TIPS:")
print("• Use Tools → Show Peak List to see all peaks")
print("• Combine assignment data with detailed multiplets")
print("• Use InChI for structural context")
print("• Toggle display options to focus on specific aspects")

print("\n" + "=" * 60)
print("🚀 Ready to add professional multiplet information!")
