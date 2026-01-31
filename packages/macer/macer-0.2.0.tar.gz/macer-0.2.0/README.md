<img src="docs/macer_logo.png" alt="macer Logo" width="30%">

# macer

![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**macer: Machine-learning accelerated Atomic Computational Environment for Research workflows**

The `macer` package provides a command-line workflow for crystal structure relaxation, molecular dynamics simulations, and lattice dynamics calculations, using a variety of Machine-Learned Force Fields (MLFFs). It integrates universal Machine Learning Interatomic Potentials (uMLIP) calculators like [MACE](https://github.com/ACEsuit/mace-foundations), [MatterSim](https://github.com/microsoft/mattersim), [SevenNet](https://github.com/MDIL-SNU/SevenNet), [CHGNet](https://github.com/CederGroupHub/chgnet), [M3GNet](https://github.com/materialsvirtuallab/m3gnet), [Allegro](https://www.nequip.net/), [Orb](https://github.com/orbital-materials/orb-models), and [FairChem](https://github.com/facebookresearch/fairchem) with libraries like [ASE (Atomic Simulation Environment)](https://wiki.fysik.dtu.dk/ase/), [Phonopy](https://github.com/phonopy/phonopy), [Phono3py](https://github.com/phonopy/phono3py), [DynaPhoPy](https://github.com/abelcarreras/DynaPhoPy), and [symfc](https://github.com/symfc/symfc).

The self-consistent harmonic approximation (SSCHA) implementation is based on [qscaild](https://github.com/vanroeke/qscaild).

---

## Key Features

-   **MLFF Integration**: Utilizes various MLFFs as interatomic potential calculators for all supported workflows with same cli commands.
-   **Structure Relaxation**: Employs ASE optimizers (FIRE, BFGS, etc.) with VASP-compatible `ISIF` modes. Results are saved directly in the input directory by default (VASP-style).
-   **Molecular Dynamics**: Performs NPT, NVT, and NVE ensemble simulations with **Physics-based Auto-parameterization**:
-   **Phonon Calculations**: Uses [Phonopy](https://github.com/phonopy/phonopy) to calculate phonon band structure, density of states (DOS), **irreducible representations (irreps)**, and Grüneisen parameters.
-   **Quasiharmonic Approximation (QHA)**: Automates the calculation of thermodynamic properties like thermal expansion and heat capacity. Includes options for volume sampling and custom output directory control.
-   **Self-Consistent Harmonic Approximation (SSCHA)**: A workflow to compute temperature-dependent effective force constants, following the [qscaild](https://github.com/vanroeke/qscaild) package. The implementation features:
-   **Anharmonic Phonon Analysis (DynaPhoPy)**: Calculates finite-temperature phonon properties by analyzing MD trajectories using [DynaPhoPy](https://github.com/abelcarreras/DynaPhoPy). This workflow:
-   **Lattice Thermal Conductivity**: Calculates lattice thermal conductivity by solving the linearized Boltzmann transport equation (LBTE) using [phono3py](https://github.com/phonopy/phono3py). Supports RTA and LBTE modes with MLFF-calculated forces.
-   **Point Defect Analysis**: Automates point defect calculations (Chemical Potential Diagram, Defect Formation Energies) using `pydefect` and `vise`, integrating MLFF relaxation via `macer`.


---

## Installation & Setup

Macer now supports a **Unified MLFF Environment**, allowing all force fields (MACE, SevenNet, MatterSim, etc.) to coexist in a single Python environment. This is achieved by "vendorizing" MACE and its legacy dependencies.

### 1. Create a Virtual Environment

We recommend using **uv** (fastest) or **conda**. Use `macer_env` as your environment name.

#### Option A: Using uv (Recommended)
```bash
# 1. Create environment
uv venv macer_env

# 2. Activate environment
source macer_env/bin/activate

# 3. Install Macer and all dependencies
uv pip install -e .
```

#### Option B: Using Conda
```bash
# 1. Create environment
conda create -n macer_env python=3.11
conda activate macer_env

# 2. Install Macer and all dependencies
pip install -e .
```

### 2. Custom Configuration (`~/.macer.yaml`)
Macer uses a configuration file named `.macer.yaml` in your home directory (`~/.macer.yaml`) to manage global default settings (e.g., default force field, compute device, and model paths).

-   **Automatic Setup**: On its first run, Macer automatically creates a `~/.macer.yaml` file populated with global defaults if it doesn't already exist.
-   **Easy Editing**: You can easily edit these settings visually using the **Interactive Mode** (`macer -i`) by selecting the **`[ Default setting editor (~/.macer.yaml) ]`** menu.

#### Configuration Format
```yaml
# ~/.macer.yaml
default_mlff: mattersim  # Options: mattersim, mace, sevennet, chgnet, m3gnet, allegro, orb, fairchem
device: cpu              # Options: cpu, mps, cuda

# Custom directory to search for MLFF model files before checking project defaults.
mlff_directory: /path/to/your/models

models:
  # Specify filenames (searched in mlff_directory or package default) or absolute paths.
  mace: mace-omat-0-small.model
  sevennet: checkpoint_sevennet_0.pth
```

### 3. Verify Installation
After installation, the `macer` command will be available globally in your environment.
```bash
macer --help
```

### 4. Installation on HPC Systems (GPU & Compiler Issues)
On High Performance Computing (HPC) systems (especially with ARM/aarch64 CPUs and NVIDIA GPUs), standard installation often fails due to:
1.  **Compiler Conflicts**: System default compilers (like `nvc`) failing to build Python packages.
2.  **PyTorch Version Mismatch**: `pip` installing CPU-only PyTorch instead of CUDA-enabled versions.

To resolve this, use our helper script which handles compiler setup and forces a CUDA-enabled PyTorch installation:

```bash
# Run this script to install macer on HPC environments
bash scripts/install_macer_gpu.sh
```

Or manually configure your environment before installing:
```bash
module load gcc       # Load GCC module
export CC=gcc         # Force C compiler to GCC
export CXX=g++        # Force C++ compiler to G++
export FC=gfortran    # Force Fortran compiler

# Install PyTorch with CUDA explicitly (example for CUDA 12.4)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# Install Macer (without dependencies first to preserve PyTorch)
pip install -e . --no-deps
pip install -e .        # Install remaining deps
```

### 5. Pre-trained Model Management (`macer util gm`)

Macer provides a centralized utility to manage and download pre-trained Machine Learning Force Field (MLFF) models. Downloaded models are stored in the `mlff-model/` directory.

#### Basic Usage
```bash
# 1. List all supported models and their installation status
macer util gm

# 2. Download ALL available models
macer util gm --model all

# 3. Download all models for a specific force field (e.g., MACE)
macer util gm --model all --ff mace

# 4. Download a specific model by its keyword
macer util gm --model sevennet-omni
```

#### Auto-Provisioning
If you run a simulation (e.g., `macer relax`) and the required model is missing from your local directory, `macer` will attempt to download it automatically using the same mechanism.

---

## Usage

The `macer` CLI is the unified entry point for all workflows. It supports `relax` and `md` directly, and integrates other tools as subcommands: `phonopy`, `pydefect`, and `util`.

### Interactive TUI Mode

For a more user-friendly experience, use the **Interactive Mode**. This provides a menu-driven interface to configure and run all `macer` workflows, manage your global configuration, and explore files with an advanced `vi`-style browser.

```bash
# Launch the interactive TUI
macer -i
```

You can access help for each command and its subcommands directly from the terminal:

```bash
macer --help
macer relax -h
macer md -h
macer phonopy [sr, pb, qha, sscha, ft, tc] -h
macer pydefect [cpd, defect, full] -h
macer util [dynaphopy, md, phonon, model, struct] -h
```

### Relaxation Examples (`macer relax`)

By default, relaxation results (`CONTCAR-*`, `OUTCAR-*`, etc.) are saved directly in the same directory as the input structure file. Use `--subdir` if you prefer a dedicated `RELAX-*` directory.

```bash
# Full cell relaxation (atoms + lattice) using the default force field
macer relax --poscar POSCAR --isif 3

# Batch relaxation for multiple structures using MACE
macer relax --poscar POSCAR-* --isif 2 --ff mace

# Use a specific Orb model (auto-downloaded by name)
macer relax --poscar POSCAR --isif 3 --ff orb --model orb_v3_conservative_inf_omat

# Generate outputs for PyDefect (single-point calculation)
macer relax --poscar POSCAR --isif 0 --pydefect

# Relaxation with a fixed c-axis
macer relax --poscar POSCAR --isif 3 --fix-axis c

# Calculate bulk modulus for multiple files
macer relax -p POSCAR-001 POSCAR-002 --bulk-modulus
```

### Molecular Dynamics Examples (`macer md`)

```bash
# 1. NPT Auto-setting (Default): Automatic barostat (via Bulk Modulus) and thermostat (40 * dt)
macer md -p POSCAR --ensemble npt --temp 300 --press 0.0 --ff mattersim

# 2. NVT Auto-setting: Automatic thermostat coupling (ttau = 40 * tstep)
macer md -p POSCAR --ensemble nvt --temp 600 --nsteps 10000

# 3. Temperature Ramping (mimicking VASP TEBEG -> TEEND)
# Gradually increase temperature from 300K to 1000K over 20000 steps
macer md -p POSCAR --ensemble nvt --temp 300 --temp-end 1000 --nsteps 20000

# 4. Restart with Velocities: macer automatically detects and loads velocity block from CONTCAR/POSCAR
macer md -p CONTCAR --ensemble npt --temp 300 --ff mace

# 5. Manual NPT: Explicitly set coupling constants (ttau=100fs, ptau=1000fs)
macer md --ensemble npt --temp 600 --press 1.0 --ttau 100 --ptau 1000 --nsteps 20000

# 6. Langevin MD: Using explicit friction coefficient (ps^-1) for NVT
macer md -p POSCAR --ensemble nvt --temp 300 --thermostat langevin --friction 10.0

# 7. MD simulation with atomic mass override
macer md --ensemble npt --temp 300 --mass H 2.014 --output-dir D_MD
```

### Phonon & Lattice Dynamics Examples (`macer phonopy`)

#### Unit Cell Symmetrization (`macer phonopy sr`)
This is a first step for any lattice dynamics calculation to ensure a high-symmetry structure.
```bash
# Iteratively relax and symmetrize a unit cell
macer phonopy sr --poscar POSCAR --tolerance 1e-3
```

#### Phonon Bands & Grüneisen Parameter (`macer phonopy pb`)
Calculates and plots the phonon band structure.
```bash
# Calculate phonon bands using an automatically determined supercell size
macer phonopy pb -p ./example/POSCAR

# Explicitly set the supercell dimension
macer phonopy pb -p ./example/POSCAR --dim 2 2 2

# Calculate and plot the Grüneisen parameter, with automatic strain estimation
macer phonopy pb -p ./example/POSCAR --dim 2 2 2 --plot-gruneisen

# Calculate irreducible representations and generate VESTA visualization for the Gamma point
macer phonopy pb -p ./example/POSCAR --irreps

# Generate VESTA visualization for all high-symmetry points in the band path
macer phonopy pb -p ./example/POSCAR --write-arrow

# Generate VESTA arrows for a specific user-defined q-point vector
macer phonopy pb -p ./example/POSCAR --write-arrow --arrow-qpoint 0.2 0.2 0.2

# Perform phonon calculation with atomic mass override (e.g., Deuterium)
macer phonopy pb -p POSCAR --mass H 2.014 --output-dir D_effect

# Calculate and plot Phonon DOS (Total + Projected).
macer phonopy pb -p POSCAR --dos --mesh 20 20 20
```

#### Quasiharmonic Approximation (`macer phonopy qha`)
Automates the full QHA workflow to compute thermodynamic properties.
```bash
# Run a full QHA workflow, automatically estimating the volume range
macer phonopy qha --poscar POSCAR --num-volumes 7 --tmax 1200

# Run QHA with a specific supercell dimension and a manually specified volume range
macer phonopy qha --poscar POSCAR --dim 2 2 2 --length-factor-min 0.98 --length-factor-max 1.02

# Run QHA using a local polynomial fit for the equation of state
macer phonopy qha --poscar POSCAR --eos local_poly
```

#### Self-Consistent Harmonic Approximation (`macer phonopy sscha`)
Performs a SSCHA workflow to find temperature-dependent effective force constants, featuring automatic ensemble regeneration.

```bash
# Basic SSCHA run at 300K with auto-sized supercell
macer phonopy sscha -p POSCAR -T 300 --free-energy-conv 0.1

# Use a MD-generated ensemble for accuracy
macer phonopy sscha -p POSCAR -T 500 --reference-method md --reference-md-nsteps 2000 --reference-md-nequil 500

# Run with ensemble regeneration enabled and a fixed random seed for reproducibility
macer phonopy sscha -p POSCAR -T 300 --max-regen 5 --seed 1234

# Load a pre-calculated initial force constant and a reference ensemble to save time
macer phonopy sscha -p POSCAR -T 300 --read-initial-fc path/to/FC_init --reference-ensemble path/to/ensemble.npz

# Optimize the cell volume and calculate effective FCs at 800 K
macer phonopy sscha -p POSCAR -T 800 --optimize-volume

# Full QSCAILD-style self-consistent optimization (structure & FCs)
macer phonopy sscha -p POSCAR -T 300 --qscaild-selfconsistent

# Include 3rd order force constants in the fitting process
macer phonopy sscha -p POSCAR -T 300 --include-third-order
```

#### Anharmonic Phonon Analysis (`macer phonopy finite-temperature`, aliased to `ft`)
Calculates finite-temperature renormalized phonon dispersion and quasiparticle properties (linewidths, shifts) using MD and DynaPhoPy.

```bash
# Standard workflow: Auto-supercell, harmonic reference, and renormalization at 800K
# (Default algorithm: FFT/Direct, -psm 2)
macer phonopy ft -p POSCAR -T 800 --ff mattersim

# Run with specific supercell and MD settings (recommended for production)
macer phonopy ft -p POSCAR -T 800 --dim 2 2 2 --md-steps 10000 --md-equil 2000

# Multi-temperature run with comparison plot (e.g., 300K vs 800K)
macer phonopy ft -p POSCAR -T 300 800 --dim 2 2 2

# High-resolution analysis: Project onto specific q-point and save quasiparticle data
macer phonopy ft -p POSCAR -T 300 --dim 3 3 3 --resolution 0.01 --projection-qpoint 0.5 0.0 0.0 --save-quasiparticles

# Direct MD: Use a large input supercell as-is (no expansion)
macer phonopy ft -p POSCAR_SUPERCELL -T 300 --no-supercell
```

#### Lattice Thermal Conductivity (`macer phonopy thermal-conductivity`, aliased to `tc`)
Calculates lattice thermal conductivity by solving the linearized Boltzmann transport equation (LBTE) using `phono3py`. This workflow automates structure relaxation, dual supercell generation (FC3/FC2), force calculation with MLFFs, and post-processing.

```bash
# Basic run with auto-configured dual supercell (FC3~12A, FC2~25A) and relaxation
macer phonopy tc -p POSCAR --mesh 11 11 11

# Run with specific supercell dimensions and temperature range
macer phonopy tc -p POSCAR --dim 2 2 2 --dim-fc2 4 4 4 --mesh 11 11 11 --tmin 0 --tmax 1000

# Run for a specific temperature and save heavy HDF5 files for advanced post-processing
macer phonopy tc -p POSCAR --mesh 11 11 11 --temp 300 --save-hdf5

# Run using LBTE mode for higher accuracy (accurate for high-k materials)
macer phonopy tc -p POSCAR --lbte
```

### Gibbs Free Energy Examples (`macer gibbs`)

Calculates the Gibbs Free Energy ($G(T)$) by integrating enthalpy from NPT MD simulations (Gibbs-Helmholtz integration).

```bash
# Calculate Gibbs energy from 100K to 1000K (default step 50K) using NPT MD
macer gibbs -p POSCAR --temp-start 100 --temp-end 1000

# Hybrid approach: Use QHA result as a low-T reference for absolute G(T)
# First, run QHA to get thermodynamic properties (e.g., at 300K)
# Then, use the free energy from QHA as the reference point
macer gibbs -p POSCAR --temp-start 300 --temp-end 1500 --qha-ref qha_results/thermal_properties.yaml

# Customize MD settings for integration
macer gibbs -p POSCAR --temp-start 100 --temp-end 500 --nsteps 50000 --ensemble npt --ff mace
```

### Defect Analysis Examples (`macer pydefect`)

The `macer pydefect` command automates the point defect calculation workflow, integrating `pydefect` and `vise` for analysis and `macer` for MLFF-based structure relaxation. It is verified to work with `pydefect` v0.9.11 and `vise` v0.9.5.

#### Chemical Potential Diagram (`macer pydefect cpd`)
Generates the Chemical Potential Diagram (CPD) and determines the target chemical potential vertices.

```bash
# Generate CPD for a formula (retrieved from Materials Project)
macer pydefect cpd -f MgAl2O4

# Generate CPD for a specific MPID with dopants
macer pydefect cpd -m mp-1234 -d Ca Ti
```

#### Defect Formation Energy (`macer pydefect defect`)
Calculates defect formation energies for a set of defects given the CPD info.

```bash
# Run defect calculations (requires standard_energies.yaml and target_vertices.yaml from CPD step)
macer pydefect defect -p POSCAR -s standard_energies.yaml -t target_vertices.yaml --matrix 2 2 2
```

#### Full Workflow (`macer pydefect full`)
Runs the entire pipeline: CPD generation -> Supercell generation -> Defect Calculation -> Analysis.

```bash
# Run full workflow for a POSCAR file
macer pydefect full -p POSCAR --matrix 2 2 2 --min_atoms 100 --max_atoms 300

# Batch run for multiple POSCAR files using a glob pattern
macer pydefect full -p POSCAR-mp-* --matrix 2 2 2 -d Cl
```

### Utility Suite (`macer util`)

The `macer util` command provides various post-processing and analysis tools, integrated into categories like `md`, `model`, and `struct`.

#### MD Post-processing (`macer util md`)

```bash
# Calculate ionic conductivity
# Automatically detects MD interval from XDATCAR/md.csv and charges from pydefect
macer util md conductivity -i ./md.traj -t 500 --dt 2

# Plot MD trajectory data (T, E, P from md.csv)
macer util md plot -i md.csv

# Calculate and plot Radial Distribution Function (RDF)
macer util md rdf -i md.traj

# Convert ASE .traj to VASP XDATCAR with a specific interval
macer util md traj2xdatcar -i md.traj --interval 50

# Print statistical summary of MD results
macer util md summary -i md.csv
```

#### DynaPhoPy Wrapper (`macer util dynaphopy`)
A direct wrapper for the `dynaphopy` CLI that benefits from Macer's runtime compatibility patches. Use this for manual, low-level trajectory analysis exactly as you would use the original `dynaphopy` command.

```bash
# Standard DynaPhoPy usage (arguments are passed through directly)
# Macer handles NumPy 2.x and Phonopy 2.x compatibility automatically.
macer util dynaphopy input_file XDATCAR -ts 0.001 --normalize_dos -i -psm 2
```

#### Phonon & Grüneisen Post-processing (`macer util phonon`)

```bash
# Plot phonon dispersion from .dat or .yaml file
macer util phonon band -i band.dat -y band.yaml

# Plot Grüneisen parameters with custom ranges and symmetric visual scaling
macer util phonon gruneisen -i gruneisen.dat -y band.yaml --gmin -50 --gmax 5
```

#### Model & Structure Utilities (`macer util model/struct`)

```bash
# Convert a model to float32 precision
macer util model fp32 -i model.pth

# Convert VASP4 POSCAR to VASP5 (adds element symbols to the header)
macer util struct vasp4to5 -i POSCAR
```


---



## Command Line Options

### `macer relax` Options

| Option | Description | Default |
|--------|-------------|---------|
| `-p`, `--poscar` | Input POSCAR file(s) or glob pattern(s). | `POSCAR` |
| `--model` | Path or name of the MLFF model. | (from `default.yaml`) |
| `--ff` | Force field to use. | (dynamic) |
| `--isif` | VASP ISIF mode (0–8) for relaxation. | 3 |
| `--no-pdf` | Do not generate the relaxation log PDF. | `False` |
| `--output-dir` | Directory to save output files. | None |
| `--subdir` | Create a `RELAX-*` subdirectory for outputs. | `False` |
| `--fmax` | Force convergence threshold (eV/Å). | 0.01 |
| `--smax` | Stress convergence threshold (eV/Å³). | 0.001 |
| `--bulk-modulus` | Perform bulk modulus calculation instead of relaxation. | `False` |
| `--strain` | Max strain for E-V curve (e.g., 0.05 for ±5%). | `0.05` |
| `--eos` | Equation of state for bulk modulus (`birchmurnaghan` or `murnaghan`). | `birchmurnaghan` |

### `macer md` Options

| Option | Description | Default |
|--------|-------------|---------|
| `-p`, `--poscar` | Input POSCAR/CONTCAR file. Supports velocity loading. | `POSCAR` |
| `--ensemble` | MD ensemble: `npt`, `nvt` (or `nte`), or `nve`. | `npt` |
| `--temp`, `--tebeg` | Target or starting temperature [K] (VASP `TEBEG`). | 300.0 |
| `--temp-end`, `--teend`| Final temperature [K] for linear ramping (VASP `TEEND`). | None |
| `--press` | Target pressure [GPa] (NPT only). | 0.0 |
| `--tstep` | MD time step [fs]. | 2.0 |
| `--ttau` | Thermostat time constant [fs]. | `0 (auto: 40*dt)` |
| `--ptau` | Barostat time constant [fs] (NPT only). | `0 (auto: from B)` |
| `--pfactor` | Directly set ASE NPT pfactor (overrides ptau). | None |
| `--nsteps` | Number of MD steps. | 20000 |
| `--output-dir` | Directory to save MD output files. | `.` |
| `--mass` | Specify atomic masses (e.g., `H 2.014`). | None |
| `--initial-relax` | Perform a full structural relaxation before the MD run. | `False` |

### `macer phonopy` Options

#### `macer phonopy pb` Options

| Option | Description | Default |
|--------|-------------|---------|
| `-p`, `--poscar` | Input POSCAR file(s). | Required |
| `-l`, `--length` | Minimum supercell lattice vector length in Å. | 20.0 |
| `--dim` | Set supercell dimension explicitly (e.g., `2 2 2`). Overrides `-l`. | None |
| `-pg`, `--plot-gruneisen` | Calculate and plot Grüneisen parameter. | False |
| `--strain` | Strain for Grüneisen calculation. If not set, estimated from bulk modulus. | None |
| `--irreps` | Calculate irreducible representations. | False |
| `--qpoint` | Q-point for irreps calculation (3 floats). | `0 0 0` |
| `--write-arrow` | Write VESTA and MCIF files for phonon mode visualization. | False |
| `--arrow-length` | Max arrow length in Å for VESTA visualization. | 1.7 |
| `--arrow-qpoint-gamma` | Generate arrows only for the Gamma point. | False |
| `--arrow-qpoint` | Generate arrows for a specific q-point vector (3 floats). | None |
| `--dos` | Calculate and plot Phonon DOS (Total + Projected). | False |
| `--mesh` | Q-point mesh for DOS calculation (3 ints). | `20 20 20` |
| `--mass` | Specify atomic masses (e.g., `H 2.014`). | None |
| `--output-dir` | Directory to save output files. | None |

#### `macer phonopy qha` Options

| Option | Description | Default |
|---|---|---|
| `--dim` | Set supercell dimension explicitly (e.g., `2 2 2`). Overrides `--min-length`. | None |
| `--num-volumes` | Number of volume points to sample for the E-V curve. | 5 |
| `--length-scale` | Symmetric strain range for volume sampling (e.g., 0.05 for ±5%). Auto-estimated if not set. | None |
| `--length-factor-min/max` | Explicitly define the min/max length scaling factors for the volume range. | None |
| `--eos` | Equation of state for fitting (`vinet`, `birch_murnaghan`, `murnaghan`, `local_poly`). | `vinet` |
| `--tmax` | Maximum temperature for thermal property calculation. | 1300 K |
| `--mass` | Specify atomic masses (e.g., `H 2.014`). | None |
| `--output-dir` | Directory to save all output files. | (auto) |

#### `macer phonopy sscha` Options

The SSCHA workflow is divided into several stages, each with its own set of options.

| Group | Option | Description | Default |
|---|---|---|---|
| **General** | `-p`, `--poscar` | Input crystal structure file (e.g., POSCAR). | Required |
| | `--ff` | Force field to use. | (dynamic) |
| | `--model` | Path or name of the MLFF model. | (from `default.yaml`) |
| | `--device` | Compute device (`cpu`, `mps`, `cuda`). | `cpu` |
| | `--modal` | Modal for SevenNet model, if required. | None |
| | `--seed` | Random seed for reproducibility. | None |
| **Initial FC** | `--initial-fmax` | Force convergence for initial relaxation (eV/Å). | 5e-3 |
| | `--dim` | Supercell dimension (e.g., `2 2 2`). Overrides `--min-length`. | (auto) |
| | `-l`, `--min-length` | Minimum supercell length if `--dim` is not set (Å). | 15.0 |
| | `--amplitude` | Displacement amplitude for 0K FC calculation (Å). | 0.03 |
| | `--pm` | Use plus/minus displacements for initial FC generation. | False |
| | `--nodiag` | Do not use diagonal displacements for initial FC generation. | False |
| | `--symprec` | Symmetry tolerance for phonopy (Å). | 1e-5 |
| | `--read-initial-fc` | Path to `FORCE_CONSTANTS` to skip initial calculation. | None |
| | `--initial-symmetry-off` | Disable `FixSymmetry` in the initial structure relaxation. | False |
| **Ensemble** | `--reference-method` | Method to generate ensemble (`random`, `md`). | `md` |
| | `--reference-n-samples` | Number of samples for `random` method. | 200 |
| | `--reference-md-nsteps` | Number of sampling steps for `md` method. | 200 |
| | `--reference-md-nequil` | Number of equilibration steps for `md` method. | 100 |
| | `--reference-md-tstep` | MD timestep in fs. | 1.0 |
| | `--md-thermostat` | Thermostat for MD ensemble (`langevin`, `nve`). | `langevin` |
| | `--md-friction` | Friction for Langevin thermostat (ps⁻¹). | 0.01 |
| | `--reference-ensemble` | Path to an existing `reference_ensemble.npz` or `.txt` to use. | None |
| | `--no-save-reference-ensemble` | Do not save the generated `reference_ensemble` file. | False |
| | `--write-xdatcar` | Write an `XDATCAR` file from the MD trajectory. | False |
| | `--xdatcar-step` | Step interval for writing frames to `XDATCAR`. | 50 |
| **SSCHA** | `-T`, `--temperature` | Target temperature in Kelvin. | Required |
| | `--max-iter` | Maximum number of reweighting iterations per cycle. | 200 |
| | `--max-regen` | Maximum number of ensemble regenerations if ESS collapses. | 200 |
| | `--ess-collapse-ratio` | ESS/total ratio below which the ensemble is regenerated. | 0.5 |
| | `--free-energy-conv` | Free energy convergence threshold (meV/atom). | 0.1 |
| | `--fc-mixing-alpha` | Linear mixing parameter for FC updates (0 < α ≤ 1). | 0.5 |
| | `--mesh` | Q-point mesh for free energy calculation (e.g., `7 7 7`). | `7 7 7` |
| | `--qscaild-selfconsistent` | Enable QSCAILD-style self-consistency (Sets method='random'). | False |
| | `--include-third-order` | Enable simultaneous fitting of 3rd order force constants. | False |
| **Volume Optimization** | `--optimize-volume` | Enable self-consistent volume optimization by minimizing free energy. | False |
| | `--max-volume-iter` | Maximum iterations for volume optimization. | 10 |
| **Output** | `--output-dir` | Directory to save all output files. | `sscha_{poscar_stem}` |
| | `--save-every` | Save intermediate `FORCE_CONSTANTS` every N steps. | 5 |
| | `--no-plot-bands` | Disable plotting of band structures. | (Plotting is on) |
| | `--gamma-label` | Label for the Gamma point in plots. | `GM` |

#### `macer phonopy thermal-conductivity` (aliased to `tc`) Options

| Option | Description | Default |
|---|---|---|
| `--mesh` | Q-point mesh for thermal conductivity calculation (e.g., `11 11 11`). | `11 11 11` |
| `-l`, `--length` | Min length for auto-determining FC3 dim (Å). | 12.0 |
| `-l2`, `--length-fc2` | Min length for auto-determining FC2 dim (Å). | 25.0 |
| `--dim` | FC3 supercell dimension (e.g., `2 2 2`). Overrides `-l`. | (auto) |
| `--dim-fc2` | FC2 supercell dimension (e.g., `4 4 4`). Overrides `-l2`. | (auto) |
| `--temp`, `--ts` | Specific temperatures to calculate (e.g., `300 400`). | None |
| `--save-hdf5` | Save heavy HDF5 files (`kappa`, `fc2`, `fc3`) for post-processing. | False |
| `--tmin/tmax/tstep` | Temperature range settings if `--temp` not set. | 0/1000/10 |
| `--amplitude` | Displacement amplitude (Å). | 0.03 |
| `--isif` | ISIF mode for initial relaxation (0 to skip). | 3 |

#### `macer phonopy finite-temperature` (aliased to `ft`) Options

| Option | Description | Default |
|---|---|---|
| `-p`, `--poscar` | Input crystal structure file. | Required |
| `-T`, `--temp` | List of temperatures to calculate (K). | Required |
| `--ensemble` | MD ensemble for renormalization: `nvt` or `npt`. | `nvt` |
| `--dim` | Supercell dimension (e.g., `2 2 2`). | (auto) |
| `-l`, `--min-length` | Min supercell length if `--dim` is not set (Å). | 15.0 |
| `--md-steps` | MD production steps. | 8000 |
| `--md-equil` | MD equilibration steps. | 2000 |
| `--time-step` | MD time step in fs. | 1.0 |
| `--ttau` | Thermostat time constant [fs]. | `0 (auto)` |
| `--ptau` | Barostat time constant [fs] (NPT only). | `0 (auto)` |
| `--pfactor` | Directly set ASE NPT pfactor. | None |
| `--thermostat` | MD thermostat (`nose-hoover`, `langevin`). | `nose-hoover` |
| `--psm` | Power spectrum algorithm (1: MEM, 2: FFT/Direct). | **2** |
| `--mem` | Number of MEM coefficients (only for `--psm 1`). | 1000 |
| `--resolution" | Power spectrum resolution (THz). | 0.05 |
| `--projection-qpoint` | Reduced q-vector for projection (e.g., `0.5 0.0 0.0`). | None |
| `--save-quasiparticles` | Save frequency shift/linewidth data to YAML. | False |
| `--thermal-properties` | Calculate thermal properties (Free energy, Entropy). | **True** |
| `--no-thermal-properties` | Disable thermal properties calculation. | False |
| `--power-spectrum` | Calculate and save power spectrum data. | **True** |
| `--no-power-spectrum` | Disable power spectrum calculation. | False |
| `--no-fcsymm` | Disable force constant symmetrization. | False |

### `macer gibbs` Options

| Option | Description | Default |
|---|---|---|
| `-p`, `--poscar` | Input crystal structure file. | `POSCAR` |
| `--temp-start` | Starting temperature (K). | 100 |
| `--temp-end` | Ending temperature (K). | 1000 |
| `--temp-step` | Temperature step size (K). | 50 |
| `--nsteps` | Number of MD production steps per temperature. | 50000 |
| `--equil-steps` | Number of MD equilibration steps. | 10000 |
| `--ensemble` | MD ensemble (`npt`, `nvt`). | `npt` |
| `--pressure` | Target pressure for NPT (GPa). | 0.0 |
| `--qha-ref` | Path to QHA result YAML for absolute G(T) reference. | None |
| `--output-dir` | Directory to save results. | (auto) |

### `macer pydefect` Options

#### `macer pydefect cpd` Options

| Option | Description | Default |
|---|---|---|
| `-f`, `--formula` | Chemical formula to retrieve from Materials Project (e.g., `MgAl2O4`). | None |
| `-m`, `--mpid` | Materials Project ID (e.g., `mp-3536`). | None |
| `-d`, `--doping` | List of dopant elements (e.g., `Ca Ti`). | None |
| `-p`, `--poscar` | Input POSCAR file(s) or glob pattern(s). | None |
| `--energy-shift-target` | Manually shift target energy in eV/atom (e.g., `0.05` to lower energy by 0.05 eV). | 0.0 |

#### `macer pydefect defect` Options

| Option | Description | Default |
|---|---|---|
| `-p`, `--poscar` | Input unit cell POSCAR file(s) or glob pattern(s). | Required |
| `-d`, `--doping` | List of dopant elements (e.g., `Ca Ti`). | None |
| `-s`, `--std_energies` | Path to `standard_energies.yaml` from CPD step. | Required |
| `-t`, `--target_vertices` | Path to `target_vertices.yaml` from CPD step. | Required |
| `--matrix` | Supercell matrix (e.g., `2 2 2`). | None |
| `--min_atoms` | Minimum number of atoms for supercell. | 50 |
| `--max_atoms` | Maximum number of atoms for supercell. | 300 |
| `--no_symmetry_analysis` | Disable symmetry analysis (requires `sites_yaml`). | False |
| `--sites_yaml` | Path to `sites.yaml` file (if symmetry analysis is disabled). | None |

#### `macer pydefect full` Options

| Option | Description | Default |
|---|---|---|
| `-p`, `--poscar` | Input unit cell POSCAR file(s) or glob pattern(s). | Required |
| `-d`, `--doping` | List of dopant elements (e.g., `Ca Ti`). | None |
| `--matrix` | Supercell matrix (e.g., `2 2 2`). | None |
| `--min_atoms` | Minimum number of atoms for supercell. | 50 |
| `--max_atoms` | Maximum number of atoms for supercell. | 300 |
| `--no_symmetry_analysis` | Disable symmetry analysis (requires `sites_yaml`). | False |
| `--sites_yaml` | Path to `sites.yaml` file (if symmetry analysis is disabled). | None |
| `--energy-shift-target` | Manually shift target energy in eV/atom. | 0.0 |

---

## Dependencies

### Core Dependencies
-   **Python** ≥ 3.10
-   **ASE** (Atomic Simulation Environment)
-   **Phonopy** & **Phono3py**
-   **Pymatgen** & **Monti**
-   **seekpath**
-   **pydefect** & **vise** (for defect analysis)

### MLFF Support (Unified Environment)
Macer supports multiple MLFFs in a single environment.
-   **MACE**: Bundled internally (legacy `e3nn` conflict is handled via shimming).
-   **SevenNet / FairChem**: Uses global `e3nn >= 0.5.1`.
-   **MatterSim**, **CHGNet**, **M3GNet (matgl)**, **Orb**, **Allegro (nequip)**: Integrated and ready to use after `pip install -e .`.

---
## Related packages
-   phonopy [https://github.com/phonopy/phonopy](https://github.com/phonopy/phonopy)
-   phono3py [https://github.com/phonopy/phono3py](https://github.com/phonopy/phono3py)
-   DynaPhoPy [https://github.com/abelcarreras/DynaPhoPy](https://github.com/abelcarreras/DynaPhoPy)
-   symfc [https://github.com/symfc/symfc](https://github.com/symfc/symfc)
-   pydefect [https://github.com/kumagai-group/pydefect](https://github.com/kumagai-group/pydefect)
-   SeeK-path [https://github.com/giovannipizzi/seekpath](https://github.com/giovannipizzi/seekpath)
---


#### Model & Structure Utilities (`macer util model/struct`)

```bash
# Convert a model to float32 precision
macer util model fp32 -i model.pth

# Convert VASP4 POSCAR to VASP5 (adds element symbols to the header)
macer util struct vasp4to5 -i POSCAR
```

---
### Mattersim Fine-tuning (`macer util ft`)
Specialized workflow for fine-tuning [Mattersim](https://github.com/microsoft/mattersim) pre-trained models. It refines pre-trained models using your own DFT data (e.g., `extended xyz` format or VASP `ML_AB` file) and performs automatic evaluation.

```bash
# Standard fine-tuning with auto-splitting (8:1:1) and auto-evaluation
macer util ft -d dataset.xyz --epochs 100

# Use 100% of data for training (no test set) with a specific base model
macer util ft -d dataset.xyz --full-train --model ./base_model.pth

# Custom validation data and differential learning rates (Head vs Backbone)
# Recommended: Higher Head LR for adapting to new chemical species
macer util ft -d train.xyz --valid-data valid.xyz --head-lr 1e-3 --backbone-lr 1e-5

# Fine-tuning without stress training (e.g., if using ISIF=0 data)
macer util ft -d dataset.xyz --epochs 10 --no-stresses
```

---

## Standalone Scripts

The `scripts/` directory contains standalone versions of some key workflows, which can be run directly with `python`.

---

## MLFF Model Attribution

This project integrates various Machine-Learned Force Fields (MLFFs). For more information, please refer to the official repositories:
*   **MACE:** [https://github.com/ACEsuit/mace-foundations](https://github.com/ACEsuit/mace-foundations)
*   **SevenNet:** [https://github.com/MDIL-SNU/SevenNet](https://github.com/MDIL-SNU/SevenNet)
*   **CHGNet:** [https://github.com/CederGroupHub/chgnet](https://github.com/CederGroupHub/chgnet)
*   **M3GNet:** [https://github.com/materialsvirtuallab/m3gnet](https://github.com/materialsvirtuallab/m3gnet)
*   **Allegro:** [https://github.com/mir-group/nequip](https://github.com/mir-group/nequip)
*   **MatterSim:** [https://github.com/microsoft/mattersim](https://github.com/microsoft/mattersim)
*   **Orb:** [https://github.com/orbital-materials/orb-models](https://github.com/orbital-materials/orb-models)
*   **FairChem:** [https://github.com/facebookresearch/fairchem](https://github.com/facebookresearch/fairchem) (Models available at [Hugging Face](https://huggingface.co/facebook/UMA))


---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.


---
 ## Contributors
- **Soungmin Bae** — [soungminbae@gmail.com](mailto:soungminbae@gmail.com), Tohoku University
- **Yasuhide Mochizuki** — [ahntaeyoung1212@gmail.com](mailto:ahntaeyoung1212@gmail.com), Institute of Science Tokyo

