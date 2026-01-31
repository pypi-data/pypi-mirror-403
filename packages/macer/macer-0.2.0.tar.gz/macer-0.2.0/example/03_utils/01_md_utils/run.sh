#!/bin/bash
macer md -p POSCAR --ff emt --dim 2 2 2 --temp 300 --nsteps 50 --output-dir md_output
macer util md summary -i md_output/md.csv
macer util md plot -i md_output/md.csv -o plots
macer util md traj2xdatcar -i md_output/md.traj -o XDATCAR
