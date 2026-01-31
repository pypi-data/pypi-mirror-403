import os
import torch
import numpy as np
import tqdm
import matplotlib.pyplot as plt
from ase.io import read
from ase.units import GPa
from macer.calculator.factory import get_calculator

def calc_r2(true, pred):
    """
    Calculates the square of the Pearson correlation coefficient (r^2).
    This is invariant to constant shifts and scales, reflecting the true 'correlation'.
    """
    if len(true) < 2:
        return np.nan
    # Use correlation matrix [0,1] element
    c = np.corrcoef(true, pred)[0, 1]
    return c**2

def evaluate_model(data_path, ff="mattersim", model_path=None, device="cpu", output_dir="."):
    """
    General model evaluation logic.
    Calculates MAE and Correlation (r^2) for Energy, Forces, and Stress.
    Generates parity plots.
    """
    print(f"Loading data for evaluation: {data_path}")
    # Explicitly set format for XML to avoid ASE auto-detect confusion
    fmt = "vasp-xml" if data_path.lower().endswith(".xml") else None
    atoms_test = read(data_path, index=':', format=fmt)
    print(f"Total structures: {len(atoms_test)}")

    print(f"Initializing calculator: FF={ff}, Model={model_path if model_path else 'Default'}")
    
    # Dynamically build kwargs to handle different calculator requirements
    calc_kwargs = {"device": device}
    calc_kwargs["model_path"] = model_path
    calc_kwargs["model_paths"] = [model_path] # For MACE compatibility
        
    calc = get_calculator(ff_name=ff, **calc_kwargs)
    
    e_true_list, e_pred_list = [], []
    f_true_list, f_pred_list = [], []
    s_true_list, s_pred_list = [], []

    print(f"\nRunning inference via macer.calculator ({device})...")
    for atoms in tqdm.tqdm(atoms_test):
        try:
            e_true = atoms.get_potential_energy() / len(atoms) 
            f_true = atoms.get_forces()
        except Exception as e:
            print(f"Warning: Skipping structure due to missing DFT data: {e}")
            continue
            
        try:
            s_true = atoms.get_stress(voigt=False) / GPa
        except:
            s_true = None

        atoms.set_calculator(calc)
        e_pred = atoms.get_potential_energy() / len(atoms)
        f_pred = atoms.get_forces()
        try:
            s_pred = atoms.get_stress(voigt=False) / GPa
        except:
            s_pred = None

        e_true_list.append(e_true)
        e_pred_list.append(e_pred)
        f_true_list.extend(f_true.flatten())
        f_pred_list.extend(f_pred.flatten())
        if s_true is not None and s_pred is not None:
            s_true_list.extend(s_true.flatten())
            s_pred_list.extend(s_pred.flatten())

    if not e_true_list:
        print("Error: No valid predictions were made.")
        return None

    e_true_arr, e_pred_arr = np.array(e_true_list), np.array(e_pred_list)
    f_true_arr, f_pred_arr = np.array(f_true_list), np.array(f_pred_list)
    s_true_arr, s_pred_arr = np.array(s_true_list), np.array(s_pred_list)

    # Metrics (Using r^2 for correlation as requested)
    mae_e_raw = np.mean(np.abs(e_true_arr - e_pred_arr))
    r2_e = calc_r2(e_true_arr, e_pred_arr)
    
    shift = np.mean(e_true_arr) - np.mean(e_pred_arr)
    e_pred_shifted = e_pred_arr + shift
    mae_e_trend = np.mean(np.abs(e_true_arr - e_pred_shifted))

    mae_f = np.mean(np.abs(f_true_arr - f_pred_arr))
    r2_f = calc_r2(f_true_arr, f_pred_arr)
    
    mae_s, r2_s = None, None
    if s_true_list:
        mae_s = np.mean(np.abs(s_true_arr - s_pred_arr))
        r2_s = calc_r2(s_true_arr, s_pred_arr)

    # Plotting helper
    def plot_parity(true, pred, title, xlabel, ylabel, filename, mae, r2):
        plt.figure(figsize=(6, 6))
        ax = plt.gca()
        ax.scatter(true, pred, alpha=0.5, s=10, edgecolors='none')
        combined = np.concatenate([true, pred])
        lims = [np.min(combined), np.max(combined)]
        ax.plot(lims, lims, 'k--', alpha=0.75, zorder=0)
        ax.set_aspect('equal', adjustable='box')
        ax.set_title(f"{title}\nMAE: {mae:.4f} | r²: {r2:.4f}")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, filename))
        plt.close()

    print(f"Generating enhanced parity plots in {os.path.abspath(output_dir)}...")
    plot_parity(e_true_arr, e_pred_shifted, "Absolute Energy (Shifted)", "True (eV/atom)", "Pred + Shift (eV/atom)", "eval_parity_energy_abs.pdf", mae_e_trend, r2_e)
    e_true_rel = e_true_arr - np.min(e_true_arr)
    e_pred_rel = e_pred_arr - np.min(e_pred_arr)
    plot_parity(e_true_rel, e_pred_rel, "Relative Energy (min=0)", "True Rel (eV/atom)", "Pred Rel (eV/atom)", "eval_parity_energy_rel.pdf", mae_e_trend, r2_e)
    plot_parity(f_true_arr, f_pred_arr, "Atomic Forces", "True (eV/Å)", "Pred (eV/Å)", "eval_parity_forces.pdf", mae_f, r2_f)
    if s_true_list:
        plot_parity(s_true_arr, s_pred_arr, "Virial Stress", "True (GPa)", "Pred (GPa)", "eval_parity_stress.pdf", mae_s, r2_s)

    results = []
    results.append("-" * 55)
    results.append(f"{ 'Metric':<15} | {'MAE':<12} | {'r² (Corr)':<12}")
    results.append("-" * 55)
    results.append(f"{ 'Energy (Raw)':<15} | {mae_e_raw:12.6f} | {r2_e:12.4f}")
    results.append(f"{ 'Energy (Trend)':<15} | {mae_e_trend:12.6f} | {r2_e:12.4f}")
    results.append(f"{ 'Forces':<15} | {mae_f:12.6f} | {r2_f:12.4f}")
    if mae_s is not None:
        results.append(f"{ 'Stress':<15} | {mae_s:12.6f} | {r2_s:12.4f}")
    else:
        results.append(f"{ 'Stress':<15} | Not available in data")
    results.append("-" * 55)
    
    return "\n".join(results)