#!/usr/bin/env python3
"""
CSV importer for compound NMR data.

Heuristically parses CSV files that contain columns for compound name and
1H/13C NMR descriptions. Produces a list of compound dictionaries compatible
with the enhanced GUI expectations:

[
  {
    "name": str,
    "smiles": Optional[str],
    "inchi": Optional[str],
    "nmr_data": {
        "1H": {"frequency": Optional[str], "solvent": Optional[str], "peaks": [ ... ]},
        "13C": {"frequency": Optional[str], "solvent": Optional[str], "peaks": [ ... ]}
    }
  },
  ...
]

Notes:
- For 1H free-text like "1H NMR (300 MHz, CDCl3) δ 7.17–7.28 (m, 5H); 2.09 (s, 3H)" we
  reuse NMRDataParser to extract peaks.
- For 13C lists like "13C NMR (75 MHz, CDCl3) δ 19.4, 37.0, 48.0, ..." we parse all floats
  and create singlet peaks.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Dict, List, Optional, Callable
import json

from nmr_data_input import NMRDataParser


NAME_FIELDS = [
    "name", "compound", "compound_name", "title", "compound name"
]
SMILES_FIELDS = [
    "smiles", "smile", "smile_string"
]
INCHI_FIELDS = [
    "inchi", "inchi_key", "inchikey", "InChI", "InChIKey"
]


def _find_col(header: List[str], candidates: List[str]) -> Optional[str]:
    low = [h.strip().lower() for h in header]
    for cand in candidates:
        if cand.lower() in low:
            return header[low.index(cand.lower())]
    return None


def _find_first_matching(header: List[str], predicate) -> Optional[str]:
    for h in header:
        if predicate(h):
            return h
    return None


from typing import Tuple


def _extract_freq_solvent(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract frequency like '300 MHz' and solvent like 'CDCl3' from parentheses.

    Returns (frequency_str, solvent_str)
    """
    if not text:
        return None, None
    m = re.search(r"\(([^)]*)\)", text)
    if not m:
        return None, None
    inside = m.group(1)
    # Find MHz piece
    freq = None
    fm = re.search(r"(\d+\.?\d*)\s*MHz", inside, flags=re.IGNORECASE)
    if fm:
        freq = f"{fm.group(1)} MHz"
    # Find solvent token (simple heuristic: token with letters/numbers and optional subscripts)
    # Prefer common solvents
    solvents = [
        "CDCl3", "DMSO-d6", "DMSO-d6", "CD3OD", "CD3CN", "C6D6", "C6D6", "Acetone-d6",
        "D2O", "Toluene-d8", "DMF-d7"
    ]
    solvent = None
    for s in solvents:
        if s.lower() in inside.lower():
            solvent = s
            break
    if solvent is None:
        # Fallback: last token with letters/numbers
        toks = re.split(r"[,;/]", inside)
        toks = [t.strip() for t in toks if t.strip()]
        for t in reversed(toks):
            if re.search(r"[A-Za-z]", t):
                solvent = t
                break
    return freq, solvent


def _parse_c13_list(text: str) -> List[Dict]:
    """Parse simple 13C list like 'δ 19.4, 37.0, 48.0' into singlet peaks."""
    if not text:
        return []
    # Strip prefix like '13C NMR (...) δ'
    t = re.sub(r"^\s*13C\s*NMR[^:]*:?", "", text, flags=re.IGNORECASE).strip()
    t = re.sub(r"^\s*[δ:]\s*", "", t)
    # Replace en-dash and em-dash with hyphen
    t = t.replace("–", "-").replace("—", "-")
    # Find all floats
    floats = re.findall(r"\d+\.\d+|\d+", t)
    peaks = []
    for f in floats:
        try:
            shift = float(f)
        except ValueError:
            continue
        peaks.append({
            "shift": shift,
            "multiplicity": "s",
            "integration": 1,
            "coupling": [],
            "intensity": 100
        })
    return peaks


def _coalesce_fields(row: Dict[str, str], headers: List[str], patterns: List[str]) -> Optional[str]:
    """Return the first non-empty field whose header contains any of the patterns."""
    pats = [p.lower() for p in patterns]
    for h in headers:
        val = row.get(h)
        if not val:
            continue
        hl = h.lower()
        if any(p in hl for p in pats):
            if val.strip():
                return val.strip()
    return None


def load_csv_database(csv_path: str, name_query: Optional[str] = None, max_records: Optional[int] = None) -> List[Dict]:
    """Load a CSV file and parse a list of compounds with NMR data.

    The importer tries to auto-detect columns:
    - name: any of NAME_FIELDS
    - smiles: any of SMILES_FIELDS (optional)
    - inchi: any of INCHI_FIELDS (optional)
    - 1H text: header containing '1h' and optionally 'nmr' or 'proton'
    - 13C text: header containing '13c' and optionally 'nmr' or 'carbon'
    It also accepts generic 'proton'/'carbon' or any header containing 'ppm'/'δ'.
    """
    compounds: List[Dict] = []
    parser = NMRDataParser()

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        # Identify primary columns
        name_col = _find_col(headers, NAME_FIELDS) or _find_first_matching(
            headers, lambda h: "name" in h.lower())
        h1_col = _find_first_matching(headers, lambda h: "1h" in h.lower() and ("nmr" in h.lower() or True))
        c13_col = _find_first_matching(headers, lambda h: "13c" in h.lower() and ("nmr" in h.lower() or True))

        # Fallbacks
        if not h1_col:
            h1_col = _find_first_matching(headers, lambda h: "proton" in h.lower() or ("nmr" in h.lower() and "1" in h.lower()))
        if not c13_col:
            c13_col = _find_first_matching(headers, lambda h: "carbon" in h.lower() or ("nmr" in h.lower() and "13" in h.lower()))

        smiles_col = _find_col(headers, SMILES_FIELDS)
        inchi_col = _find_col(headers, INCHI_FIELDS)

        count = 0
        query = (name_query or "").strip().lower()
        for row in reader:
            name = (row.get(name_col) or "").strip() if name_col else ""
            if not name:
                # Try to find any non-empty textual identifier
                name = _coalesce_fields(row, headers, ["name", "title", "compound"]) or "Unknown"

            if query and query not in name.lower():
                # Try a few other fields if name doesn't match
                if not any((row.get(col) or "").strip().lower().find(query) != -1 for col in (SMILES_FIELDS + INCHI_FIELDS) if isinstance(col, str)):
                    continue

            smiles = (row.get(smiles_col) or "").strip() if smiles_col else ""
            inchi = (row.get(inchi_col) or "").strip() if inchi_col else ""

            h1_text = (row.get(h1_col) or "").strip() if h1_col else None
            c13_text = (row.get(c13_col) or "").strip() if c13_col else None

            # Additional heuristic: if no explicit columns, try any field containing '1H'/'13C'
            if not h1_text:
                h1_text = _coalesce_fields(row, headers, ["1h", "proton", "δ ", "delta", "ppm"])
            if not c13_text:
                c13_text = _coalesce_fields(row, headers, ["13c", "carbon", "δ ", "delta", "ppm"])

            nmr_data: Dict[str, Dict] = {}

            # Parse 1H
            if h1_text and any(x in h1_text.lower() for x in ["1h", "δ", ")", "("]):
                freq, solvent = _extract_freq_solvent(h1_text)
                peaks_h1 = parser.parse_nmr_text(h1_text, nucleus="1H")
                if peaks_h1:
                    nmr_data["1H"] = {
                        "frequency": freq,
                        "solvent": solvent,
                        "peaks": peaks_h1,
                    }

            # Parse 13C
            if c13_text:
                freq_c, solv_c = _extract_freq_solvent(c13_text)
                peaks_c13 = parser.parse_nmr_text(c13_text, nucleus="13C")
                if not peaks_c13:
                    peaks_c13 = _parse_c13_list(c13_text)
                if peaks_c13:
                    nmr_data["13C"] = {
                        "frequency": freq_c,
                        "solvent": solv_c,
                        "peaks": peaks_c13,
                    }

            if not nmr_data:
                # Skip rows without NMR content
                continue

            compounds.append({
                "name": name,
                "smiles": smiles or None,
                "inchi": inchi or None,
                "nmr_data": nmr_data,
            })
            count += 1
            if max_records and count >= max_records:
                break

    return compounds


def load_json_database(json_path: str, name_query: Optional[str] = None, smiles_query: Optional[str] = None,
                       max_records: Optional[int] = 50) -> List[Dict]:
    """Load JSON or JSON lines file, parsing records into the common structure.

    Heuristically detects fields for name, SMILES, InChI, and 1H/13C text. Supports
    large JSONL by streaming line-by-line.
    """
    results: List[Dict] = []
    parser = NMRDataParser()
    name_q = (name_query or "").strip().lower()
    smiles_q = (smiles_query or "").strip().lower()

    # Try to detect JSON lines vs array
    with open(json_path, "r", encoding="utf-8") as f:
        first_chunk = f.read(4096)
        f.seek(0)
        is_jsonl = "\n" in first_chunk and first_chunk.strip().startswith("{")

        def process_record(rec: Dict) -> Optional[Dict]:
            headers = list(rec.keys())
            # Name
            name = rec.get("name") or rec.get("compound_name") or rec.get("IUPAC_name") or rec.get("iupac_name")
            if not name:
                # Try any text field
                for k in headers:
                    v = rec.get(k)
                    if isinstance(v, str) and len(v) > 0 and "name" in k.lower():
                        name = v
                        break
            name = (name or "").strip()

            if name_q and name_q not in name.lower():
                # If name doesn't match, try SMILES
                smi = (rec.get("smiles") or rec.get("SMILES") or rec.get("canonical_smiles") or "").strip()
                if not (smiles_q and smiles_q in smi.lower()):
                    return None

            # Identify 1H and 13C text fields
            def pick_text(keys_like: List[str]) -> Optional[str]:
                for k in headers:
                    v = rec.get(k)
                    if not isinstance(v, str):
                        continue
                    lowk = k.lower()
                    if any(tag in lowk for tag in keys_like):
                        if any(tok in v.lower() for tok in ["1h", "13c", "δ", "ppm", "nmr", "hz", " s, ", " m, "]):
                            return v
                return None

            h1_text = pick_text(["1h", "hnmr", "proton"]) or rec.get("nmr_1h")
            c13_text = pick_text(["13c", "cnmr", "carbon"]) or rec.get("nmr_13c")

            nmr_data: Dict[str, Dict] = {}
            if h1_text:
                freq, solvent = _extract_freq_solvent(h1_text)
                peaks_h1 = parser.parse_nmr_text(h1_text, nucleus="1H")
                if peaks_h1:
                    nmr_data["1H"] = {"frequency": freq, "solvent": solvent, "peaks": peaks_h1}
            if c13_text:
                freq_c, solv_c = _extract_freq_solvent(c13_text)
                peaks_c13 = parser.parse_nmr_text(c13_text, nucleus="13C")
                if not peaks_c13:
                    peaks_c13 = _parse_c13_list(c13_text)
                if peaks_c13:
                    nmr_data["13C"] = {"frequency": freq_c, "solvent": solv_c, "peaks": peaks_c13}

            if not nmr_data:
                return None

            return {
                "name": name or "Unknown",
                "smiles": rec.get("smiles") or rec.get("SMILES"),
                "inchi": rec.get("inchi") or rec.get("InChI") or rec.get("InChIKey"),
                "nmr_data": nmr_data,
            }

        if is_jsonl:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                out = process_record(rec)
                if out:
                    results.append(out)
                    if max_records and len(results) >= max_records:
                        break
        else:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    data = data.get("records") or data.get("data") or []
            except json.JSONDecodeError:
                data = []
            for rec in data:
                if not isinstance(rec, dict):
                    continue
                out = process_record(rec)
                if out:
                    results.append(out)
                    if max_records and len(results) >= max_records:
                        break

    return results
