import argparse
import os
import sys
import glob
import csv
import numpy as np
from pathlib import Path

from ase.io import read, write
from ase.io.trajectory import Trajectory
from ase.md.npt import NPT
from ase.md.verlet import VelocityVerlet
from ase.build import make_supercell
from ase.md.langevin import Langevin
# NVT: prefer Nose–Hoover chain; fallback to Berendsen if unavailable.
try:
    from ase.md.nose_hoover_chain import NoseHooverChainNVT as NVT_NHC
except Exception:
    NVT_NHC = None
try:
    from ase.md.nvtberendsen import NVTBerendsen as NVT_Ber
except Exception:
    NVT_Ber = None
try:
    from ase.md.nptberendsen import NPTBerendsen as NPT_Ber
except Exception:
    NPT_Ber = None

from ase.md.logger import MDLogger
from ase.geometry import cellpar_to_cell
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary, ZeroRotation
import ase.units as u


import numpy as np
from pathlib import Path

from ase import units as u
from ase.io import read, write
from ase.io.trajectory import Trajectory
from ase.md.langevin import Langevin
from ase.md.npt import NPT
from ase.md.verlet import VelocityVerlet
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary, ZeroRotation
from ase.build import make_supercell

from macer.calculator.factory import get_calculator, get_available_ffs
from macer.defaults import DEFAULT_MODELS, resolve_model_path, DEFAULT_DEVICE
from macer.utils.validation import check_poscar_format
from macer.utils.logger import Logger
from macer.molecular_dynamics.gibbs import run_gibbs_workflow

try:
    from ase.md.nptberendsen import NPTBerendsen as NPT_Ber
    from ase.md.nvtberendsen import NVTBerendsen as NVT_Ber
except ImportError:
    NPT_Ber = None
    NVT_Ber = None

# --- Defaults -----------------------------------------------------------------

from macer.defaults import DEFAULT_MODELS, _macer_root, _model_root, DEFAULT_DEVICE, resolve_model_path

# Unit conversion: 1 (eV/Å^3) = 160.21766208 GPa
EV_A3_TO_GPa = 160.21766208


def parse_poscar_header_for_xdatcar(poscar_path="POSCAR"):
    """Read species and counts from POSCAR header for XDATCAR blocks."""
    atoms = read(poscar_path, format="vasp")
    all_symbols = atoms.get_chemical_symbols()
    species = list(dict.fromkeys(all_symbols))
    counts = [all_symbols.count(spec) for spec in species]
    return species, counts


def get_md_parser():
    # Determine default force field based on installed extras
    available_ffs = get_available_ffs()
    _dynamic_default_ff = available_ffs[0] if available_ffs else None

    parser = argparse.ArgumentParser(
        description="Minimal NpT, NVT (NTE), or NVE MD with MACE + ASE (inputs: POSCAR; outputs: md.traj/md.log/XDATCAR/md.csv)",
        epilog="""
Examples:
  # 1. NPT Auto-setting: Automatic barostat (via Bulk Modulus estimation) and thermostat (40 * dt)
  macer md -p POSCAR --ensemble npt --temp 300 --press 0.0 --tstep 2.0 --ff mattersim

  # 2. NVT Auto-setting: Automatic thermostat coupling (ttau = 40 * tstep)
  macer md -p POSCAR --ensemble nvt --temp 600 --nsteps 10000 --tstep 1.0

  # 3. Manual NPT: Explicitly set coupling constants (ttau=100fs, ptau=1000fs)
  macer md -p POSCAR --ensemble npt --temp 600 --press 1.0 --ttau 100 --ptau 1000 --nsteps 20000 --tstep 2.0

  # 4. Langevin MD: Using explicit friction coefficient (ps^-1) for NVT
  macer md -p POSCAR --ensemble nvt --temp 300 --thermostat langevin --friction 10.0 --tstep 1.0

  # 5. NVE (Microcanonical): Initial temp 300 K, constant volume and energy
  macer md -p POSCAR --ensemble nve --temp 300 --nsteps 5000 --tstep 0.5

  # 6. Gibbs Free Energy (Temperature Integration):
  macer md -p POSCAR --gibbs --temp 100 --temp-end 1000 --temp-step 50 --tstep 2.0 --nsteps 50000 --equil-steps 10000

  # 7. Gibbs with QHA Reference (Absolute Free Energy):
  macer md -p POSCAR --gibbs --temp 100 --temp-end 1000 --qha-ref thermal_properties.yaml --nsteps 50000 --equil-steps 10000
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False # Don't add help here, main parser will handle it
    )

    parser.add_argument("--poscar", "-p", type=str, default=None,
                        help="Input POSCAR file (VASP format atomic structure input).")
    parser.add_argument("--cif", "-c", type=str, default=None,
                        help="Input CIF file (will be converted to POSCAR).")

    # MLFF Settings
    mlff_group = parser.add_argument_group('MLFF Model Settings')
    mlff_group.add_argument("--model", default=None, help="Path to the MLFF model file. Defaults to a specific model for each FF if not provided.")
    mlff_group.add_argument("--ff", type=str, default=_dynamic_default_ff, choices=get_available_ffs(), help="Force field to use.")
    mlff_group.add_argument("--modal", type=str, default=None, help="Modal for SevenNet model, if required.")
    mlff_group.add_argument("--device", choices=["cpu", "mps", "cuda"], default=DEFAULT_DEVICE, help="compute device")

    # MD Ensemble & Parameters
    md_params_group = parser.add_argument_group('MD Ensemble & Parameters')
    md_params_group.add_argument("--ensemble", choices=["npt", "nte", "nvt", "nve"], default="npt",
                        help="MD ensemble: npt, nvt (alias for nte), or nve.")
    md_params_group.add_argument("--dim", type=int, nargs='+', help="Supercell dimension (e.g. '2 2 2'). Applied before MD.")
    md_params_group.add_argument("--temp", "--tebeg", "--temp-start", type=float, default=300.0, help="Target temperature [K] (default: 300.0). Alias for TEBEG. Acts as Start Temp for Gibbs.")
    md_params_group.add_argument("--temp-end", "--teend", type=float, default=None, help="Final target temperature [K] for linear ramping (mimics VASP TEEND). Acts as End Temp for Gibbs.")
    md_params_group.add_argument("--press", type=float, default=0.0, help="target pressure [GPa] (NPT only) (default: 0.0)")
    md_params_group.add_argument("--tstep", type=float, default=2.0, help="MD time step [fs] (default: 2.0)")
    md_params_group.add_argument("--nsteps", type=int, default=20000, help="number of MD steps (default: 20000)")
    
    # Thermostat/Barostat
    md_params_group.add_argument("--thermostat", choices=["nose-hoover", "langevin", "berendsen"], default="nose-hoover",
                        help="Thermostat algorithm (default: nose-hoover). Note: ASE NPT only supports Nose-Hoover or Berendsen.")
    md_params_group.add_argument("--ttau", type=float, default=0,
                        help="Thermostat time constant [fs] (default: 0, which auto-calculates as 40 * time_step, mimicking VASP's SMASS=0). For Langevin, derived from friction if not set.")
    md_params_group.add_argument("--ptau", type=float, default=0,
                        help="Barostat time constant [fs] (NPT only, default: 0, which auto-calculates from bulk modulus).")
    md_params_group.add_argument("--pfactor", type=float, default=None, help="Directly set ASE NPT pfactor (overrides ptau).")
    md_params_group.add_argument("--friction", type=float, default=None, help="Friction coefficient for Langevin MD [ps^-1].")
    
    md_params_group.add_argument("--seed", type=int, default=None, help="random seed (None for random)")
    md_params_group.add_argument("--mass", nargs='+', help="Specify atomic masses. Format: Symbol Mass Symbol Mass ... (e.g. --mass H 2.014 D 2.014)")

    # Gibbs Settings
    gibbs_group = parser.add_argument_group('Gibbs Settings')
    gibbs_group.add_argument("--gibbs", action="store_true", help="Enable Gibbs Free Energy calculation workflow (Temperature Integration).")
    gibbs_group.add_argument("--temp-step", type=float, default=50.0, help="Temperature step (K) for Gibbs scan. Default: 50.0")
    gibbs_group.add_argument("--temps", type=float, nargs='+', help="Specific temperatures to sample for Gibbs. Overrides scan settings.")
    gibbs_group.add_argument("--equil-steps", type=int, default=10000, help="Equilibration steps per temperature for Gibbs. Default: 10000")
    gibbs_group.add_argument("--qha-ref", help="Optional: Path to thermal_properties.yaml (from phonopy) for absolute G reference.")
    gibbs_group.add_argument("--prefix", default="gibbs", help="Prefix for Gibbs output files. Default: gibbs")

    # Output Settings
    output_group = parser.add_argument_group('Output Settings')
    output_group.add_argument("--output-dir", type=str, default=".", help="Directory to save MD output files.")
    output_group.add_argument("--save-every", type=int, default=100, help="traj/log save interval (default: 100)")
    output_group.add_argument("--xdat-every", type=int, default=1, help="XDATCAR write interval (default: 1)")
    output_group.add_argument("--print-every", type=int, default=1, help="stdout print interval (default: 1)")
    output_group.add_argument("--csv", default="md.csv", help="CSV log path for MD outputs")
    output_group.add_argument("--xdatcar", default="XDATCAR", help="XDATCAR path")
    output_group.add_argument("--traj", default="md.traj", help="ASE trajectory path")
    output_group.add_argument("--log", default="md.log", help="MD text log path")

    # Initial Relaxation Settings
    init_relax_group = parser.add_argument_group('Initial Relaxation Settings')
    init_relax_group.add_argument("--initial-relax", action="store_true", help="Perform initial structural relaxation before MD.")
    init_relax_group.add_argument("--initial-relax-optimizer", type=str, default="FIRE", help="Optimizer for initial relaxation (e.g., FIRE, BFGS, LBFGS).")
    init_relax_group.add_argument("--initial-relax-fmax", type=float, default=0.01, help="Force convergence threshold for initial relaxation (eV/Å).")
    init_relax_group.add_argument("--initial-relax-smax", type=float, default=0.001, help="Stress convergence threshold for initial relaxation (eV/Å³).")
    init_relax_group.add_argument("--initial-relax-symprec", type=float, default=1e-5, help="Symmetry tolerance for FixSymmetry during initial relaxation (default: 1e-5 Å).")
    init_relax_group.add_argument("--initial-relax-no-symmetry",
        dest="initial_relax_use_symmetry",
        action="store_false",
        help="Disable the FixSymmetry constraint during initial relaxation."
    )

    return parser

def run_md_simulation(args):
    # --- Dispatch to Gibbs Workflow if requested ---
    if args.gibbs:
        print(">>> Triggering Gibbs Free Energy Workflow via 'macer md --gibbs'...")
        # Ensure temp_end is set for Gibbs if not provided
        if args.temp_end is None:
            print("Warning: --temp-end not specified for Gibbs scan. Using default 1000 K.")
            args.temp_end = 1000.0
        
        run_gibbs_workflow(args)
        return
    # -----------------------------------------------

    from pathlib import Path
    # Determine input path based on priority -p > -c
    is_cif_mode = False
    if args.poscar:
        input_file_path = args.poscar
    elif args.cif:
        input_file_path = args.cif
        is_cif_mode = True
    else:
        raise ValueError("Please provide structure input via -p (POSCAR) or -c (CIF) option.")

    # Check for input file existence first
    input_path = Path(input_file_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found at '{input_path}'. Please provide a valid file.")

    if not is_cif_mode:
        try:
            check_poscar_format(input_path)
        except ValueError as e:
            raise ValueError(f"POSCAR format error: {e}")

    # Handle CIF conversion
    if is_cif_mode:
        try:
            atoms_in = read(str(input_path))
            write('POSCAR', atoms_in, format='vasp')
            args.poscar = 'POSCAR' # Update args for later use
            print(f"Converted {input_file_path} to POSCAR.")
        except Exception as e:
            raise ValueError(f"Error converting CIF {input_file_path}: {e}")

    # If output_dir is default ('.'), create a new directory based on input and mlff
    if args.output_dir == ".":
        input_poscar_dir = os.path.dirname(os.path.abspath(args.poscar))
        if not input_poscar_dir:
             input_poscar_dir = "."
        
        base_dir_name = f"MD-{Path(args.poscar).name}-mlff={args.ff}"
        output_dir_candidate = Path(input_poscar_dir) / base_dir_name
        
        # Handle duplicates
        final_output_dir = output_dir_candidate
        i = 1
        while final_output_dir.exists():
            final_output_dir = Path(input_poscar_dir) / f"{base_dir_name}-NEW{i:02d}"
            i += 1
        
        args.output_dir = str(final_output_dir)
        print(f"Output directory set to: {args.output_dir}")

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # 0) Read input structure.
    atoms = read(args.poscar, format="vasp")
    
    # --- 0.1 Supercell Creation ---
    if args.dim:
        if len(args.dim) == 3:
            sc_matrix = np.diag(args.dim)
        elif len(args.dim) == 9:
            sc_matrix = np.array(args.dim).reshape(3, 3)
        else:
            raise ValueError("--dim must be 3 or 9 integers.")
        
        atoms = make_supercell(atoms, sc_matrix)
        
        # Reorder atoms to match Phonopy convention:
        # Phonopy expects: [Atom1_images, Atom2_images, ...]
        # Within images: x-fastest loop (x varies first, then y, then z).
        # ASE make_supercell (diagonal): z-fastest loop (z varies first, then y, then x).
        
        # 1. Identify unit cell count and dimensions
        n_unit = len(atoms) // np.prod(args.dim)
        nx, ny, nz = args.dim[0], args.dim[1], args.dim[2]
        
        # 2. Build map from (ix, iy, iz) tuple to ASE index j
        # ASE loop: for x in range(nx): for y in range(ny): for z in range(nz): yield atom
        # So ASE index j = ix * (ny*nz) + iy * nz + iz
        
        # 3. Build map for Phonopy order
        # Phonopy loop: for z in range(nz): for y in range(ny): for x in range(nx): yield atom
        # But wait, Phonopy is x-fastest?
        # Let's verify: Phonopy (2,2,2): 000, 100, 010, 110, 001... 
        # actually Phonopy GRIDs depend on mesh generation, but supercell creation usually follows 
        # get_supercell_matrix logic.
        # Based on previous observation: 0.375->0.875 (x changed). So x is indeed fastest.
        # So Phonopy index k = iz * (ny*nx) + iy * nx + ix
        
        new_order = []
        for i in range(n_unit): # For each atom in unit cell
            # We want to append images in Phonopy order
            for k in range(np.prod(args.dim)):
                # Decode Phonopy index k back to (ix, iy, iz)
                # Phonopy: k = iz*(ny*nx) + iy*nx + ix (Assume z is slowest, x is fastest)
                iz = k // (nx * ny)
                rem = k % (nx * ny)
                iy = rem // nx
                ix = rem % nx
                
                # Encode to ASE index j
                # ASE: j = ix*(ny*nz) + iy*nz + iz
                j = ix * (ny * nz) + iy * nz + iz
                
                # Global index in ASE atoms list
                # ASE list is: [Cell 0 (all atoms), Cell 1 (all atoms)...] -- Wait, NO.
                # ASE make_supercell returns: [Atom1_Cell0, Atom2_Cell0..., Atom1_Cell1...] 
                # OR [Atom1_Cell0, Atom1_Cell1...] ?
                # Checked earlier: ['H', 'He', 'H', 'He'...] for 2 cells. 
                # So ASE returns: [Cell0_AllAtoms, Cell1_AllAtoms...]
                
                # So ASE global index = j * n_unit + i
                new_order.append(j * n_unit + i)
                
        atoms = atoms[new_order]
        
        print(f"--- Supercell Created (Phonopy-style reordered: x-fastest) ---")
        print(f"  Matrix: {args.dim}")
        print(f"  New atom count: {len(atoms)}")
        
        # Save supercell POSCAR for record
        write(os.path.join(args.output_dir, "POSCAR_supercell"), atoms, format="vasp")

    def load_vasp_velocities(path, atoms, tstep_fs):
        """Read velocity block from VASP CONTCAR/POSCAR and set to atoms."""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 8: return False
            
            # Line 7: Atom counts
            counts = [int(x) for x in lines[6].split()]
            n_atoms = sum(counts)
            if n_atoms != len(atoms):
                return False
            
            # Find start of velocity block
            # Skip positions (starts at line 8 or 9)
            offset = 7
            if lines[offset].strip().lower().startswith('s'):
                offset += 1
            offset += 1
            
            pos_end = offset + n_atoms
            current_line = pos_end
            vel_start = -1
            
            while current_line < len(lines):
                line = lines[current_line].strip()
                if not line:
                    current_line += 1
                    continue
                if "lattice velocities" in line.lower():
                    current_line += 8
                    continue
                parts = line.split()
                if len(parts) == 3:
                    try:
                        [float(x) for x in parts]
                        vel_start = current_line
                        break
                    except ValueError:
                        pass
                current_line += 1
            
            if vel_start != -1 and (len(lines) - vel_start) >= n_atoms:
                vels = []
                for i in range(n_atoms):
                    vels.append([float(x) for x in lines[vel_start+i].split()])
                
                # Conversion: VASP (A/step) -> ASE (A/ASE_TIME)
                dt_ase = tstep_fs * u.fs
                atoms.set_velocities(np.array(vels) / dt_ase)
                return True
        except Exception:
            return False
        return False

    # --- Parse mass override ---
    mass_map = {}
    if args.mass:
        if len(args.mass) % 2 != 0:
            raise ValueError("Error: --mass option requires pairs of Symbol Mass (e.g. H 2.014).")
        for i in range(0, len(args.mass), 2):
            sym = args.mass[i]
            try:
                m = float(args.mass[i+1])
                mass_map[sym] = m
            except ValueError:
                raise ValueError(f"Error: Invalid mass value for {sym}: {args.mass[i+1]}")
        print(f"--- Atomic mass override ---")
        
        # Apply masses to atoms object
        current_masses = atoms.get_masses()
        symbols = atoms.get_chemical_symbols()
        new_masses = []
        for i, sym in enumerate(symbols):
            if sym in mass_map:
                new_masses.append(mass_map[sym])
            else:
                new_masses.append(current_masses[i])
        atoms.set_masses(new_masses)
        
        for sym, m in mass_map.items():
            print(f"  {sym:3s} : {m:8.4f} amu")
        print("----------------------------")

    # Determine model_path based on FF if not explicitly provided
    current_model_path = args.model
    if current_model_path is None:
        default_model_name = DEFAULT_MODELS.get(args.ff)
        if default_model_name:
            current_model_path = resolve_model_path(default_model_name)
        else:
            print(f"Warning: No default model found for force field '{args.ff}' in default-model.yaml. Proceeding without a model path.")
    else:
        current_model_path = resolve_model_path(current_model_path)

    # Calculator.
    try:
        calc_kwargs = {
            "model_path": current_model_path,
            "device": args.device,
            "modal": args.modal,
        }
        
        # If the selected ff is not mace, and the model path is the default mace model,
        # set model_path to None so that the respective calculator can use its own default.
        # This check should use current_model_path, not args.model, to avoid TypeError with None.
        if args.ff != "mace" and current_model_path is not None and DEFAULT_MODELS.get("mace") and os.path.abspath(current_model_path) == os.path.abspath(os.path.join(_model_root, DEFAULT_MODELS["mace"])):
            calc_kwargs["model_path"] = None

        # Special handling for MACE model_paths which expects a list
        if args.ff == "mace":
            calc_kwargs["model_paths"] = [calc_kwargs["model_path"]]
            del calc_kwargs["model_path"]

        calc = get_calculator(ff_name=args.ff, **calc_kwargs)
    except (RuntimeError, ValueError) as e:
        raise RuntimeError(f"Error initializing calculator: {e}")

    atoms.calc = calc

    # Initial relaxation if requested
    if args.initial_relax:
        print(f"Performing initial relaxation with {args.initial_relax_optimizer} (fmax={args.initial_relax_fmax}, smax={args.initial_relax_smax})...")
        atoms = relax_structure(
            input_file=atoms,
            fmax=args.initial_relax_fmax,
            smax=args.initial_relax_smax,
            device=args.device,
            isif=3, # Full relaxation (atoms and cell)
            quiet=False, # Show output for initial relaxation
            model_path=args.model,
            optimizer_name=args.initial_relax_optimizer,
            # Suppress output files from relax_structure for initial relaxation
            contcar_name=os.devnull,
            outcar_name=os.devnull,
            xml_name=os.devnull,
            make_pdf=False,
            write_json=False,
            ff=args.ff,
            modal=args.modal,
            symprec=args.initial_relax_symprec,
            use_symmetry=args.initial_relax_use_symmetry
        )
        print("Initial relaxation completed.")
        # Re-attach calculator after relaxation, as relax_structure might create a new Atoms object
        try:
            calc = get_calculator(ff_name=args.ff, **calc_kwargs)
        except (RuntimeError, ValueError) as e:
            raise RuntimeError(f"Error re-initializing calculator after relaxation: {e}")
        atoms.calc = calc

    # Upper-triangular cell is recommended for NPT (harmless for NVT; keeps cell normalized).
    tri_cell = cellpar_to_cell(atoms.cell.cellpar())
    atoms.set_cell(tri_cell, scale_atoms=True)
    atoms.pbc = True

    # Initialize velocities: Try to load from file first, otherwise MB distribution.
    loaded_vel = load_vasp_velocities(args.poscar, atoms, args.tstep)
    if loaded_vel:
        print(f"--- Velocities loaded from {args.poscar} ---")
    else:
        rng = (np.random.default_rng(args.seed) if args.seed is not None else None)
        MaxwellBoltzmannDistribution(atoms, temperature_K=args.temp, force_temp=True, rng=rng)
        Stationary(atoms)
        ZeroRotation(atoms)

    # 1) MD integrator setup.
    timestep = args.tstep * u.fs
    
    # Handle auto ttau (SMASS=0)
    if args.ttau == 0:
        args.ttau = 40.0 * args.tstep
        print(f"--- Thermostat Setting ---")
        print(f"  Auto-calculating ttau (similar to VASP SMASS=0)")
        print(f"  Selected ttau: {args.ttau:.2f} fs (40 * dt)")

    # Handle auto ptau / pfactor
    pfactor = args.pfactor
    if args.ensemble == "npt" and pfactor is None:
        if args.ptau == 0:
            print(f"--- Barostat Setting (Auto) ---")
            print(f"  Estimating bulk modulus for automatic pfactor setting...")
            from macer.relaxation.bulk_modulus import get_bulk_modulus_and_volume
            B_GPa, _ = get_bulk_modulus_and_volume(atoms, args)
            
            if B_GPa is not None:
                # Rule of thumb for ptau selection
                if B_GPa > 100:
                    ptau_val = 200.0 # Stiff
                elif B_GPa > 30:
                    ptau_val = 500.0 # Medium
                else:
                    ptau_val = 1000.0 # Soft
                
                # Formula: pfactor = ptau^2 * B
                # Units: ptau in fs (internal time), B in eV/A^3 (internal pressure)
                B_eVA3 = B_GPa / 160.21766208
                # Note: ASE NPT pfactor expects (time_unit)^2 * pressure_unit
                # Since we use u.fs for timestep, we should use u.fs for ptau here as well
                pfactor = (ptau_val * u.fs)**2 * (B_eVA3 * u.eV / u.Angstrom**3)
                
                print(f"  Calculated Bulk Modulus: {B_GPa:.2f} GPa")
                print(f"  Selected ptau: {ptau_val:.2f} fs")
                print(f"  Resulting pfactor: {pfactor:.4e} (ASE internal)")
            else:
                print(f"  Warning: Bulk modulus estimation failed. Falling back to ptau=1000 fs.")
                ptau_val = 1000.0
                pfactor = (ptau_val * u.fs)**2 * (100.0 / 160.21766208 * u.eV / u.Angstrom**3) # Assume ~100GPa fallback
        else:
            # User provided non-zero ptau
            pfactor = (args.ptau * u.fs)**2 * (100.0 / 160.21766208 * u.eV / u.Angstrom**3)
            print(f"--- Barostat Setting ---")
            print(f"  Using user-provided ptau: {args.ptau:.2f} fs")

    # Handle Friction -> Tau conversion if friction is provided
    # Friction gamma (ps^-1). Tau (fs) = 1/gamma_fs. 
    # 1 ps^-1 = 0.001 fs^-1.
    # tau = 1 / (friction * 0.001) = 1000 / friction.
    if args.friction is not None and args.friction > 0:
        new_ttau = 1000.0 / args.friction
        print(f"--- Thermostat Setting ---")
        print(f"  Friction provided: {args.friction} ps^-1")
        print(f"  Converted to time constant (tau): {new_ttau:.2f} fs")
        args.ttau = new_ttau

    ttime = args.ttau * u.fs
    
    print(f"--- MD Ensemble: {args.ensemble.upper()} ---")
    print(f"  Thermostat: {args.thermostat}")
    
    if args.ensemble == "npt":
        # NPT with Nose–Hoover barostat (ASE NPT).
        extstress = args.press * u.GPa
        
        if args.thermostat == "langevin":
            print("  Warning: ASE NPT does not support Langevin thermostat natively.")
            print(f"  Using Nose-Hoover with tau={args.ttau:.2f} fs (equivalent to requested friction).")
            # Fallback to Nose-Hoover
            dyn = NPT(atoms, timestep=timestep, temperature_K=args.temp,
                      externalstress=extstress, ttime=ttime, pfactor=pfactor)
        
        elif args.thermostat == "berendsen":
            if NPT_Ber:
                # NPTBerendsen uses 'taut' and 'taup'
                dyn = NPT_Ber(atoms, timestep=timestep, temperature_K=args.temp,
                              pressure_au=extstress, taut=ttime, taup=args.ptau * u.fs)
            else:
                raise ImportError("NPTBerendsen not available in this ASE version.")
        
        else: # nose-hoover (default)
            dyn = NPT(atoms, timestep=timestep, temperature_K=args.temp,
                      externalstress=extstress, ttime=ttime, pfactor=pfactor)

    elif args.ensemble == "nve":
        # NVE (microcanonical) with Velocity-Verlet integrator.
        dyn = VelocityVerlet(atoms, timestep=timestep)
    elif args.ensemble in ["nte", "nvt"]:
        # NVT Logic
        if args.thermostat == "langevin":
            # Langevin (friction is handled via ttau conversion above if provided, 
            # but ASE Langevin takes friction parameter directly in atomic units or specialized units)
            # ASE Langevin signature: friction in [1/fs] usually if units are not standard? 
            # ASE docs: "friction: Strength of the friction parameter in time^-1."
            # If we use ase.units, we should be careful. 
            # Usually: friction is characteristic frequency.
            # If args.friction was provided (ps^-1), we need to pass it carefully.
            # However, we converted it to args.ttau. 
            # Langevin friction = 1/ttau? 
            # Let's use the explicit friction if provided, or derive from ttau.
            
            fric_val = 0.0
            if args.friction:
                # args.friction is in ps^-1. 
                # ASE Langevin expects units consistent with timestep.
                # If timestep is in fs, friction should be in fs^-1.
                # 1 ps^-1 = 1e-3 fs^-1.
                fric_val = args.friction * 1e-3 
            else:
                # Derived from ttau (fs)
                # gamma = 1/tau
                fric_val = 1.0 / args.ttau
                
            dyn = Langevin(atoms, timestep=timestep, temperature_K=args.temp, friction=fric_val)
            print(f"  Langevin friction set to: {fric_val:.6f} fs^-1")

        elif args.thermostat == "berendsen":
             if NVT_Ber:
                dyn = NVT_Ber(atoms, timestep=timestep, temperature_K=args.temp, taut=ttime)
             else:
                raise ImportError("NVTBerendsen not available.")
        
        else: # nose-hoover (default)
            if NVT_NHC is not None:
                dyn = NVT_NHC(atoms, timestep=timestep, temperature_K=args.temp, tdamp=ttime)
            elif NVT_Ber is not None:
                print("  Warning: Nose-Hoover Chain not found, falling back to Berendsen.")
                dyn = NVT_Ber(atoms, timestep=timestep, temperature_K=args.temp, taut=ttime)
            else:
                 raise ImportError("No NVT integrator found.")
    else:
        # This should not be reached due to argparse choices
        raise ValueError(f"Unknown ensemble: {args.ensemble}")

    # 2) Logging: trajectory + text logger.
    traj_path = os.path.join(args.output_dir, args.traj)
    traj = Trajectory(traj_path, "w", atoms)
    dyn.attach(traj.write, interval=args.save_every)
    log_path = os.path.join(args.output_dir, args.log)
    
    orig_stdout = sys.stdout
    with Logger(log_path) as lg:
        sys.stdout = lg
        # Write Command
        print(f"Command: {' '.join(sys.argv)}")

        # 3) XDATCAR setup.
        # Derive species and counts directly from the current atoms object (supercell compliant)
        all_symbols = atoms.get_chemical_symbols()
        species = list(dict.fromkeys(all_symbols)) # maintain order
        counts = [all_symbols.count(spec) for spec in species]
        
        xdatcar_path = os.path.join(args.output_dir, args.xdatcar)
        xdat_handle = open(xdatcar_path, "w")

        # 4) CSV (custom observables) setup.
        csv_path = os.path.join(args.output_dir, args.csv)
        csv_handle = open(csv_path, "w", newline="")
        csv_writer = csv.writer(csv_handle)
        csv_writer.writerow(["step", "time_fs", "Epot_eV", "Ekin_eV", "Etot_eV", "T_K", "a_A", "b_A", "c_A", "Vol_A3", "P_GPa", "H_eV"])

        # State & utilities.
        config_idx = 0
        step_counter = 0

        def write_xdatcar_block():
            """Append one XDATCAR configuration block from current Atoms state."""
            current_step = step_counter + 1
            
            # If it's the very first step, write the Title/Scale/Lattice/Species/Counts header
            if current_step == 1:
                xdat_f = xdat_handle
                xdat_f.write(" ".join(species) + "\n")
                xdat_f.write("    1.000000\n")
                # First frame lattice
                for vec in atoms.cell:
                    xdat_f.write(f"     {vec[0]:11.6f} {vec[1]:11.6f} {vec[2]:11.6f}\n")
                xdat_f.write(" " + " ".join(f"{s:>2}" for s in species) + "\n")
                xdat_f.write(" " + " ".join(f"{c:16d}" for c in counts) + "\n")

            # Standard VASP XDATCAR repeats Lattice for every frame in NPT/Variable Cell runs
            if current_step > 1 and args.ensemble == "npt":
                xdat_f = xdat_handle
                xdat_f.write(" ".join(species) + "\n")
                xdat_f.write("    1.000000\n")
                for vec in atoms.cell:
                    xdat_f.write(f"     {vec[0]:11.6f} {vec[1]:11.6f} {vec[2]:11.6f}\n")
                xdat_f.write(" " + " ".join(f"{s:>2}" for s in species) + "\n")
                xdat_f.write(" " + " ".join(f"{c:16d}" for c in counts) + "\n")
                
            xdat_handle.write(f"Direct configuration= {current_step:5d}\n")
            
            # Handle Selective Dynamics (FixAtoms constraints in ASE)
            from ase.constraints import FixAtoms
            fix_atoms = [c for c in atoms.constraints if isinstance(c, FixAtoms)]
            if fix_atoms:
                # Get a boolean mask of fixed atoms
                fixed_mask = np.zeros(len(atoms), dtype=bool)
                for c in fix_atoms:
                    fixed_mask[c.index] = True
                
                for i, s in enumerate(atoms.get_scaled_positions(wrap=False)):
                    flag = "  F  F  F" if fixed_mask[i] else "  T  T  T"
                    xdat_handle.write(f"   {s[0]:.8f}   {s[1]:.8f}   {s[2]:.8f}{flag}\n")
            else:
                for s in atoms.get_scaled_positions(wrap=False):
                    xdat_handle.write(f"   {s[0]:.8f}   {s[1]:.8f}   {s[2]:.8f}\n")

        def write_contcar():
            """Save current structure and velocities to CONTCAR in strict VASP MD format."""
            contcar_path = os.path.join(args.output_dir, "CONTCAR")
            
            with open(contcar_path, "w") as f:
                # 1. Header (comment)
                f.write(f"generated by macer md (step {step_counter})\n")
                # 2. Scale
                f.write("   1.00000000000000\n")
                # 3. Lattice
                for vec in atoms.cell:
                    f.write(f"     {vec[0]:18.16f} {vec[1]:18.16f} {vec[2]:18.16f}\n")
                # 4. Species and Counts
                f.write(" " + "  ".join(species) + "\n")
                f.write(" " + "  ".join(str(c) for c in counts) + "\n")
                
                # 5. Coordinate Type
                f.write("Direct\n")
                
                # 6. Positions
                for s in atoms.get_scaled_positions(wrap=False):
                    f.write(f"  {s[0]:18.16f}  {s[1]:18.16f}  {s[2]:18.16f}\n")
                
                f.write("\n") # Blank line after positions
                
                # 7. Lattice Velocities (for NPT/NTE)
                if args.ensemble in ["npt", "nte"]:
                    f.write("Lattice velocities and vectors\n")
                    f.write("           1\n")
                    # Note: ASE's NPT doesn't expose lattice velocities easily in a standard way.
                    # We write zeros or minimal placeholders to maintain format compatibility.
                    for _ in range(3):
                        f.write("  0.00000000E+00  0.00000000E+00  0.00000000E+00\n")
                    for vec in atoms.cell:
                        f.write(f"  {vec[0]:14.8E}  {vec[1]:14.8E}  {vec[2]:14.8E}\n")
                    f.write("\n")

                # 8. Atomic Velocities (in A/step)
                # ASE velocity is A / (ASE time unit). 
                # VASP CONTCAR velocity is A / step.
                # Factor: (ASE time unit / 1 fs) * args.tstep
                # But ASE's atoms.get_velocities() returns A/ASE_TIME.
                # To get A/step: vel_ase * (timestep_in_ase_units)
                dt_ase = args.tstep * u.fs
                velocities = atoms.get_velocities() * dt_ase
                
                for v in velocities:
                    f.write(f"  {v[0]:18.16E}  {v[1]:18.16E}  {v[2]:18.16E}\n")

        def collect_observables():
            """Compute a set of common MD observables from the current state."""
            epot = atoms.get_potential_energy()
            ekin = atoms.get_kinetic_energy()
            etot = epot + ekin
            temp = atoms.get_temperature()
            vol = atoms.get_volume()
            
            # Stress
            stress_voigt = atoms.get_stress(voigt=True)
            stress_GPa = stress_voigt * EV_A3_TO_GPa
            p_GPa = -np.mean(stress_GPa[:3])
            
            H = etot + (p_GPa / EV_A3_TO_GPa) * vol
            t_fs = step_counter * args.tstep
            
            cell_lengths = atoms.cell.lengths() # [a, b, c]
            
            return epot, ekin, etot, temp, vol, p_GPa, H, t_fs, cell_lengths, stress_GPa

        def print_status_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs, cell_lengths):
            """Pretty single-line status for stdout."""
            a, b, c = cell_lengths
            # Use original stdout for terminal progress if we want, or let Logger handle both
            sys.stdout = orig_stdout
            
            # If ramping, show target temperature
            target_str = ""
            if args.temp_end is not None:
                current_target = args.temp + (args.temp_end - args.temp) * step_counter / args.nsteps
                target_str = f" [Target={current_target:6.1f} K]"

            print(
                f"Step{step_counter:7d} | t={t_fs:7.2f} fs | "
                f"Epot={epot: .4f} eV | Etot={etot: .4f} eV | "
                f"T={temp:6.1f} K{target_str} | Vol={vol:7.2f} A^3 | "
                f"Cell=[{a:.2f}, {b:.2f}, {c:.2f}] | P={p_GPa: 6.3f} GPa"
            )
            sys.stdout = lg

        def write_csv_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs, cell_lengths):
            """Append one row of observables to the CSV log."""
            a, b, c = cell_lengths
            csv_writer.writerow([step_counter, t_fs, epot, ekin, etot, temp, a, b, c, vol, p_GPa, H])

        def write_log_line(epot, ekin, etot, temp, vol, t_fs, cell_lengths, stress_GPa):
            """Append one row to the text log (file only)."""
            t_ps = t_fs / 1000.0
            a, b, c = cell_lengths
            # Write directly to the log file to avoid terminal clutter
            lg.log.write(
                f"{t_ps:<14.4f} {etot:<12.3f} {epot:<12.3f} {ekin:<11.3f} {temp:<9.1f} "
                f"{a:<10.3f} {b:<10.3f} {c:<10.3f} {vol:<9.3f} "
                f"{stress_GPa[0]:>10.3f} {stress_GPa[1]:>10.3f} {stress_GPa[2]:>10.3f} "
                f"{stress_GPa[3]:>10.3f} {stress_GPa[4]:>10.3f} {stress_GPa[5]:>10.3f}\n"
            )

        # Initial (step 0) record: console + XDATCAR + CSV.
        epot, ekin, etot, temp, vol, p_GPa, H, t_fs, cell_lengths, stress_GPa = collect_observables()
        print_status_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs, cell_lengths)
        write_xdatcar_block()
        write_contcar()
        write_csv_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs, cell_lengths)
        step_counter += 1  # subsequent integration starts at step 1

        # Per-step callback.
        def on_step():
            """Callback executed every step."""
            nonlocal step_counter
            
            # Handle Temperature Ramping (VASP TEBEG -> TEEND style)
            if args.temp_end is not None:
                tebeg = args.temp
                teend = args.temp_end
                # Linear interpolation: T = tebeg + (teend - tebeg) * current_step / total_steps
                new_temp = tebeg + (teend - tebeg) * step_counter / args.nsteps
                
                # Update target temperature for various ASE dynamics objects
                if hasattr(dyn, 'set_temperature'):
                    # For Langevin, NPT, etc.
                    try:
                        dyn.set_temperature(temperature_K=new_temp)
                    except TypeError:
                        # Some older ASE versions might have different signatures
                        dyn.temperature_K = new_temp
                elif hasattr(dyn, 'temperature_K'):
                    dyn.temperature_K = new_temp
            
            epot, ekin, etot, temp, vol, p_GPa, H, t_fs, cell_lengths, stress_GPa = collect_observables()
            
            if (step_counter % args.print_every) == 0:
                print_status_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs, cell_lengths)
            
            # Synchronize XDATCAR with traj saving (save_every)
            if (step_counter % args.xdat_every) == 0:
                write_xdatcar_block()
            
            if (step_counter % args.save_every) == 0:
                write_contcar()
            
            write_csv_line(epot, ekin, etot, temp, vol, p_GPa, H, t_fs, cell_lengths)
            step_counter += 1

        dyn.attach(on_step, interval=1)

        # 5) Run MD.
        dyn.run(args.nsteps)

        # 6) Finalize.
        xdat_handle.close()
        csv_handle.close()
        
        # --- 7) Automatic MD Analysis & Plotting ---
        print("\n" + "="*60)
        print("--- Automatic MD Analysis & Plotting ---")
        print("="*60)
        
        from macer.utils.md_tools import print_md_summary, plot_md_thermo, plot_cell_evolution, plot_rdf
        
        # 7.1 Statistical Summary
        try:
            print("\n[Analysis] Generating statistical summary from md.csv...")
            print_md_summary(csv_path)
        except Exception as e:
            print(f"  Warning: Summary generation failed: {e}")

        # 7.2 Thermodynamic Plot (T, E, P)
        try:
            print("[Analysis] Plotting thermodynamic properties (T, E, P)...")
            thermo_plot_path = os.path.join(args.output_dir, "md_thermo.pdf")
            plot_md_thermo(csv_path, output_path=thermo_plot_path)
            print(f"  Saved to: {thermo_plot_path}")
        except Exception as e:
            print(f"  Warning: Thermodynamic plotting failed: {e}")

        # 7.3 Cell Evolution Plot (a, b, c, Vol)
        try:
            print("[Analysis] Plotting cell evolution (a, b, c, Vol)...")
            cell_plot_path = os.path.join(args.output_dir, "md_cell.pdf")
            plot_cell_evolution(csv_path, output_path=cell_plot_path)
            print(f"  Saved to: {cell_plot_path}")
        except Exception as e:
            print(f"  Warning: Cell evolution plotting failed: {e}")

        # 7.4 RDF Plot
        try:
            print("[Analysis] Calculating and plotting RDF...")
            rdf_plot_path = os.path.join(args.output_dir, "md_rdf.pdf")
            if plot_rdf(traj_path, output_path=rdf_plot_path):
                print(f"  Saved to: {rdf_plot_path}")
        except Exception as e:
            print(f"  Warning: RDF plotting failed: {e}")
            
        print("\n" + "="*60)
        
    sys.stdout = orig_stdout
    print(f"Done ({args.ensemble.upper()} MD): outputs saved to {args.output_dir}")
    print(f"  Check log file: {args.log}")
