import glob
import pandas as pd
import numpy as np
import os
from pathlib import Path
import re

# Base directory
base_dir = Path("/path/to/data/")

# Get lists of relevant files
epis = sorted(base_dir.glob("sub*/func/*_bold.nii"))
t1s_all = sorted(base_dir.glob("sub*/anat/*t1_BrainExtractionBrain.nii.gz"))
fmaps_all = sorted(base_dir.glob("sub*/fmap/{name}_gre_fmap_processed*/*"))
mags_all = sorted(base_dir.glob("sub*/fmap/*_gre_field_map*_BrainExtractionBrain.nii.gz"))

# Group by subject
subject_ids = sorted(set(p.name[:3] for p in epis))
design_dir = base_dir / "designs"
feats_dir = base_dir / "feats"
template_path = design_dir / "design_template.fsf"

for sub_id in subject_ids:
    # Get EPI runs
    sub_epis = sorted([f for f in epis if f.name.startswith(sub_id)], key=lambda x: int(re.search(r'run-(\d+)_bold.nii', x.name).group(1)))

    # Find matching T1, fmap, and mag files
    sub_t1s = [f for f in t1s_all if sub_id in f.name]
    sub_fmaps = sorted([f for f in fmaps_all if sub_id in f.name])
    sub_mags = sorted([f for f in mags_all if sub_id in f.name])

    # Create triplet logic
    if len(sub_fmaps) == 1:
        sub_fmaps *= 3
    if len(sub_mags) == 1:
        sub_mags *= 3
    if len(sub_t1s) == 1:
        sub_t1s *= 3

    # Match run-specific fmap/mag logic
    if any(re.search(r'gre_field_map_(\d+)', f.name) for f in sub_mags):
        run_code_to_index = {}
        for i, mag in enumerate(sub_mags):
            match = re.search(r'gre_field_map_(\d+)', mag.name)
            if match:
                code = match.group(1)
                if code == "1":
                    run_code_to_index[0] = i  # run 1
                elif code == "23":
                    run_code_to_index[1] = i  # run 2
                    run_code_to_index[2] = i  # run 3
                elif code == "12": 
                    run_code_to_index[0] = i  # run 1
                    run_code_to_index[1] = i  # run 2
                elif code == "3":
                    run_code_to_index[2] = i  # run 3
        mag_choices = [sub_mags[run_code_to_index.get(i, 0)] for i in range(3)]
        fmap_choices = [sub_fmaps[run_code_to_index.get(i, 0)] for i in range(3)]
    else:
        mag_choices = sub_mags
        fmap_choices = sub_fmaps

    for run_idx, epi in enumerate(sub_epis):
        t1 = sub_t1s[run_idx]
        mag = mag_choices[run_idx]
        fmap = fmap_choices[run_idx]
        run_num = run_idx + 1
        name = sub_id
        output = feats_dir / f"{name}_{run_num}"

        # Get number of volumes
        vols = os.popen(f"fslnvols {epi}").read().strip()

        # Prepare fsf file
        template = open(template_path)
        design_out = design_dir / f"{name}_{run_num}_design.fsf"
        with open(design_out, 'w') as f_out:
            for line in template:
                line = line.replace("X-OUTPUT-X", str(output))
                line = line.replace("X-VOLS-X", str(vols))
                line = line.replace("X-EPI-X", str(epi))
                line = line.replace("X-FMAP-X", str(fmap))
                line = line.replace("X-MAG-X", str(mag))
                line = line.replace("X-T1-X", str(t1))
                f_out.write(line)
        template.close()
        print(f"✅ Created design file for {name} run {run_num}")


#sbatch the fsf files
import time 
fsfs = sorted(glob.glob('/path/to/designs/*design.fsf'))

for i in range(len(fsfs)):
    fsf = fsfs[i]
    os.system('sbatch -c 3 feat %s' %(fsf))
    time.sleep(2)
    


