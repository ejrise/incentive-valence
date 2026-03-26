from pathlib import Path
import ants
import subprocess

# Set paths
template_path = Path('/path/to/MNI152_T1_2mm_brain.nii.gz')
func_path = Path('X-FUNC-X')
func_avg_path = Path('X-FUNCAVG-X')
t1_brain_path = Path('X-T1-X')
tran1 = 'X-TRAN1-X'
tran2 = 'X-TRAN2-X'
output_dir = Path('/path/to/bold_final')
prefix = 'X-PREFIX-X'

# Run ANTs registration (sr = SyN with rigid initialization)
ants_reg_cmd = [
    "antsRegistrationSyN.sh",
    "-d", "3",
    "-f", str(func_avg_path),
    "-m", str(t1_brain_path),
    "-t", "sr",
    "-o", str(output_dir / prefix)
]
subprocess.run(ants_reg_cmd, check=True)

# Get transform files
tran3 = output_dir / f"{prefix}0GenericAffine.mat"
tran4 = output_dir / f"{prefix}1InverseWarp.nii.gz"

# Read images
func_img = ants.image_read(str(func_path))
template_img = ants.image_read(str(template_path))

# Apply all transforms in order
transforms = [tran1, tran2, str(tran3), str(tran4)]
invert_flags = [False, False, True, False]

bold_final = ants.apply_transforms(
    fixed=template_img,
    moving=func_img,
    transformlist=transforms,
    imagetype=3,
    whichtoinvert=invert_flags
)

# Save output
output_path = output_dir / f"{prefix}bold_final_2mm.nii.gz"
ants.image_write(bold_final, str(output_path))

