#!/usr/bin/env python

from pathlib import Path
import numpy as np
import time
import os

# === CONFIGURABLE PARAMETERS ===
sub_pattern = 'sub-*'  # Set your subject ID pattern here (e.g., '40*')

base_dir = Path('/path/to/data')
feat_dir = base_dir / 'feats'
design_dir = base_dir / 'designs'
template_script = design_dir / 'better_move_funcs_template.py'

template_path = Path('/path/to/MNI152_T1_2mm_brain.nii.gz')

# === LOAD INPUTS ===
funcs = sorted(feat_dir.glob(f'{sub_pattern}.feat/filtered_func_data.nii.gz'))
func_avgs = sorted(feat_dir.glob(f'{sub_pattern}.feat/mean_func.nii.gz'))
t1_brains = sorted(base_dir.glob(f'{sub_pattern}/anat/*t1_BrainExtractionBrain.nii.gz'))
tran1s = sorted(base_dir.glob(f'{sub_pattern}/anat/*t1_1Warp.nii.gz'))
tran2s = sorted(base_dir.glob(f'{sub_pattern}/anat/*t1_0GenericAffine.mat'))

# Repeat each transform/brain 3 times (3 runs per subject)
t1_brains = np.repeat(t1_brains, 3)
tran1s = np.repeat(tran1s, 3)
tran2s = np.repeat(tran2s, 3)
runs = list(range(1, 4)) * (len(t1_brains) // 3)

# === READ TEMPLATE ONCE ===
with open(template_script, 'r') as f:
    template_lines = f.readlines()

# === LOOP THROUGH SUBJECTS/RUNS ===
for i, func in enumerate(funcs):
    func_avg = func_avgs[i]
    t1_brain = t1_brains[i]
    tran1 = tran1s[i]
    tran2 = tran2s[i]
    run = runs[i]

    # Grab subject ID from the .feat folder name (e.g., '401.feat')
    name = func.parent.name[:3]  # Adjust if subject ID is longer

    prefix = f"{name}_{run}"
    output_file = design_dir / f"{prefix}_move_funcs.py"

    # Placeholders to replace in template
    replacements = {
        "X-FUNC-X": str(func),
        "X-FUNCAVG-X": str(func_avg),
        "X-T1-X": str(t1_brain),
        "X-TRAN1-X": str(tran1),
        "X-TRAN2-X": str(tran2),
        "X-PREFIX-X": prefix
    }

    # Write the filled-in template
    with open(output_file, 'w') as out_file:
        for line in template_lines:
            for key, value in replacements.items():
                line = line.replace(key, value)
            out_file.write(line)

# Paths
design_dir = Path('/path/to/designs')
scripts = sorted(design_dir.glob("*move_funcs.py"))
batch_dir = Path('/path/to/designs')
batch_dir.mkdir(parents=True, exist_ok=True)  # Ensure the output dir exists

for script in scripts:
    prefix = script.stem[:5]  # Grabs first 5 characters of the filename
    print(f"Submitting {prefix}")

    batch_file = batch_dir / f"{prefix}.job"

    # Write the SLURM batch file
    with open(batch_file, 'w') as fh:
        fh.writelines([
            "#!/bin/bash\n",
            "#SBATCH -c 12\n",
            "cd /path/to/designs\n",
            "eval \"$(conda shell.bash hook)\"\n",
            "conda activate /path/to/anaconda3/envs/antsPy\n",
            "which python\n",
            "python -c \"import ants; print('ants module is working')\"\n",
            f"python3 {script}\n"
        ])

    os.system(f"sbatch {batch_file}")
    time.sleep(3)





