import numpy as np
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ase.io import read
from ase.eos import EquationOfState
from scipy.optimize import curve_fit
from macer.calculator.factory import get_calculator

def murnaghan(V, E0, B0, Bp, V0):
    """
    Murnaghan equation of state.
    """
    return E0 + B0 * V / (Bp * (Bp - 1)) * ((V0 / V)**(Bp - 1) + (Bp - 1)) - B0 * V0 / (Bp - 1)

def run_bulk_modulus_calculation(
    input_path, strain, n_points, eos, no_eos_plot,
    ff, model, device, modal
):
    """
    Performs a bulk modulus calculation for a single input file.
    """
    input_basename = os.path.basename(input_path)
    output_dir = os.path.dirname(os.path.abspath(input_path))
    if not output_dir:
        output_dir = "."

    # 1. Read initial structure from POSCAR
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    atoms = read(input_path, format="vasp")
    print(f"Read initial structure from {input_path} ({len(atoms)} atoms)")

    # 2. Set up calculator
    current_model_path = model
    if current_model_path is None:
        from macer.defaults import DEFAULT_MODELS, _macer_root, _model_root, resolve_model_path
        default_model_name = DEFAULT_MODELS.get(ff)
        if default_model_name:
            current_model_path = resolve_model_path(default_model_name)
    else:
        from macer.defaults import resolve_model_path
        current_model_path = resolve_model_path(current_model_path)

    calc_kwargs = {
        "model_path": current_model_path,
        "device": device,
        "modal": modal,
    }
    if ff == "mace":
        calc_kwargs["model_paths"] = [calc_kwargs.get("model_path")]
        del calc_kwargs["model_path"]

    atoms.calc = get_calculator(ff_name=ff, **calc_kwargs)
    print(f"Using force field: {ff} on device: {device}")
    if current_model_path:
        print(f"Using model: {current_model_path}")

    # 3. Volume scaling and energy calculation
    print(f"\nCalculating energies for {n_points} volume points with strain range +/- {strain*100:.1f}%")
    volumes = []
    energies = []
    for scale in np.linspace(1 - strain, 1 + strain, n_points):
        scaled_atoms = atoms.copy()
        scaled_atoms.calc = atoms.calc
        scaled_atoms.set_cell(atoms.get_cell() * scale**(1/3.0), scale_atoms=True)
        
        energy = scaled_atoms.get_potential_energy()
        volume = scaled_atoms.get_volume()
        volumes.append(volume)
        energies.append(energy)
        print(f"  Volume scale: {scale:.4f}, Volume: {volume:.3f} A^3, Energy: {energy:.6f} eV")
    
    volumes = np.array(volumes)
    energies = np.array(energies)

    # 4. Fit E-V curve
    plot_filename = os.path.join(output_dir, f"eos-{input_basename}.pdf")

    if eos == "murnaghan":
        print("\nFitting data with Murnaghan EoS...")
        try:
            # Initial guess
            E0_guess = min(energies)
            V0_guess = volumes[np.argmin(energies)]
            B0_guess = 100 / 160.21766208 # ~100 GPa in eV/A^3
            Bp_guess = 4.0
            
            popt, pcov = curve_fit(murnaghan, volumes, energies, p0=[E0_guess, B0_guess, Bp_guess, V0_guess])
            E0, B0, Bp, V0 = popt

            B0_GPa = B0 * 160.21766208

            print("\n--- Murnaghan EoS Fit Results ---")
            print(f"Equilibrium volume (V0): {V0:.4f} A^3")
            print(f"Minimum energy (E0): {E0:.6f} eV")
            print(f"Bulk modulus (B0): {B0_GPa:.3f} GPa")
            print(f"Bulk modulus prime (B0'): {Bp:.3f}")

            if not no_eos_plot:
                v_fit = np.linspace(min(volumes), max(volumes), 200)
                plt.figure()
                plt.plot(volumes, energies, 'o', label='Calculated data')
                plt.plot(v_fit, murnaghan(v_fit, *popt), '-', label='Murnaghan fit')
                plt.xlabel('Volume (Å³)')
                plt.ylabel('Energy (eV)')
                plt.legend()
                plt.savefig(plot_filename)
                print(f"E-V curve plotted to: {plot_filename}")

        except Exception as e:
            print(f"\nError during Murnaghan fitting: {e}")
            return

    elif eos == "birchmurnaghan":
        print("\nFitting data with Birch-Murnaghan EoS (ASE)...")
        try:
            eos = EquationOfState(volumes, energies, eos="birchmurnaghan")
            v0, e0, B = eos.fit()
            
            B_GPa = B * 160.21766208

            print("\n--- Birch-Murnaghan EoS Fit Results ---")
            print(f"Equilibrium volume (V0): {v0:.4f} A^3")
            print(f"Minimum energy (E0): {e0:.6f} eV")
            print(f"Bulk modulus (B0): {B_GPa:.3f} GPa")

            if not no_eos_plot:
                eos.plot(filename=plot_filename)
                print(f"E-V curve plotted to: {plot_filename}")

        except Exception as e:
            print(f"\nError fitting Birch-Murnaghan EoS: {e}")
            return

    print("\nBulk modulus calculation finished.")

def get_bulk_modulus_and_volume(atoms, calc_args, strain=0.05, n_points=7):
    """
    Calculates and returns the bulk modulus and equilibrium volume per atom.
    `calc_args` should be a namespace or dict with ff, model, device, modal.
    """
    # 1. Set up calculator
    current_model_path = calc_args.model
    if current_model_path is None:
        from macer.defaults import DEFAULT_MODELS, _macer_root, resolve_model_path
        default_model_name = DEFAULT_MODELS.get(calc_args.ff)
        if default_model_name:
            current_model_path = resolve_model_path(default_model_name)
    else:
        from macer.defaults import resolve_model_path
        current_model_path = resolve_model_path(current_model_path)

    calculator_kwargs = {
        "model_path": current_model_path,
        "device": calc_args.device,
        "modal": calc_args.modal,
    }
    if calc_args.ff == "mace":
        calculator_kwargs["model_paths"] = [calculator_kwargs.get("model_path")]
        del calculator_kwargs["model_path"]

    # Important: create a copy of atoms to not modify the original one with a calculator
    atoms_copy = atoms.copy()
    atoms_copy.calc = get_calculator(ff_name=calc_args.ff, **calculator_kwargs)

    # 2. Volume scaling and energy calculation
    volumes = []
    energies = []
    for scale in np.linspace(1 - strain, 1 + strain, n_points):
        scaled_atoms = atoms_copy.copy()
        scaled_atoms.calc = atoms_copy.calc
        scaled_atoms.set_cell(atoms_copy.get_cell() * scale**(1/3.0), scale_atoms=True)
        
        energy = scaled_atoms.get_potential_energy()
        volume = scaled_atoms.get_volume()
        volumes.append(volume)
        energies.append(energy)
    
    volumes = np.array(volumes)
    energies = np.array(energies)

    # 3. Fit E-V curve (using birchmurnaghan as it's robust)
    try:
        eos = EquationOfState(volumes, energies, eos="birchmurnaghan")
        v0, e0, B = eos.fit()
    except Exception as e:
        print(f"Warning: Could not fit E-V curve to get bulk modulus: {e}")
        return None, None # Return None on failure

    # 4. Return B in GPa and V0 per atom
    B_GPa = B * 160.21766208
    v0_per_atom = v0 / len(atoms)
    return B_GPa, v0_per_atom
