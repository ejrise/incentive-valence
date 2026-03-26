#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlined script for generating barplots of t-statistics per COPE and region,
fitting a mu and sd for each (Cope, Region), and running open-vs-closed
contrast analysis for the whole dataset.
"""

import pandas as pd
import pymc3 as pm
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ------------------ USER SPECIFIED ------------------
dataset = 'controls_complex'   # dataset name (e.g. 'controls' or 'controls_complex')
func_rel = 0                   # set to 1 to keep only left hemisphere, else 0
# ----------------------------------------------------

# Load and filter data
from pathlib import Path
try:
    _SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    _SCRIPT_DIR = Path.cwd()
CSV_PATH = _SCRIPT_DIR / ".." / ".." / ".." / "data" / "preprocessed" / "fMRI" / f"revmumford_anova_{dataset}.csv"
df = pd.read_csv(CSV_PATH)
df = df[df.Model == 0].reset_index(drop=True)
print(f"Subjects dropped: {df[df.jackpot_effect <= 0]['Subject'].nunique()} of {df['Subject'].nunique()}")

df = df.loc[df.jackpot_effect>0]

# Optionally keep only left hemisphere
if func_rel == 1:
    df = df[~df['Region'].str.startswith('r')].reset_index(drop=True)

# Define region ordering (and prefix 'c' for complex datasets)
region_order = [
    'lBFmb', 'lBFsep', 'lamBL', 'lamCEN', 'lvPut', 'lGPi', 'lSTH', 'ldPut',
    'lvlThal', 'lM1noul', 'lM1ul', 'lPMd', 'lPMv', 'lSMA', 'lCMA', 'lNA',
    'rBFmb', 'rBFsep', 'ramBL', 'ramCEN', 'rvPut', 'rGPi', 'rSTH', 'rdPut',
    'rvlThal', 'rM1noul', 'rM1ul', 'rPMd', 'rPMv', 'rSMA', 'rCMA', 'rNA'
]
to_prefix = {'ramBL', 'ramCEN', 'lamBL', 'lamCEN'}
if 'complex' in dataset:
    region_order = [f"{r}c" if r in to_prefix else r for r in region_order]

# Make Region categorical in the desired order, then sort
df['Region'] = pd.Categorical(df['Region'], categories=region_order, ordered=True)
df = df.sort_values(['Cope', 'Region']).reset_index(drop=True)

# Count observations per (Cope, Region)
n_param = (
    df
    .groupby(['Cope', 'Region'])
    .size()
    .reset_index(name='count')
)
N = len(n_param)

# Build index vector mapping each row in df to one of the N parameters
idx = np.repeat(np.arange(N), n_param['count'].values)
y   = df['Activation'].values

# ------------------ Bayesian model fitting ------------------
with pm.Model() as model:
    mu  = pm.Normal('mu', 0, 1, shape=N)
    sd  = pm.HalfNormal('sd', 1, shape=N)
    nu  = pm.HalfNormal('nu', 1)
    pm.StudentT('obs', mu=mu[idx], sigma=sd[idx], nu=nu, observed=y)
    trace = pm.sample(5000, tune=5000, cores=4, return_inferencedata=False)

tracedf = pm.trace_to_dataframe(trace)

# helper for 89% HDI excluding zero
def sig_0(samples):
    hdi = pm.hdi(samples, hdi_prob=0.89)
    return (hdi[0] > 0) or (hdi[1] < 0)

# ROPE analysis helper - for t-statistics, a reasonable ROPE might be [-0.1, 0.1]
def rope_analysis(samples, rope_lower=-0.1, rope_upper=0.1):
    """
    Perform ROPE analysis on samples.
    Returns: (hdi_lower, hdi_upper, rope_decision)
    rope_decision: 'reject' (effect exists), 'accept' (negligible effect), 'undecided'
    """
    hdi = pm.hdi(samples, hdi_prob=0.89)
    hdi_lower, hdi_upper = hdi[0], hdi[1]
    
    # Check overlap with ROPE
    if hdi_upper < rope_lower or hdi_lower > rope_upper:
        # HDI completely outside ROPE - reject null (effect exists)
        decision = 'reject'
    elif hdi_lower >= rope_lower and hdi_upper <= rope_upper:
        # HDI completely inside ROPE - accept null (negligible effect)
        decision = 'accept'
    else:
        # HDI partially overlaps ROPE - undecided
        decision = 'undecided'
    
    return hdi_lower, hdi_upper, decision

# COPE descriptive labels
cope_text = [
    'jackpot>standard, inst.cue, stick func.',
    'robber>standard, inst.cue, stick func.',
    'standard>baseline, go cue, RT-scaled',
    'jackpot>baseline, go cue, RT-scaled',
    'robber>baseline, go cue, RT-scaled',
    'all_trialtypes>baseline, go cue, stick func.'
]

# Compute median effects & significance flags for each parameter
medians = np.array([tracedf[f'mu__{i}'].median() for i in range(N)])
sigs    = np.array([sig_0(tracedf[f'mu__{i}'].values) for i in range(N)])

# Append to parameter table
param_df = n_param.copy()
param_df['median'] = medians
param_df['sig']    = sigs

# ------------------ barplots by COPE ------------------
num_cope  = param_df['Cope'].nunique()
n_regions = len(region_order)

# y-axis ticks
gmin, gmax = param_df['median'].min(), param_df['median'].max()
y_ticks    = sorted(set(np.round([
    np.floor(gmin / 0.05) * 0.05,
    0,
    np.ceil(gmax / 0.05) * 0.05
], 2)))

# color palette (one color per COPE)
colors = list(mcolors.TABLEAU_COLORS.values())
if num_cope > len(colors):
    extra = plt.get_cmap('Set2').colors
    colors.extend(extra[: num_cope - len(colors)])

fig, axs = plt.subplots(
    num_cope, 1,
    figsize=(35, num_cope * 4.5),
    dpi=300,
    squeeze=False
)
bar_width = 0.8

for i, ax in enumerate(axs.flatten()):
    cope_id = i + 1
    sub = param_df[param_df['Cope'] == cope_id]
    # ensure regions in the specified order
    sub = sub.set_index('Region').loc[region_order].reset_index()
    x = np.arange(n_regions)
    y_vals  = sub['median'].values
    sig_vals= sub['sig'].values

    for xi, yi, s in zip(x, y_vals, sig_vals):
        ax.bar(
            xi, yi,
            width=bar_width,
            color=(colors[i] if s else 'white'),
            edgecolor=colors[i]
        )

    ax.set_xticks(x)
    ax.set_xticklabels(region_order, rotation=45, ha='right', va='top', fontsize=12)
    ax.set_yticks(y_ticks)
    ax.set_ylabel('t-statistic for COPE', fontsize=14)
    ax.axhline(0, color='k', linewidth=1)
    ax.set_ylim(y_ticks[0], y_ticks[-1])
    ax.set_title(cope_text[i], fontsize=16)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(f'revmumford_gmix_{dataset}.png', dpi=300)
plt.show()

# ------------------ contrast analysis for whole dataset ------------------
# rebuild contrast_spec (simple + complex)
base_weights = {
    'lamBL':   1,  # open‐loop
    'lamCEN':   1,
    'lvPut':   1,
    'lBFmb':   1,
    'lBFsep':   1,
    'ldPut':  -1,  # closed‐loop
    'lGPi':   -1,
    'lvlThal': -1,
}
contrast_spec = {r: 0 for r in region_order}
for region, w in base_weights.items():
    if region in contrast_spec:
        contrast_spec[region] = w
    complex_r = f'{region}c'
    if complex_r in contrast_spec:
        contrast_spec[complex_r] = w

out_fname = f'revmumford_contrast_{dataset}.txt'
with open(out_fname, 'w') as outf:
    # Original contrast analysis
    outf.write("=" * 60 + "\n")
    outf.write("OPEN vs CLOSED LOOP CONTRAST ANALYSIS\n")
    outf.write("=" * 60 + "\n\n")
    
    for cope_id in sorted(param_df['Cope'].unique()):
        outf.write(f"=== Contrast for COPE {cope_id} ===\n")
        inds = param_df.index[param_df['Cope'] == cope_id].tolist()
        regions = param_df.loc[inds, 'Region'].values
        vec = np.array([contrast_spec[r] for r in regions], dtype=float)
        open_ix   = np.where(vec ==  1)[0]
        closed_ix = np.where(vec == -1)[0]
        if len(open_ix) < 1 or len(closed_ix) < 1:
            outf.write(f"COPE {cope_id}: need ≥1 open & ≥1 closed → skipping\n")
            continue
        mu_cols    = [f"mu__{i}" for i in inds]
        posterior  = tracedf[mu_cols].values
        open_mean   = posterior[:, open_ix].mean(axis=1)
        closed_mean = posterior[:, closed_ix].mean(axis=1)
        contrast_samps = open_mean - closed_mean
        hdi = pm.hdi(contrast_samps, hdi_prob=0.89)
        sig = (hdi[0] > 0) or (hdi[1] < 0)
        outf.write(
            f"COPE {cope_id}: Δ = {contrast_samps.mean():.3f}, "
            f"89% HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}], "
            + ("Credible difference ≠ 0\n" if sig else "No credible difference\n")
        )

    # NEW ANALYSIS 1: Test closed and open loops against zero for each COPE
    outf.write("\n" + "=" * 60 + "\n")
    outf.write("OPEN AND CLOSED LOOP REGIONS vs ZERO\n")
    outf.write("=" * 60 + "\n\n")
    
    for cope_id in sorted(param_df['Cope'].unique()):
        outf.write(f"=== COPE {cope_id} vs Zero ===\n")
        inds = param_df.index[param_df['Cope'] == cope_id].tolist()
        regions = param_df.loc[inds, 'Region'].values
        vec = np.array([contrast_spec[r] for r in regions], dtype=float)
        open_ix   = np.where(vec ==  1)[0]
        closed_ix = np.where(vec == -1)[0]
        
        if len(open_ix) >= 1:
            mu_cols = [f"mu__{inds[i]}" for i in open_ix]
            posterior = tracedf[mu_cols].values
            open_mean = posterior.mean(axis=1)
            hdi = pm.hdi(open_mean, hdi_prob=0.89)
            sig = (hdi[0] > 0) or (hdi[1] < 0)
            outf.write(
                f"Open-loop regions: Mean = {open_mean.mean():.3f}, "
                f"89% HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}], "
                + ("Credible difference ≠ 0\n" if sig else "No credible difference from 0\n")
            )
        
        if len(closed_ix) >= 1:
            mu_cols = [f"mu__{inds[i]}" for i in closed_ix]
            posterior = tracedf[mu_cols].values
            closed_mean = posterior.mean(axis=1)
            hdi = pm.hdi(closed_mean, hdi_prob=0.89)
            sig = (hdi[0] > 0) or (hdi[1] < 0)
            outf.write(
                f"Closed-loop regions: Mean = {closed_mean.mean():.3f}, "
                f"89% HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}], "
                + ("Credible difference ≠ 0\n" if sig else "No credible difference from 0\n")
            )
        outf.write("\n")

    # NEW ANALYSIS 2: Individual region ROPE analysis
    outf.write("\n" + "=" * 60 + "\n")
    outf.write("INDIVIDUAL REGION ROPE ANALYSIS (ROPE = [-0.1, 0.1])\n")
    outf.write("=" * 60 + "\n\n")
    
    for cope_id in sorted(param_df['Cope'].unique()):
        outf.write(f"=== COPE {cope_id} - Individual Regions ===\n")
        outf.write(f"{'Region':<12} {'Mean':<8} {'HDI_Lower':<10} {'HDI_Upper':<10} {'ROPE_Decision':<12}\n")
        outf.write("-" * 55 + "\n")
        
        cope_data = param_df[param_df['Cope'] == cope_id]
        for _, row in cope_data.iterrows():
            param_idx = row.name
            samples = tracedf[f'mu__{param_idx}'].values
            hdi_lower, hdi_upper, decision = rope_analysis(samples)
            outf.write(f"{row['Region']:<12} {samples.mean():<8.3f} {hdi_lower:<10.3f} {hdi_upper:<10.3f} {decision:<12}\n")
        outf.write("\n")

    # NEW ANALYSIS 3: COPE 3 vs COPE 4 comparison
    outf.write("\n" + "=" * 60 + "\n")
    outf.write("COPE 3 vs COPE 4 COMPARISON (All Regions)\n")
    outf.write("=" * 60 + "\n\n")
    
    cope3_data = param_df[param_df['Cope'] == 3]
    cope4_data = param_df[param_df['Cope'] == 4]
    
    if len(cope3_data) > 0 and len(cope4_data) > 0:
        outf.write(f"{'Region':<12} {'COPE3_Mean':<11} {'COPE4_Mean':<11} {'Diff_Mean':<10} {'HDI_Lower':<10} {'HDI_Upper':<10} {'Significant':<12}\n")
        outf.write("-" * 80 + "\n")
        
        for region in region_order:
            cope3_row = cope3_data[cope3_data['Region'] == region]
            cope4_row = cope4_data[cope4_data['Region'] == region]
            
            if len(cope3_row) > 0 and len(cope4_row) > 0:
                cope3_idx = cope3_row.index[0]
                cope4_idx = cope4_row.index[0]
                
                cope3_samples = tracedf[f'mu__{cope3_idx}'].values
                cope4_samples = tracedf[f'mu__{cope4_idx}'].values
                diff_samples = cope3_samples - cope4_samples
                
                hdi = pm.hdi(diff_samples, hdi_prob=0.89)
                sig = (hdi[0] > 0) or (hdi[1] < 0)
                
                outf.write(f"{region:<12} {cope3_samples.mean():<11.3f} {cope4_samples.mean():<11.3f} "
                          f"{diff_samples.mean():<10.3f} {hdi[0]:<10.3f} {hdi[1]:<10.3f} "
                          f"{'Yes' if sig else 'No':<12}\n")
    else:
        outf.write("COPE 3 or COPE 4 data not available for comparison.\n")

    # NEW ANALYSIS 4: CIRCUIT-LEVEL COPE 3 vs COPE 4 comparison
    outf.write("\n" + "=" * 60 + "\n")
    outf.write("CIRCUIT-LEVEL COPE 3 vs COPE 4 COMPARISON\n")
    outf.write("=" * 60 + "\n\n")
    
    if len(cope3_data) > 0 and len(cope4_data) > 0:
        # Get indices for COPE 3
        cope3_inds = param_df.index[param_df['Cope'] == 3].tolist()
        cope3_regions = param_df.loc[cope3_inds, 'Region'].values
        cope3_vec = np.array([contrast_spec[r] for r in cope3_regions], dtype=float)
        cope3_open_ix = np.where(cope3_vec == 1)[0]
        cope3_closed_ix = np.where(cope3_vec == -1)[0]
        
        # Get indices for COPE 4
        cope4_inds = param_df.index[param_df['Cope'] == 4].tolist()
        cope4_regions = param_df.loc[cope4_inds, 'Region'].values
        cope4_vec = np.array([contrast_spec[r] for r in cope4_regions], dtype=float)
        cope4_open_ix = np.where(cope4_vec == 1)[0]
        cope4_closed_ix = np.where(cope4_vec == -1)[0]
        
        # Open-loop circuit comparison
        if len(cope3_open_ix) >= 1 and len(cope4_open_ix) >= 1:
            outf.write("=== Open-Loop Circuit: COPE 3 vs COPE 4 ===\n")
            
            # COPE 3 open-loop
            cope3_open_mu_cols = [f"mu__{cope3_inds[i]}" for i in cope3_open_ix]
            cope3_open_posterior = tracedf[cope3_open_mu_cols].values
            cope3_open_mean = cope3_open_posterior.mean(axis=1)
            
            # COPE 4 open-loop
            cope4_open_mu_cols = [f"mu__{cope4_inds[i]}" for i in cope4_open_ix]
            cope4_open_posterior = tracedf[cope4_open_mu_cols].values
            cope4_open_mean = cope4_open_posterior.mean(axis=1)
            
            # Difference
            open_diff = cope3_open_mean - cope4_open_mean
            open_hdi = pm.hdi(open_diff, hdi_prob=0.89)
            open_sig = (open_hdi[0] > 0) or (open_hdi[1] < 0)
            
            outf.write(f"COPE 3 Open-loop mean: {cope3_open_mean.mean():.3f}\n")
            outf.write(f"COPE 4 Open-loop mean: {cope4_open_mean.mean():.3f}\n")
            outf.write(f"Difference (COPE3 - COPE4): {open_diff.mean():.3f}\n")
            outf.write(f"89% HDI: [{open_hdi[0]:.3f}, {open_hdi[1]:.3f}]\n")
            outf.write("Credible difference ≠ 0\n" if open_sig else "No credible difference\n")
            outf.write("\n")
        
        # Closed-loop circuit comparison
        if len(cope3_closed_ix) >= 1 and len(cope4_closed_ix) >= 1:
            outf.write("=== Closed-Loop Circuit: COPE 3 vs COPE 4 ===\n")
            
            # COPE 3 closed-loop
            cope3_closed_mu_cols = [f"mu__{cope3_inds[i]}" for i in cope3_closed_ix]
            cope3_closed_posterior = tracedf[cope3_closed_mu_cols].values
            cope3_closed_mean = cope3_closed_posterior.mean(axis=1)
            
            # COPE 4 closed-loop
            cope4_closed_mu_cols = [f"mu__{cope4_inds[i]}" for i in cope4_closed_ix]
            cope4_closed_posterior = tracedf[cope4_closed_mu_cols].values
            cope4_closed_mean = cope4_closed_posterior.mean(axis=1)
            
            # Difference
            closed_diff = cope3_closed_mean - cope4_closed_mean
            closed_hdi = pm.hdi(closed_diff, hdi_prob=0.89)
            closed_sig = (closed_hdi[0] > 0) or (closed_hdi[1] < 0)
            
            outf.write(f"COPE 3 Closed-loop mean: {cope3_closed_mean.mean():.3f}\n")
            outf.write(f"COPE 4 Closed-loop mean: {cope4_closed_mean.mean():.3f}\n")
            outf.write(f"Difference (COPE3 - COPE4): {closed_diff.mean():.3f}\n")
            outf.write(f"89% HDI: [{closed_hdi[0]:.3f}, {closed_hdi[1]:.3f}]\n")
            outf.write("Credible difference ≠ 0\n" if closed_sig else "No credible difference\n")
            outf.write("\n")
        
        # Interaction effect: (COPE3_open - COPE4_open) - (COPE3_closed - COPE4_closed)
        if (len(cope3_open_ix) >= 1 and len(cope4_open_ix) >= 1 and 
            len(cope3_closed_ix) >= 1 and len(cope4_closed_ix) >= 1):
            outf.write("=== Interaction Effect: Circuit × COPE ===\n")
            interaction = open_diff - closed_diff
            interaction_hdi = pm.hdi(interaction, hdi_prob=0.89)
            interaction_sig = (interaction_hdi[0] > 0) or (interaction_hdi[1] < 0)
            
            outf.write(f"Interaction effect: {interaction.mean():.3f}\n")
            outf.write(f"89% HDI: [{interaction_hdi[0]:.3f}, {interaction_hdi[1]:.3f}]\n")
            outf.write("Credible interaction ≠ 0\n" if interaction_sig else "No credible interaction\n")
    else:
        outf.write("COPE 3 or COPE 4 data not available for circuit comparison.\n")

print(f"\nExtended analysis results written to {out_fname}")

# Also create a summary CSV for individual region analysis
summary_data = []
for cope_id in sorted(param_df['Cope'].unique()):
    cope_data = param_df[param_df['Cope'] == cope_id]
    for _, row in cope_data.iterrows():
        param_idx = row.name
        samples = tracedf[f'mu__{param_idx}'].values
        hdi_lower, hdi_upper, decision = rope_analysis(samples)
        summary_data.append({
            'COPE': cope_id,
            'Region': row['Region'],
            'Mean': samples.mean(),
            'HDI_Lower': hdi_lower,
            'HDI_Upper': hdi_upper,
            'ROPE_Decision': decision
        })

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv(f'revmumford_individual_regions_{dataset}.csv', index=False)
print(f"Individual region summary saved to revmumford_individual_regions_{dataset}.csv")