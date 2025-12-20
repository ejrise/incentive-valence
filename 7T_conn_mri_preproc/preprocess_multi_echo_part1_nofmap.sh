#!/bin/bash -l
#SBATCH --nodes=1 --ntasks-per-node=1
#SBATCH --mem=20G
cd $SLURM_SUBMIT_DIR

date
hostname
###########################################################################################################################################

#Set up the environmental variables
FSLDIR=/sw/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH
export PATH=$PATH:/sw/afni/bin

base_dir="/path/to/base/dir"
sub="subject_id"

#define directories 
sub_dir=$base_dir/$sub
echo "The subject directory is $sub_dir"
t1=$sub_dir/anat/$sub"_acq-3_T1w.nii" #change to preferred T1 image out of the 3 contrasts
mni=$base_dir/MNI152_T1_2mm_brain.nii.gz

#############################f###############################################################################################################

#check if brain is already extracted. If it isn't, run ANTs brain extraction. 
if [ -e $sub_dir/$sub"_t1_BrainExtractionBrain.nii.gz" ]; then
echo "renaming t1 files"
mv $sub_dir/$sub"_t1_BrainExtractionBrain.nii.gz" $sub_dir/$sub"_t1_mp2rage_brain.nii.gz"
mv $sub_dir/$sub"_t1_BrainExtractionMask.nii.gz" $sub_dir/$sub"_t1_mp2rage_mask.nii.gz" 
fi

if [ -e $sub_dir/$sub"_t1_mp2rage_brain.nii.gz" ]; then
echo "brain already extracted"
else
echo "extracting T1 brain"
antsBrainExtraction.sh -d 3 -a $t1 -e $base_dir/Ants_templates/T_template0.nii.gz -m $base_dir/Ants_templates/T_template0_BrainCerebellumProbabilityMask.nii.gz -f $base_dir/Ants_templates/T_template0_BrainCerebellumRegistrationMask.nii.gz -o $sub_dir/$sub"_t1_"
mv $sub_dir/$sub"_t1_BrainExtractionBrain.nii.gz" $sub_dir/$sub"_t1_mp2rage_brain.nii.gz"
mv $sub_dir/$sub"_t1_BrainExtractionMask.nii.gz" $sub_dir/$sub"_t1_mp2rage_mask.nii.gz" 
fi 

t1_brain=$sub_dir/$sub"_t1_mp2rage_brain.nii.gz"
echo "the t1 brain file is: $t1_brain"

#check if T1 has been resampled. If not, resample to 2mm voxel resolution.
if [ -e $sub_dir/$sub"_t1_mp2rage_2mm.nii.gz" ]; then
echo "T1 already resampled to func resolution"
else
echo "Resampling T1 to func 2mm resolution"
flirt -in $t1 -ref $t1 -applyisoxfm 2.0 -nosearch -out $sub_dir/$sub"_t1_mp2rage_2mm.nii.gz"
fi 

#check if T1 has been resampled. If not, resample to 2mm voxel resolution.
if [ -e $sub_dir/$sub"_t1_mp2rage_brain_2mm.nii.gz" ]; then
echo "T1 brain already resampled to func resolution"
else
echo "Resampling T1 brain to func 2mm resolution"
flirt -in $t1_brain -ref $t1_brain -applyisoxfm 2.0 -nosearch -out $sub_dir/$sub"_t1_mp2rage_brain_2mm.nii.gz"
fi 

fslmaths $sub_dir/$sub"_t1_mp2rage_brain_2mm.nii.gz" -bin $sub_dir/$sub"_t1_mp2rage_brain_mask_2mm.nii.gz"
t1_2mm=$sub_dir/$sub"_t1_mp2rage_2mm.nii.gz"
t1_brain_2mm=$sub_dir/$sub"_t1_mp2rage_brain_2mm.nii.gz"
t1_brain_mask_2mm=$sub_dir/$sub"_t1_mp2rage_brain_mask_2mm.nii.gz"

#check if MNI has been registered to T1 for future mask movement. If not, register T1 to MNI. 
if [ -e $sub_dir/$sub"_mni2highresWarped.nii.gz" ]; then
echo "T1 brain already registered to MNI space"
else
echo "Registering MNI to 2mm T1 brain"
antsRegistrationSyN.sh -d 3 -f $t1_brain_2mm -m $mni -t sr -o $sub_dir/$sub"_mni2highres" - restrict-deformation 1x1x0
fi

#check if flirt has been used to register MNI to T1 for future mask movement. If not, register MNI to T1 
if [ -e $sub_dir/$sub"_flirtmni2highres.mat" ]; then
echo "MNI template already registered to t1"
else
echo "Registering MNI to 2mm T1 brain with flirt"
flirt -in $mni -ref $t1_brain_2mm -out $sub_dir/$sub"_flirtmni2highres" 
flirt -in $mni -ref $t1_brain_2mm -omat $sub_dir/$sub"_flirtmni2highres.mat" 
fi

#transform all OLC and CLC Masks (in MNI space) to participant T1 space with flirt 
region_path=$base_dir"/regions/all_regions"
mkdir $sub_dir/$sub"_region_masks"

find "$region_path" -type f | while read -r file_path; do
file_name=$(basename "$file_path")
echo "the file name is" $file_name
variable_name="${file_name%.nii.gz}"
echo "Transforming region: $variable_name"
flirt -in $file_path -ref $t1_brain_2mm -applyxfm -init $sub_dir/$sub"_flirtmni2highres.mat" -out $sub_dir/$sub"_region_masks"/$variable_name"_to_t1_flirt.nii.gz" 
done

#check if ANTs has been used for registration of T1 to MNI for future fisher's Z map movement. If not, register T1 to MNI
if [ -e $sub_dir/$sub"_antshighres2mniWarped.nii.gz" ]; then
echo "T1 already registered with ANTs to MNI space"
else
echo "Registering T1 brain to MNI space"
antsRegistrationSyN.sh -d 3 -f $mni -m $t1_brain_2mm -o $sub_dir/$sub"_antshighres2mni" - restrict-deformation 1x1x0
fi 
 
#Identify echo files, rename them, and list their volumes and TR 
echo "Renaming Echoes"
file1=$sub_dir/func/$sub"_task-rest_echo-1_bold.nii"
file2=$sub_dir/func/$sub"_task-rest_echo-2_bold.nii"
file3=$sub_dir/func/$sub"_task-rest_echo-3_bold.nii"
scp $file1 $sub_dir/$sub"_epi_echo1.nii"
scp $file2 $sub_dir/$sub"_epi_echo2.nii"
scp $file3 $sub_dir/$sub"_epi_echo3.nii"
echo "Running analysis on" $file1 $file2 $file3

echo "Echoes already renamed"
file1=$sub_dir/$sub"_epi_echo1.nii"
file2=$sub_dir/$sub"_epi_echo2.nii"
file3=$sub_dir/$sub"_epi_echo3.nii"
echo "Running analysis on" $file1 $file2 $file3

echo1=$sub_dir/$sub"_epi_echo1.nii.gz"
echo2=$sub_dir/$sub"_epi_echo2.nii.gz"
echo3=$sub_dir/$sub"_epi_echo3.nii.gz"

echo "the epi files are: $echo1 $echo2 $echo3"

result1=$(fslinfo $echo1 | grep dim4)
result2=$(fslinfo $echo2 | grep dim4)
result3=$(fslinfo $echo3 | grep dim4)

#the total volumes and TR for these should be 300 and 2.1 
echo "The Volumes and TR for echo 1 are:" $result1
echo "The Volumes and TR for echo 2 are:" $result2
echo "The Volumes and TR for echo 3 are:" $result3

#get fsl motion outliers. Check fd_plot for movement. 
if [ -e $sub_dir/participant_session_confound.txt ]; then
echo "fsl motion outliers already calculated"
else
echo "Getting FSL motion outliers with threshold 0.2mm"
mot_thresh=0.2
fsl_motion_outliers -i $echo1 -o $sub_dir/participant_session_confound.txt --fd --thresh=$mot_thresh -s $sub_dir/fd.txt -p $sub_dir/fd_plot -v > $sub_dir/participant_session_confound.txt 
fi 



