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

base_dir="/zwork/rizor/asap/7t_controls"
sub="subject_id"

#define directories 
sub_dir=$base_dir/$sub
echo "The subject directory is $sub_dir"

############################################################################################################################################

t1_2mm=$sub_dir/$sub"_t1_mp2rage_2mm.nii.gz"
t1_brain_2mm=$sub_dir/$sub"_t1_mp2rage_brain_2mm.nii.gz"
t1_brain_mask_2mm=$sub_dir/$sub"_t1_mp2rage_brain_mask_2mm.nii.gz"

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

#get SBref image as a reference for motion and distortion correction for the epi data
if [ -e $sub_dir/$sub"_SBRef_avg.nii.gz" ]; then
echo "SBref avg file already identified and renamed"
else

echo "identifying SBRef files"
epi_echo1_SBRef=$sub_dir/func/$sub"_task-rest_echo-1_sbref.nii"
epi_echo2_SBRef=$sub_dir/func/$sub"_task-rest_echo-2_sbref.nii"
epi_echo3_SBRef=$sub_dir/func/$sub"_task-rest_echo-3_sbref.nii"

echo "SBRef image 1: $epi_echo1_SBRef"
echo "SBRef image 2: $epi_echo2_SBRef"
echo "SBRef image 3: $epi_echo3_SBRef"

fslmerge -t $sub_dir/$sub"_SBRef_merged" $epi_echo1_SBRef $epi_echo2_SBRef $epi_echo3_SBRef
fslmaths $sub_dir/$sub"_SBRef_merged.nii.gz" -Tmean $sub_dir/$sub"_SBRef_avg.nii.gz"
fi 

SBRef=$sub_dir/$sub"_SBRef_avg.nii.gz"
echo "The SBRef file is: $SBRef"

#Brain extract the SBRef image 
if [ -e $sub_dir/$sub"_SBRef_brain.nii.gz" ]; then
echo "SBRef brain extraction already run"
else
echo "Running brain extraction on SBRef"
bet $SBRef $sub_dir/$sub"_SBRef_avg_brain" -f 0.40 -g 0.25 -m #these parameters may need to be changed depending on subject for good mask
fi

SBRef_brain=$sub_dir/$sub"_SBRef_avg_brain.nii.gz"
SBRef_brain_mask=$sub_dir/$sub"_SBRef_avg_brain_mask.nii.gz"

#get transforms for the SBRef image registration to the T1 and the distortion correction 
if [ -e $sub_dir/$sub"_SBRef2struct.mat" ]; then
echo "SBRef T1 registration and distortion correction already run"
else
echo "Running T1 registration and distortion correction on SBRef"
epi_reg --epi=$SBRef_brain --t1=$t1_2mm --t1brain=$t1_brain_2mm --out=$sub_dir/$sub"_SBRef2struct" 
fi

transform=$sub_dir/$sub"_SBRef2struct.mat"

#get motion correction of epi echo 1 
if [ -e $sub_dir/$sub"_epi_echo1_mc.mat" ]; then
echo "Echo1 motion correction already done"
else
echo "Running motion correction to SBRef image of echo 1"
mcflirt -in $echo1 -out $sub_dir/$sub"_epi_echo1_mc" -mats -plots -reffile $SBRef -rmsrel -rmsabs -spline_final
fsl_tsplot -i $sub_dir/$sub"_epi_echo1_mc.par" -t 'MCFLIRT estimated rotations (radians)' -u 1 --start=1 --finish=3 -a x,y,z -w 640 -h 144 -o rot.png 
fsl_tsplot -i $sub_dir/$sub"_epi_echo1_mc.par" -t 'MCFLIRT estimated translations (mm)' -u 1 --start=4 --finish=6 -a x,y,z -w 640 -h 144 -o trans.png 
fsl_tsplot -i $sub_dir/$sub"_epi_echo1_mc_abs.rms",$sub_dir/$sub"_epi_echo1_mc_rel.rms" -t 'MCFLIRT estimated mean displacement (mm)' -u 1 -w 640 -h 144 -a absolute,relative -o disp.png
fi

mc_transform=$sub_dir/$sub"_epi_echo1_mc.mat" 
epi_echo1_mc=$sub_dir/$sub"_epi_echo1_mc.nii.gz"

#apply motion correction to epi echoes 2 and 3
if [ -e $sub_dir/$sub_"epi_echo3_mc.nii.gz" ]; then
echo "Motion correction to echoes 2 and 3 already done"
else
echo "Running motion correction of echoes 2 and 3"
applyxfm4D $echo2 $SBRef $sub_dir/$sub"_epi_echo2_mc" $mc_transform -fourdigit 
applyxfm4D $echo3 $SBRef $sub_dir/$sub"_epi_echo3_mc" $mc_transform -fourdigit 
fi

epi_echo2_mc=$sub_dir/$sub"_epi_echo2_mc.nii.gz"
epi_echo3_mc=$sub_dir/$sub"_epi_echo3_mc.nii.gz"

#slice time correct all of the echoes 
if [ -e $sub_dir/$sub_"epi_echo1_mc_st.nii.gz" ]; then
echo "Slice time correction already run"
else
echo "Running slice time correction on all echoes"
slicetimer -i $epi_echo1_mc --out=$sub_dir/$sub"_epi_echo1_mc_st" -r 2.100000 --ocustom=$sub_dir/slicetime/slicetimeorder.txt
slicetimer -i $epi_echo2_mc --out=$sub_dir/$sub"_epi_echo2_mc_st" -r 2.100000 --ocustom=$sub_dir/slicetime/slicetimeorder.txt
slicetimer -i $epi_echo3_mc --out=$sub_dir/$sub"_epi_echo3_mc_st" -r 2.100000 --ocustom=$sub_dir/slicetime/slicetimeorder.txt
fi

epi_echo1_mc_st=$sub_dir/$sub"_epi_echo1_mc_st.nii.gz"
epi_echo2_mc_st=$sub_dir/$sub"_epi_echo2_mc_st.nii.gz"
epi_echo3_mc_st=$sub_dir/$sub"_epi_echo3_mc_st.nii.gz"

#apply SBRef mask to echo data to get brain epi data 
echo "Applying SBRef brain mask to motion and slice time corrected epis"  
fslmaths $epi_echo1_mc_st -mas $SBRef_brain_mask $sub_dir/$sub"_epi_echo1_mc_st_brain.nii.gz"
fslmaths $epi_echo2_mc_st -mas $SBRef_brain_mask $sub_dir/$sub"_epi_echo2_mc_st_brain.nii.gz"
fslmaths $epi_echo3_mc_st -mas $SBRef_brain_mask $sub_dir/$sub"_epi_echo3_mc_st_brain.nii.gz"

#apply registration to t1 to all echoes 
echo "Applying distortion correction and warping epi images to T1 2mm brain"
flirt -in $sub_dir/$sub"_epi_echo1_mc_st_brain.nii.gz" -ref $t1_brain_2mm -applyxfm -init $sub_dir/$sub"_SBRef2struct.mat"  -out $sub_dir/$sub"_epi_echo1_preproc.nii.gz"
flirt -in $sub_dir/$sub"_epi_echo2_mc_st_brain.nii.gz" -ref $t1_brain_2mm -applyxfm -init $sub_dir/$sub"_SBRef2struct.mat"  -out $sub_dir/$sub"_epi_echo2_preproc.nii.gz"
flirt -in $sub_dir/$sub"_epi_echo3_mc_st_brain.nii.gz" -ref $t1_brain_2mm -applyxfm -init $sub_dir/$sub"_SBRef2struct.mat"  -out $sub_dir/$sub"_epi_echo3_preproc.nii.gz"

#get mask for Tedana of the epi brain
echo "Getting echo1 mask for Tedana" 
fslmaths $sub_dir/$sub"_epi_echo1_preproc.nii.gz" -bin $sub_dir/$sub"_epi_preproc_mask.nii.gz" 
fslroi $sub_dir/$sub"_epi_preproc_mask.nii.gz" $sub_dir/$sub"_epi_preproc_mask.nii.gz" 0 1



