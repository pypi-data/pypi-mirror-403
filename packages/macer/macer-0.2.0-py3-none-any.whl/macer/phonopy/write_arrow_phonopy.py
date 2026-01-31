# -*- coding: utf-8 -*-
"""
This module is adapted from a script originally by ADI, modified by Gemini.
It extracts phonon eigenvectors from a phonopy `band.yaml` file
and generates VESTA files to visualize the phonon modes as arrows.
It now includes functionality to generate the base VESTA file from a POSCAR
using the same logic as example/vesta-translation/poscar2vesta.py.
"""

import numpy as np
import sys
import os
import yaml
from pathlib import Path
import math

#<editor-fold desc="poscar2vesta Conversion Logic">
def _normalize(v):
    norm = math.sqrt(sum(x*x for x in v))
    return [x/norm for x in v] if norm > 0 else v

def _dot(v1, v2):
    return sum(x*y for x, y in zip(v1, v2))

def _length(v):
    return math.sqrt(sum(x*x for x in v))

def _lattice_params(basis):
    a_vec, b_vec, c_vec = basis
    a = _length(a_vec)
    b = _length(b_vec)
    c = _length(c_vec)
    try:
        alpha = math.degrees(math.acos(round(_dot(b_vec, c_vec) / (b * c), 10)))
        beta = math.degrees(math.acos(round(_dot(a_vec, c_vec) / (a * c), 10)))
        gamma = math.degrees(math.acos(round(_dot(a_vec, b_vec) / (a * b), 10)))
    except (ValueError, ZeroDivisionError):
        alpha, beta, gamma = 90.0, 90.0, 90.0
    return a, b, c, alpha, beta, gamma

def _mat_mul_vec(m, v):
    return [
        m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
        m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
        m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2]
    ]

def _invert_3x3(m):
    det = m[0][0] * (m[1][1] * m[2][2] - m[2][1] * m[1][2]) - \
          m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + \
          m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    if abs(det) < 1e-9: return [[0]*3 for _ in range(3)]
    invDet = 1.0 / det
    minv = [[0]*3 for _ in range(3)]
    minv[0][0] = (m[1][1] * m[2][2] - m[2][1] * m[1][2]) * invDet
    minv[0][1] = (m[0][2] * m[2][1] - m[0][1] * m[2][2]) * invDet
    minv[0][2] = (m[0][1] * m[1][2] - m[0][2] * m[1][1]) * invDet
    minv[1][0] = (m[1][2] * m[2][0] - m[1][0] * m[2][2]) * invDet
    minv[1][1] = (m[0][0] * m[2][2] - m[0][2] * m[2][0]) * invDet
    minv[1][2] = (m[1][0] * m[0][2] - m[0][0] * m[1][2]) * invDet
    minv[2][0] = (m[1][0] * m[2][1] - m[2][0] * m[1][1]) * invDet
    minv[2][1] = (m[2][0] * m[0][1] - m[0][0] * m[2][1]) * invDet
    minv[2][2] = (m[0][0] * m[1][1] - m[1][0] * m[0][1]) * invDet
    return minv

def _read_poscar_for_vesta(filepath):
    with open(filepath, 'r') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    title, scale = lines[0], float(lines[1])
    lattice = [[float(x) * scale for x in lines[i].split()] for i in range(2, 5)]
    
    line5_parts = lines[5].split()
    try:
        counts = [int(x) for x in line5_parts]
        elements = [f"E{i+1}" for i in range(len(counts))]
        coord_line_idx = 6
    except ValueError:
        elements, counts = line5_parts, [int(x) for x in lines[6].split()]
        coord_line_idx = 7
    
    atom_types = [el for el, count in zip(elements, counts) for _ in range(count)]
    
    # Handle optional "Selective dynamics" (Fixed by Gemini)
    if lines[coord_line_idx].strip().lower().startswith('s'):
        coord_line_idx += 1

    coord_type = lines[coord_line_idx].lower()
    coord_start_idx = coord_line_idx + 1
    
    atoms = []
    element_counters = {el: 0 for el in elements}
    
    inv_lattice = None
    if 'cart' in coord_type or 'k' in coord_type:
        inv_lattice = _invert_3x3(np.array(lattice).T)

    for i in range(sum(counts)):
        parts = lines[coord_start_idx + i].split()
        coords = [float(x) for x in parts[:3]]
        
        if inv_lattice:
            coords = _mat_mul_vec(inv_lattice, coords)
        
        # Keep coords within [0, 1) if desired, but VESTA handles >1
        coords = [c % 1.0 for c in coords]
        
        el = atom_types[i]
        element_counters[el] += 1
        atoms.append({'element': el, 'coords': coords, 'label': f"{el}{element_counters[el]}"})

    return title, lattice, atoms, list(elements)

def _generate_vesta_content(title, lattice, atoms, unique_elements):
    """
    Generates the full VESTA file content with standard headers, colors, and footer.
    Matches the style of the user provided CORRECTED file.
    """
    a, b, c, alpha, beta, gamma = _lattice_params(lattice)

    # Header
    content = [
        "#VESTA_FORMAT_VERSION 3.5.4\n\n",
        "CRYSTAL\n\n",
        f"TITLE\n{title}\n\n",
        "GROUP\n1 1 P 1\n",
        "SYMOP\n 0.000000  0.000000  0.000000  1  0  0   0  1  0   0  0  1   1\n -1.0 -1.0 -1.0  0 0 0  0 0 0  0 0 0\n",
        "TRANM 0\n 0.000000  0.000000  0.000000  1  0  0   0  1  0   0  0  1\n",
        "LTRANSL\n -1\n 0.000000  0.000000  0.000000  0.000000  0.000000  0.000000\n",
        "LORIENT\n -1   0   0   0   0\n 1.000000  0.000000  0.000000  1.000000  0.000000  0.000000\n 0.000000  0.000000  1.000000  0.000000  0.000000  1.000000\n",
        "LMATRIX\n 1.000000  0.000000  0.000000  0.000000\n 0.000000  1.000000  0.000000  0.000000\n 0.000000  0.000000  1.000000  0.000000\n 0.000000  0.000000  0.000000  1.000000\n 0.000000  0.000000  0.000000\n",
        "CELLP\n",
        f"  {a:.6f}   {b:.6f}   {c:.6f}  {alpha:.6f}  {beta:.6f}  {gamma:.6f}\n",
        f"  0.000000   0.000000   0.000000   0.000000   0.000000   0.000000\n"
    ]

    # STRUC
    content.append("STRUC\n")
    for i, atom in enumerate(atoms):
        el, lbl, (x, y, z) = atom['element'], atom['label'], atom['coords']
        # Adjusted formatting to match CORRECTED: {i+1} {el}        {lbl}
        content.append(f"  {i+1} {el:<9} {lbl:<4} 1.0000   {x:.6f}   {y:.6f}   {z:.6f}    1a       1\n")
        content.append("                            0.000000   0.000000   0.000000  0.00\n")
    content.append("  0 0 0 0 0 0 0\n")

    # THERI (Dummy)
    content.append(f"THERI {len(atoms)}\n")
    for i, atom in enumerate(atoms):
        content.append(f"  {i+1}        {atom['label']} -0.000000\n")
    content.append("  0 0 0\n")
    
    # SHAPE & BOUND (Dummy defaults)
    content.append("SHAPE\n  0       0       0       0   0.000000  0   192   192   192   192\n")
    content.append("BOUND\n       0        1         0        1         0        1\n  0   0   0   0  0\n")
    content.append("SBOND\n  0 0 0 0\n")

    # Colors and Radii - Extended Defaults + Specifics from user example
    cpk_colors = {
        'H': (255, 255, 255), 'He': (217, 255, 255), 'Li': (204, 128, 255), 'Be': (194, 255, 0),
        'B': (255, 181, 181), 'C': (144, 144, 144), 'N': (48, 80, 248), 'O': (254, 3, 0),
        'F': (144, 224, 80), 'Ne': (179, 227, 245), 'Na': (171, 92, 242), 'Mg': (138, 255, 0),
        'Al': (191, 166, 166), 'Si': (240, 200, 160), 'P': (255, 128, 0), 'S': (255, 255, 48),
        'Cl': (31, 240, 31), 'Ar': (128, 209, 227), 'K': (143, 64, 212), 'Ca': (61, 255, 0),
        'Sc': (230, 230, 230), 'Ti': (120, 202, 254), 'V': (166, 166, 171), 'Cr': (138, 153, 199),
        'Mn': (156, 122, 199), 'Fe': (224, 102, 51), 'Co': (240, 144, 160), 'Ni': (80, 208, 80),
        'Cu': (200, 128, 51), 'Zn': (125, 128, 176), 'Ga': (194, 143, 143), 'Ge': (102, 143, 143),
        'As': (189, 128, 227), 'Se': (255, 161, 0), 'Br': (166, 41, 41), 'Kr': (92, 184, 209),
        'Rb': (112, 46, 176), 'Sr': (0, 255, 38), 'Y': (148, 255, 255), 'Zr': (148, 224, 224),
    }
    cpk_radii = {
         'H': 0.8, 'C': 1.0, 'N': 1.0, 'O': 0.74, 'F': 1.0, 'Si': 1.18, 'P': 1.10, 'S': 1.04,
         'Cl': 1.0, 'K': 2.35, 'Ca': 1.97, 'Ti': 1.47, 'Fe': 1.3, 'Co': 1.25, 'Ni': 1.24,
         'Cu': 1.28, 'Zn': 1.33, 'Ga': 1.22, 'Ge': 1.22, 'As': 1.2, 'Se': 1.17, 'Br': 1.14,
         'Sr': 2.15, 'Zr': 1.6, 'Mo': 1.4,
    }

    # SITET
    content.append("SITET\n")
    for i, atom in enumerate(atoms):
        el = atom['element']
        label = atom['label']
        rad = cpk_radii.get(el, 1.2)
        r, g, b_col = cpk_colors.get(el, (200, 200, 200))
        # CORRECTED uses 200 200 200 for the second color triplet in SITET
        content.append(f"  {i+1:<8} {label:<4} {rad:.4f} {r} {g} {b_col} 200 200 200 204  0\n")
    content.append("  0 0 0 0 0 0\n")

    # Vectors Placeholders (Matching VESTA structure)
    content.append("VECTR\n 0 0 0 0 0\n")
    content.append("VECTT\n 0 0 0 0 0\n")
    content.append("SPLAN\n  0   0   0   0\n")

    # Footer
    content.append("LBLAT\n -1\nLBLSP\n -1\nDLATM\n -1\nDLBND\n -1\nDLPLY\n -1\nPLN2D\n  0   0   0   0\nATOMT\n")
    
    # ATOMT
    for i, el in enumerate(unique_elements):
         rad = cpk_radii.get(el, 1.2)
         r, g, b_col = cpk_colors.get(el, (200, 200, 200))
         content.append(f"  {i+1:<9} {el:<3} {rad:.4f} {r} {g} {b_col} {r} {g} {b_col} 204\n")
    content.append("  0 0 0 0 0 0\n")

    # Static Footer Block
    footer_static = """SCENE
 1.000000  0.000000  0.000000  0.000000
 0.000000  1.000000  0.000000  0.000000
 0.000000  0.000000  1.000000  0.000000
 0.000000  0.000000  0.000000  1.000000
  0.000   0.000
  0.000
  1.000
HBOND 0 2

STYLE
DISPF 37753794
MODEL   0  1  0
SURFS   0  1  1
SECTS  32  1
FORMS   0  1
ATOMS   0  0  1
BONDS   1
POLYS   1
VECTS 1.000000
FORMP
  1  1.0   0   0   0
ATOMP
 24  24   0  50  2.0   0
BONDP
  1  16  0.250  2.000 127 127 127
POLYP
 204 1  1.000 180 180 180
ISURF
  0   0   0   0
TEX3P
  1  0.00000E+00  1.00000E+00
SECTP
  1  5.00000E-01  5.00000E-01  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00
CONTR
 0.1 -1 1 1 10 -1 2 5
 2 1 2 1
   0   0   0
   0   0   0
   0   0   0
   0   0   0
HKLPP
 192 0  0.000 254 204 102
UCOLP
   0   1  1.000   0   0   0
COMPS 1
LABEL 1    12  1.000 0
PROJT 0  0.962
BKGRC
 255 255 255
DPTHQ 1 -0.5000  3.5000
LIGHT0 1
 1.000000  0.000000  0.000000  0.000000
 0.000000  1.000000  0.000000  0.000000
 0.000000  0.000000  1.000000  0.000000
 0.000000  0.000000  0.000000  1.000000
 0.000000  0.000000 20.000000  0.000000
 0.000000  0.000000 -1.000000
  26  26  26 255
 179 179 179 255
 255 255 255 255
LIGHT1
 1.000000  0.000000  0.000000  0.000000
 0.000000  1.000000  0.000000  0.000000
 0.000000  0.000000  1.000000  0.000000
 0.000000  0.000000  0.000000  1.000000
 0.000000  0.000000 20.000000  0.000000
 0.000000  0.000000 -1.000000
   0   0   0   0
   0   0   0   0
   0   0   0   0
LIGHT2
 1.000000  0.000000  0.000000  0.000000
 0.000000  1.000000  0.000000  0.000000
 0.000000  0.000000  1.000000  0.000000
 0.000000  0.000000  0.000000  1.000000
 0.000000  0.000000 20.000000  0.000000
 0.000000  0.000000 -1.000000
   0   0   0   0
   0   0   0   0
   0   0   0   0
LIGHT3
 1.000000  0.000000  0.000000  0.000000
 0.000000  1.000000  0.000000  0.000000
 0.000000  0.000000  1.000000  0.000000
 0.000000  0.000000  0.000000  1.000000
 0.000000  0.000000 20.000000  0.000000
 0.000000  0.000000 -1.000000
   0   0   0   0
   0   0   0   0
   0   0   0   0
SECCL 0

TEXCL 0

ATOMM
   0   0   0 255
  25.600
BONDM
   0   0   0 255
 128.000
POLYM
 255 255 255 255
 128.000
SURFM
   0   0   0 255
 128.000
FORMM
 255 255 255 255
 128.000
HKLPM
 255 255 255 255
 128.000
"""
    content.append(footer_static)

    return "".join(content)

def _generate_mcif_content(title, lattice, atoms, vectors):
    """
    Generates the content for a magnetic CIF (.mcif) file.
    """
    a, b, c, alpha, beta, gamma = _lattice_params(lattice)
    
    content = [
        "#======================================================================",
        "# CRYSTAL DATA (generated from VESTA style structure)",
        "#----------------------------------------------------------------------",
        "data_VESTA_phase_1",
        "",
        f"_chemical_name_common                  '{title}'",
        f"_cell_length_a                         {a:.6f}",
        f"_cell_length_b                         {b:.6f}",
        f"_cell_length_c                         {c:.6f}",
        f"_cell_angle_alpha                      {alpha:.6f}",
        f"_cell_angle_beta                       {beta:.6f}",
        f"_cell_angle_gamma                      {gamma:.6f}",
        "_space_group_name_H-M_alt              'P 1'",
        "_space_group_IT_number                 1",
        "",
        "loop_",
        "_space_group_symop_operation_xyz",
        "   'x, y, z'",
        "",
        "loop_",
        "   _atom_site_label",
        "   _atom_site_occupancy",
        "   _atom_site_fract_x",
        "   _atom_site_fract_y",
        "   _atom_site_fract_z",
        "   _atom_site_adp_type",
        "   _atom_site_U_iso_or_equiv",
        "   _atom_site_type_symbol",
    ]
    
    for atom in atoms:
        lbl = atom['label']
        el = atom['element']
        x, y, z = atom['coords']
        # Format: label occ x y z adp iso type
        content.append(f"   {lbl:<10} 1.000 {x:12.6f} {y:12.6f} {z:12.6f}    Uiso  ? {el}")
        
    content.append("")
    content.append("loop_")
    content.append("   _atom_site_moment_label")
    content.append("   _atom_site_moment_crystalaxis_x")
    content.append("   _atom_site_moment_crystalaxis_y")
    content.append("   _atom_site_moment_crystalaxis_z")
    
    for atom, vec in zip(atoms, vectors):
        lbl = atom['label']
        mx, my, mz = vec
        content.append(f"   {lbl:<10} {mx:12.6f} {my:12.6f} {mz:12.6f}")

    content.append("")
    return "\n".join(content)
#</editor-fold>

def _parse_yaml_for_arrows(band_yaml_path: Path):
    """Parses the band.yaml file using pyyaml."""
    if not band_yaml_path.exists():
        raise FileNotFoundError(f"Phonopy band file '{band_yaml_path}' not found.")
    with open(band_yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    if 'phonon' not in data:
        raise ValueError(f"'{band_yaml_path}' does not appear to be a valid Phonopy band.yaml file.")
    return data

def _get_special_points_map(phonopy_data):
    """Creates a map of q-point index to special point label."""
    if 'labels' not in phonopy_data or 'segment_nqpoint' not in phonopy_data:
        return {}
        
    segments = phonopy_data['segment_nqpoint']
    labels = phonopy_data['labels']
    
    # print(f"[ARROW_DEBUG] Found {len(segments)} segments and {len(labels)} label pairs.")

    special_points = {}
    current_idx = 0
    
    for i, seg_len in enumerate(segments):
        if i < len(labels):
            start_label, end_label = [l.upper().replace("GAMMA", "GM") for l in labels[i]]
            special_points[current_idx] = start_label
            end_idx = current_idx + seg_len - 1
            special_points[end_idx] = end_label
            
        current_idx += seg_len
        
    # print(f"[ARROW_DEBUG] Generated special_points map: {special_points}")
    return special_points

def _parse_irreps_yaml(irreps_yaml_path: Path):
    """Parses irreps.yaml to map band indices to labels."""
    if not irreps_yaml_path or not irreps_yaml_path.exists():
        return None, {}
    
    try:
        with open(irreps_yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        q_pos = data.get("q-position")
        normal_modes = data.get("normal_modes", [])
        label_map = {}
        for mode in normal_modes:
            label = mode.get("ir_label")
            indices = mode.get("band_indices", [])
            if label and indices:
                for idx in indices:
                    label_map[idx] = label
        return q_pos, label_map
    except Exception as e:
        print(f"Warning: Failed to parse irreps file: {e}", file=sys.stderr)
        return None, {}

def write_vesta_files_for_arrows(
    band_yaml_path: Path,
    poscar_path: Path,
    output_dir: Path,
    arrow_length: float = 1.5,
    arrow_min_cutoff: float = 0.1,
    arrow_qpoint_gamma: bool = False,
    qpoint_index: int | None = None,
    irreps_yaml_path: Path | None = None,
    target_q_point: list[float] | None = None,
):
    """
    Extracts phonon modes from yaml and writes VESTA files for visualization.
    Generates a base .vesta file from the POSCAR first, then uses it as a template.
    """
    try:
        title, lattice, atoms, unique_elements = _read_poscar_for_vesta(poscar_path)
        base_vesta_content = _generate_vesta_content(title, lattice, atoms, unique_elements)
        
        base_vesta_path = output_dir / f"{poscar_path.stem}.vesta"
        with open(base_vesta_path, 'w') as f:
            f.write(base_vesta_content)
        print(f"  Generated base VESTA file: {base_vesta_path}")

        phonopy_data = _parse_yaml_for_arrows(band_yaml_path)
        irreps_q_pos, irreps_label_map = _parse_irreps_yaml(irreps_yaml_path)

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return

    phonons = phonopy_data.get('phonon', [])
    if not phonons:
        print("Warning: No phonon data found in band.yaml.", file=sys.stderr)
        return

    # --- Determine Mode and Filter Q-points ---
    special_points_map = {i: lbl for i, lbl in enumerate(phonopy_data.get('labels', [])) if lbl}
    
    indices_to_process, labels_for_q_indices = [], {}
    if target_q_point is not None:
        print(f"  Mode: Writing arrows for specific target q-point: {target_q_point}")
        # Pinpoint calculation (usually from qpoints.yaml)
        if len(phonons) == 1:
            indices_to_process = [0]
            if 0 in special_points_map:
                labels_for_q_indices[0] = special_points_map[0]
        else:
            for idx, ph in enumerate(phonons):
                q_pos = ph.get('q-position')
                if q_pos and np.allclose(q_pos, target_q_point, atol=1e-4):
                    if idx not in indices_to_process:
                        indices_to_process.append(idx)
                        if idx in special_points_map:
                            labels_for_q_indices[idx] = special_points_map[idx]
    elif qpoint_index is not None:
        print(f"  Mode: Writing arrows for specified q-point index: {qpoint_index}")
        if 0 <= qpoint_index < len(phonons):
            indices_to_process.append(qpoint_index)
        else:
            print(f"Error: q-point index {qpoint_index} is out of range (0-{len(phonons)-1}).")
            return
    elif arrow_qpoint_gamma:
        print("  Mode: Writing arrows for Gamma point only.")
        for idx, ph in enumerate(phonons):
            if np.linalg.norm(ph.get('q-position', [1,1,1])) < 1e-4:
                if idx not in indices_to_process:
                    indices_to_process.append(idx)
                    labels_for_q_indices[idx] = "GAMMA"
    else: 
        if special_points_map:
            print("  Mode: Writing arrows for special q-points (default).")
            indices_to_process = sorted(special_points_map.keys())
            labels_for_q_indices = special_points_map
        else:
             print("  Mode: Writing arrows for all q-points in file (default).")
             indices_to_process = list(range(len(phonons)))

    if not indices_to_process:
        print("Warning: No q-points matched the specified criteria.")
        return
    
    print(f"  Preparing to write VESTA files for {len(indices_to_process)} q-points...")
    THZ_TO_CM1, natoms = 33.3564095, phonopy_data.get('natom', 0)
    
    with open(base_vesta_path, 'r') as f:
        template_content = f.read()

    for i, q_idx in enumerate(indices_to_process):
        phonon_qpoint = phonons[q_idx]
        q_pos = phonon_qpoint.get('q-position')
        q_pos_str = '%.2f_%.2f_%.2f' % (q_pos[0], q_pos[1], q_pos[2])
        
        folder_idx = i + 1
        
        # When processing a specific target q-point, write directly to the output_dir.
        # Otherwise, create sub-directories for each q-point from the band path.
        current_output_dir = output_dir
        if target_q_point is None and len(indices_to_process) > 1:
            label = labels_for_q_indices.get(q_idx, "QP")
            current_output_dir = output_dir / f"QPOINTS_{folder_idx:03d}-{label}={q_pos_str}"
        
        current_output_dir.mkdir(exist_ok=True, parents=True)
        
        is_irreps_qpoint = False
        if irreps_q_pos is not None and np.allclose(q_pos, irreps_q_pos, atol=1e-4):
            is_irreps_qpoint = True

        for band_idx, band_data in enumerate(phonon_qpoint.get('band', [])):
            eigenvectors = band_data.get('eigenvector')
            if not eigenvectors:
                continue

            # New scaling logic: per-mode normalization
            displacements = np.array([[v[0] for v in eig_vec] for eig_vec in eigenvectors])
            lengths = np.linalg.norm(displacements, axis=1)
            max_disp_length = np.max(lengths) if lengths.size > 0 else 0
            
            scale_factor = 1.0
            if max_disp_length > 1e-8: # Avoid division by zero for non-moving modes
                scale_factor = arrow_length / max_disp_length

            vectr_block = "VECTR\n"
            scaled_vectors = []
            for atom_idx, disp_vec in enumerate(displacements):
                scaled_disp = disp_vec * scale_factor
                if np.linalg.norm(scaled_disp) < arrow_min_cutoff:
                    scaled_disp = np.zeros(3)
                
                scaled_vectors.append(scaled_disp)
                vectr_block += f"{atom_idx+1:>5d}{scaled_disp[0]:10.5f}{scaled_disp[1]:10.5f}{scaled_disp[2]:10.5f}\n"
                vectr_block += f"{atom_idx+1:>5d} 0 0 0 0\n  0 0 0 0 0\n"
            vectr_block += '0 0 0 0 0\n'

            freq_thz = band_data.get('frequency', 0)
            freq_cm1 = freq_thz * THZ_TO_CM1
            filename_q_label = labels_for_q_indices.get(q_idx, q_pos_str)
            
            ir_label_part = ""
            if is_irreps_qpoint:
                ir_label = irreps_label_map.get(band_idx + 1)
                if ir_label:
                    ir_label_part = f"-{ir_label}"
            
            filename_base = f"MODE{band_idx+1:03d}-QPOINTS={filename_q_label}{ir_label_part}-freq={freq_cm1:.2f}cm-1"
            vesta_filename = f"{filename_base}.vesta"
            mcif_filename = f"{filename_base}.mcif"
            
            vectt_block = "VECTT\n"
            for atom_idx in range(natoms):
                vectt_block += f"{atom_idx+1:>5d}  0.500 255   0   0 0\n"
            vectt_block += '0 0 0 0 0\n'
            
            parts = template_content.split('VECTR', 1)
            pre_vectr = parts[0]
            subparts = parts[1].split('SPLAN', 1)
            post_splan = subparts[1]
            
            new_content = pre_vectr + vectr_block + vectt_block + "SPLAN" + post_splan
            
            with open(current_output_dir / vesta_filename, 'w') as f:
                f.write(new_content)
                
            # Generate and write MCIF
            mcif_content = _generate_mcif_content(title, lattice, atoms, scaled_vectors)
            with open(current_output_dir / mcif_filename, 'w') as f:
                f.write(mcif_content)

    print(f"  Done. VESTA and MCIF files for arrows are written in {output_dir}")