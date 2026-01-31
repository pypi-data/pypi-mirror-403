import os
import numpy as np
import xml.etree.ElementTree as ET
import json
from pymatgen.io.ase import AseAtomsAdaptor
from monty.json import MontyEncoder
import tempfile
import shutil

def write_outcar(atoms, energy, outcar_name="OUTCAR"):
    """Write a pymatgen-parsable OUTCAR with more realistic dummy data."""
    forces = atoms.get_forces()
    cart_positions = atoms.get_positions()
    drift = np.mean(forces, axis=0)
    n_atoms = len(atoms)
    volume = atoms.get_volume()

    direct_cell = atoms.get_cell()
    reciprocal_cell = np.linalg.inv(direct_cell).T
    direct_lengths = np.linalg.norm(direct_cell, axis=1)
    reciprocal_lengths = np.linalg.norm(reciprocal_cell, axis=1)
    scaled_positions = atoms.get_scaled_positions()
    symbols = atoms.get_chemical_symbols()
    unique_symbols = sorted(list(set(symbols)))

    with open(outcar_name, "w") as f:
        # --- Dummy Header & Parameters for pymatgen parsing ---
        f.write(" vasp.6.5.0 24Aug23 (build 2023-08-24 10:00:00) complex\n")
        f.write("\n")
        for sym in unique_symbols:
            f.write(f" POTCAR:    PAW_PBE {sym.ljust(2)} 01Jan2000 (PAW_PBE {sym.ljust(2)} 01Jan2000)\n")
        f.write("\n")

        # --- Dummy INCAR section ---
        f.write(" INCAR:\n")
        f.write("   ENCUT  =      520.000\n")
        f.write("   ISMEAR =          0\n")
        f.write("   SIGMA  =        0.05\n")
        f.write("   ISIF   =          3\n")
        f.write("   IBRION =          2\n")
        f.write("\n")

        # --- Dummy Parameters section ---
        f.write(" Parameters (and plain-wave basis):\n")
        f.write(" total plane-waves  NPLWV =      10000\n")
        # --- Dummy table for per-kpoint plane waves ---
        f.write("\n\n\n" + "-"*104 + "\n\n\n")
        f.write(" k-point   1 :       0.0000    0.0000    0.0000\n")
        f.write("  number of plane waves:    10000\n\n")
        f.write(" maximum and minimum number of plane-waves:    10000   10000\n")
        f.write(f"  NELECT =    {float(n_atoms * 6):.4f}\n")
        f.write(f"    k-points           NKPTS =      1   k-points in BZ     NKDIM =      1   number of bands    NBANDS=     10\n")
        f.write(f"  NBANDS =        {n_atoms * 4}\n")
        f.write("\n")

        # --- Lattice and Geometry ---
        f.write(f" volume of cell : {volume:12.4f}\n\n")
        f.write("  direct lattice vectors                    reciprocal lattice vectors\n")
        for i in range(3):
            d = direct_cell[i]
            r = reciprocal_cell[i]
            f.write(f"    {d[0]:12.9f} {d[1]:12.9f} {d[2]:12.9f}    {r[0]:12.9f} {r[1]:12.9f} {r[2]:12.9f}\n")
        f.write("\n")
        f.write("  length of vectors\n")
        f.write(f"    {direct_lengths[0]:12.9f} {direct_lengths[1]:12.9f} {direct_lengths[2]:12.9f}    {reciprocal_lengths[0]:12.9f} {reciprocal_lengths[1]:12.9f} {reciprocal_lengths[2]:12.9f}\n")
        f.write("\n")

        # --- Dummy Electronic Structure ---
        f.write(" E-fermi :   0.0000     alpha+bet :       0.0000     alpha-bet :       0.0000\n\n")

        # --- Positions and Forces ---
        f.write("  position of ions in fractional coordinates (direct lattice)\n")
        for pos in scaled_positions:
            f.write(f"     {pos[0]:11.9f} {pos[1]:11.9f} {pos[2]:11.9f}\n")
        f.write("\n")
        f.write(" POSITION                                       TOTAL-FORCE (eV/Angst)\n")
        f.write(" -----------------------------------------------------------------------------------\n")
        for i in range(n_atoms):
            x, y, z = cart_positions[i]
            fx, fy, fz = forces[i]
            f.write(f" {x:12.5f} {y:12.5f} {z:12.5f}   {fx:12.6f} {fy:12.6f} {fz:12.6f}\n")
        f.write(" -----------------------------------------------------------------------------------\n")
        f.write(f"  total drift:                         {drift[0]:12.6f} {drift[1]:12.6f} {drift[2]:12.6f}\n\n")

        # --- Stress Tensor (converted to kB) ---
        f.write("  TOTAL-FORCE (eV/Angst)  ... external pressure =      0.00 kB  Pullay stress =      0.00 kB\n")
        f.write("  in kB         XX          YY          ZZ          XY          YZ          ZX\n")
        try:
            stress_kBar = atoms.get_stress(voigt=True) * 160.21766208 * 10
            s_vasp = [stress_kBar[0], stress_kBar[1], stress_kBar[2], stress_kBar[5], stress_kBar[3], stress_kBar[4]]
            f.write(f"  Total    {s_vasp[0]:11.4f} {s_vasp[1]:11.4f} {s_vasp[2]:11.4f} {s_vasp[3]:11.4f} {s_vasp[4]:11.4f} {s_vasp[5]:11.4f}\n")
        except Exception:
            f.write("  Total         0.0000      0.0000      0.0000      0.0000      0.0000      0.0000\n")
        f.write("\n")

        # --- Final Energy ---
        f.write(" FREE ENERGIE OF THE ION-ELECTRON SYSTEM (eV)\n")
        f.write(" ---------------------------------------------------\n")
        f.write(f"  free  energy   TOTEN  =  {energy:20.8f} eV\n")
        f.write(f"  energy  without entropy=  {energy:20.8f}  energy(sigma->0) =  {energy:20.8f}\n")
    print(f" Wrote {outcar_name} (with dummy data for pymatgen)")

def write_vasprun_xml(atoms, energy, xml_name="vasprun.xml", steps_data=None):
    """
    Write a minimal yet robust vasprun.xml (10-20KB) parsable by 
    ASE, Pymatgen, and Phonopy.
    """
    if xml_name == os.devnull: return
    if steps_data is None:
        steps_data = [{'atoms': atoms, 'energy': energy, 'forces': atoms.get_forces()}]

    n_atoms = len(atoms)
    symbols = atoms.get_chemical_symbols()
    unique_symbols = []
    symbol_counts = []
    for s in symbols:
        if not unique_symbols or s != unique_symbols[-1]:
            unique_symbols.append(s)
            symbol_counts.append(1)
        else:
            symbol_counts[-1] += 1

    root = ET.Element("modeling")
    
    # 1. Essential Headers
    gen = ET.SubElement(root, "generator")
    ET.SubElement(gen, "i", name="program", type="string").text = "vasp"
    ET.SubElement(gen, "i", name="version", type="string").text = "6.5.0"

    incar = ET.SubElement(root, "incar")
    ET.SubElement(incar, "i", name="ISMEAR", type="int").text = "0"

    kpoints = ET.SubElement(root, "kpoints")
    ET.SubElement(kpoints, "i", name="nkpts", type="int").text = "1"
    var_k = ET.SubElement(kpoints, "varray", name="kpointlist")
    ET.SubElement(var_k, "v").text = " 0.0 0.0 0.0 "
    var_w = ET.SubElement(kpoints, "varray", name="weights")
    ET.SubElement(var_w, "v").text = " 1.0 "

    params = ET.SubElement(root, "parameters")
    elec = ET.SubElement(params, "separator", name="electronic")
    ET.SubElement(elec, "i", name="NELECT", type="float").text = str(float(n_atoms * 6))
    ET.SubElement(elec, "i", name="NELM", type="int").text = "60"

    # 2. Atom Info (Strict formatting for Pymatgen)
    atominfo = ET.SubElement(root, "atominfo")
    ET.SubElement(atominfo, "i", name="atoms").text = f" {n_atoms} "
    ET.SubElement(atominfo, "i", name="types").text = f" {len(unique_symbols)} "
    at_types = ET.SubElement(atominfo, "array", name="atomtypes")
    set_types = ET.SubElement(at_types, "set")
    for sym, count in zip(unique_symbols, symbol_counts):
        rc = ET.SubElement(set_types, "rc")
        for v in [str(count), sym.ljust(3), "1.0", "6.0", f"PAW_PBE {sym}"]:
            ET.SubElement(rc, "c").text = f" {v} "

    at_list = ET.SubElement(atominfo, "array", name="atoms")
    set_atoms = ET.SubElement(at_list, "set")
    sym_to_type = {s: i+1 for i, s in enumerate(unique_symbols)}
    for s in symbols:
        rc = ET.SubElement(set_atoms, "rc")
        ET.SubElement(rc, "c").text = f" {s.ljust(3)} "
        ET.SubElement(rc, "c").text = f" {sym_to_type[s]} "

    # 3. Initial Structure (Required by ASE)
    init_atoms = steps_data[0]['atoms']
    struct_init = ET.SubElement(root, "structure", name="initialpos")
    crystal_init = ET.SubElement(struct_init, "crystal")
    basis_init = ET.SubElement(crystal_init, "varray", name="basis")
    for vec in init_atoms.get_cell():
        ET.SubElement(basis_init, "v").text = f" {vec[0]:22.16f} {vec[1]:22.16f} {vec[2]:22.16f} "
    pos_init = ET.SubElement(struct_init, "varray", name="positions")
    for p in init_atoms.get_scaled_positions():
        ET.SubElement(pos_init, "v").text = f" {p[0]:22.16f} {p[1]:22.16f} {p[2]:22.16f} "

    # 4. Calculation Steps
    for step in steps_data:
        curr_atoms, curr_energy = step['atoms'], step['energy']
        calc = ET.SubElement(root, "calculation")
        
        # scstep (Required by ASE)
        sc = ET.SubElement(calc, "scstep")
        en_sc = ET.SubElement(sc, "energy")
        ET.SubElement(en_sc, "i", name="e_fr_energy").text = f"{curr_energy:.16f}"
        ET.SubElement(en_sc, "i", name="e_wo_entrp").text = f"{curr_energy:.16f}"
        ET.SubElement(en_sc, "i", name="e_0_energy").text = f"{curr_energy:.16f}"

        # Energy Block (Required by Pymatgen)
        en_final = ET.SubElement(calc, "energy")
        ET.SubElement(en_final, "i", name="e_fr_energy").text = f"{curr_energy:.16f}"
        ET.SubElement(en_final, "i", name="e_wo_entrp").text = f"{curr_energy:.16f}"
        ET.SubElement(en_final, "i", name="e_0_energy").text = f"{curr_energy:.16f}"

        # Forces (Required by Phonopy)
        if step.get('forces') is not None:
            f_node = ET.SubElement(calc, "varray", name="forces")
            for f in step['forces']:
                ET.SubElement(f_node, "v").text = f" {f[0]:22.16f} {f[1]:22.16f} {f[2]:22.16f} "

        # Structure (Required by all)
        struct = ET.SubElement(calc, "structure")
        crystal = ET.SubElement(struct, "crystal")
        basis = ET.SubElement(crystal, "varray", name="basis")
        for vec in curr_atoms.get_cell():
            ET.SubElement(basis, "v").text = f" {vec[0]:22.16f} {vec[1]:22.16f} {vec[2]:22.16f} "
        positions = ET.SubElement(struct, "varray", name="positions")
        for p in curr_atoms.get_scaled_positions():
            ET.SubElement(positions, "v").text = f" {p[0]:22.16f} {p[1]:22.16f} {p[2]:22.16f} "

    ET.indent(root, space="  ", level=0)
    ET.ElementTree(root).write(xml_name, encoding="utf-8", xml_declaration=True)
    print(f" Wrote {xml_name} (Minimal Standard)")

def write_calc_results_json(atoms, energy, filename="calc_results.json"):
    """Produce fully compliant CalcResults for pydefect."""
    pmg_struct = AseAtomsAdaptor.get_structure(atoms)
    data = {
        "@module": "pydefect.analyzer.calc_results",
        "@class": "CalcResults",
        "structure": pmg_struct.as_dict(),
        "energy": float(energy),
        "magnetization": 0.0,
        "potentials": [0.0 for _ in range(len(atoms))],
        "electronic_conv": True,
        "ionic_conv": True,
    }
    with open(filename, "w") as f:
        json.dump(data, f, cls=MontyEncoder, indent=2)
    print(f"Wrote {filename} (Directly usable by pydefect)")

def write_pydefect_dummy_files(output_dir="."):
    """Convenience wrapper for pydefect analysis preparation."""
    # unitcell.yaml
    with open(os.path.join(output_dir, "unitcell.yaml"), "w") as f:
        f.write("system: MacerSystem\nvbm: 0.0\ncbm: 5.0\n")
    print("Wrote unitcell.yaml (Dummy)")