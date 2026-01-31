from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from ase.io import read, write, iread
import yaml

# Constants
KB_J = 1.380649e-23     # Boltzmann constant in J/K
E_CHARGE = 1.60217663e-19 # Elementary charge in C
ANGSTROM = 1e-10        # m

def traj2xdatcar(traj_path: str, out_path: str = "XDATCAR", interval: int = 1):
    """
    Convert an ASE .traj file to a VASP XDATCAR file, 
    supporting variable cell (NPT) with full header repetition for each frame.
    Configuration numbers reflect the actual MD steps based on the interval.
    """
    traj_file = Path(traj_path)
    if not traj_file.exists():
        print(f"Error: Trajectory file '{traj_path}' not found.")
        return False
    
    print(f"Reading trajectory: {traj_path} (Interval: {interval})...")
    try:
        configs = list(iread(str(traj_file)))
        if not configs:
            print("Warning: Trajectory is empty.")
            return False
        
        print(f"Loaded {len(configs)} frames.")
        
        # Determine species and counts once
        atoms0 = configs[0]
        symbols = atoms0.get_chemical_symbols()
        species = list(dict.fromkeys(symbols))
        counts = [symbols.count(s) for s in species]
        # Use simple species list for system name to avoid "Al4"
        system_name = "".join(species)

        # Manual XDATCAR writing to match standard VASP format
        with open(out_path, 'w') as f:
            # --- Global Header (Once) ---
            atoms0 = configs[0]
            symbols = atoms0.get_chemical_symbols()
            species = list(dict.fromkeys(symbols))
            counts = [symbols.count(s) for s in species]
            system_name = "".join(species)

            f.write(f"{system_name}\n")
            f.write("    1.000000\n")
            # Initial lattice (placeholder, required by format)
            for vec in atoms0.cell:
                f.write(f"     {vec[0]:11.6f} {vec[1]:11.6f} {vec[2]:11.6f}\n")
            f.write(" " + " ".join(f"{s:>2}" for s in species) + "\n")
            f.write(" " + " ".join(f"{c:16d}" for c in counts) + "\n")

            # --- Frames ---
            for i, atoms in enumerate(configs):
                current_step = i * interval + 1
                
                # Write Lattice for every frame (standard for variable cell MD)
                # But skip for step 1 as it's already in the header
                if current_step > 1:
                    f.write(f"{system_name}\n")
                    f.write("    1.000000\n")
                    for vec in atoms.cell:
                        f.write(f"     {vec[0]:11.6f} {vec[1]:11.6f} {vec[2]:11.6f}\n")
                    f.write(" " + " ".join(f"{s:>2}" for s in species) + "\n")
                    f.write(" " + " ".join(f"{c:16d}" for c in counts) + "\n")
                
                f.write(f"Direct configuration= {current_step:5d}\n")
                scaled_pos = atoms.get_scaled_positions(wrap=True)
                for pos in scaled_pos:
                    f.write(f"   {pos[0]:.8f}   {pos[1]:.8f}   {pos[2]:.8f}\n")
                    
        print(f"Successfully converted {traj_path} -> {out_path}")
        return True
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def print_md_summary(csv_path: str):
    """Print a statistical summary of the md.csv file."""
    import pandas as pd
    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"Error: CSV file '{csv_path}' not found.")
        return
    
    try:
        df = pd.read_csv(csv_path)
        print(f"\nMD Statistical Summary for: {csv_path}")
        print("-" * 50)
        # Check available columns
        available = df.columns.tolist()
        cols = ['T_K', 'P_GPa', 'Epot_eV', 'Etot_eV', 'Vol_A3']
        cols = [c for c in cols if c in available]
        
        summary = df[cols].describe().loc[['mean', 'std', 'min', 'max']]
        print(summary.to_string())
        print("-" * 50)
    except Exception as e:
        print(f"Error reading CSV for summary: {e}")

def plot_md_thermo(csv_path: str, output_path: str = "md_thermo.pdf"):
    """Plot T, Epot, and P from md.csv."""
    import pandas as pd
    try:
        df = pd.read_csv(csv_path)
        if 'time_fs' in df.columns:
            time = df['time_fs'] / 1000.0 # ps
            xlabel = "Time (ps)"
        else:
            time = df['step']
            xlabel = "Step"

        fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
        
        # 1. Temperature
        if 'T_K' in df.columns:
            axes[0].plot(time, df['T_K'], color='C0', label='Temperature')
            axes[0].set_ylabel("Temp (K)")
            axes[0].grid(True, alpha=0.3)
        
        # 2. Potential Energy
        if 'Epot_eV' in df.columns:
            axes[1].plot(time, df['Epot_eV'], color='C1', label='E_pot')
            axes[1].set_ylabel("E_pot (eV)")
            axes[1].grid(True, alpha=0.3)
            # Use relative energy if it's too large
            if np.max(df['Epot_eV']) - np.min(df['Epot_eV']) < 100:
                 axes[1].ticklabel_format(useOffset=False)

        # 3. Pressure
        if 'P_GPa' in df.columns:
            axes[2].plot(time, df['P_GPa'], color='C2', label='Pressure')
            axes[2].set_ylabel("Pressure (GPa)")
            axes[2].set_xlabel(xlabel)
            axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
    except Exception as e:
        print(f"Error plotting thermodynamic properties: {e}")

def plot_cell_evolution(csv_path: str, output_path: str = "md_cell.pdf"):
    """Plot a, b, c and Vol from md.csv."""
    import pandas as pd
    try:
        df = pd.read_csv(csv_path)
        if 'time_fs' in df.columns:
            time = df['time_fs'] / 1000.0 # ps
            xlabel = "Time (ps)"
        else:
            time = df['step']
            xlabel = "Step"

        fig, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
        
        # 1. Lattice constants
        if all(c in df.columns for c in ['a_A', 'b_A', 'c_A']):
            axes[0].plot(time, df['a_A'], label='a')
            axes[0].plot(time, df['b_A'], label='b')
            axes[0].plot(time, df['c_A'], label='c')
            axes[0].set_ylabel("Lattice Constant (Å)")
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
        
        # 2. Volume
        if 'Vol_A3' in df.columns:
            axes[1].plot(time, df['Vol_A3'], color='C3')
            axes[1].set_ylabel("Volume (Å$^3$)")
            axes[1].set_xlabel(xlabel)
            axes[1].grid(True, alpha=0.3)
            
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
    except Exception as e:
        print(f"Error plotting cell evolution: {e}")

def plot_rdf(traj_path: str, output_path: str = "md_rdf.pdf", rmax: float = 8.0, nbins: int = 100, skip_ratio: float = 0.2):
    """Plot Radial Distribution Function (RDF) from trajectory with auto-rmax adjustment."""
    try:
        from ase.geometry.analysis import Analysis
        
        # Read trajectory
        traj = list(iread(traj_path))
        if not traj:
            print("Warning: Trajectory is empty, skipping RDF.")
            return False
        
        # Skip initial equilibration frames
        start_idx = int(len(traj) * skip_ratio)
        subset = traj[start_idx:]
        if not subset:
            subset = [traj[-1]]

        # Auto-adjust rmax based on cell size (rmax < min_cell_dim / 2)
        cell_lengths = subset[0].cell.lengths()
        min_dim = np.min(cell_lengths)
        safe_rmax = min_dim / 2.0 - 0.1
        if rmax > safe_rmax:
            # print(f"  [RDF] Adjusting rmax from {rmax:.2f} to {safe_rmax:.2f} due to cell size ({min_dim:.2f} A)")
            rmax = safe_rmax
        
        # Use first frame symbols to get pairs
        symbols = subset[0].get_chemical_symbols()
        unique_elements = sorted(list(set(symbols)))
        
        ana = Analysis(subset)
        
        plt.figure(figsize=(8, 6))
        
        # 1. Total RDF (Average over all frames)
        rdf_total = ana.get_rdf(rmax=rmax, nbins=nbins)
        # Analysis.get_rdf returns a list of arrays (one for each frame)
        rdf_mean = np.mean(rdf_total, axis=0)
        r = np.linspace(0, rmax, nbins)
        plt.plot(r, rdf_mean, label="Total", color='black', linewidth=2)
        
        # 2. Pairwise RDF (if multiple elements)
        if len(unique_elements) > 1:
            for i in range(len(unique_elements)):
                for j in range(i, len(unique_elements)):
                    el1 = unique_elements[i]
                    el2 = unique_elements[j]
                    try:
                        rdf_pair = ana.get_rdf(rmax=rmax, nbins=nbins, elements=(el1, el2))
                        rdf_p_mean = np.mean(rdf_pair, axis=0)
                        plt.plot(r, rdf_p_mean, label=f"{el1}-{el2}", alpha=0.7)
                    except:
                        continue
        
        plt.xlabel("Distance (Å)")
        plt.ylabel("g(r)")
        plt.title(f"Radial Distribution Function (rmax={rmax:.2f} Å)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return True
    except Exception as e:
        print(f"Error calculating RDF: {e}")
        return False

def md_summary(csv_path: str):
    """Alias for print_md_summary for backward compatibility."""
    print_md_summary(csv_path)

def load_default_charges():
    """Load default oxidation states from pydefect database if available."""
    try:
        import pydefect
        pydefect_path = Path(pydefect.__file__).parent
        yaml_path = pydefect_path / "database" / "oxidation_state.yaml"
        if yaml_path.exists():
            with open(yaml_path, "r") as f:
                return yaml.safe_load(f)
    except:
        pass
    return {}

def detect_interval(input_path):
    """Try to detect interval from XDATCAR or neighboring md.csv."""
    input_path = Path(input_path)
    
    # 1. Try to find an XDATCAR (either the input itself or in the same dir)
    xdatcar_path = None
    if 'XDATCAR' in input_path.name:
        xdatcar_path = input_path
    else:
        # Look for XDATCAR in the same directory
        candidate = input_path.parent / "XDATCAR"
        if candidate.exists():
            xdatcar_path = candidate

    if xdatcar_path:
        try:
            configs = []
            with open(xdatcar_path, 'r') as f:
                for line in f:
                    if "Direct configuration=" in line:
                        val = line.split('=')[1].strip().split()[0]
                        configs.append(int(val))
                    if len(configs) >= 2:
                        break
            if len(configs) >= 2:
                return configs[1] - configs[0]
        except:
            pass

    # 2. Try to find md.csv in the same directory
    csv_path = input_path.parent / "md.csv"
    if csv_path.exists():
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            if 'Step' in df.columns and len(df) >= 2:
                return int(df['Step'].iloc[1] - df['Step'].iloc[0])
        except:
            pass

    return None

def calculate_conductivity(traj_path, temp, dt, interval=1, charges_str="", out_prefix="md_results", charge_msd=False):
    """Calculate ionic conductivity from trajectory."""
    traj_path = Path(traj_path)
    if not traj_path.exists():
        print(f"Error: Trajectory file '{traj_path}' not found.")
        return

    # Auto-detect interval if not provided
    if interval == 1:
        detected = detect_interval(traj_path)
        if detected:
            interval = detected
            print(f"Auto-detected interval: {interval}")

    # Setup output path (same dir as input)
    out_dir = traj_path.parent
    out_prefix_path = out_dir / out_prefix
    log_file = out_prefix_path.with_suffix(".log")

    def log_print(msg):
        print(msg)
        with open(log_file, "a") as f:
            f.write(msg + "\n")

    with open(log_file, "w") as f:
        f.write("---" * 10 + " MD Conductivity Analysis ---" + "---" * 10 + "\n")
        f.write(f"Input: {traj_path}\n")
        f.write(f"Temp: {temp} K\n")
        f.write(f"Time step: {dt} fs\n")
        f.write(f"Interval: {interval}\n")

    log_print(f"Reading trajectory: {traj_path}")
    try:
        # Auto-detect format
        fmt = 'vasp-xdatcar' if 'XDATCAR' in str(traj_path) else None
        # Use iread in a loop to avoid internal np.array issues in ASE/iread/list
        traj = []
        
        try:
            for atoms in iread(str(traj_path), format=fmt):
                traj.append(atoms)
        except Exception as e:
            if fmt == 'vasp-xdatcar':
                print(f"Standard XDATCAR reading failed: {e}. Trying robust mode...")
                import io
                with open(str(traj_path), 'r') as f:
                    content = f.read()
                if not content.strip():
                    raise ValueError("File is empty")
                first_line = content.splitlines()[0]
                pieces = content.split(first_line + '\n')
                traj = []
                for p in pieces:
                    if not p.strip(): continue
                    try:
                        frames = read(io.StringIO(first_line + '\n' + p), index=':', format='vasp-xdatcar')
                        traj.extend(frames)
                    except:
                        continue
                if not traj:
                    raise e
                print(f"Successfully read {len(traj)} frames in robust mode.")
            else:
                raise e
    except Exception as e:
        print(f"Error reading trajectory: {e}")
        if 'XDATCAR' in str(traj_path):
            print("Tip: VASP XDATCAR reading can be strict. Try using 'md.traj' instead for better compatibility.")
        return

    if not traj or len(traj) < 2:
        print("Error: Trajectory is too short or empty. Need at least 2 frames.")
        return

    n_steps = len(traj)
    vol_A3 = traj[0].get_volume()
    vol_m3 = vol_A3 * (ANGSTROM ** 3)
    species = sorted(list(set(traj[0].get_chemical_symbols())))
    
    # Charges
    defaults = load_default_charges()
    charges = defaults.copy()
    if charges_str:
        for p in charges_str.split(','):
            if ':' in p:
                el, q = p.split(':')
                charges[el.strip()] = float(q)

    log_print(f"Steps: {n_steps}, Volume: {vol_A3:.2f} A^3")
    log_print("Using oxidation states:")
    for sp in species:
        q = charges.get(sp, None)
        if q is None:
            q = 0.0
            log_print(f"  {sp}: {q} (Warning: not found in defaults, using 0.0)")
        else:
            log_print(f"  {sp}: {q}")
        charges[sp] = q
    
    # Use stack instead of np.array for safer creation from list of arrays
    pos_list = [atoms.get_scaled_positions() for atoms in traj]
    scaled_pos = np.stack(pos_list)
    
    d_scaled = scaled_pos[1:] - scaled_pos[:-1]
    d_scaled -= np.round(d_scaled)
    cum_disp_scaled = np.zeros_like(scaled_pos)
    cum_disp_scaled[1:] = np.cumsum(d_scaled, axis=0)
    
    cell = traj[0].get_cell()
    unwrapped_real = np.dot(cum_disp_scaled + scaled_pos[0], cell)

    dt_eff = dt * interval
    time_ps = np.arange(n_steps) * dt_eff * 1e-3

    results = {}
    plt.figure(figsize=(8, 6))
    
    for sp in species:
        indices = [i for i, s in enumerate(traj[0].get_chemical_symbols()) if s == sp]
        pos_sp = unwrapped_real[:, indices, :]
        disp_from_0 = pos_sp - pos_sp[0]
        msd = np.mean(np.sum(disp_from_0**2, axis=2), axis=1)
        
        s, e = int(n_steps*0.1), int(n_steps*0.9)
        if e > s + 1:
            slope, intercept = np.polyfit(time_ps[s:e], msd[s:e], 1)
        else:
            slope = 0
            intercept = 0
        
        D_cm2_s = (slope / 6.0) * 1e-8 * 1e4
        q = charges.get(sp, 0.0) * E_CHARGE
        sigma = ((len(indices)/vol_m3) * (q**2) * (slope/6.0*1e-8)) / (KB_J * temp) if q != 0 else 0
        
        results[sp] = {'D': D_cm2_s, 'sigma': sigma}
        log_print(f"\n--- Species: {sp} ---")
        log_print(f"  Diff. Coeff (D): {D_cm2_s:.3e} cm^2/s")
        log_print(f"  Conductivity (sigma_NE): {sigma:.3e} S/m ({sigma*10:.2f} mS/cm)")
        
        plt.plot(time_ps, msd, label=f"{sp} ($D$={D_cm2_s:.1e})")
        if e > s + 1:
            plt.plot(time_ps[s:e], slope * time_ps[s:e] + intercept, '--', alpha=0.5, color='gray')

    total_sigma = sum(r['sigma'] for r in results.values())
    log_print(f"\nTotal Conductivity: {total_sigma*10:.2f} mS/cm")
    
    plt.xlabel("Time (ps)")
    plt.ylabel(r"MSD (\AA^2)")
    plt.title(rf"MSD @ {temp}K (Total $\sigma$ = {total_sigma*10:.2f} mS/cm)")
    plt.legend(); plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plot_file = out_prefix_path.with_suffix(".pdf")
    plt.savefig(plot_file)
    log_print(f"Plot saved to {plot_file}")
    log_print(f"Log saved to {log_file}")

def analyze_cell_evolution(traj_path, dt, skip_ps=0.0, interval=1, out_prefix="cell_evolution", poscar_out="POSCAR-cell-averaged"):
    """Analyze cell parameter evolution (a, b, c, Vol) and calculate averages after skip_ps."""
    traj_path = Path(traj_path)
    if not traj_path.exists():
        print(f"Error: Trajectory file '{traj_path}' not found.")
        return

    # Auto-detect interval if not provided
    if interval == 1:
        detected = detect_interval(traj_path)
        if detected:
            interval = detected
            print(f"Auto-detected interval (frame saving frequency): {interval}")

    # Setup output
    out_dir = traj_path.parent
    if out_prefix.endswith('.pdf'):
        out_prefix = out_prefix[:-4]
    
    # If out_prefix is just a name, put it in out_dir. If it's a path, use it as is.
    if "/" in out_prefix or "\\" in out_prefix:
        out_prefix_path = Path(out_prefix)
    else:
        out_prefix_path = out_dir / out_prefix
        
    log_file = out_prefix_path.with_suffix(".log")

    def log_print(msg):
        print(msg)
        with open(log_file, "a") as f:
            f.write(msg + "\n")

    with open(log_file, "w") as f:
        f.write("---" * 10 + " Cell Evolution Analysis ---" + "---" * 10 + "\n")
        f.write(f"Input: {traj_path}\n")
        f.write(f"Time step (dt): {dt} fs\n")
        f.write(f"Interval (sampling step): {interval}\n")
        f.write(f"Skip first: {skip_ps} ps\n\n")

    log_print(f"Reading trajectory: {traj_path} ...")
    
    # Robust reading logic (copied from calculate_conductivity)
    try:
        fmt = 'vasp-xdatcar' if 'XDATCAR' in str(traj_path) else None
        traj = []
        try:
            for atoms in iread(str(traj_path), format=fmt):
                traj.append(atoms)
        except Exception as e:
            if fmt == 'vasp-xdatcar':
                print(f"Standard XDATCAR reading failed: {e}. Trying robust mode...")
                import io
                with open(str(traj_path), 'r') as f:
                    content = f.read()
                if not content.strip():
                    raise ValueError("File is empty")
                first_line = content.splitlines()[0]
                pieces = content.split(first_line + '\n')
                traj = []
                for p in pieces:
                    if not p.strip(): continue
                    try:
                        frames = read(io.StringIO(first_line + '\n' + p), index=':', format='vasp-xdatcar')
                        traj.extend(frames)
                    except:
                        continue
                if not traj: raise e
                print(f"Successfully read {len(traj)} frames in robust mode.")
            else:
                raise e
    except Exception as e:
        print(f"Error reading trajectory: {e}")
        return

    n_steps = len(traj)
    if n_steps == 0:
        print("Error: Empty trajectory.")
        return

    # Extract Data
    a_list, b_list, c_list, v_list = [], [], [], []
    
    for atoms in traj:
        lengths = atoms.cell.lengths()
        vol = atoms.get_volume()
        a_list.append(lengths[0])
        b_list.append(lengths[1])
        c_list.append(lengths[2])
        v_list.append(vol)
        
    a_arr = np.array(a_list)
    b_arr = np.array(b_list)
    c_arr = np.array(c_list)
    v_arr = np.array(v_list)
    
    dt_eff = dt * interval
    time_ps = np.arange(n_steps) * dt_eff * 1e-3
    
    # Statistics
    mask = time_ps >= skip_ps
    if not np.any(mask):
        log_print(f"Warning: skip_ps ({skip_ps}) is larger than total time ({time_ps[-1]:.2f}). Using last frame only.")
        mask[-1] = True
        
    avg_a = np.mean(a_arr[mask])
    std_a = np.std(a_arr[mask])
    avg_b = np.mean(b_arr[mask])
    std_b = np.std(b_arr[mask])
    avg_c = np.mean(c_arr[mask])
    std_c = np.std(c_arr[mask])
    avg_v = np.mean(v_arr[mask])
    std_v = np.std(v_arr[mask])
    
    log_print(f"Total time: {time_ps[-1]:.2f} ps (Skipped first {skip_ps:.2f} ps)")
    log_print(f"Averaging over: {time_ps[-1] - skip_ps:.2f} ps ({np.sum(mask)} frames)")
    log_print("-" * 40)
    log_print(f"      Mean      Std      (Unit)")
    log_print(f" a:   {avg_a:.4f}    {std_a:.4f}    Ang")
    log_print(f" b:   {avg_b:.4f}    {std_b:.4f}    Ang")
    log_print(f" c:   {avg_c:.4f}    {std_c:.4f}    Ang")
    log_print(f" Vol: {avg_v:.4f}    {std_v:.4f}    Ang^3")
    log_print("-" * 40)
    
    # --- Averaged Structure Calculation ---
    try:
        subset_indices = np.where(mask)[0]
        if len(subset_indices) > 0:
            # 1. Average Cell (Matrix)
            cells = np.array([traj[i].get_cell() for i in subset_indices])
            avg_cell = np.mean(cells, axis=0)

            # 2. Average Positions (Unwrapped Fractional)
            # Use the first frame of the subset as the reference anchor
            # Then unwrap subsequent frames relative to the previous one
            
            # Collect wrapped fractional coordinates
            frac_coords = np.array([traj[i].get_scaled_positions(wrap=True) for i in subset_indices])
            
            # Unwrap
            unwrapped_frac = np.zeros_like(frac_coords)
            unwrapped_frac[0] = frac_coords[0]
            
            for i in range(1, len(frac_coords)):
                # Calculate displacement in fractional coords
                diff = frac_coords[i] - frac_coords[i-1]
                # Adjust for PBC: if diff > 0.5, it likely wrapped around 1->0 (-1 shift)
                # if diff < -0.5, it likely wrapped around 0->1 (+1 shift)
                diff -= np.round(diff)
                unwrapped_frac[i] = unwrapped_frac[i-1] + diff
                
            avg_frac = np.mean(unwrapped_frac, axis=0)
            # Wrap average positions back to [0, 1)
            avg_frac_wrapped = avg_frac % 1.0
            
            # Create Averaged Atoms
            avg_atoms = traj[subset_indices[0]].copy()
            avg_atoms.set_cell(avg_cell)
            avg_atoms.set_scaled_positions(avg_frac_wrapped)
            
            # Output Path
            if "/" in poscar_out or "\\" in poscar_out:
                out_poscar_path = Path(poscar_out)
            else:
                out_poscar_path = out_dir / poscar_out
                
            write(str(out_poscar_path), avg_atoms, format='vasp')
            log_print(f"Averaged structure saved to: {out_poscar_path}")

    except Exception as e:
        log_print(f"Error calculating averaged structure: {e}")

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    
    # Plot Cell Lengths
    ax1.plot(time_ps, a_arr, label='a', alpha=0.8)
    ax1.plot(time_ps, b_arr, label='b', alpha=0.8)
    ax1.plot(time_ps, c_arr, label='c', alpha=0.8)
    
    # Add mean lines (dashed) for the averaged region
    if skip_ps < time_ps[-1]:
        ax1.axvline(x=skip_ps, color='k', linestyle=':', label='Start Avg')
        ax1.hlines(avg_a, skip_ps, time_ps[-1], colors='C0', linestyles='--')
        ax1.hlines(avg_b, skip_ps, time_ps[-1], colors='C1', linestyles='--')
        ax1.hlines(avg_c, skip_ps, time_ps[-1], colors='C2', linestyles='--')

    ax1.set_ylabel("Lattice Constant (Å)")
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_title(f"Cell Parameters Evolution (Skip {skip_ps} ps)")

    # Plot Volume
    ax2.plot(time_ps, v_arr, label='Volume', color='C3', alpha=0.9)
    if skip_ps < time_ps[-1]:
        ax2.axvline(x=skip_ps, color='k', linestyle=':')
        ax2.hlines(avg_v, skip_ps, time_ps[-1], colors='C3', linestyles='--')
        
    ax2.set_ylabel("Volume (Å$^3$)")
    ax2.set_xlabel("Time (ps)")
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_file = out_prefix_path.with_suffix(".pdf")
    plt.savefig(plot_file)
    log_print(f"Plot saved to {plot_file}")
    log_print(f"Log saved to {log_file}")
