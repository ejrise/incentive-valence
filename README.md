# incentive-valence

## Overview

This repository contains scripts for [Incentive valence differentially engages open- and closed-loop basal ganglia circuits during movement initiation](https://www.biorxiv.org/content/10.64898/2025.12.21.695842v1)

The scripts include preprocessing and analysis code for both Experiment 1 (7T multi-echo MRI resting-state functional connectivity data) and Experiment 2 (3T fMRI data and coinciding task behavior). 

---

## Repository Structure
```
incentive-valence/
├── 7T_conn_mri_preproc/ # Preprocessing scripts for raw multi-echo 7T data (Experiment 1)
├── 3T_task_mri_preproc/ # Preprocessing scipts for raw 3T data (Experiment 2) 
├── masks/               # ROI masks used for both experiments 
├── analysis/            # Scripts for analysis of clean data 
└── figures/             # Scripts to reproduce manuscript figures
```

---

## Requirements

- Python 3.11.5
  - Key packages: PyMC 5.10, ArviZ, Numpy 
- GNU bash, version 5.2.21(1)-release (x86_64-conda-linux-gnu)
- Neuroimaging Tools: FSL 6.0.7.12, TE Dependent ANAlysis (Tedana) 24.0.1, Advanced Normalization Tools (ANTs) 2.3.4, PhysIO toolbox 6.0.1, CONN Toolbox (Matlab) 

Or if using a requirements file:
```
pip install -r requirements.txt
```
---

## Data Repositories 

- [Experiment 1 Raw data](https://openneuro.org/datasets/ds005264)
- [Experiment 2 Raw data](https://openneuro.org/datasets/ds005263)
- [Clean data](https://doi.org/10.5281/zenodo.19210141)


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
