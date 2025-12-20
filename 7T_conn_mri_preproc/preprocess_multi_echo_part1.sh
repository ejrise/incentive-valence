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
t1=$sub_dir/anat/$sub"_acq-3_T1w.nii" #change to preferred T1 file contrast 
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

#check if T1 brain has been resampled. If not, resample to 2mm voxel resolution.
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

#check if ANTs MNI has been registered to T1 for future mask movement. If not, register T1 to MNI. 
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
fsl_motion_outliers -i $echo1 -o $sub_dir/participant_session_confound.txt --fd --thresh=$mot_thresh -s $sub_dir/fd.txt -p $sub_dir/fd_plot 
fi 

#prepare fieldmap and mag images for distortion correction
echo "preparing fmap and mag images for distortion correction" 

if [ -e $sub_dir/$sub"_fmap_AP.nii" ]; then
echo "fmap files already identified and renamed"
spin_echo_AP=$sub_dir/$sub"_fmap_AP.nii.gz"
spin_echo_PA=$sub_dir/$sub"_fmap_PA.nii.gz"
else

echo "identifying fmap files and renaming"

spin_echo_PA=$sub_dir/fmap/$sub"_dir-PA_epi.nii"
spin_echo_AP=$sub_dir/fmap/$sub"_dir-AP_epi.nii"

echo "fmap image PA: $spin_echo_PA"
echo "fmap image AP: $spin_echo_AP"

scp $spin_echo_PA $sub_dir/$sub"_fmap_PA.nii" 
scp $spin_echo_AP $sub_dir/$sub"_fmap_AP.nii" 
fi 

spin_echo_PA=$sub_dir/$sub"_fmap_PA.nii" 
spin_echo_AP=$sub_dir/$sub"_fmap_AP.nii" 

echo "Final fmap image 1: $spin_echo_PA"
echo "Final fmap image 2: $spin_echo_AP"

#total readout time is 0.0304001 for 7T_control_01-7T_control_08 and 0.0294501 for 7T_control_09-7T_control_21

readout=0.0294501

echo "Subject ID: $sub"
echo "Readout time: $readout"

#run topup to generate field map and mag from the spin echo epi scans
if [ -e $sub_dir/$sub"_fmap.nii.gz" ]; then
echo "topup already run"
else
echo "preparing params file and running topup"
echo "readout time is $readout"
rm -f $sub_dir/acq_params.txt
touch $sub_dir/acq_params.txt

echo '0 1 0' $readout >> $sub_dir/acq_params.txt 
echo '0 1 0' $readout >> $sub_dir/acq_params.txt 
echo '0 1 0' $readout >> $sub_dir/acq_params.txt 
echo '0 -1 0' $readout >> $sub_dir/acq_params.txt 
echo '0 -1 0' $readout >> $sub_dir/acq_params.txt 
echo '0 -1 0' $readout >> $sub_dir/acq_params.txt 

fslmerge -t $sub_dir/$sub"_merged_fmaps" $spin_echo_PA $spin_echo_AP

topup --verbose --imain=$sub_dir/$sub"_merged_fmaps.nii.gz" --datain=$sub_dir/acq_params.txt --config=$FSLDIR/src/topup/flirtsch/b02b0.cnf --out=$sub_dir/rs_topup --iout=$sub_dir/topup_mag --fout=$sub_dir/$sub"_fmap"
fslroi $sub_dir/topup_mag.nii.gz $sub_dir/$sub"_mag.nii.gz" 0 3
fslmaths $sub_dir/$sub"_mag.nii.gz" -Tmean $sub_dir/$sub"_mag.nii.gz"
fi

fmap_mag=$sub_dir/$sub"_mag.nii.gz"
fmap=$sub_dir/$sub"_fmap.nii.gz"

echo "The fmap file is: $fmap"
echo "The mag file is: $fmap_mag"

#brain extract the topup mag brain 
if [ -e $sub_dir/$sub"_mag_brain.nii.gz" ]; then
echo "mag brain already extracted"
else
echo "extracting mag brain" 
antsBrainExtraction.sh -d 3 -a $fmap_mag -e $base_dir/Ants_templates_T2/T_template3.nii.gz -m $base_dir/Ants_templates_T2/T_template_BrainCerebellumProbabilityMask.nii.gz -f $base_dir/Ants_templates_T2/T_template_BrainCerebellumExtractionMask.nii.gz -o $sub_dir/#$sub"_topup_mag_"
mv $sub_dir/$sub"_topup_mag_BrainExtractionBrain.nii.gz" $sub_dir/$sub"_mag_brain.nii.gz"
mv $sub_dir/$sub"_topup_mag_BrainExtractionMask.nii.gz" $sub_dir/$sub"_mag_brain_mask.nii.gz" 
fi 

mag_brain=$sub_dir/$sub"_mag_brain.nii.gz"
echo "Time to check mag brain file: $mag_brain"

#this brain extraction may or may not be good. If not, used bet_fsl.sh
echo "If brain extraction wasn't good, use ../bet_fsl.sh"

