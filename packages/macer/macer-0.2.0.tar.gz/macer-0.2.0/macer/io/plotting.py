import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def plot_relaxation_log(prefix, output_dir, energies, steps, forces_hist, stress_hist, isif, atoms):
    fig, ax1 = plt.subplots(figsize=(6, 4))
    
    if energies and len(energies) > 1:
        # Calculate energy difference relative to the final energy
        e_final = energies[-1]
        e_diff = np.abs(np.array(energies) - e_final)
        
        # Replace 0 with a small number to avoid log(0) issues, though abs(diff) will be 0 at the last step
        # A better approach for log plot of convergence is to mask zeros or add epsilon
        # Here we mask zeros for plotting
        mask = e_diff > 1e-12
        
        ax1.semilogy(np.array(steps)[mask], e_diff[mask], color="tab:blue", marker="o", lw=1.0, label="|E - E_final| (eV)")
        ax1.set_ylabel("|E - E_final| (eV) [log scale]", color="tab:blue")
    elif energies:
        # Fallback for single step or single point in list
        ax1.plot(steps, energies, color="tab:blue", marker="o", lw=1.0, label="Total Energy (eV)")
        ax1.set_ylabel("Energy (eV)", color="tab:blue")
    else:
        e_final = atoms.get_potential_energy()
        ax1.scatter([0], [e_final], color="tab:blue", label="Single-point Energy (eV)")
        ax1.set_ylabel("Energy (eV)", color="tab:blue")

    ax1.set_xlabel("Optimization step" if energies else "Single point")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax1.grid(alpha=0.3)

    if energies and forces_hist:
        ax2 = ax1.twinx()
        ax2.semilogy(steps, forces_hist, color="tab:red", marker="s", lw=1.0, label="Fmax (eV/Å)")
        if isif >= 3:
            ax2.semilogy(steps, stress_hist, color="tab:green", marker="^", lw=1.0, label="σmax (eV/Å³)")
        ax2.set_ylabel("Force / Stress [log scale]", color="tab:red")
        ax2.tick_params(axis="y", labelcolor="tab:red")
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        # Combine legends
        ax1.legend(lines + lines2, labels + labels2, loc="upper right")
    else:
        ax1.legend(loc="best")

    plt.title(f"Relaxation progress ({prefix})")
    plt.tight_layout()
    pdf_name = os.path.join(output_dir, f"relax-{prefix}_log.pdf")
    plt.savefig(pdf_name)
    plt.close(fig)
    print(f" Saved detailed log plot -> {pdf_name}")
