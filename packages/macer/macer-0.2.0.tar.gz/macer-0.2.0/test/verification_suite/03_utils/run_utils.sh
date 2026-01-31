#!/bin/bash
set -e

echo ">>> [03_utils] Starting Utilities Verification..."

# Generate data for testing utils
echo "  Generating test data via MD..."
macer md -p POSCAR --ff emt --dim 2 2 2 --ensemble nvt --temp 300 --nsteps 50 --save-every 10 --output-dir verif_md

# 3.1. MD Utils
echo "  [3.1] MD Utils..."
macer util md summary -i verif_md/md.csv
macer util md traj2xdatcar -i verif_md/md.traj -o verif_md/XDATCAR_util
macer util md plot -i verif_md/md.csv -o verif_md/plot_util
macer util md cell -i verif_md/md.traj -o verif_md/cell_util
macer util md rdf -i verif_md/md.traj -o verif_md/rdf_util --rmax 1.9

# 3.2. Struct & Model
echo "  [3.2] Struct & Model..."
macer util struct vasp4to5 -i POSCAR -o POSCAR_v5
macer util model list

# 3.3. Dynaphopy Wrapper
echo "  [3.3] Dynaphopy Wrapper..."
macer dynaphopy POSCAR verif_md/XDATCAR -q 0 0 0 -pd --silent

echo ">>> [03_utils] Verification Complete."