#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to extract and save posterior distributions for visualization.
Outputs both ROI-level and circuit-level posteriors for COPEs 3, 4, 5.
Now includes hemisphere-specific circuit analyses and additional motor subdivisions.
"""

import pandas as pd
import pymc3 as pm
import numpy as np
import pickle

# ------------------ USER SPECIFIED ------------------
dataset = 'controls_complex'   # dataset name
func_rel = 0                   # set to 1 to keep only left hemisphere
# ----------------------------------------------------

# Load and filter data
import os
from pathlib import Path
try:
    _SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    _SCRIPT_DIR = Path.cwd()
data_path = _SCRIPT_DIR / ".." / ".." / ".." / "data" / "preprocessed" / "fMRI" / f"revmumford_anova_{dataset}.csv"
df = pd.read_csv(data_path)
df = df[df.Model == 0].reset_index(drop=True)
df = df.loc[df.jackpot_effect > 0]

# Optionally keep only left hemisphere
if func_rel == 1:
    df = df[~df['Region'].str.startswith('r')].reset_index(drop=True)

# Define region ordering
region_order = [
    'lBFmb', 'lBFsep', 'lamBL', 'lamCEN', 'lvPut', 'lGPi', 'lSTH', 'ldPut',
    'lvlThal', 'lM1noul', 'lM1ul', 'lPMd', 'lPMv', 'lSMA', 'lCMA', 'lNA',
    'rBFmb', 'rBFsep', 'ramBL', 'ramCEN', 'rvPut', 'rGPi', 'rSTH', 'rdPut',
    'rvlThal', 'rM1noul', 'rM1ul', 'rPMd', 'rPMv', 'rSMA', 'rCMA', 'rNA'
]
to_prefix = {'ramBL', 'ramCEN', 'lamBL', 'lamCEN'}
if 'complex' in dataset:
    region_order = [f"{r}c" if r in to_prefix else r for r in region_order]

# Make Region categorical and sort
df['Region'] = pd.Categorical(df['Region'], categories=region_order, ordered=True)
df = df.sort_values(['Cope', 'Region']).reset_index(drop=True)

# Count observations per (Cope, Region)
n_param = df.groupby(['Cope', 'Region']).size().reset_index(name='count')
N = len(n_param)

# Build index vector
idx = np.repeat(np.arange(N), n_param['count'].values)
y = df['Activation'].values

# ------------------ Bayesian model fitting ------------------
print("Fitting Bayesian model...")
with pm.Model() as model:
    mu = pm.Normal('mu', 0, 1, shape=N)
    sd = pm.HalfNormal('sd', 1, shape=N)
    nu = pm.HalfNormal('nu', 1)
    pm.StudentT('obs', mu=mu[idx], sigma=sd[idx], nu=nu, observed=y)
    trace = pm.sample(5000, tune=5000, cores=4, return_inferencedata=False)

tracedf = pm.trace_to_dataframe(trace)

# ------------------ Define circuit membership ------------------
# Define which ROIs belong to which circuit - separated by hemisphere
# Left hemisphere circuits
left_olc_regions = {'lamBL', 'lamCEN', 'lvPut', 'lBFmb', 'lBFsep'}
left_clc_regions = {'ldPut', 'lGPi', 'lvlThal'}  # Remove STH from CLC
left_stopping_regions = {'lSTH'}  # STH as separate stopping circuit
left_incentive_regions = {'lNA'}  # Incentive/value circuit
left_premotor_regions = {'lCMA', 'lSMA', 'lPMd', 'lPMv'}  # Pre-motor planning
left_m1ul_regions = {'lM1ul'}  # Primary motor (upper limb)
left_m1noul_regions = {'lM1noul'}  # Primary motor (non-upper limb)

# Right hemisphere circuits
right_olc_regions = {'ramBL', 'ramCEN', 'rvPut', 'rBFmb', 'rBFsep'}
right_clc_regions = {'rdPut', 'rGPi', 'rvlThal'}  # Remove STH from CLC
right_stopping_regions = {'rSTH'}  # STH as separate stopping circuit
right_incentive_regions = {'rNA'}
right_premotor_regions = {'rCMA', 'rSMA', 'rPMd', 'rPMv'}
right_m1ul_regions = {'rM1ul'}
right_m1noul_regions = {'rM1noul'}

# Combined circuits (for backward compatibility)
olc_regions = left_olc_regions | right_olc_regions
clc_regions = left_clc_regions | right_clc_regions
stopping_regions = left_stopping_regions | right_stopping_regions
incentive_regions = left_incentive_regions | right_incentive_regions
premotor_regions = left_premotor_regions | right_premotor_regions
m1ul_regions = left_m1ul_regions | right_m1ul_regions
m1noul_regions = left_m1noul_regions | right_m1noul_regions

# Add 'c' suffix for complex datasets if needed
if 'complex' in dataset:
    # Update left hemisphere
    left_olc_regions = {f"{r}c" if r in to_prefix else r for r in left_olc_regions}
    left_clc_regions = {f"{r}c" if r in to_prefix else r for r in left_clc_regions}
    # Update right hemisphere
    right_olc_regions = {f"{r}c" if r in to_prefix else r for r in right_olc_regions}
    right_clc_regions = {f"{r}c" if r in to_prefix else r for r in right_clc_regions}
    # Update combined
    olc_regions = {f"{r}c" if r in to_prefix else r for r in olc_regions}
    clc_regions = {f"{r}c" if r in to_prefix else r for r in clc_regions}

# Context mapping
context_map = {3: 'standard', 4: 'jackpot', 5: 'robber'}

# ------------------ Extract ROI-level posteriors ------------------
print("Extracting ROI-level posteriors...")
roi_posteriors = {}

for cope_id in [3, 4, 5]:  # Only COPEs 3, 4, 5
    context = context_map[cope_id]
    roi_posteriors[context] = {}
    
    cope_data = n_param[n_param['Cope'] == cope_id]
    
    for _, row in cope_data.iterrows():
        region = row['Region']
        param_idx = row.name
        
        # Extract posterior samples for this ROI
        samples = tracedf[f'mu__{param_idx}'].values
        
        # Determine circuit membership and hemisphere
        hemisphere = 'left' if region.startswith('l') else 'right'
        
        # Determine circuit
        if region in olc_regions:
            circuit = 'OLC'
        elif region in clc_regions:
            circuit = 'CLC'
        elif region in stopping_regions:
            circuit = 'Stopping'
        elif region in incentive_regions:
            circuit = 'Incentive'
        elif region in premotor_regions:
            circuit = 'PreMotor'
        elif region in m1ul_regions:
            circuit = 'M1ul'
        elif region in m1noul_regions:
            circuit = 'M1noul'
        else:
            circuit = 'Other'
        
        roi_posteriors[context][region] = {
            'samples': samples,
            'mean': samples.mean(),
            'hdi': pm.hdi(samples, hdi_prob=0.89),
            'circuit': circuit,
            'hemisphere': hemisphere
        }

# ------------------ Helper function for circuit posteriors ------------------
def compute_circuit_posterior(cope_id, context, region_set, circuit_name, n_param, tracedf):
    """Helper function to compute circuit-level posteriors"""
    cope_inds = n_param.index[n_param['Cope'] == cope_id].tolist()
    cope_regions = n_param.loc[cope_inds, 'Region'].values
    
    circuit_inds = [i for i, r in zip(cope_inds, cope_regions) if r in region_set]
    
    if circuit_inds:
        mu_cols = [f'mu__{i}' for i in circuit_inds]
        posterior = tracedf[mu_cols].values
        mean_samples = posterior.mean(axis=1)
        
        return {
            'samples': mean_samples,
            'mean': mean_samples.mean(),
            'hdi': pm.hdi(mean_samples, hdi_prob=0.89),
            'roi_count': len(circuit_inds),
            'rois': [r for r in cope_regions[np.isin(cope_inds, circuit_inds)]]
        }
    return None

# ------------------ Compute circuit-level posteriors ------------------
print("Computing circuit-level posteriors...")
circuit_posteriors = {}
circuit_posteriors_by_hemisphere = {'left': {}, 'right': {}}

for cope_id in [3, 4, 5]:
    context = context_map[cope_id]
    circuit_posteriors[context] = {}
    circuit_posteriors_by_hemisphere['left'][context] = {}
    circuit_posteriors_by_hemisphere['right'][context] = {}
    
    # Bilateral circuits (combined)
    circuits_bilateral = [
        ('OLC', olc_regions),
        ('CLC', clc_regions),
        ('Stopping', stopping_regions),
        ('Incentive', incentive_regions),
        ('PreMotor', premotor_regions),
        ('M1ul', m1ul_regions),
        ('M1noul', m1noul_regions)
    ]
    
    for circuit_name, region_set in circuits_bilateral:
        result = compute_circuit_posterior(cope_id, context, region_set, circuit_name, n_param, tracedf)
        if result:
            circuit_posteriors[context][circuit_name] = result
    
    # Left hemisphere circuits
    circuits_left = [
        ('OLC', left_olc_regions),
        ('CLC', left_clc_regions),
        ('Stopping', left_stopping_regions),
        ('Incentive', left_incentive_regions),
        ('PreMotor', left_premotor_regions),
        ('M1ul', left_m1ul_regions),
        ('M1noul', left_m1noul_regions)
    ]
    
    for circuit_name, region_set in circuits_left:
        result = compute_circuit_posterior(cope_id, context, region_set, circuit_name, n_param, tracedf)
        if result:
            circuit_posteriors_by_hemisphere['left'][context][circuit_name] = result
    
    # Right hemisphere circuits
    circuits_right = [
        ('OLC', right_olc_regions),
        ('CLC', right_clc_regions),
        ('Stopping', right_stopping_regions),
        ('Incentive', right_incentive_regions),
        ('PreMotor', right_premotor_regions),
        ('M1ul', right_m1ul_regions),
        ('M1noul', right_m1noul_regions)
    ]
    
    for circuit_name, region_set in circuits_right:
        result = compute_circuit_posterior(cope_id, context, region_set, circuit_name, n_param, tracedf)
        if result:
            circuit_posteriors_by_hemisphere['right'][context][circuit_name] = result

# ------------------ Compute contrast posteriors ------------------
print("Computing contrast posteriors...")
contrast_posteriors = {}
contrast_posteriors_by_hemisphere = {'left': {}, 'right': {}}

# Helper function for contrasts
def compute_contrast(context1_data, context2_data, label):
    if context1_data and context2_data:
        samples1 = context1_data['samples']
        samples2 = context2_data['samples']
        diff_samples = samples1 - samples2
        return {
            'samples': diff_samples,
            'mean': diff_samples.mean(),
            'hdi': pm.hdi(diff_samples, hdi_prob=0.89)
        }
    return None

# Compute contrasts for each hemisphere
for hemi in ['left', 'right']:
    hemi_circuits = circuit_posteriors_by_hemisphere[hemi]
    hemi_contrasts = contrast_posteriors_by_hemisphere[hemi]
    
    # Between-circuit contrasts (OLC - CLC) for each context
    for context in ['standard', 'jackpot', 'robber']:
        if context in hemi_circuits:
            # OLC vs CLC
            if 'OLC' in hemi_circuits[context] and 'CLC' in hemi_circuits[context]:
                result = compute_contrast(
                    hemi_circuits[context]['OLC'],
                    hemi_circuits[context]['CLC'],
                    f'{context}_OLC-CLC'
                )
                if result:
                    hemi_contrasts[f'{context}_OLC-CLC'] = result
            
            # M1ul vs M1noul
            if 'M1ul' in hemi_circuits[context] and 'M1noul' in hemi_circuits[context]:
                result = compute_contrast(
                    hemi_circuits[context]['M1ul'],
                    hemi_circuits[context]['M1noul'],
                    f'{context}_M1ul-M1noul'
                )
                if result:
                    hemi_contrasts[f'{context}_M1ul-M1noul'] = result
    
    # Within-circuit context changes (jackpot - standard)
    for circuit in ['OLC', 'CLC', 'Stopping', 'Incentive', 'PreMotor', 'M1ul', 'M1noul']:
        if ('standard' in hemi_circuits and 'jackpot' in hemi_circuits and
            circuit in hemi_circuits['standard'] and circuit in hemi_circuits['jackpot']):
            result = compute_contrast(
                hemi_circuits['jackpot'][circuit],
                hemi_circuits['standard'][circuit],
                f'{circuit}_jackpot-standard'
            )
            if result:
                hemi_contrasts[f'{circuit}_jackpot-standard'] = result

# Also compute bilateral contrasts for backward compatibility
for context in ['standard', 'jackpot', 'robber']:
    # OLC vs CLC
    if 'OLC' in circuit_posteriors[context] and 'CLC' in circuit_posteriors[context]:
        result = compute_contrast(
            circuit_posteriors[context]['OLC'],
            circuit_posteriors[context]['CLC'],
            f'{context}_OLC-CLC'
        )
        if result:
            contrast_posteriors[f'{context}_OLC-CLC'] = result
    
    # M1ul vs M1noul
    if 'M1ul' in circuit_posteriors[context] and 'M1noul' in circuit_posteriors[context]:
        result = compute_contrast(
            circuit_posteriors[context]['M1ul'],
            circuit_posteriors[context]['M1noul'],
            f'{context}_M1ul-M1noul'
        )
        if result:
            contrast_posteriors[f'{context}_M1ul-M1noul'] = result

# Within-circuit context changes for bilateral
for circuit in ['OLC', 'CLC', 'Stopping', 'Incentive', 'PreMotor', 'M1ul', 'M1noul']:
    if ('standard' in circuit_posteriors and 'jackpot' in circuit_posteriors and
        circuit in circuit_posteriors['standard'] and circuit in circuit_posteriors['jackpot']):
        result = compute_contrast(
            circuit_posteriors['jackpot'][circuit],
            circuit_posteriors['standard'][circuit],
            f'{circuit}_jackpot-standard'
        )
        if result:
            contrast_posteriors[f'{circuit}_jackpot-standard'] = result

# ------------------ Save all posteriors ------------------
output_data = {
    'roi_posteriors': roi_posteriors,
    'circuit_posteriors': circuit_posteriors,
    'circuit_posteriors_by_hemisphere': circuit_posteriors_by_hemisphere,
    'contrast_posteriors': contrast_posteriors,
    'contrast_posteriors_by_hemisphere': contrast_posteriors_by_hemisphere,
    'metadata': {
        'dataset': dataset,
        'n_samples': len(tracedf),
        'contexts': ['standard', 'jackpot', 'robber'],
        'circuits': ['OLC', 'CLC', 'Stopping', 'Incentive', 'PreMotor', 'M1ul', 'M1noul'],
        'left_olc_regions': list(left_olc_regions),
        'left_clc_regions': list(left_clc_regions),
        'left_stopping_regions': list(left_stopping_regions),
        'left_incentive_regions': list(left_incentive_regions),
        'left_premotor_regions': list(left_premotor_regions),
        'left_m1ul_regions': list(left_m1ul_regions),
        'left_m1noul_regions': list(left_m1noul_regions),
        'right_olc_regions': list(right_olc_regions),
        'right_clc_regions': list(right_clc_regions),
        'right_stopping_regions': list(right_stopping_regions),
        'right_incentive_regions': list(right_incentive_regions),
        'right_premotor_regions': list(right_premotor_regions),
        'right_m1ul_regions': list(right_m1ul_regions),
        'right_m1noul_regions': list(right_m1noul_regions)
    }
}

output_file = f'posteriors_{dataset}.pkl'
with open(output_file, 'wb') as f:
    pickle.dump(output_data, f)

print(f"\nPosteriors saved to {output_file}")

# ------------------ Print summary statistics ------------------
def print_circuit_summary(hemi_name, circuit_data, contrast_data):
    """Helper to print summary for one hemisphere"""
    print("\n" + "="*60)
    print(f"{hemi_name.upper()} HEMISPHERE - CIRCUIT-LEVEL SUMMARY")
    print("="*60)
    
    for context in ['standard', 'jackpot', 'robber']:
        print(f"\n{context.upper()} CONTEXT:")
        if context in circuit_data:
            for circuit in ['OLC', 'CLC', 'Stopping', 'Incentive', 'PreMotor', 'M1ul', 'M1noul']:
                if circuit in circuit_data[context]:
                    data = circuit_data[context][circuit]
                    hdi = data['hdi']
                    sig = (hdi[0] > 0) or (hdi[1] < 0)
                    print(f"  {circuit}: β = {data['mean']:.3f}, HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}]" + 
                          (" *" if sig else ""))
    
    print("\n" + "="*60)
    print(f"{hemi_name.upper()} - BETWEEN-CIRCUIT CONTRASTS")
    print("="*60)
    
    print("\nOLC - CLC:")
    for context in ['standard', 'jackpot', 'robber']:
        key = f'{context}_OLC-CLC'
        if key in contrast_data:
            data = contrast_data[key]
            hdi = data['hdi']
            sig = (hdi[0] > 0) or (hdi[1] < 0)
            print(f"  {context}: Δ = {data['mean']:.3f}, HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}]" + 
                  (" *" if sig else ""))
    
    print("\nM1ul - M1noul:")
    for context in ['standard', 'jackpot', 'robber']:
        key = f'{context}_M1ul-M1noul'
        if key in contrast_data:
            data = contrast_data[key]
            hdi = data['hdi']
            sig = (hdi[0] > 0) or (hdi[1] < 0)
            print(f"  {context}: Δ = {data['mean']:.3f}, HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}]" + 
                  (" *" if sig else ""))
    
    print("\n" + "="*60)
    print(f"{hemi_name.upper()} - WITHIN-CIRCUIT CONTEXT CHANGES (Jackpot - Standard)")
    print("="*60)
    
    for circuit in ['OLC', 'CLC', 'Stopping', 'Incentive', 'PreMotor', 'M1ul', 'M1noul']:
        key = f'{circuit}_jackpot-standard'
        if key in contrast_data:
            data = contrast_data[key]
            hdi = data['hdi']
            sig = (hdi[0] > 0) or (hdi[1] < 0)
            print(f"{circuit}: Δ = {data['mean']:.3f}, HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}]" + 
                  (" *" if sig else ""))

# Print left hemisphere summary
print_circuit_summary('left', 
                     circuit_posteriors_by_hemisphere['left'],
                     contrast_posteriors_by_hemisphere['left'])

# Print right hemisphere summary
print_circuit_summary('right',
                     circuit_posteriors_by_hemisphere['right'],
                     contrast_posteriors_by_hemisphere['right'])

# Print bilateral summary
print("\n" + "="*60)
print("BILATERAL (COMBINED) CIRCUIT-LEVEL SUMMARY")
print("="*60)

for context in ['standard', 'jackpot', 'robber']:
    print(f"\n{context.upper()} CONTEXT:")
    for circuit in ['OLC', 'CLC', 'Stopping', 'Incentive', 'PreMotor', 'M1ul', 'M1noul']:
        if circuit in circuit_posteriors[context]:
            data = circuit_posteriors[context][circuit]
            hdi = data['hdi']
            sig = (hdi[0] > 0) or (hdi[1] < 0)
            print(f"  {circuit}: β = {data['mean']:.3f}, HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}]" + 
                  (" *" if sig else ""))

print("\n" + "="*60)
print("BILATERAL - M1ul vs M1noul CONTRASTS")
print("="*60)

for context in ['standard', 'jackpot', 'robber']:
    key = f'{context}_M1ul-M1noul'
    if key in contrast_posteriors:
        data = contrast_posteriors[key]
        hdi = data['hdi']
        sig = (hdi[0] > 0) or (hdi[1] < 0)
        print(f"{context}: Δ = {data['mean']:.3f}, HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}]" + 
              (" *" if sig else ""))