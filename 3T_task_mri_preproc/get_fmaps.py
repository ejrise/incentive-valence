
import glob
import os
import re
from pathlib import Path

base_dir = "/path/to/data"

# Get magnitude brain paths
mag_brains = sorted(glob.glob(f"{base_dir}/sub*/fmap/*gre_field_map*BrainExtractionBrain.nii.gz"))

# Get and sort phase images: first by subject, then by numerical index before _e2_ph
phase_files = sorted(
    glob.glob(f"{base_dir}/sub*/fmap/*_phasediff*.nii"),
)

# Loop through all magnitude images
for i, mag_brain in enumerate(mag_brains):
    mag_path = Path(mag_brain)

    # Match gre_field_map with optional number
    name_match = re.search(r"(sub-\d.*)_gre_field_map(?:_(\d+))?_BrainExtractionBrain", mag_path.name)
    if not name_match:
        print(f"❌ Could not extract name from: {mag_path.name}")
        continue

    name = name_match.group(1)
    fmap_number = name_match.group(2)  # Will be None if no number
    sub = re.match(r"(sub-\d+)", name).group(1)

    # Get the corresponding phase files (assuming phase files are in correct order)
    if i >= len(phase_files):
        print(f"⚠️ Not enough phase images to match for {mag_path}")
        continue

    phase_path = phase_files[i]

    # Build output folder path
    output_folder = f"{base_dir}/{sub}/fmap/{name}_gre_fmap_processed"

    # 🔍 Print match info. Make sure mag and phase images match each other
    print(f"🧠 Subject: {sub}")
    print(f"🧲 Magnitude Image: {mag_path}")
    print(f"🌀 Phase Image: {phase_path}")
    print(f"📁 Output Folder: {output_folder}")

    confirm = input("👉 Are these correct? Type 'y' to continue: ").strip().lower()
    if confirm != "y":
        print("⏭️ Skipping...\n")
        continue

    run_code = input("🔢 Enter run code (e.g., 1, 2… or 0 for no number): ").strip() #write the runs that correspond with this fmap file (can be multiple, e.g. 23 for runs 2 and 3)

    if run_code == "0":
        final_output_folder = f"{base_dir}/{sub}/fmap/{name}_gre_fmap_processed"
        final_mag_path = mag_path  # Leave unchanged
    else:
        final_output_folder = f"{base_dir}/{sub}/fmap/{name}_gre_fmap_processed_{run_code}"
        # Rename the mag file path with the run number
        new_mag_name = re.sub(r'gre_field_map(_\d+)?', f'gre_field_map_{run_code}', mag_path.name)
        new_mag_path = mag_path.with_name(new_mag_name)
        os.rename(mag_path, new_mag_path)
        final_mag_path = new_mag_path

    # Final call
    os.system(
        f'bash /path/to/prepare_fieldmap_eal.sh SIEMENS "{phase_path}" "{final_mag_path}" "{final_output_folder}" 2.46'
    )



