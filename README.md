# incentive-valence

## Overview

Code and cleaned data for Dundon & Rizor et al., Incentive valence differentially engages open- and closed-loop basal ganglia circuits during movement initiation (2025, *PNAS*). Experiment 1: 7T resting-state connectivity of ventral and dorsal putamen. Experiment 2: 3T task fMRI during an incentivized precision reaching task

---

## Repository Structure
```
incentive-valence/
├── data/
│   ├── raw/
│   │   └── behavioral/
│   │       └── fmri_task/
│   └── preprocessed/
│       ├── behavioral/
│       └── fMRI/
└── scripts/
    ├── paradigm/
    ├── preprocessing/
    │   ├── behavioral/
    │   └── fMRI/
    │       ├── 7T/
    │       │   └── templates/
    │       └── Task/
    │           └── templates/
    └── analysis/
        ├── descriptives/
        └── fMRI/
            ├── connectome_plots/
            ├── make_GLM_timing_files/
            └── bayes_studentT_of_L2s/
```
---


## Details

```
repo/data/raw/behavioral/fmri_task/
    {subject_id}_Session{run}_{date_time}/
```

Raw output from the incentivized reaching task. One directory per subject per run (3 runs per subject). Naming: `{subject_id}_Session{1,2,3}_{timestamp}`. Also contains `sequence1.csv` (trial sequence shared across all subjects/runs; columns: cue type, pre-instruction wait duration, pre-go hold duration).

```
repo/scripts/preprocessing/fMRI/Task
```
Scripts to process BIDS-formatted raw 3T Task MRI images [found here](https://openneuro.org/datasets/ds005264). Requires FSL and ANTs. Please see `README_3T.txt` for details about correct fieldmap assignment. 
- `t1_extract.py`: Extracts brain for anatomical and fmap magnitude images.
- `get_fmaps.py`: Generates fieldmaps from magnitude and phase images, asks to confirm correct fieldmap assignment to participant run.
- `make_designs.py`: Creates FSL FEAT design files (1 per subject-run) for motion and distortion correction, requires `templates/design_template.fsf`. Run these with FSL FEAT before proceeding. 
- `make_move_func_templates.py`: After FEAT preprocessing, makes scripts (1 per subject-run) to use ANTs to spatially normalize images to MNI152 2mm template. Run these scripts (can be modified to submit via slurm on distributed computing cluster) to output final BOLD images ready for model estimation. 

```
repo/scripts/preprocessing/fMRI/7T
```
Scripts to process BIDS-formatted raw 7T multi-echo resting state MRI images [found here](https://openneuro.org/datasets/ds005263). Requires FSL, ANTs, Tedana, and CONN Toolbox (MATLAB). Please see `README_7T.txt` for more details. 

- `preprocess_multi_echo_part1[_nofmap].sh`: Use "nofmap" version if subject does not have fmap magnitude and phase images. Brain extracts T1 images, registers T1 to MNI152 template, and gets fsl motion outliers for motion correction. 
- `get_slicetime_files.py`: Obtains subject-run slicetime files for FSL slicetime correction preprocessing 
- `preprocess_multi_echo_part2[_nofmap].sh`: Use "nofmap" version if subject does not have fmap magnitude and phase images. For all 3 echoes, applies motion/distortion correction, slice time correction, and spatial normalization to T1 image. Make sure to check that brain extraction of SBRef image is good. 
- `tedana_script.py`: Runs Tedana ICA denoising of multi-echo images and outputs a final denoised file. 
- `create_physio_jobs.m` + `run_physio_jobs.m`: Creates templates for the PhysIO toolbox (MATLAB) to generate regressors based on respiration and pulse data. 
- `denoised_funcs_to_mni.sh`: Normalizes denoised BOLD images to MNI space. After this, the MNI normalized denoised BOLD images, MNI normalized T1 images, motion outier info, and physio regressors are ready to be imported into CONN_Toolbox for functional connectivity estimation (see SI methods for this process).


```
repo/scripts/preprocessing/behavioral/makeDF_wFSs.py
```

Reads raw task pickles and `sequence1.csv`. Extracts trial-level kinematics (RT, peak velocity, peak acceleration, time-to-peak measures, quarter-acceleration onset times, initial cursor position, false starts, post-error/post-false-start flags) and timing variables (cue onset, reach onset, deceleration onset/duration). Outputs to `repo/data/preprocessed/behavioral/IVdata_wFSs.csv`.

```
repo/scripts/analysis/descriptives/
    make_SI_success_variance_figure.py
    kinematic_ANOVAs_full_factorial.py
    makeSI_VelTraces.py
    effect_counts.py
    get_cell_means.py
```

All read from `repo/data/preprocessed/behavioral/IVdata_wFSs.csv` (except `makeSI_VelTraces.py`, which reads raw pickles). All output in place.

- `make_SI_success_variance_figure.py`: Success/reward variance, cue-effect correlations, temporal drift, init-outcome coupling. Outputs Fig. S12 (`FigureS1.pdf/png` and split versions).
- `kinematic_ANOVAs_full_factorial.py`: Full factorial RM ANOVA (incentive x run x hold) with Greenhouse-Geisser correction. Outputs SI Table 3 (`anova_full_factorial.tex`), posthoc comparisons (`posthoc_full_factorial.txt`), Fig. S13 (`main_effects.pdf/png`), and Fig. S14 (`interaction_drilldown.pdf/png`).
- `makeSI_VelTraces.py`: Velocity traces by condition (go-cue and onset-aligned, raw and time-normalized). Outputs Fig. S15 (`SI_velocity_traces.pdf/png`).
- `effect_counts.py`: Counts subjects showing faster init under jackpot/robber vs standard. Console output only (feeds N=62 imaging exclusion criterion).
- `get_cell_means.py`: Computes condition-level cell means (e.g., Jackpot RT vs Standard RT) for ANOVA reporting.

```
repo/scripts/paradigm/
    IV_task.py
    IV_functions.py
    IV_practice.py
    IV_compute_bonus.py
    IV_compute_median_rt.py
    IV_find_pupil.py
    IV_shut_down_eyelink.py
    EyeLinkCoreGraphicsPsychoPy.py
    compute_RT.py
    Data/
    eyeData/
    images/
```

PsychoPy experiment code. `IV_task.py` is the main entry point; other `IV_*.py` files are supporting functions. Raw behavioral data output to `Data/`; eye-tracking data to `eyeData/`; task stimuli and trial sequence in `images/`.

```
repo/scripts/analysis/fMRI/make_GLM_timing_files/
    make_fmri_events_reverse_mumford.py
```

Generates 3-column FSL timing files for the first-level GLM from preprocessed behavioral data. Reads from `repo/data/preprocessed/behavioral/IVdata_wFSs.csv`. Outputs one subdirectory per subject (in place), each containing per-run timing files for instruction cue sticks, RT-scaled go-phase regressors, go cue sticks, reach execution, and hold period.

```
repo/scripts/analysis/fMRI/connectome_plots/
    makeOcto_from_matlab.py
```

Generates circular connectome plots from CONN toolbox output (.mat files). Configure `model` and `seed` at top of script to produce each plot. FDR correction over upper triangle (CONN method). Reads from `repo/data/preprocessed/fMRI/`. Outputs Figs. S1-S9 in place (one run per seed/model combination).

```
repo/scripts/analysis/fMRI/bayes_studentT_of_L2s/
    fit_revmumford_with_tests_LEFT.py
    get_data_for_figure.py
    make_figure.py
```

Hierarchical Bayesian model (Student's t likelihood, PyMC) fitting group-level activation parameters from L2 ROI data. Reads from `repo/data/preprocessed/fMRI/`. All output in place.

- `fit_revmumford_with_tests_LEFT.py`: Fits the model. Outputs barplots, open-vs-closed loop contrast analysis, ROPE analysis, and COPE comparisons.
- `get_data_for_figure.py`: Re-fits the model and extracts ROI-level and circuit-level posteriors (OLC, CLC, Stopping, Incentive, PreMotor, M1ul, M1noul) plus between-circuit and between-context contrasts. Outputs `posteriors_{dataset}.pkl`.
- `make_figure.py`: Loads the pickle from above. Outputs main text Fig. 3 panels (`figure_main_{dataset}.pdf/png`), ROI-level supplement (`figure_supplement_roi_{dataset}.pdf/png`), and an alternative layout (`figure_alternative_{dataset}.pdf/png`).

---
## Requirements

- Python 3.11
  - Key packages: PyMC 5.10, ArviZ , NumPy 
- GNU bash, version 5.2.21(1)-release (x86_64-conda-linux-gnu)
- Neuroimaging Tools: FSL 6.0.7.12, TE Dependent ANAlysis (Tedana) 24.0.1, Advanced Normalization Tools (ANTs) 2.3.4, PhysIO toolbox 6.0.1, CONN Toolbox (Matlab) 

Or if using a requirements file:
```
pip install -r requirements.txt
```
---

## Raw Data Repositories 

- [Experiment 1 Raw data](https://openneuro.org/datasets/ds005264)
- [Experiment 2 Raw data](https://openneuro.org/datasets/ds005263)

---

## Citation

If you use this code, please cite:

Dundon, N. M., Rizor, E.J., Stasiak, J., Wang, J., Li, T., Sabugo, K., Villaneuva, C., Barandon, P., Babenko, V.,  Beverly-Aylwin, R., Stump, A., Santander, T., Bostan, A. C., Lapate, R. C., & Grafton, S. T. (2025). Incentive valence differentially engages open- and closed-loop basal ganglia circuits during movement initiation. *bioRxiv*. https://doi.org/10.64898/2025.12.21.695842
```bibtex
@article{,
  author  = {Dundon, N. M., Rizor, E.J., Stasiak, J., Wang, J., Li, T., Sabugo, K., Villaneuva, C., Barandon, P., Babenko, V.,  Beverly-Aylwin, R., Stump, A., Santander, T., Bostan, A. C., Lapate, R. C., & Grafton, S. T.},
  title   = {Incentive valence differentially engages open- and closed-loop basal ganglia circuits during movement initiation},
  journal = {bioRxiv},
  year    = {2025},
  doi     = {https://doi.org/10.64898/2025.12.21.695842}
}
```
---

## License

This repository is licensed under the [MIT License](LICENSE).
