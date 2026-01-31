
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import yaml
import math
from pathlib import Path
from ase.io import read

def plot_md_log(csv_path: str, out_prefix: str = "md_plot"):
    """Plot T, P, E from md.csv."""
    if not Path(csv_path).exists():
        print(f"Error: {csv_path} not found.")
        return
    
    df = pd.read_csv(csv_path)
    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    
    # Temperature
    axes[0].plot(df['time_fs'], df['T_K'], color='r')
    axes[0].set_ylabel("Temperature (K)")
    
    # Potential Energy
    axes[1].plot(df['time_fs'], df['Epot_eV'], color='b')
    axes[1].set_ylabel("Potential Energy (eV)")
    
    # Pressure
    if 'P_GPa' in df.columns:
        axes[2].plot(df['time_fs'], df['P_GPa'], color='g')
        axes[2].set_ylabel("Pressure (GPa)")
    
    axes[2].set_xlabel("Time (fs)")
    plt.tight_layout()
    plt.savefig(f"{out_prefix}.pdf")
    print(f"MD plots saved to {out_prefix}.pdf")

def plot_rdf(traj_path: str, out_prefix: str = "rdf_plot", r_max: float = 10.0, n_bins: int = 200):
    """Calculate and plot Radial Distribution Function (RDF) from trajectory."""
    print(f"Reading trajectory for RDF: {traj_path}")
    try:
        # Read the last 20% of frames for better statistics of equilibrated state
        all_configs = read(traj_path, index=':')
        n_frames = len(all_configs)
        start_idx = int(n_frames * 0.8)
        configs = all_configs[start_idx:]
        print(f"Using last {len(configs)} frames for RDF averaging.")
    except Exception as e:
        print(f"Error reading trajectory: {e}")
        return

    from ase.geometry.analysis import Analysis
    
    # Get all unique elements
    species = sorted(list(set(configs[0].get_chemical_symbols())))
    pairs = []
    for i, s1 in enumerate(species):
        for j, s2 in enumerate(species):
            if i <= j:
                pairs.append((s1, s2))

    plt.figure(figsize=(10, 6))
    
    for s1, s2 in pairs:
        print(f"  - Calculating RDF for {s1}-{s2}...")
        all_rdf = []
        for atoms in configs:
            ana = Analysis(atoms)
            # rdf returns [r_values, rdf_values]
            rdf = ana.get_rdf(rmax=r_max, nbins=n_bins, elements=[s1, s2])[0]
            all_rdf.append(rdf)
        
        avg_rdf = np.mean(all_rdf, axis=0)
        r_axis = np.linspace(0, r_max, n_bins)
        plt.plot(r_axis, avg_rdf, label=f"{s1}-{s2}")

    plt.xlabel(r"Distance $r$ ($\AA$)")
    plt.ylabel(r"Radial Distribution $g(r)$")
    plt.title(f"Radial Distribution Function (Averaged over last {len(configs)} frames)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, r_max)
    plt.ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(f"{out_prefix}.pdf")
    print(f"RDF plot saved to {out_prefix}.pdf")

def _parse_phonon_dat(dat_path):
    """
    Parse phonopy-style .dat files. Returns a list of bands, 
    where each band is a list of segments, and each segment is a list of [x, y, (g)].
    """
    if not Path(dat_path).exists():
        print(f"Error: File not found: {dat_path}")
        return []

    bands = []
    current_band = []
    current_segment = []
    
    with open(dat_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                if current_segment:
                    current_band.append(np.array(current_segment))
                    current_segment = []
                continue
            if line.startswith('#'):
                if "mode" in line.lower() and current_band:
                    bands.append(current_band)
                    current_band = []
                continue
            
            parts = [float(x) for x in line.split()]
            current_segment.append(parts)
            
    if current_segment:
        current_band.append(np.array(current_segment))
    if current_band:
        bands.append(current_band)
        
    return bands

def _parse_phonon_yaml(yaml_path):
    """
    Parse phonopy band.yaml or gruneisen.yaml.
    Returns: (bands, labels_dict)
    labels_dict: {'ticks': [dist1, dist2, ...], 'labels': ['G', 'M', ...]}
    """
    if not Path(yaml_path).exists():
        return [], None

    print(f"Parsing YAML for data and labels: {yaml_path}")
    try:
        with open(yaml_path, 'r') as f:
            try:
                from yaml import CLoader as Loader
            except ImportError:
                from yaml import Loader
            data = yaml.load(f, Loader=Loader)
    except Exception as e:
        print(f"Error reading YAML: {e}")
        return [], None

    if 'phonon' not in data:
        return [], None

    nq = len(data['phonon'])
    nband = len(data['phonon'][0]['band'])
    distances = np.array([q['distance'] for q in data['phonon']])
    
    segment_indices = [0]
    if 'segment_nqpoint' in data:
        curr = 0
        for n in data['segment_nqpoint']:
            curr += n
            segment_indices.append(curr)
    else:
        for i in range(1, nq):
            if distances[i] < distances[i-1]:
                segment_indices.append(i)
        segment_indices.append(nq)

    bands = []
    for b_idx in range(nband):
        curr_band = []
        for s_idx in range(len(segment_indices)-1):
            start, end = segment_indices[s_idx], segment_indices[s_idx+1]
            seg_data = []
            for i in range(start, end):
                q = data['phonon'][i]
                row = [q['distance'], q['band'][b_idx]['frequency']]
                if 'gruneisen' in q['band'][b_idx]:
                    row.append(q['band'][b_idx]['gruneisen'])
                seg_data.append(row)
            curr_band.append(np.array(seg_data))
        bands.append(curr_band)

    labels_info = None
    if 'labels' in data and 'segment_nqpoint' in data:
        ticks = []
        labels = []
        curr_idx = 0
        for i, pair in enumerate(data['labels']):
            if i == 0 or data['labels'][i-1][1] != pair[0]:
                ticks.append(distances[curr_idx])
                labels.append(pair[0])
            curr_idx += data['segment_nqpoint'][i]
            actual_idx = min(curr_idx - 1, nq - 1)
            ticks.append(distances[actual_idx])
            labels.append(pair[1])
            
        unique_ticks = []
        unique_labels = []
        for t, l in zip(ticks, labels):
            if not unique_ticks or not np.isclose(t, unique_ticks[-1]):
                unique_ticks.append(t)
                unique_labels.append(l)
            else:
                if l != unique_labels[-1]:
                    unique_labels[-1] = f"{unique_labels[-1]}|{l}"
        labels_info = {'ticks': unique_ticks, 'labels': unique_labels}

    return bands, labels_info

def plot_phonon_band(dat_path, out_pdf="phonon_band.pdf", fmin=None, fmax=None, labels=None, yaml_path=None):
    """Plot phonon dispersion from .dat or .yaml file."""
    labels_info = None
    
    # 1. Load Data
    if str(dat_path).endswith('.yaml'):
        bands, labels_info = _parse_phonon_yaml(dat_path)
    else:
        bands = _parse_phonon_dat(dat_path)
    
    # 2. Load Labels from YAML (if not already loaded from dat_path)
    if labels_info is None:
        y_path = Path(yaml_path) if yaml_path else Path(dat_path).with_suffix('.yaml')
        if y_path.exists():
            _, labels_info = _parse_phonon_yaml(y_path)

    if not bands:
        print(f"Error: No data found in {dat_path}")
        return

    plt.figure(figsize=(8, 6))
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["font.family"] = "serif"
    
    all_x = []
    segment_boundaries = [0]
    
    for i, band in enumerate(bands):
        curr_x = 0
        for j, segment in enumerate(band):
            x = segment[:, 0]
            y = segment[:, 1]
            plt.plot(x, y, color='b', linewidth=1.0, alpha=0.8)
            if i == 0:
                all_x.extend(x)
                curr_x = x[-1]
                segment_boundaries.append(curr_x)

    all_x = np.unique(all_x)
    plt.xlim(all_x[0], all_x[-1])
    if fmin is not None or fmax is not None:
        plt.ylim(fmin, fmax)
    
    plt.ylabel("Frequency (THz)")
    plt.axhline(0, color='k', linestyle='-', linewidth=0.5)
    
    unique_boundaries = np.unique(segment_boundaries)
    if labels:
        label_list = labels.split()
        if len(label_list) == len(unique_boundaries):
            clean_labels = [l.replace("GAMMA", "$\\Gamma$").replace("GM", "$\\Gamma$") for l in label_list]
            plt.xticks(unique_boundaries, clean_labels)
        else:
            print(f"Warning: Number of labels ({len(label_list)}) does not match boundaries ({len(unique_boundaries)})")
            plt.xticks(unique_boundaries)
    elif labels_info:
        clean_labels = [l.replace("GAMMA", "$\\Gamma$").replace("GM", "$\\Gamma$") for l in labels_info['labels']]
        plt.xticks(labels_info['ticks'], clean_labels)
        unique_boundaries = labels_info['ticks']
    else:
        plt.xticks(unique_boundaries)

    for b in unique_boundaries:
        plt.axvline(b, color='k', linestyle='-', linewidth=0.5, alpha=0.5)

    plt.tight_layout()
    plt.savefig(out_pdf)
    plt.close()
    print(f"Phonon band plot saved to {out_pdf}")

def plot_gruneisen_band(dat_path, out_prefix="gruneisen", fmin=None, fmax=None, gmin=None, gmax=None, filter_outliers=3.0, labels=None, yaml_path=None):
    """Plot Gruneisen band and mode parameters from .dat or .yaml file."""
    labels_info = None
    
    # 1. Load Data
    if str(dat_path).endswith('.yaml'):
        bands, labels_info = _parse_phonon_yaml(dat_path)
    else:
        bands = _parse_phonon_dat(dat_path)
    
    # 2. Load Labels from YAML
    if labels_info is None:
        y_path = Path(yaml_path) if yaml_path else Path(dat_path).with_suffix('.yaml')
        if y_path.exists():
            _, labels_info = _parse_phonon_yaml(y_path)

    if not bands:
        print(f"Error: No data found in {dat_path}")
        return

    all_data = []
    for band in bands:
        for segment in band:
            all_data.append(segment)
    data = np.vstack(all_data)
    
    x = data[:, 0]
    y = data[:, 1]
    if data.shape[1] < 3:
        print(f"Error: No Grüneisen data found in {dat_path}. Make sure the file contains 3 columns.")
        return
    g = data[:, 2]
    
    # Determine plot limits first
    # If user provided limits, use them. Otherwise, calculate using outlier-aware defaults.
    q1, q3 = np.percentile(g, [25, 75])
    iqr = q3 - q1
    auto_vmin = q1 - filter_outliers * iqr
    auto_vmax = q3 + filter_outliers * iqr
    
    vmin = gmin if gmin is not None else float(math.floor(max(g.min(), auto_vmin)))
    vmax = gmax if gmax is not None else float(math.ceil(min(g.max(), auto_vmax)))
    
    # Data mask: Only remove points that are truly outside our determined plot range
    mask = (g >= vmin) & (g <= vmax)
    print(f"Plotting range: [{vmin:.2f}, {vmax:.2f}]. Points outside this range are hidden.")
    
    x_filt, y_filt, g_filt = x[mask], y[mask], g[mask]
    
    # 1. Gruneisen Band Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    plt.rcParams["pdf.fonttype"] = 42
    
    # Use TwoSlopeNorm to keep 0 as white (diverging scale)
    from matplotlib.colors import TwoSlopeNorm, Normalize
    vmin = gmin if gmin is not None else g_filt.min()
    vmax = gmax if gmax is not None else g_filt.max()
    
    if vmin < 0 < vmax:
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
        # Generate symmetric number of ticks for the colorbar (equally spaced on graph)
        n_side = 4 
        ticks = np.concatenate([np.linspace(vmin, 0, n_side + 1), 
                                np.linspace(0, vmax, n_side + 1)[1:]])
    else:
        norm = Normalize(vmin=vmin, vmax=vmax)
        ticks = None
    
    sc = ax.scatter(x_filt, y_filt, c=g_filt, cmap='bwr', s=5, norm=norm, alpha=0.8)
    cb = fig.colorbar(sc, ax=ax, ticks=ticks)
    cb.set_label("Grüneisen parameter")
    
    ax.set_ylabel("Frequency (THz)")
    ax.set_xlim(x.min(), x.max())
    if fmin is not None or fmax is not None: ax.set_ylim(fmin, fmax)
    
    segment_boundaries = [0]
    for seg in bands[0]:
        segment_boundaries.append(seg[-1, 0])
    unique_boundaries = np.unique(segment_boundaries)
    
    if labels:
        label_list = labels.split()
        if len(label_list) == len(unique_boundaries):
            clean_labels = [l.replace("GAMMA", "$\\Gamma$").replace("GM", "$\\Gamma$") for l in label_list]
            ax.set_xticks(unique_boundaries)
            ax.set_xticklabels(clean_labels)
    elif labels_info:
        clean_labels = [l.replace("GAMMA", "$\\Gamma$").replace("GM", "$\\Gamma$") for l in labels_info['labels']]
        ax.set_xticks(labels_info['ticks'])
        ax.set_xticklabels(clean_labels)
        unique_boundaries = labels_info['ticks']

    for b in unique_boundaries:
        ax.axvline(b, color='k', linestyle='-', linewidth=0.5, alpha=0.5)

    plt.tight_layout()
    plt.savefig(f"{out_prefix}_band.pdf")
    print(f"Gruneisen band plot saved to {out_prefix}_band.pdf")
    
    # 2. Mode Parameter Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Apply Piecewise Linear Scale to Y-axis if 0 is within range
    if vmin < 0 < vmax:
        from matplotlib.scale import FuncScale
        def forward(y):
            return np.where(y > 0, y / vmax, y / abs(vmin))
        def inverse(y):
            return np.where(y > 0, y * vmax, y * abs(vmin))
        ax.set_yscale('function', functions=(forward, inverse))
        ax.set_yticks(ticks)
    
    ax.scatter(x_filt, g_filt, c=g_filt, cmap='bwr', s=5, norm=norm, alpha=0.8)
    cb2 = fig.colorbar(sc, ax=ax, ticks=ticks)
    cb2.set_label("Grüneisen parameter")
    
    ax.set_ylabel("Mode Grüneisen parameter")
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(vmin, vmax)
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    
    for b in unique_boundaries:
        ax.axvline(b, color='k', linestyle='-', linewidth=0.5, alpha=0.5)
    
    if labels or labels_info:
        ax.set_xticks(unique_boundaries)
        ax.set_xticklabels(clean_labels)

    plt.tight_layout()
    plt.savefig(f"{out_prefix}_mode_parameter.pdf")
    print(f"Mode Gruneisen plot saved to {out_prefix}_mode_parameter.pdf")
    plt.close('all')

def plot_relax_log(log_path: str, out_prefix: str = "relax_plot"):
    """Plot convergence from relax_log.txt."""
    print("plot_relax_log: To be implemented.")
