#!/bin/bash
#--------------------------------------------------------------------------------------#
# prepare_fieldmap - script to process fieldmap images into form suitable for FEAT (rad/s)
#
# Mark Jenkinson, Johannes Klein and Karla Miller, FMRIB Centre
#
# Copyright (C) 2004-2008 University of Oxford 
#
# SHCOPYRIGHT
#
# V1 2005_07_28 Johannes Klein/Mark Jenkinson, FMRIB Centre
# V2 2007_07_05 KLM: added input for TE time (seems to be 2.46 now??)
# V2 2007_07_06 KLM: added detection of magnitude image dimensions
# V4 2007_09_15 KLM: changed to work with new fsltools
# V5 2008_03_19 MJ: major modifications to do sanity checking and work with both  VARIAN and OCMR data - first supported version in FMRIB
# V6 2014_09_25 TS: major spelling error modifications fixed
# V7 2014_09_26 EAL: Calculates with GE scanner # Edited 07/09/2015 EAL
# V8 2016_04_12 EAL: Mac compatible (minor updates)
#--------------------------------------------------------------------------------------#
#
#-------------------------------- VARIABLES --------------------------------#

#--------------------------- DEFAULT SETTINGS ------------------------------#
text_editors=('kwrite' 'gedit' 'open -a /Applications/TextWrangler.app' 'open' 'nano' 'emacs') # text editor commands in order of preference

IFS_original="${IFS}" # whitespace separator
IFS=$'\n' # newline separator (needed when paths have whitespace)
#------------------------- SCRIPT HELP MESSAGE -----------------------------#
script_usage () { # Script explanation
	echo "${red}HELP MESSAGE: ${gre}${script_path}${whi}
${ora}DESCRIPTION${whi}: Prepares a fieldmap suitable for FEAT from ${ora}GE${whi}, ${ora}SIEMENS${whi} or ${ora}VARIAN${whi} data - saves output in rad/s format
<${ora}scanner${whi}> can be SIEMENS or VARIAN
<${ora}magnitude image${whi}> should be Brain Extracted (with BET or otherwise)
<${ora}deltaTE${whi}> is the echo time difference of the fieldmap sequence - find this out form the operator (defaults are *usually* 2.00ms on GE, 2.46ms on SIEMENS and 2.5ms on VARIAN)
${ora}--nocheck${whi} suppresses automatic sanity checking of image size/range/dimensions
     
${ora}USAGE${whi}: Input <${ora}scanner${whi}> <${ora}phase_image${whi}> <${ora}magnitude_image${whi}> <${ora}out_image${whi}> <${ora}deltaTE${whi} (in ms)> [${ora}--nocheck${whi}]
 [${ora}1${whi}] ${gre}${script_path} ${ora}SIEMENS images_3_gre_field_mapping images_4_gre_field_mapping fmap_rads 2.65${whi}
     
${ora}USAGE${whi}:
 [${ora}1${whi}] ${gre}${script_path}${whi}
     
${ora}OPTIONS${whi}: Can input multiple options in any order
 ${pur}-cs${whi}  Prevent screen from clearing before script processes
 ${pur}-h${whi} or ${pur}--help${whi}  Display this message
 ${pur}-nc${whi}  Prevent color printing in terminal
 ${pur}-o${whi} or ${pur}--open${whi} Open this script
     
${ora}DEFAULT SETTINGS${whi}:
 text editors: ${gre}${text_editors[@]}${whi}
     
${ora}VERSION: ${gre}${version_number}${whi}
${red}END OF HELP: ${gre}${script_path}${whi}"
	exit_message 0
} # script_usage

#----------------------- GENERAL SCRIPT VARIABLES --------------------------#
script_path="${BASH_SOURCE[0]}" # Script path (becomes absolute path later)
version_number='8.0'            # Script version number

	###--- 'yes' or 'no' options (inputs do the opposite of default) ---###
activate_colors='yes' # 'yes': Display messages in color [INPUT: '-nc']
activate_help='no'    # 'no' : Display help message      [INPUT: '-h' or '--help']
clear_screen='yes'    # 'yes': Clear screen at start     [INPUT: '-cs']
open_script='no'      # 'no' : Open this script          [INPUT: '-o' or '--open']
suggest_help='no'     # 'no' : Suggest help (within script option: '-nh')

#-------------------------------- FUNCTIONS --------------------------------#
option_eval () { # Evaluate inputs
	if [ "${1}" == '-cs' 2>/dev/null ] || [ "${1}" == '-h' 2>/dev/null ] || \
	   [ "${1}" == '--help' 2>/dev/null ] || [ "${1}" == '-nc' 2>/dev/null ] || \
	   [ "${1}" == '-o' 2>/dev/null ] || [ "${1}" == '--open' 2>/dev/null ]; then
		activate_options "${1}"
	fi
} # option_eval

activate_options () { # Activate input options
	if [ "${1}" == '-cs' ]; then
		clear_screen='no'    # Do NOT clear screen at start
	elif [ "${1}" == '-h' ] || [ "${1}" == '--help' ]; then
		activate_help='yes'  # Display help message
	elif [ "${1}" == '-nc' ]; then
		activate_colors='no' # Do NOT display messages in color
	elif [ "${1}" == '-o' ] || [ "${1}" == '--open' ]; then
		open_script='yes'    # Open this script
	else # if option is not defined here (for debugging)
		bad_inputs+=("ERROR:activate_options:${1}")
	fi
} # activate_options

color_formats () { # Print colorful terminal text
	if [ "${activate_colors}" == 'yes' 2>/dev/null ]; then
		whi=`tput setab 0; tput setaf 7` # Black background, white text
		red=`tput setab 0; tput setaf 1` # Black background, red text
		ora=`tput setab 0; tput setaf 3` # Black background, orange text
		gre=`tput setab 0; tput setaf 2` # Black background, green text
		blu=`tput setab 0; tput setaf 4` # Black background, blue text
		pur=`tput setab 0; tput setaf 5` # Black background, purple text
		formatreset=`tput sgr0`          # Reset to default terminal settings
	fi
} # color_formats

mac_readlink () { # Get absolute path of a file
	dir_mac=$(dirname "${1}")   # Directory path
	file_mac=$(basename "${1}") # Filename
	wd_mac="$(pwd)" # Working directory path

	if [ -d "${dir_mac}" ]; then
		cd "${dir_mac}"
		echo "$(pwd)/${file_mac}" # Print full path
		cd "${wd_mac}" # Change directory back to original directory
	else
		echo "${1}" # Print input
	fi
} # mac_readlink

open_text_editor () { # Opens input file
	file_to_open="${1}"
	valid_text_editor='no'
	
	if [ -f "${file_to_open}" ]; then
		for i in ${!text_editors[@]}; do # Loop through indices
			${text_editors[i]} "${file_to_open}" 2>/dev/null &
			pid="$!" # Background process ID
			check_text_pid=(`ps "${pid}" |grep "${pid}"`) # Check if pid is running
			
			if [ "${#check_text_pid[@]}" -gt '0' ]; then
				valid_text_editor='yes'
				break
			fi
		done

		if [ "${valid_text_editor}" == 'no' 2>/dev/null ]; then
			echo "${red}NO VALID TEXT EDITORS: ${ora}${text_editors[@]}${whi}"
			exit_message 99 -nh
		fi
	else
		echo "${red}MISSING FILE: ${ora}${file_to_open}${whi}"
	fi
} # open_text_editor

bet_check() {
  # check that absolute image has been brain extracted
  imroot=$1
  nvox=`$FSLDIR/bin/fslstats ${imroot} -v | awk '{ print $1 }'`;
  nvoxnz=`$FSLDIR/bin/fslstats ${imroot} -V | awk '{ print $1 }'`;
  if [ `echo $nvoxnz / $nvox \> 0.90 | bc -l` -eq 1 ] ; then
      echo "Magnitude (abs) image should be brain extracted"
      echo "Please run BET on image ${imroot} before using it here"
      exit 2
  fi
}

check_name_space () { # Exit script if filename contains a space
	for file_inputs; do
		check_space=($(echo "${file_inputs}" |grep ' '))
		if [ "${#check_space[@]}" -gt '0' ]; then
			echo "${red}FILENAMES CANNOT CONTAIN SPACES: ${ora}${file_inputs}${whi}"
			exit_message 99 -nm
		fi
	done
} # check_name_space

clean_up_edge() {
    # does some despiking filtering to clean up the edge of the fieldmap
    # args are: <fmap> <mask> <tmpnam>
    outfile=$1
    maskim=$2
    tmpnm=$3
    $FSLDIR/bin/fugue --loadfmap=${outfile} --savefmap=${tmpnm}_tmp_fmapfilt -m ${maskim} --despike --despikethreshold=2.1
    $FSLDIR/bin/fslmaths ${maskim} -kernel 2D -ero ${tmpnm}_tmp_eromask 
    $FSLDIR/bin/fslmaths ${maskim} -sub ${tmpnm}_tmp_eromask -thr 0.5 -bin ${tmpnm}_tmp_edgemask 
    $FSLDIR/bin/fslmaths ${tmpnm}_tmp_fmapfilt -mas ${tmpnm}_tmp_edgemask ${tmpnm}_tmp_fmapfiltedge
    $FSLDIR/bin/fslmaths ${outfile} -mas ${tmpnm}_tmp_eromask -add ${tmpnm}_tmp_fmapfiltedge ${outfile}
}

demean_image() {
  # demeans image
  # args are: <image> <mask> <tmpnm>
  outim=$1
  maskim=$2
  tmpnm=$3
  $FSLDIR/bin/fslmaths ${outim} -mas ${maskim} ${tmpnm}_tmp_fmapmasked
  $FSLDIR/bin/fslmaths ${outim} -sub `$FSLDIR/bin/fslstats ${tmpnm}_tmp_fmapmasked -k ${maskim} -P 50` -mas ${maskim} ${outim} -odt float
}

###############################################################################

varian_process() { # Process varian fieldmap
  phaseroot=$1
  absroot=$2
  outfile=`$FSLDIR/bin/remove_ext $3`
  deltaTE=$4
  sanitycheck=$5
  tmpnm=$6

  nt=`$FSLDIR/bin/fslval ${phaseroot} dim4`;
  if [ $nt -ne 2 ] ; then
      echo "Phase image must contain two separate volumes!"
      echo "Use the 4D image containing two volumes of wrapped phase"
      exit 2
  fi

  # check range of phase data (should be close to 2*pi = 6.28)
  if [ $sanitycheck = yes ] ; then
      rr=`$FSLDIR/bin/fslstats ${phaseroot} -R`;
      rmin=`echo $rr | awk '{ print $1 }'`;
      rmax=`echo $rr | awk '{ print $2 }'`;
      range=`echo $rmax - $rmin | bc -l`;
      nrange=`echo $range / 6.28 | bc -l`;
      range_ok=yes;
      if [ `echo "$nrange < 0.9" | bc -l` -eq 1 ] ; then
	  range_ok=no;
      fi
      if [ `echo "$nrange > 1.1" | bc -l` -eq 1 ] ; then
	  range_ok=no;
      fi
      if [ $range_ok = no ] ; then
	  echo "Phase image values do not have expected range"
	  echo "Expecting range of 2*pi (6.28) but found $rmin to $rmax (range of $range)"
	  echo "Please re-scale or find correct image"
	  exit 2
      fi
      
      bet_check ${absroot}
  fi
  
  # make brain mask
  maskim=${tmpnm}_tmp_mask
  $FSLDIR/bin/fslmaths $absroot -thr 0.00000001 -bin $maskim

  # unwrap phase
  uphaseroot=${tmpnm}_tmp_uph
  $FSLDIR/bin/prelude -a $absroot -p $phaseroot -m $maskim -o $uphaseroot -v

  # create fieldmap
  asym=`echo $deltaTE / 1000 | bc -l`
  $FSLDIR/bin/fugue -p $uphaseroot --asym=$asym --mask=$maskim --savefmap=$outfile

  # Demean to avoid gross shifting
  demean_image ${outfile} ${maskim} ${tmpnm}

  # Clean up edge voxels
  clean_up_edge ${outfile} ${maskim} ${tmpnm}
} # varian_process

###############################################################################

siemens_process() { # Process siemens fieldmap
  phaseroot=$1
  absroot=$2
  outfile=`$FSLDIR/bin/remove_ext $3`
  deltaTE=$4
  sanitycheck=$5
  tmpnm=$6

  newphaseroot=${phaseroot}

  # check range of phase data (should be close to 4096)
  if [ $sanitycheck = yes ] ; then
      rr=`$FSLDIR/bin/fslstats ${phaseroot} -R;`
      rmin=`echo $rr | awk '{ print $1 }'`;
      rmax=`echo $rr | awk '{ print $2 }'`;
      range=`echo $rmax - $rmin | bc -l`;SIEMENS
      nrange=`echo $range / 4096 | bc -l`;
      if [ `echo "$nrange < 2.1" | bc -l` -eq 1 ] ; then
	  if [ `echo "$nrange > 1.9" | bc -l` -eq 1 ] ; then
	      # MRIcron range is typically twice that of dicom2nifti
	      newphaseroot=${tmpnm}_tmp_phase
	      $FSLDIR/bin/fslmaths ${phaseroot} -div 2 ${newphaseroot}
	  fi
      fi
      if [ `echo "$nrange < 0.9" | bc -l` -eq 1 ] ; then
	  echo "Phase image values do not have expected range"
	  echo "Expecting at least 90% of 0 to 4096, but found $rmin to $rmax"
	  echo "Please re-scale or find correct image, or force executation of this script with --nocheck"
	  exit 2
      fi
  
      # check that absolute image has been brain extracted
      bet_check ${absroot}
  fi
  
  # make brain mask
  maskim=${tmpnm}_tmp_mask
  $FSLDIR/bin/fslmaths $absroot -thr 0.00000001 -bin $maskim
  
  # Convert phasemap to radians
  $FSLDIR/bin/fslmaths ${newphaseroot} -div 2048 -sub 1 -mul 3.14159 -mas ${maskim} ${tmpnm}_tmp_ph_radians -odt float
  
  # Unwrap phasemap
  $FSLDIR/bin/prelude -p ${tmpnm}_tmp_ph_radians -a ${absroot} -m ${maskim} -o ${tmpnm}_tmp_ph_radians_unwrapped -v
  
  # Convert to rads/sec (dTE is echo time difference)
  asym=`echo $dTE / 1000 | bc -l`
  $FSLDIR/bin/fslmaths ${tmpnm}_tmp_ph_radians_unwrapped -div $asym ${tmpnm}_tmp_ph_rps -odt float
  
  # Call FUGUE to extrapolate from mask (fill holes, etc)
  $FSLDIR/bin/fugue --loadfmap=${tmpnm}_tmp_ph_rps --mask=${maskim} --savefmap=$outfile
  
  # Demean to avoid gross shifting
  demean_image ${outfile} ${maskim} ${tmpnm}
  
  # Clean up edge voxels
  clean_up_edge ${outfile} ${maskim} ${tmpnm}
} # siemens_process

ge_process () { # Process GE fieldmap
phaseroot=$1
  absroot=$2
  outfile=`$FSLDIR/bin/remove_ext $3`
  dTE=$4
  tmpnm=$5

  newphaseroot=${phaseroot}

 rr=`$FSLDIR/bin/fslstats ${phaseroot} -R;`
 rmin=`echo $rr | awk '{ print $1 }'`;
 rmax=`echo $rr | awk '{ print $2 }'`;
 range=`echo $rmax - $rmin | bc -l`

rmin_add=`echo ${rmin%.*} |grep -o '[0-9]*'`
r_tot=$((${rmin_add%.*} + ${rmax%.*}))

if [ $r_tot -ne ${range%.*} ]; then
echo "${red} r_tot (${r_tot}) does not equal range (${range%.*})${whi}"
exit 1
fi

bet_check ${absroot}
  
  # make brain mask
  maskim=${tmpnm}_tmp_mask
  $FSLDIR/bin/fslmaths $absroot -thr 0.00000001 -bin $maskim
  
  # Convert phasemap to radians
  $FSLDIR/bin/fslmaths ${newphaseroot} -add ${rmin_add} -div ${r_tot} -sub 0.5 -mul 6.28319 -mas ${maskim} ${tmpnm}_tmp_ph_radians -odt float
  
  # Unwrap phasemap
  $FSLDIR/bin/prelude -p ${tmpnm}_tmp_ph_radians -a ${absroot} -m ${maskim} -o ${tmpnm}_tmp_ph_radians_unwrapped -v
  
  # Convert to rads/sec (dTE is echo time difference)
  asym=`echo $dTE / 1000 | bc -l`
  $FSLDIR/bin/fslmaths ${tmpnm}_tmp_ph_radians_unwrapped -div $asym ${tmpnm}_tmp_ph_rps -odt float
  
  # Call FUGUE to extrapolate from mask (fill holes, etc)
  $FSLDIR/bin/fugue --loadfmap=${tmpnm}_tmp_ph_rps --mask=${maskim} --savefmap=$outfile
  
  # Demean to avoid gross shifting
  demean_image ${outfile} ${maskim} ${tmpnm}
  
  # Clean up edge voxels
  clean_up_edge ${outfile} ${maskim} ${tmpnm}
} # ge_process

#-------------------------------- MESSAGES ---------------------------------#
exit_message () { # Message before exiting script
	if [ -z "${1}" 2>/dev/null ] || ! [ "${1}" -eq "${1}" 2>/dev/null ]; then
		exit_type='0'
	else
		exit_type="${1}"
	fi
	
	if [ "${exit_type}" -ne '0' ]; then
		suggest_help='yes'
	fi
	
	for exit_inputs; do
		if [ "${exit_inputs}" == '-nh' 2>/dev/null ]; then
			suggest_help='no'
		fi
	done

	# Suggest help message
	if [ "${suggest_help}" == 'yes' 2>/dev/null ]; then
		echo "${ora}TO DISPLAY HELP MESSAGE TYPE: ${gre}${script_path} -h${whi}"
	fi
	
	printf "${formatreset}\n"
	IFS="${IFS_original}" # Reset IFS
	exit "${exit_type}"
} # exit_message

re_enter_input_message () { # Displays invalid input message
	clear
	echo "${red}INVALID INPUT: ${ora}"
	printf '%s\n' ${@}
	echo "${pur}PLEASE RE-ENTER INPUT${whi}"
} # re_enter_input_message

#---------------------------------- CODE -----------------------------------#
script_path=$(mac_readlink "${script_path}") # similar to 'readlink -f' in linux

for inputs; do # Reads through all inputs
	option_eval "${inputs}"
done

if ! [ "${clear_screen}" == 'no' 2>/dev/null ]; then
	clear     # Clears screen unless activation of input option: '-cs'
fi

color_formats # Activates or inhibits colorful output

# Display help message or open file
if [ "${activate_help}" == 'yes' 2>/dev/null ]; then # '-h' or '--help'
	script_usage
elif [ "${open_script}" == 'yes' 2>/dev/null ]; then # '-o' or '--open'
	open_text_editor "${script_path}" ${text_editors[@]}
	exit_message 0
fi

# Exit script if invalid inputs found
if [ "${#bad_inputs[@]}" -gt '0' ]; then
	re_enter_input_message ${bad_inputs[@]}
	exit_message 1
fi

scanner="${1}"
phase_image="${2}"
mag_image="${3}"
out_image="${4}"
delta_te="${5}"
extra_option="${6}"

if [ $# -lt 5 ] ; then
  usage
  exit 1
fi

check_name_space $(basename "${phase_image}") $(basename "${mag_image}") $(basename "${out_image}")

check_phase_space=($(echo "${phase_image}" |grep ' '))
check_mag_space=($(echo "${mag_image}" |grep ' '))
check_out_space=($(echo "${out_image}" |grep ' '))

wd="$(pwd)" # Change directories if path(s) contain spaces
if [ "${#check_phase_space[@]}" -gt '0' ] || [ "${#check_mag_space[@]}" -gt '0' ] || \
   [ "${#check_out_space[@]}" -gt '0' ]; then
	if [ "${phase_image}" == "${mag_image}" 2>/dev/null ] && [ "${mag_image}" == "${out_image}" 2>/dev/null ]; then
		common_dir=$(dirname "${phase_image}") # If all files are the same
	else
		check_phase_dir=($(echo "${phase_image}" |sed "s@/@\\${IFS}@g"))
		check_mag_dir=($(echo "${mag_image}" |sed "s@/@\\${IFS}@g"))
		check_out_dir=($(echo "${out_image}" |sed "s@/@\\${IFS}@g"))
		common_dir='/' # Directory that is common to both files
		for i in ${!check_phase_dir[@]}; do
			phase_single_dir="${check_phase_dir[${i}]}"
			mag_single_dir="${check_mag_dir[${i}]}"
			out_single_dir="${check_out_dir[${i}]}"
			if [ "${phase_single_dir}" == "${mag_single_dir}" 2>/dev/null ] && [ "${mag_single_dir}" == "${out_single_dir}" 2>/dev/null ]; then
				common_dir="${common_dir}${phase_single_dir}/"
			else # Paths no longer in common
				break
			fi
		done
	fi # if [ "${phase_image}" == "${mag_image}" 2>/dev/null ] && [ "${mag_image}" == "${out_image}" 2>/dev/null ]
	
	# If space(s) in paths are in a common folder then space erros can be avoided
	phase_image=$(echo "${phase_image}" |sed "s@^${common_dir}@@g")
	mag_image=$(echo "${mag_image}" |sed "s@^${common_dir}@@g")
	out_image=$(echo "${out_image}" |sed "s@^${common_dir}@@g")
	check_name_space "${phase_image}" "${mag_image}" "${out_image}" # Exit if space occurs beyond common path
	cd "${common_dir}" # Go to common directory to avoid spaces
fi # if [ "${#check_phase_space[@]}" -gt '0' ] || [ "${#check_mag_space[@]}" -gt '0' ] || [ "${#check_out_space[@]}" -gt '0' ]

if [ `$FSLDIR/bin/imtest ${phase_image}` -ne 1 ]; then
 echo "${phase_image} not found/not an image file"
 exit 1
fi

if [ `$FSLDIR/bin/imtest ${mag_image}` -ne 1 ]; then
 echo "${mag_image} not found/not an image file"
 exit 1
fi

phaseroot=`$FSLDIR/bin/remove_ext ${phase_image}`
absroot=`$FSLDIR/bin/remove_ext ${mag_image}`
outfile=${phaseroot}_field_rps
if [ $# -ge 4 ]; then
  outfile=`$FSLDIR/bin/remove_ext ${out_image}`
fi

dTE=2.46
if [ $# -ge 5 ]; then
  dTE="${delta_te}"
fi

sanitycheck=yes
if [ $# -ge 6 ] ; then
  if [ X${extra_option} = X--nocheck ] ; then
      sanitycheck=no
  fi
fi  

if [ $sanitycheck = yes ] ; then
    badval=false;
    if [ `echo "$dTE < 0.1" | bc -l` -eq 1 ] ; then badval=true; fi
    if [ `echo "$dTE > 10.0" | bc -l` -eq 1 ] ; then badval=true; fi
    if [ $badval = true ] ; then
	echo "Unlikely difference in TE found: dTE = $dTE milliseconds"
	echo "Expecting values between 0.1 and 10.0 milliseconds"
	echo "To force the script to use this value use the --nocheck argument"
	exit 2
    fi
fi

tmpnm=`$FSLDIR/bin/tmpnam`

if [ "${scanner}" != SIEMENS -a "${scanner}" != OCMR -a "${scanner}" != VARIAN -a "${scanner}" != GE ] ; then
    usage
    echo " "
    echo "${red}First argument must be ${gre}SIEMENS${whi}, ${gre}GE${whi} or ${gre}VARIAN${whi}"
    exit 1
fi

# check that phase and magnitude images are the same size
nz=`$FSLDIR/bin/fslval ${absroot} dim3`;
ny=`$FSLDIR/bin/fslval ${absroot} dim2`;
nx=`$FSLDIR/bin/fslval ${absroot} dim1`;
dz=`$FSLDIR/bin/fslval ${absroot} pixdim3`;
dy=`$FSLDIR/bin/fslval ${absroot} pixdim2`;
dx=`$FSLDIR/bin/fslval ${absroot} pixdim1`;
pnz=`$FSLDIR/bin/fslval ${phaseroot} dim3`;
pny=`$FSLDIR/bin/fslval ${phaseroot} dim2`;
pnx=`$FSLDIR/bin/fslval ${phaseroot} dim1`;
pdz=`$FSLDIR/bin/fslval ${phaseroot} pixdim3`;
pdy=`$FSLDIR/bin/fslval ${phaseroot} pixdim2`;
pdx=`$FSLDIR/bin/fslval ${phaseroot} pixdim1`;
samesize=true;
if [ $nz -ne $pnz ] ; then samesize=false; fi
if [ $ny -ne $pny ] ; then samesize=false; fi
if [ $nx -ne $pnx ] ; then samesize=false; fi
if [ `echo $dz != $pdz | bc -l` -eq 1 ] ; then samesize=false; fi
if [ `echo $dy != $pdy | bc -l` -eq 1 ] ; then samesize=false; fi
if [ `echo $dx != $pdx | bc -l` -eq 1 ] ; then samesize=false; fi
if [ $samesize = false ] ; then
    echo "Phase and Magnitude images must have the same number of voxels and voxel dimensions";
    echo "Current dimensions are:"
    echo "  Phase image:     $pnx x $pny x $pnz with dims of $pdx x $pdy x $pdz mm";
    echo "  Magnitude image: $nx x $ny x $nz with dims of $dx x $dy x $dz mm";
    echo "Fix this (probably in reconstruction stage) before re-running this script"
    if [ "${scanner}" = OCMR ] ; then 
	echo "Possibly try the script: fix_OCMR_fieldmaps"; 
    fi
    exit 2
fi

if [ "${scanner}" = VARIAN ] ; then
  varian_process $phaseroot $absroot $outfile $dTE $sanitycheck $tmpnm
elif [ "${scanner}" = SIEMENS ] ; then
  siemens_process $phaseroot $absroot $outfile $dTE $sanitycheck $tmpnm
elif [ "${scanner}" = GE ] ; then
  ge_process $phaseroot $absroot $outfile $dTE $tmpnm
else
echo "${red}PLEASE INPUT: ${ora}GE${red}, ${ora}SIEMENS${red} or ${ora}VARIAN${red} as first option after script name${whi}"
fi 2>/dev/null

rm -rf ${tmpnm}_tmp_*
echo "Done. Created ${outfile} for use with FEAT."

exit_message 0
