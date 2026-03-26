#!/bin/bash -l
###########################################################################################################################################

#Set up the environmental variables
FSLDIR=/sw/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH
export PATH=$PATH:/sw/afni/bin

###########################################################################################################################################


for sub in sub-01; do
 echo "Processing subject: $sub"
 base_dir="/path/to/your/data"
 sub_dir=$base_dir/$sub
 mni=$base_dir/MNI152_T1_2mm_brain.nii.gz
 func=$sub_dir/desc-denoised_bold.nii.gz #denosied Tedana output
 output=$base_dir/final_bolds_and_masks/$sub"_denoised_bold_mni.nii.gz"

 antsApplyTransforms -d 3 -e 3 -i $func -r $mni -t $sub_dir/$sub"_antshighres2mni1Warp.nii.gz" -t $sub_dir/$sub"_antshighres2mni0GenericAffine.mat" -o $output
 
done 
