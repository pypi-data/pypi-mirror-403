#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
band_path.py
Generates phonopy band.conf content from a POSCAR file using SeeK-path.
This module is a refactored version of scripts/seekpath2bandconf.py for reusability.
"""

import re
import math
from pathlib import Path
import numpy as np

# (optional) silence DeprecationWarnings from spglib
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    import seekpath
except ImportError:
    seekpath = None


# ------------------------- POSCAR I/O -------------------------

def read_poscar(poscar_path: Path):
    with poscar_path.open("r", encoding="utf-8") as f:
        raw = [ln.rstrip("\n") for ln in f]

    def next_nonempty(i):
        while i < len(raw) and raw[i].strip() == "":
            i += 1
        return i

    i = next_nonempty(0)
    if i >= len(raw):
        raise ValueError("POSCAR is empty")

    comment = raw[i]; i = next_nonempty(i+1)
    if i >= len(raw):
        raise ValueError("POSCAR: missing scale line")
    scale = float(raw[i].split()[0]); i = next_nonempty(i+1)

    # lattice vectors
    lat = []
    for _ in range(3):
        if i >= len(raw):
            raise ValueError("POSCAR: missing lattice vectors")
        parts = raw[i].split()
        if len(parts) < 3:
            raise ValueError("POSCAR: lattice vector line has < 3 numbers")
        vec = [float(x) for x in parts[:3]]
        lat.append([scale * v for v in vec])
        i = next_nonempty(i+1)

    if i >= len(raw):
        raise ValueError("POSCAR: missing symbols/counts line")

    # Detect VASP5 (symbols line) vs VASP4
    tokens = raw[i].split()

    def is_number(x):
        try:
            float(x); return True
        except Exception:
            return False

    vasp5 = (tokens and any(not is_number(t) for t in tokens))
    if vasp5:
        symbols = tokens[:]                   # e.g. Na Zr P O
        i = next_nonempty(i+1)
        if i >= len(raw):
            raise ValueError("POSCAR: missing counts line after symbols")
        counts = [int(x) for x in raw[i].split()]
        i = next_nonempty(i+1)
        if len(symbols) != len(counts):
            if len(symbols) > len(counts):
                symbols = symbols[:len(counts)]
            else:
                symbols = symbols + [f"E{j+1}" for j in range(len(counts)-len(symbols))]
    else:
        # VASP4: counts here, no symbols line
        counts = [int(x) for x in tokens]
        symbols = []  # no symbols; ATOM_NAME will be blank unless overridden
        i = next_nonempty(i+1)

    # Optional "Selective dynamics"
    if i < len(raw) and raw[i].strip().lower().startswith("selective"):
        i = next_nonempty(i+1)

    # Coordinate type
    if i >= len(raw):
        raise ValueError("POSCAR: missing coordinate type line")
    ctok = raw[i].strip().lower()
    direct = ctok.startswith("d")
    cart = ctok.startswith("c")
    if not (direct or cart):
        raise ValueError(f"POSCAR: unknown coordinate type line: {raw[i]}")
    i = next_nonempty(i+1)

    # Atom coordinates
    nat = sum(counts)
    coord_lines, read = [], 0
    while i < len(raw) and read < nat:
        if raw[i].strip() != "":
            coord_lines.append(raw[i])
            read += 1
        i += 1
    if read < nat:
        raise ValueError("POSCAR: not enough atomic coordinate lines")

    if direct:
        frac = []
        for ln in coord_lines:
            parts = ln.split()
            x, y, z = [float(u) for u in parts[:3]]
            frac.append([x, y, z])
    else:
        A = np.array(lat).T  # columns a,b,c
        Ainv = np.linalg.inv(A)
        frac = []
        for ln in coord_lines:
            parts = ln.split()
            cx, cy, cz = [float(u) for u in parts[:3]]
            f = Ainv @ (scale * np.array([cx, cy, cz]))
            frac.append(f.tolist())

    # kinds: build from counts
    kinds = []
    nsp = len(counts)
    for si in range(nsp):
        kinds.extend([si + 1] * counts[si])

    return {
        "comment": comment,
        "lattice": lat,
        "frac": frac,
        "kinds": kinds,
        "symbols": symbols,  # may be []
        "counts": counts,
    }


# ------------------------- phonopy_disp.yaml -> DIM -------------------------

def read_dim_from_yaml(yaml_path: Path):
    """Return [a,b,c] or a 3x3 matrix or None if not found or file missing."""
    try:
        return _read_dim_yaml_inner(yaml_path)
    except FileNotFoundError:
        return None

def _read_dim_yaml_inner(yaml_path: Path):
    dim = None
    pat_dim = re.compile(r'^\s*dim:\s*"([^"]+)"\s*$', re.IGNORECASE)
    pat_row = re.compile(r'^\s*-\s*\[\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\]\s*$')

    # First, try to read supercell_matrix
    rows, in_super = [], False
    with yaml_path.open("r", encoding="utf-8") as f:
        for ln in f:
            if "supercell_matrix" in ln:
                in_super = True
                continue
            if in_super:
                if ln.strip().startswith("- ["):
                    m = pat_row.match(ln)
                    if m:
                        rows.append([int(m.group(i)) for i in range(1, 4)])
                else:
                    break
    if len(rows) == 3:
        return np.array(rows)  # Return the full 3x3 matrix

    # If no matrix, fall back to reading 'dim' tag
    with yaml_path.open("r", encoding="utf-8") as f:
        for ln in f:
            m = pat_dim.match(ln)
            if m:
                parts = m.group(1).split()
                if len(parts) == 3 and all(p.lstrip("-").isdigit() for p in parts):
                    dim = [int(p) for p in parts]
                break
    
    return dim # Returns list of 3, or None


# ------------------------- helpers -------------------------

def _fmt(x):
    v = float(x)
    if abs(v) < 1e-12:
        v = 0.0
    s = f"{v:.3f}"
    if s == "-0.000":
        s = "0.000"
    return s

def _clean_label(lbl: str, gamma="GM"):
    if lbl is None: return str(lbl)
    if lbl.upper() == "GAMMA":
        return gamma
    return lbl.replace("_", "")


# ------------------------- label chain & band -------------------------

def _build_label_chain(path_segments):
    if not path_segments:
        return []
    chain = []
    s0, e0 = path_segments[0]
    chain.append(s0); chain.append(e0)
    for (s, e) in path_segments[1:]:
        if chain[-1] != s:
            chain.append(s)
        chain.append(e)
    dedup = [chain[0]]
    for lab in chain[1:]:
        if lab != dedup[-1]:
            dedup.append(lab)
    return dedup

def _band_points_one_line_from_seekpath(path_data, gamma_label="GM"):
    pc = path_data["point_coords"]
    segs = path_data["path"]
    chain = _build_label_chain(segs)
    labels = [_clean_label(x, gamma_label) for x in chain]
    pts = [f"{_fmt(pc[lab][0])} {_fmt(pc[lab][1])} {_fmt(pc[lab][2])}" for lab in chain]
    band_line = "BAND = " + "    ".join(pts)
    return band_line, labels, chain  # chain: raw labels for summary


# ------------------------- atom-name override -------------------------

def _parse_atom_override(atom_names, rename, symbols_from_poscar):
    if atom_names:
        return atom_names.split()
    if rename:
        ren = {}
        for pair in rename.split(","):
            old, new = pair.split("=")
            ren[old.strip()] = new.strip()
        if symbols_from_poscar:
            return [ren.get(s, s) for s in symbols_from_poscar]
        else:
            return []
    return symbols_from_poscar


# ------------------------- pretty summary -------------------------

def print_summary(poscar_path: Path, path_data, chain_labels, gamma_cleaned_labels, dim, dim_source):
    try:
        poscar_disp = str(poscar_path.resolve())
    except Exception:
        poscar_disp = str(poscar_path)

    sg_int = path_data.get("spacegroup_international", "?")
    sg_no  = path_data.get("spacegroup_number", "?")
    bravais = path_data.get("bravais_lattice", "?")

    print("------------------------------------------------------------")
    print(f"[Seekpath] POSCAR: {poscar_disp}")
    print(f"[Seekpath] Space group: {sg_int} (No.{sg_no}), Bravais: {bravais}")
    cleaned_labels_str = [str(l) for l in gamma_cleaned_labels if l is not None]
    print(f"[Seekpath] Q-path (labels): {' - '.join(cleaned_labels_str)}")
    print("[Seekpath] Q-points (reciprocal crystal units):")
    pc = path_data["point_coords"]
    for raw_lab, clean_lab in zip(chain_labels, gamma_cleaned_labels):
        k = pc[raw_lab]
        lab_str = str(clean_lab) if clean_lab is not None else "None"
        print(f"  {lab_str:>4s} : {_fmt(k[0])}  {_fmt(k[1])}  {_fmt(k[2])}")
    print(f"[Seekpath] Total q-points: {len(chain_labels)}")

    if dim is None:
        print("[Info] DIM not set. The output band.conf may contain a blank 'DIM =' line.")
    elif isinstance(dim, np.ndarray) and dim.shape == (3, 3):
        print(f"[Seekpath] Supercell Matrix:\n{dim}\n(source: {dim_source})")
    else:
        print(f"[Seekpath] DIM = {dim[0]} {dim[1]} {dim[2]}  (source: {dim_source})")
    print("------------------------------------------------------------")


# ------------------------- main function -------------------------

def generate_band_conf(
    poscar_path: Path,
    yaml_path: Path | None = None,
    out_path: Path = Path("band.conf"),
    gamma_label: str = "GM",
    symprec: float = 1e-3,
    dim_override: str | None = None,
    no_defaults: bool = False,
    atom_names_override: str | None = None,
    rename_override: str | None = None,
    print_summary_flag: bool = True,
):
    """
    Generates a phonopy band.conf file from a POSCAR file using SeeK-path.
    """
    if seekpath is None:
        raise ImportError("seekpath is not installed. Please install it with 'pip install seekpath'")

    pos = read_poscar(poscar_path)
    atom_names = _parse_atom_override(atom_names_override, rename_override, pos["symbols"])
    lattice, positions, numbers = pos["lattice"], pos["frac"], pos["kinds"]
    cell = (lattice, positions, numbers)

    path_data = seekpath.get_path(cell, symprec=symprec)

    band_line, labels, chain_raw = _band_points_one_line_from_seekpath(path_data, gamma_label=gamma_label)

    dim_val = None
    dim_source = None

    # Logic to determine dim_val, prioritizing yaml
    if yaml_path and Path(yaml_path).exists():
        dim_val = read_dim_from_yaml(Path(yaml_path))
        if dim_val is not None:
            dim_source = "phonopy_disp.yaml"
    
    # If yaml reading fails or file doesn't exist, check dim_override
    if dim_val is None and dim_override:
        dim_source = "--dim"
        parts = dim_override.split()
        try:
            int_parts = [int(p) for p in parts]
            if len(int_parts) == 3:
                dim_val = int_parts
            elif len(int_parts) == 9:
                dim_val = np.array(int_parts).reshape(3, 3)
            else:
                print("[WARN] --dim must contain 3 or 9 integers; ignoring it.")
                dim_source = None
        except ValueError:
            print("[WARN] --dim contained non-integer values; ignoring it.")
            dim_source = None

    out_lines = []
    if atom_names:
        out_lines.append(f"ATOM_NAME = {' '.join(atom_names)}")
    else:
        out_lines.append("ATOM_NAME =")

    # Write DIM tag based on the type of dim_val
    if dim_val is None:
        out_lines.append("DIM =")
    elif isinstance(dim_val, np.ndarray) and dim_val.shape == (3, 3):
        dim_str = " ".join(map(str, dim_val.flatten().astype(int)))
        out_lines.append(f"DIM = {dim_str}")
    elif isinstance(dim_val, list) and len(dim_val) == 3:
        out_lines.append(f"DIM = {dim_val[0]} {dim_val[1]} {dim_val[2]}")
    else:
        out_lines.append("DIM =") # Fallback

    out_lines.append(band_line)
    label_str = ' '.join(str(x) for x in labels if x is not None)
    out_lines.append(f"BAND_LABELS = {label_str}")
    if not no_defaults:
        out_lines.append("#FORCE_SETS = READ")
        out_lines.append("FORCE_CONSTANTS = READ")
        out_lines.append("EIGENVECTORS = .TRUE.")

    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {out_path}")

    if print_summary_flag:
        # Adapt dim_val for print_summary which expects a 3-element list or None
        dim_for_summary = None
        if isinstance(dim_val, list) and len(dim_val) == 3:
            dim_for_summary = dim_val
        elif isinstance(dim_val, np.ndarray) and dim_val.shape == (3,3):
             # For summary, just show the matrix itself if it's non-diagonal
             if np.count_nonzero(dim_val - np.diag(np.diagonal(dim_val))) != 0:
                 dim_for_summary = dim_val
             else: # It's a diagonal matrix
                 dim_for_summary = np.diagonal(dim_val).astype(int).tolist()
        print_summary(poscar_path, path_data, chain_raw, labels, dim_for_summary, dim_source)
