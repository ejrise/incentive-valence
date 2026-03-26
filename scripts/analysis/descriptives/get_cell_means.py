#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_cell_means.py

Computes cell means and marginal means consistent with the full factorial
RM ANOVA (cue x hold x run).  Marginal means are the unweighted average
of the cell means across the levels of the marginalised factors, which is
how the ANOVA estimates them regardless of unequal trial counts per cell.

Outputs for each variable:
  - Full cell means (cue x hold x run)
  - Cue x Hold cell means (marginalised over run)
  - Cue marginal means   (marginalised over hold and run)
  - Cue effects relative to Standard at each hold level and overall
"""
import numpy as np
import pandas as pd
from pathlib import Path
# ==============================================================================
# CONFIG
# ==============================================================================
try:
    _SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    _SCRIPT_DIR = Path.cwd()
CSV_PATH = _SCRIPT_DIR / ".." / ".." / ".." / "data" / "preprocessed" / "behavioral" / "IVdata_wFSs.csv"

VARIABLES = [
    {"name": "success",      "display_name": "success rate", "stat": "mean"},
    {"name": "init",         "display_name": "RT", "stat": "median"},
    {"name": "false_start",  "display_name": "false starts", "stat": "mean"},
    {"name": "maxvel",       "display_name": "max. velocity", "stat": "median"},
    {"name": "maxacc",       "display_name": "max. acceleration", "stat": "median"},
    {"name": "maxacct",      "display_name": "time to max. acc.", "stat": "median"},
]

FACTORS = ["cue", "run", "hold"]
CUE_LABELS  = {0: 'Standard', 1: 'Jackpot', 2: 'Robber'}
HOLD_LABELS = {False: 'Short', True: 'Long'}

def prep_dataframe(df, measurement, anchor=None):
    df2 = df.copy()
    if df2['hold'].dtype == object:
        df2['hold'] = df2['hold'].map({'True': True, 'False': False})
    df2['hold'] = df2['hold'].astype(bool)
    df2['success'] = df2['outcome'] == 1
    df2 = df2.replace([np.inf, -np.inf], np.nan).dropna(subset=[measurement])
    df2.loc[df2['cue'] == 3, 'cue'] = 0
    if anchor is not None:
        df2[measurement] = df2[measurement] - anchor
    return df2

def aggregate_within_subject(df, measurement, statistic):
    """Aggregate trials within each subject x cue x hold x run cell."""
    stat = statistic.lower()
    if stat == 'mean':
        return df.groupby(['sub_orig'] + FACTORS, as_index=False)[measurement].mean()
    else:
        return df.groupby(['sub_orig'] + FACTORS, as_index=False)[measurement].median()

def run():
    df = pd.read_csv(CSV_PATH)

    for cfg in VARIABLES:
        m = cfg["name"]
        display_name = cfg.get("display_name", m)
        s = cfg.get("stat", "median")
        anchor = cfg.get("anchor", None)

        df_prep = prep_dataframe(df, m, anchor)
        df_agg  = aggregate_within_subject(df_prep, m, s)

        print(f"\n{'='*60}")
        print(f"{display_name.upper()} ({s})")
        print(f"ANOVA-consistent means (averaged across cell means)")
        print('='*60)

        # --- Full cell means: cue x hold x run --------------------------
        full_cells = df_agg.groupby(FACTORS)[m].mean()
        print("\nFull cell means (cue x hold x run):")
        for (cue, run, hold), val in full_cells.items():
            print(f"  {CUE_LABELS[cue]:>10s}  Run {run}  {HOLD_LABELS[hold]:>5s}  {val:.4f}")

        # --- Cue x Hold marginal means (averaged over run) ---------------
        cue_hold = df_agg.groupby(['sub_orig', 'cue', 'hold'])[m].mean().reset_index()
        ch_means = cue_hold.groupby(['cue', 'hold'])[m].mean().unstack()
        ch_sems  = cue_hold.groupby(['cue', 'hold'])[m].sem().unstack()

        ch_means.index   = [CUE_LABELS.get(c, c) for c in ch_means.index]
        ch_means.columns = [HOLD_LABELS.get(c, c) for c in ch_means.columns]
        ch_sems.index    = [CUE_LABELS.get(c, c) for c in ch_sems.index]
        ch_sems.columns  = [HOLD_LABELS.get(c, c) for c in ch_sems.columns]

        print("\nCue x Hold cell means (marginalised over run):")
        print(ch_means.round(4).to_string())
        print("\nCue x Hold SEMs:")
        print(ch_sems.round(4).to_string())

        # --- Cue marginal means (averaged over hold and run) -------------
        cue_marg = df_agg.groupby(['sub_orig', 'cue'])[m].mean().reset_index()
        marg_means = cue_marg.groupby('cue')[m].mean()
        marg_sems  = cue_marg.groupby('cue')[m].sem()

        print("\nCue marginal means (marginalised over hold and run):")
        for c in sorted(marg_means.index):
            print(f"  {CUE_LABELS[c]:>10s}  {marg_means[c]:.4f}  (SEM {marg_sems[c]:.4f})")

        # --- Cue effects relative to Standard ----------------------------
        print("\nCue effects (relative to Standard):")

        # Overall marginal
        std_marg = marg_means[0]
        for c in [1, 2]:
            diff = marg_means[c] - std_marg
            print(f"  Overall:     {CUE_LABELS[c]:>10s} - Standard = {diff:+.4f}")

        # By hold level
        ch_means_raw = cue_hold.groupby(['cue', 'hold'])[m].mean().unstack()
        for hold_val, hold_label in HOLD_LABELS.items():
            if hold_val not in ch_means_raw.columns:
                continue
            std_val = ch_means_raw.loc[0, hold_val]
            for c in [1, 2]:
                diff = ch_means_raw.loc[c, hold_val] - std_val
                print(f"  {hold_label:>5s} hold:  {CUE_LABELS[c]:>10s} - Standard = {diff:+.4f}")

if __name__ == "__main__":
    run()