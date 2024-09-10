#!/bin/bash

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=100:00:00
#SBATCH --partition=blanca-shirts
#SBATCH --qos=blanca-shirts
#SBATCH --account=blanca-shirts
#SBATCH --gres=gpu
#SBATCH --job-name=sfe_opc_test
#SBATCH --output=slurm_codes/sfe_opc_test.log

module purge
module avail
ml anaconda
conda activate old-evaluator-vsites

function convert_ff_to_v3 () {
    FF="/projects/bamo6610/software/anaconda/env/old-evaluator-vsites/lib/python3.9/site-packages/openforcefields/offxml/$1"
    cp /projects/bamo6610/software/anaconda/env/old-evaluator-vsites/lib/python3.9/site-packages/openforcefields/offxml/$1 $FF
    sed -i 's/    <vdW version="0.4" potential="Lennard-Jones-12-6" combining_rules="Lorentz-Berthelot" scale12="0.0" scale13="0.0" scale14="0.5" scale15="1.0" cutoff="9.0 \* angstrom \*\* 1" switch_width="1.0 \* angstrom \*\* 1" periodic_method="cutoff" nonperiodic_method="no-cutoff">/    <vdW version="0.3" potential="Lennard-Jones-12-6" combining_rules="Lorentz-Berthelot" scale12="0.0" scale13="0.0" scale14="0.5" scale15="1.0" cutoff="9.0 \* angstrom" switch_width="1.0 \* angstrom" method="cutoff">/g' $FF
    sed -i 's/    <Electrostatics version="0.4" scale12="0.0" scale13="0.0" scale14="0.8333333333" scale15="1.0" cutoff="9.0 \* angstrom \*\* 1" switch_width="0.0 \* angstrom \*\* 1" periodic_potential="Ewald3D-ConductingBoundary" nonperiodic_potential="Coulomb" exception_potential="Coulomb">/    <Electrostatics version="0.3" scale12="0.0" scale13="0.0" scale14="0.8333333333" scale15="1.0" cutoff="9.0 \* angstrom" switch_width="0.0 \* angstrom" method="PME">/g' $FF
    echo "converted $FF"
}

OFF="openff-1.3.1.offxml"
WATERFF="opc.offxml"

convert_ff_to_v3 "$OFF"
convert_ff_to_v3 "$WATERFF"

export OFF
export WATERFF

python sfe_npsamples.py
echo "Test of CC(C)C with 1000 total molecules using opc water and sage 1.3.1"

sacct --format=jobid,jobname,cputime,elapsed