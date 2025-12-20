import os
from tedana import workflows

sub="subject_id"
sub_dir="/path/to/subs/%s" %sub
echo_file1=sub_dir + "/%s_epi_echo1_preproc.nii.gz" %sub
echo_file2=sub_dir + "/%s_epi_echo2_preproc.nii.gz" %sub
echo_file3=sub_dir + "/%s_epi_echo3_preproc.nii.gz" %sub
mask=sub_dir + "/%s_epi_preproc_mask.nii.gz"  %sub

workflows.tedana_workflow(
    data=[echo_file1, echo_file2, echo_file3],
    tes=[15.20, 33.87, 52.54],
    out_dir=sub_dir,
    mask=mask,
    tedpca=100,
    fittype="curvefit",
    fixed_seed=42,
    gscontrol="gsr",
    debug=True,
    verbose=True,
    overwrite=True,
)
 

# echo times for 7T_control_01-7T_control_08 15.20, 34.23, 53.26
# echo times for 7T_control_09-7T_control_28 15.20, 33.87, 52.54
