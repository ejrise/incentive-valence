#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Study 2 Q3/Q4: Comprehensive success/reward variance analysis.
Panels:
  A - Success rate histogram
  B - Normalized reward rate histogram
  C - RT cue effects vs success rate
  D - FS cue effects vs success rate
  E - Velocity cue effects vs success rate
  F - Temporal drift (quintiles)
  G - RT cue effects vs learning slope
  H - AUC: init predicting success (per subject)
  I - Point-biserial r: init vs success (per subject)
"""
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import stats
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

# ==============================================================================
# CONFIG
# ==============================================================================
try:
    _SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    _SCRIPT_DIR = Path.cwd()
CSV_PATH = _SCRIPT_DIR / ".." / ".." / ".." / "data" / "preprocessed" / "behavioral" / "IVdata_wFSs.csv"
OUT_PNG = "FigureS1.png"
OUT_PDF = "FigureS1.pdf"
OUT_PNG_A = "FigureS1a.png"
OUT_PDF_A = "FigureS1a.pdf"
OUT_PNG_B = "FigureS1b.png"
OUT_PDF_B = "FigureS1b.pdf"
N_BINS = 5

EXCLUDE_SUBS = [308, 311, 312, 332, 339, 340]
APPLY_EXCLUSIONS = False

CORRELATION_METRIC = 'success_rate'

REWARDS = {
    0: {'success': 0.2, 'fail': 0.0},
    1: {'success': 1.6, 'fail': 0.0},
    2: {'success': 0.0, 'fail': -1.6},
}

# =========================
# ===== STYLE =============
# =========================
BASE_FONTSIZE_PT = 8
BASE_LINEWIDTH_PT = 0.7
HIST_COLOR = '#888888'
ACCENT_COLOR = '#E67E22'

def apply_style():
    matplotlib.rcParams.update({
        "font.family": "Helvetica",
        "font.size": BASE_FONTSIZE_PT,
        "axes.titlesize": BASE_FONTSIZE_PT,
        "axes.labelsize": BASE_FONTSIZE_PT,
        "xtick.labelsize": BASE_FONTSIZE_PT,
        "ytick.labelsize": BASE_FONTSIZE_PT,
        "lines.linewidth": BASE_LINEWIDTH_PT,
        "axes.linewidth": BASE_LINEWIDTH_PT,
    })

def clean_ax(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# =========================
# ======= HELPERS =========
# =========================
def calc_corr(x, y):
    mask = x.notna() & y.notna()
    r, p = stats.pearsonr(x[mask], y[mask])
    return r, p

def scatter_effect_panel(ax, x, y_jp, y_rb, r_jp, p_jp, r_rb, p_rb, xlabel, ylabel, title_letter):
    """Generic scatter for cue-effect vs some x-variable."""
    ax.scatter(x, y_jp,
               c='#b3e696', alpha=0.6, edgecolors='none', s=30,
               label=f'Jackpot: r={r_jp:.2f}, p={p_jp:.3f}')
    ax.scatter(x, y_rb,
               c='#ffb3ff', alpha=0.6, edgecolors='none', s=30,
               label=f'Robber: r={r_rb:.2f}, p={p_rb:.3f}')
    mask_jp = x.notna() & y_jp.notna()
    mask_rb = x.notna() & y_rb.notna()
    x_range = np.array([x.min(), x.max()])
    s_jp, i_jp = np.polyfit(x[mask_jp], y_jp[mask_jp], 1)
    s_rb, i_rb = np.polyfit(x[mask_rb], y_rb[mask_rb], 1)
    ax.plot(x_range, s_jp * x_range + i_jp, color='#6abf40', linewidth=1)
    ax.plot(x_range, s_rb * x_range + i_rb, color='#e066e0', linewidth=1)
    ax.axhline(0, color='gray', linestyle=':', linewidth=0.5)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=6, frameon=False, loc='best')
    ax.set_title(title_letter, fontweight='bold', loc='left')
    clean_ax(ax)

# =========================
# ======= ANALYSIS ========
# =========================
def run():
    apply_style()
    df = pd.read_csv(CSV_PATH)
    if APPLY_EXCLUSIONS:
        df = df[~df['sub_orig'].isin(EXCLUDE_SUBS)]

    df.loc[df['cue'] == 3, 'cue'] = 0
    df['success'] = (df['outcome'] == 1).astype(int)
    df['false_start'] = df['false_start'].astype(int) if 'false_start' in df.columns else np.nan

    def get_reward(row):
        cue = row['cue']
        return REWARDS[cue]['success'] if row['success'] == 1 else REWARDS[cue]['fail']
    df['reward'] = df.apply(get_reward, axis=1)

    # --- Per-subject metrics ---
    subjects = df['sub_orig'].unique()
    records = []

    for sub_id in subjects:
        sd = df[df['sub_orig'] == sub_id]
        success_rate = sd['success'].mean()
        reward_rate = sd['reward'].mean()

        rt_standard = sd.loc[sd['cue'] == 0, 'init'].median()
        rt_jackpot = sd.loc[sd['cue'] == 1, 'init'].median()
        rt_robber = sd.loc[sd['cue'] == 2, 'init'].median()
        rt_effect_jackpot = rt_jackpot - rt_standard if pd.notna(rt_jackpot) and pd.notna(rt_standard) else np.nan
        rt_effect_robber = rt_robber - rt_standard if pd.notna(rt_robber) and pd.notna(rt_standard) else np.nan

        fs_standard = sd.loc[sd['cue'] == 0, 'false_start'].mean()
        fs_jackpot = sd.loc[sd['cue'] == 1, 'false_start'].mean()
        fs_robber = sd.loc[sd['cue'] == 2, 'false_start'].mean()
        fs_effect_jackpot = fs_jackpot - fs_standard if pd.notna(fs_jackpot) and pd.notna(fs_standard) else np.nan
        fs_effect_robber = fs_robber - fs_standard if pd.notna(fs_robber) and pd.notna(fs_standard) else np.nan

        vel_standard = sd.loc[sd['cue'] == 0, 'maxvel'].median()
        vel_jackpot = sd.loc[sd['cue'] == 1, 'maxvel'].median()
        vel_robber = sd.loc[sd['cue'] == 2, 'maxvel'].median()
        vel_effect_jackpot = vel_jackpot - vel_standard if pd.notna(vel_jackpot) and pd.notna(vel_standard) else np.nan
        vel_effect_robber = vel_robber - vel_standard if pd.notna(vel_robber) and pd.notna(vel_standard) else np.nan

        records.append({
            'sub_orig': sub_id,
            'success_rate': success_rate,
            'reward_rate': reward_rate,
            'rt_effect_jackpot': rt_effect_jackpot,
            'rt_effect_robber': rt_effect_robber,
            'fs_effect_jackpot': fs_effect_jackpot,
            'fs_effect_robber': fs_effect_robber,
            'vel_effect_jackpot': vel_effect_jackpot,
            'vel_effect_robber': vel_effect_robber,
        })

    subj_df = pd.DataFrame(records)
    n_subj = len(subj_df)
    success_lo = np.percentile(subj_df['success_rate'], 2.5)
    success_hi = np.percentile(subj_df['success_rate'], 97.5)
    n_negative_reward = (subj_df['reward_rate'] < 0).sum()

    # --- Temporal drift ---
    df['trial_num'] = df.groupby('sub_orig').cumcount() + 1
    df['trial_bin'] = df.groupby('sub_orig')['trial_num'].transform(
        lambda x: pd.qcut(x, N_BINS, labels=False) + 1
    )
    temporal = df.groupby(['sub_orig', 'trial_bin'])['success'].mean().reset_index()
    temporal_agg = temporal.groupby('trial_bin')['success'].agg(['mean', 'sem'])

    # --- Per-subject learning slope ---
    learning_slopes = []
    for sub_id in subjects:
        st = temporal[temporal['sub_orig'] == sub_id]
        if len(st) >= 2:
            slope, _, _, _, _ = stats.linregress(st['trial_bin'], st['success'])
        else:
            slope = np.nan
        learning_slopes.append({'sub_orig': sub_id, 'learning_slope': slope})
    slope_df = pd.DataFrame(learning_slopes)
    subj_df = subj_df.merge(slope_df, on='sub_orig', how='left')

    # --- Correlations ---
    corr_metric = CORRELATION_METRIC
    corr_label = 'Success rate' if corr_metric == 'success_rate' else 'Mean reward/trial'

    # RT vs success rate (panel C)
    r_rt_jp, p_rt_jp = calc_corr(subj_df[corr_metric], subj_df['rt_effect_jackpot'])
    r_rt_rb, p_rt_rb = calc_corr(subj_df[corr_metric], subj_df['rt_effect_robber'])
    # FS vs success rate (panel D)
    r_fs_jp, p_fs_jp = calc_corr(subj_df[corr_metric], subj_df['fs_effect_jackpot'])
    r_fs_rb, p_fs_rb = calc_corr(subj_df[corr_metric], subj_df['fs_effect_robber'])
    # Velocity vs success rate (panel E)
    r_vel_jp, p_vel_jp = calc_corr(subj_df[corr_metric], subj_df['vel_effect_jackpot'])
    r_vel_rb, p_vel_rb = calc_corr(subj_df[corr_metric], subj_df['vel_effect_robber'])
    # Learning slope vs RT cue effects (panel G)
    r_slope_rt_jp, p_slope_rt_jp = calc_corr(subj_df['learning_slope'], subj_df['rt_effect_jackpot'])
    r_slope_rt_rb, p_slope_rt_rb = calc_corr(subj_df['learning_slope'], subj_df['rt_effect_robber'])

    # --- Per-subject init vs outcome (panels H-I) ---
    df_valid = df.loc[df.outcome.isin([1, 2])].dropna(subset=['init']).copy()
    df_valid['success_binary'] = (df_valid.outcome == 1).astype(int)

    aucs = []
    corrs = []

    for s in df_valid['sub'].unique():
        sd = df_valid.loc[df_valid['sub'] == s]
        if sd.success_binary.nunique() < 2:
            continue
        r = sd[['init', 'success_binary']].corr().iloc[0, 1]
        corrs.append(r)
        X = sd.init.values.reshape(-1, 1)
        y = sd.success_binary.values
        clf = LogisticRegression(solver='lbfgs')
        clf.fit(X, y)
        auc = roc_auc_score(y, clf.predict_proba(X)[:, 1])
        aucs.append(auc)

    aucs = np.array(aucs)
    corrs = np.array(corrs)

    # =========================================================================
    # PLOTTING HELPER: draws all 9 panels onto supplied axes dict
    # =========================================================================
    def draw_panels(axes):
        """
        axes: dict with keys 'A'..'I' (only those present will be drawn).
        """
        # --- A: Success rate histogram ---
        if 'A' in axes:
            ax = axes['A']
            ax.hist(subj_df['success_rate'], bins=15, color=HIST_COLOR, edgecolor='white', alpha=0.8)
            ax.axvline(subj_df['success_rate'].mean(), color='black', linestyle='--', linewidth=1)
            ax.axvline(success_lo, color='black', linestyle=':', linewidth=0.7)
            ax.axvline(success_hi, color='black', linestyle=':', linewidth=0.7)
            ax.text(0.95, 0.95, f'95% CI: [{success_lo:.2f}, {success_hi:.2f}]',
                    transform=ax.transAxes, ha='right', va='top', fontsize=6)
            ax.set_xlabel('Success rate')
            ax.set_ylabel('N participants')
            ax.set_title('A', fontweight='bold', loc='left')
            clean_ax(ax)

        # --- B: Reward rate histogram ---
        if 'B' in axes:
            ax = axes['B']
            ax.hist(subj_df['reward_rate'], bins=15, color=HIST_COLOR, edgecolor='white', alpha=0.8)
            ax.axvline(subj_df['reward_rate'].mean(), color='black', linestyle='--', linewidth=1)
            ax.axvline(0, color='red', linestyle=':', linewidth=0.7)
            ax.text(0.95, 0.95, f'{n_subj - n_negative_reward}/{n_subj} > 0',
                    transform=ax.transAxes, ha='right', va='top', fontsize=6)
            ax.set_xlabel('Mean reward per trial')
            ax.set_ylabel('N participants')
            ax.set_title('B', fontweight='bold', loc='left')
            clean_ax(ax)

        # --- C: RT cue effects vs success rate ---
        if 'C' in axes:
            scatter_effect_panel(
                axes['C'], subj_df[corr_metric],
                subj_df['rt_effect_jackpot'], subj_df['rt_effect_robber'],
                r_rt_jp, p_rt_jp, r_rt_rb, p_rt_rb,
                corr_label, 'RT effect (cond. \u2212 standard, s)', 'C')

        # --- D: FS cond. effects vs success rate ---
        if 'D' in axes:
            scatter_effect_panel(
                axes['D'], subj_df[corr_metric],
                subj_df['fs_effect_jackpot'], subj_df['fs_effect_robber'],
                r_fs_jp, p_fs_jp, r_fs_rb, p_fs_rb,
                corr_label, 'FS effect (cond. \u2212 standard)', 'D')

        # --- E: Velocity cond. effects vs success rate ---
        if 'E' in axes:
            scatter_effect_panel(
                axes['E'], subj_df[corr_metric],
                subj_df['vel_effect_jackpot'], subj_df['vel_effect_robber'],
                r_vel_jp, p_vel_jp, r_vel_rb, p_vel_rb,
                corr_label, 'Velocity effect (cond. \u2212 standard)', 'E')

        # --- F: Temporal drift ---
        if 'F' in axes:
            ax = axes['F']
            bins = temporal_agg.index.values
            means = temporal_agg['mean'].values
            sems = temporal_agg['sem'].values
            ax.errorbar(bins, means, yerr=sems, fmt='o', color='black', capsize=3, markersize=4)
            slope_c, int_c = np.polyfit(bins, means, 1)
            ax.plot(bins, slope_c * bins + int_c, color='black', linewidth=1)
            trend_r, trend_p = stats.pearsonr(temporal['trial_bin'], temporal['success'])
            ax.text(0.95, 0.05, f'r = {trend_r:.2f}, p = {trend_p:.3f}',
                    transform=ax.transAxes, ha='right', va='bottom', fontsize=6)
            ax.set_xlabel('Trial quintile')
            ax.set_ylabel('Success rate')
            ax.set_xticks(bins)
            ax.set_ylim(0.2, 0.8)
            ax.set_title('F', fontweight='bold', loc='left')
            clean_ax(ax)

        # --- G: RT cond. effects vs learning slope ---
        if 'G' in axes:
            scatter_effect_panel(
                axes['G'], subj_df['learning_slope'],
                subj_df['rt_effect_jackpot'], subj_df['rt_effect_robber'],
                r_slope_rt_jp, p_slope_rt_jp, r_slope_rt_rb, p_slope_rt_rb,
                'Learning slope', 'RT effect (cond. \u2212 standard, s)', 'G')

        # --- H: AUC distribution ---
        if 'H' in axes:
            ax = axes['H']
            ax.hist(aucs, bins=15, color=HIST_COLOR, edgecolor='white', alpha=0.8)
            ax.axvline(0.5, color='black', ls='--', lw=1, label='chance')
            ax.axvline(np.median(aucs), color=ACCENT_COLOR, ls='-', lw=1,
                       label=f'median = {np.median(aucs):.2f}')
            ax.set_xlabel('AUC (init predicting success)')
            ax.set_ylabel('N participants')
            ax.legend(fontsize=6, frameon=False)
            ax.set_xlim(0.4, 1.0)
            ax.set_title('H', fontweight='bold', loc='left')
            clean_ax(ax)

        # --- I: Point-biserial r distribution ---
        if 'I' in axes:
            ax = axes['I']
            ax.hist(corrs, bins=15, color=HIST_COLOR, edgecolor='white', alpha=0.8)
            ax.axvline(0, color='black', ls='--', lw=1)
            ax.axvline(np.median(corrs), color=ACCENT_COLOR, ls='-', lw=1,
                       label=f'median r = {np.median(corrs):.2f}')
            ax.set_xlabel('r (init, success)')
            ax.set_ylabel('N participants')
            ax.legend(fontsize=6, frameon=False)
            ax.set_title('I', fontweight='bold', loc='left')
            clean_ax(ax)

    # =========================================================================
    # FIGURE S1 (full, A-I)
    # =========================================================================
    fig = plt.figure(figsize=(7, 7.5))
    gs = GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.4)

    axes_full = {
        'A': fig.add_subplot(gs[0, 0]),
        'B': fig.add_subplot(gs[0, 1]),
        'C': fig.add_subplot(gs[0, 2]),
        'D': fig.add_subplot(gs[1, 0]),
        'E': fig.add_subplot(gs[1, 1]),
        'F': fig.add_subplot(gs[1, 2]),
        'G': fig.add_subplot(gs[2, 0]),
        'H': fig.add_subplot(gs[2, 1]),
        'I': fig.add_subplot(gs[2, 2]),
    }
    draw_panels(axes_full)
    fig.savefig(OUT_PNG, dpi=300, bbox_inches='tight')
    fig.savefig(OUT_PDF, bbox_inches='tight')
    plt.close(fig)

    # =========================================================================
    # FIGURE S1a (A-G for reviewer split)
    # =========================================================================
    fig_a = plt.figure(figsize=(7, 7.5))
    gs_a = GridSpec(3, 3, figure=fig_a, hspace=0.45, wspace=0.4)

    axes_a = {
        'A': fig_a.add_subplot(gs_a[0, 0]),
        'B': fig_a.add_subplot(gs_a[0, 1]),
        'C': fig_a.add_subplot(gs_a[1, 0]),
        'D': fig_a.add_subplot(gs_a[1, 1]),
        'E': fig_a.add_subplot(gs_a[1, 2]),
        'F': fig_a.add_subplot(gs_a[2, 0]),
        'G': fig_a.add_subplot(gs_a[2, 1]),
    }
    draw_panels(axes_a)
    fig_a.savefig(OUT_PNG_A, dpi=300, bbox_inches='tight')
    fig_a.savefig(OUT_PDF_A, bbox_inches='tight')
    plt.close(fig_a)

    # =========================================================================
    # FIGURE S1b (H-I for reviewer split)
    # =========================================================================
    fig_b = plt.figure(figsize=(4.67, 2.0))
    gs_b = GridSpec(1, 2, figure=fig_b, wspace=0.45)

    axes_b = {
        'H': fig_b.add_subplot(gs_b[0, 0]),
        'I': fig_b.add_subplot(gs_b[0, 1]),
    }
    draw_panels(axes_b)
    fig_b.savefig(OUT_PNG_B, dpi=300, bbox_inches='tight')
    fig_b.savefig(OUT_PDF_B, bbox_inches='tight')
    plt.close(fig_b)

    # --- PRINT SUMMARY ---
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(f"\nSUCCESS RATE (n={n_subj}):")
    print(f"  Mean +/- SD: {subj_df['success_rate'].mean():.3f} +/- {subj_df['success_rate'].std():.3f}")
    print(f"  95% CI: [{success_lo:.3f}, {success_hi:.3f}]")
    print(f"\nREWARD RATE:")
    print(f"  Mean +/- SD: {subj_df['reward_rate'].mean():.3f} +/- {subj_df['reward_rate'].std():.3f}")
    print(f"  Positive: {n_subj - n_negative_reward}/{n_subj}")
    print(f"\nTEMPORAL DRIFT:")
    trend_r, trend_p = stats.pearsonr(temporal['trial_bin'], temporal['success'])
    print(f"  r = {trend_r:.3f}, p = {trend_p:.3f}")
    print(f"\nLEARNING SLOPE vs RT CUE EFFECTS:")
    print(f"  Slope mean +/- SD: {subj_df['learning_slope'].mean():.4f} +/- {subj_df['learning_slope'].std():.4f}")
    print(f"  RT Jackpot:  r = {r_slope_rt_jp:.3f}, p = {p_slope_rt_jp:.3f}")
    print(f"  RT Robber:   r = {r_slope_rt_rb:.3f}, p = {p_slope_rt_rb:.3f}")
    print(f"\nCORRELATIONS ({corr_label} vs cue effects):")
    print(f"  RT Jackpot:  r = {r_rt_jp:.3f}, p = {p_rt_jp:.3f}")
    print(f"  RT Robber:   r = {r_rt_rb:.3f}, p = {p_rt_rb:.3f}")
    print(f"  FS Jackpot:  r = {r_fs_jp:.3f}, p = {p_fs_jp:.3f}")
    print(f"  FS Robber:   r = {r_fs_rb:.3f}, p = {p_fs_rb:.3f}")
    print(f"  Vel Jackpot: r = {r_vel_jp:.3f}, p = {p_vel_jp:.3f}")
    print(f"  Vel Robber:  r = {r_vel_rb:.3f}, p = {p_vel_rb:.3f}")
    print(f"\nINIT vs OUTCOME (n={len(aucs)}):")
    print(f"  AUC:  median={np.median(aucs):.3f}, mean={np.mean(aucs):.3f}, "
          f"range=[{np.min(aucs):.3f}, {np.max(aucs):.3f}]")
    print(f"  Corr: median={np.median(corrs):.3f}, mean={np.mean(corrs):.3f}, "
          f"range=[{np.min(corrs):.3f}, {np.max(corrs):.3f}]")
    print(f"  N with AUC < 0.65: {np.sum(aucs < 0.65)} / {len(aucs)}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run()