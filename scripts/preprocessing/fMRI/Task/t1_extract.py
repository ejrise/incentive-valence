#!/usr/bin/env python

import os
import shutil
import glob
import re
from pathlib import Path
import ants

# Set environment variables
os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = "4"
os.environ["ANTS_RANDOM_SEED"] = "3"

# Define base directory and subject information
base_dir = Path("/path/to/data")
sub = "subject_id" #e.g., sub-333
sub_dir = base_dir / sub

# Paths for templates
template_dir = base_dir / "Ants_templates"
oasis_template = template_dir / "T_template0.nii.gz"
probability_mask = template_dir / "T_template0_BrainCerebellumProbabilityMask.nii.gz"
registration_mask = template_dir / "T_template0_BrainCerebellumRegistrationMask.nii.gz"
mni_template = base_dir / "MNI152_T1_2mm_brain.nii.gz"

# Paths for extracted T1 brain
t1_brain_path = sub_dir / f"{sub}_t1_BrainExtractionBrain.nii.gz"

# If T1 brain doesn't exist, extract it using ANTs
if not t1_brain_path.exists():
    t1_files = list(sub_dir.glob("/anat/*T1w.nii"))
    if t1_files:
        os.system(f"antsBrainExtraction.sh -d 3 -a {t1_files[0]} -e {oasis_template} "
                  f"-m {probability_mask} -f {registration_mask} -o {sub_dir}/anat/{sub}_t1_")

# Paths for field map brain extraction
fmap_brain_path = sub_dir / f"{sub}_gre_field_map_BrainExtractionBrain.nii.gz"

if not fmap_brain_path.exists():
    # Get all matching field mapping files
    fmap_files = sorted(sub_dir.glob("/fmap/*magnitude1*.nii"))

    if len(fmap_files) > 1:

        # Assign new names
        fmap_1 = f"{sub}_magnitude1A.nii"
        fmap_2 = f"{sub}_magnitude1B.nii"

        for i, fmap in enumerate([fmap_1, fmap_2], start=1):
            output_prefix = sub_dir / fmap / f"{sub}_gre_field_map_{i}_"
            os.system(f"antsBrainExtraction.sh -d 3 -a {fmap} -e {oasis_template} "
                      f"-m {probability_mask} -f {registration_mask} -o {output_prefix}")

    elif len(fmap_files) == 1:
        output_prefix = sub_dir / fmap / f"{sub}_gre_field_map_"
        os.system(f"antsBrainExtraction.sh -d 3 -a {fmap_files[0]} -e {oasis_template} "
                  f"-m {probability_mask} -f {registration_mask} -o {output_prefix}")

# Load images using ANTs
t1_brain = ants.image_read(str(t1_brain_path))
template = ants.image_read(str(mni_template))

# Path for transformed T1 image
t1_warped_path = sub_dir / f"{sub}_t1_warped.nii.gz"

if not t1_warped_path.exists():
    t1_to_template = ants.registration(
        fixed=template, moving=t1_brain, type_of_transform="SyN", outprefix=f"{sub}_t1_"
    )
    ants.image_write(t1_to_template["warpedmovout"], str(t1_warped_path))






