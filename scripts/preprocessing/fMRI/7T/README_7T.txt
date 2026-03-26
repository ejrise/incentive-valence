preprocess
1. preprocess_multi_echo_part1.sh with or without fmap for bad fmap subs (use bet_fsl.sh for to get mag brain if ANTs/default BET isn't good)

2. get_slicetime_files.py to get custom slicetime correction files 

2. preprocess_multi_echo_part2.sh with or without fmap (use bet_fsl.sh for to get SBRef brain if ANTs/default BET isn't good)

3. tedana_script.py for Tedana denoising 

4. Prepare physio regressor files: with physIO toolbox in MATLAB, create and run physio jobs scripts for cardiac and respiratory files

5. Normalize denoised data to MNI with denoised_funcs_to_mni.sh before inputting into CONN Toolbox

To replicate the findings in Dundon, Rizor et al., next use CONN toolbox as directed in the supplementary information. 