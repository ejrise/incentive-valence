#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SI Figure: Velocity traces by incentive condition.

Top row    - aligned to go cue (shows RT/timing differences)
Bottom row - aligned to movement onset (shows vigor/amplitude differences)

Left column  - raw clipped traces (first N frames at 60 Hz)
Right column - time-normalized traces (0-100% movement time)

Lives in:    wkdir/scripts/analysis/descriptives/
Reads from:  wkdir/data/raw/behavioral/fmri_task/
"""

import glob
import pickle
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.interpolate import interp1d

# =========================
# ========= PATHS =========
# =========================
try:
    _SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    _SCRIPT_DIR = Path.cwd()

ROOT_DIR = _SCRIPT_DIR.parents[2]
DATA_DIR = ROOT_DIR / "data" / "raw" / "behavioral" / "fmri_task"
OUT_DIR  = _SCRIPT_DIR

# =========================
# ========= CONFIG ========
# =========================
SUBS = [
    '301','303','304','306','307','308','309','310','311','312',
    '313','314','315','316','317','318','319','320','321','322',
    '323','324','325','328','330','331','332','333','335','336',
    '337','338','339','340','341','342','343','344','345','346',
    '347','348','349','350','351','353','354','355','356','357',
    '358','360','361','362','364','365','366','367','368','369',
    '370','371','372','373','374','376','377','379',
]

N_CLIP       = 50       # frames from go cue (~833 ms at 60 Hz)
N_CLIP_ONSET = 40       # frames from movement onset (~667 ms)
N_NORM       = 101
FS           = 60
INIT_THRESH  = 0.01     # tangential displacement threshold (matching init)

COLORS = ['#b0b0b0', '#b3e696', '#ffb3ff']
LABELS = ["Standard", "Jackpot", "Robber"]
CUE_MAP = {0: 0, 3: 0, 1: 1, 2: 2}

# =========================
# ===== STYLE (fixed) =====
# =========================
DOC_WIDTH_CM      = 17.8
GUTTER_CM         = 1.2
PANEL_WIDTH_CM    = 4.5
MARGINS_CM        = dict(left=1.0, right=0.5, top=0.8, bottom=0.8)
BASE_FONTSIZE_PT  = 7
BASE_LINEWIDTH_PT = 0.7

OUT_PDF = "SI_velocity_traces.pdf"
OUT_PNG = "SI_velocity_traces.png"


def apply_style():
    matplotlib.rcParams.update({
        "font.family":      "Helvetica",
        "font.size":        BASE_FONTSIZE_PT,
        "axes.titlesize":   BASE_FONTSIZE_PT,
        "axes.labelsize":   BASE_FONTSIZE_PT,
        "xtick.labelsize":  BASE_FONTSIZE_PT,
        "ytick.labelsize":  BASE_FONTSIZE_PT,
        "legend.fontsize":  BASE_FONTSIZE_PT,
        "lines.linewidth":  BASE_LINEWIDTH_PT,
        "axes.linewidth":   BASE_LINEWIDTH_PT,
        "xtick.major.width": BASE_LINEWIDTH_PT,
        "ytick.major.width": BASE_LINEWIDTH_PT,
        "figure.constrained_layout.use": False,
    })


# =========================
# ====== DATA LOADING =====
# =========================
def _find_onset_frame(cursor):
    """Movement onset frame: first frame where tangential displacement
    >= INIT_THRESH, matching the init computation in makeDF_wFSs.py."""
    xy = np.array(cursor)
    xy_d = np.sqrt(np.sum(np.diff(xy, axis=0) ** 2, axis=1))
    hits = np.where(xy_d >= INIT_THRESH)[0]
    if len(hits) > 0:
        return hits[0]
    return None


def load_velocity_traces():
    """Extract per-trial velocity and onset frame from the pickle files.

    Returns
    -------
    traces : dict  {cond_idx: list of (sub_idx, v_full, onset_frame)}
        v_full is the full radial velocity trace from go cue.
        onset_frame is the frame index of movement onset.
    """
    traces = {0: [], 1: [], 2: []}

    for sub_idx, participant in enumerate(SUBS):
        files = sorted(glob.glob(str(DATA_DIR / (participant + '*'))))
        if len(files) != 3:
            print(f"Warning: expected 3 files for {participant}, "
                  f"found {len(files)}")
            continue

        for fpath in files:
            with open(fpath, "rb") as fp:
                b = pickle.load(fp)

            startxy = np.array(b[-1]["startxy"])

            for trial in range(len(b) - 2):
                if b[trial]["jumped_gun"] == 1:
                    continue

                cond = CUE_MAP.get(b[trial]["cue"])
                if cond is None:
                    continue

                cursor = b[trial]["reach_cursor"]
                cursor_arr = np.array(cursor)
                d = np.sqrt(np.sum((cursor_arr - startxy) ** 2, axis=1))
                v = np.diff(d)

                onset = _find_onset_frame(cursor)
                traces[cond].append((sub_idx, v, onset))

    return traces


# =========================
# ====== AVERAGING ========
# =========================
def _subject_nanmedian_clipped(trial_list, n_subs, n_clip):
    """Clip/pad each trial to n_clip frames, nanmedian within subject."""
    buckets = {}
    for sub_idx, v, _ in trial_list:
        buckets.setdefault(sub_idx, []).append(v)

    out = np.full((n_subs, n_clip), np.nan)
    for sub_idx, trials in buckets.items():
        padded = []
        for v in trials:
            row = np.full(n_clip, np.nan)
            n = min(len(v), n_clip)
            row[:n] = v[:n]
            padded.append(row)
        out[sub_idx, :] = np.nanmedian(np.vstack(padded), axis=0)
    return out


def _subject_nanmedian_onset_clipped(trial_list, n_subs, n_clip):
    """Clip/pad each trial from onset to n_clip frames post-onset,
    nanmedian within subject."""
    buckets = {}
    for sub_idx, v, onset in trial_list:
        if onset is None:
            continue
        buckets.setdefault(sub_idx, []).append((v, onset))

    out = np.full((n_subs, n_clip), np.nan)
    for sub_idx, trials in buckets.items():
        padded = []
        for v, onset in trials:
            row = np.full(n_clip, np.nan)
            v_post = v[onset:]
            n = min(len(v_post), n_clip)
            row[:n] = v_post[:n]
            padded.append(row)
        out[sub_idx, :] = np.nanmedian(np.vstack(padded), axis=0)
    return out


def _subject_nanmedian_normalized(trial_list, n_subs, from_onset=False):
    """Interpolate each trial to 0-100% movement time,
    nanmedian within subject.

    If from_onset is True, normalize only the post-onset portion."""
    pct = np.linspace(0, 100, N_NORM)

    buckets = {}
    for sub_idx, v, onset in trial_list:
        if from_onset and onset is None:
            continue
        buckets.setdefault(sub_idx, []).append((v, onset))

    out = np.full((n_subs, N_NORM), np.nan)
    for sub_idx, trials in buckets.items():
        interped = []
        for v, onset in trials:
            seg = v[onset:] if from_onset else v
            if len(seg) < 3:
                continue
            t_pct = np.linspace(0, 100, len(seg))
            f = interp1d(t_pct, seg, kind='linear')
            interped.append(f(pct))
        if interped:
            out[sub_idx, :] = np.nanmedian(np.vstack(interped), axis=0)
    return out


def _group_stats(sub_array):
    """nanmean and SEM across subjects, n varies per timepoint."""
    n_valid = np.sum(~np.isnan(sub_array), axis=0).astype(float)
    n_valid[n_valid == 0] = np.nan
    mean = np.nanmean(sub_array, axis=0)
    sem  = np.nanstd(sub_array, axis=0, ddof=1) / np.sqrt(n_valid)
    return mean, sem


# =========================
# ======= PLOTTING ========
# =========================
def make_figure(traces):
    apply_style()
    plt.close('all')

    cm2in = 1 / 2.54
    nrows = 2
    ncols = 2

    ylabel_space_cm = 0.8
    xlabel_space_cm = 0.5
    title_space_cm  = 0.3
    panel_h_cm      = PANEL_WIDTH_CM

    total_w_cm = (MARGINS_CM['left']
                  + ncols * (ylabel_space_cm + PANEL_WIDTH_CM)
                  + (ncols - 1) * GUTTER_CM
                  + MARGINS_CM['right'])

    total_h_cm = (MARGINS_CM['top']
                  + nrows * (title_space_cm + panel_h_cm + xlabel_space_cm)
                  + (nrows - 1) * GUTTER_CM
                  + MARGINS_CM['bottom'])

    fig_w = total_w_cm * cm2in
    fig_h = total_h_cm * cm2in
    fig = plt.figure(figsize=(fig_w, fig_h))

    axes = []
    for row in range(nrows):
        for col in range(ncols):
            x_cm = (MARGINS_CM['left']
                    + ylabel_space_cm
                    + col * (ylabel_space_cm + PANEL_WIDTH_CM + GUTTER_CM))

            y_cm = (MARGINS_CM['bottom']
                    + (nrows - row - 1)
                      * (title_space_cm + panel_h_cm + xlabel_space_cm
                         + GUTTER_CM)
                    + xlabel_space_cm)

            axes.append(fig.add_axes([
                (x_cm * cm2in) / fig_w,
                (y_cm * cm2in) / fig_h,
                (PANEL_WIDTH_CM * cm2in) / fig_w,
                (panel_h_cm * cm2in) / fig_h,
            ]))

    n_subs = len(SUBS)

    # ---- Panel A: go-cue aligned, raw clipped ----
    ax = axes[0]
    x_time = np.arange(N_CLIP) / FS
    for cond in range(3):
        sub_arr = _subject_nanmedian_clipped(traces[cond], n_subs, N_CLIP)
        mean, sem = _group_stats(sub_arr)
        ax.plot(x_time, mean, color=COLORS[cond], label=LABELS[cond])
        ax.fill_between(x_time, mean - sem, mean + sem,
                        color=COLORS[cond], alpha=0.3, edgecolor='none')
    ax.set_xlabel("time from go cue (s)")
    ax.set_title("go-cue aligned")

    # ---- Panel B: go-cue aligned, time-normalized ----
    ax = axes[1]
    x_pct = np.linspace(0, 100, N_NORM)
    for cond in range(3):
        sub_arr = _subject_nanmedian_normalized(
            traces[cond], n_subs, from_onset=False)
        mean, sem = _group_stats(sub_arr)
        ax.plot(x_pct, mean, color=COLORS[cond], label=LABELS[cond])
        ax.fill_between(x_pct, mean - sem, mean + sem,
                        color=COLORS[cond], alpha=0.3, edgecolor='none')
    ax.set_xlabel("% movement time (from go cue)")
    ax.set_title("go-cue aligned, time-normalized")

    # ---- Panel C: onset-aligned, raw clipped ----
    ax = axes[2]
    x_time_onset = np.arange(N_CLIP_ONSET) / FS
    for cond in range(3):
        sub_arr = _subject_nanmedian_onset_clipped(
            traces[cond], n_subs, N_CLIP_ONSET)
        mean, sem = _group_stats(sub_arr)
        ax.plot(x_time_onset, mean, color=COLORS[cond], label=LABELS[cond])
        ax.fill_between(x_time_onset, mean - sem, mean + sem,
                        color=COLORS[cond], alpha=0.3, edgecolor='none')
    ax.set_xlabel("time from movement onset (s)")
    ax.set_title("onset-aligned")

    # ---- Panel D: onset-aligned, time-normalized ----
    ax = axes[3]
    for cond in range(3):
        sub_arr = _subject_nanmedian_normalized(
            traces[cond], n_subs, from_onset=True)
        mean, sem = _group_stats(sub_arr)
        ax.plot(x_pct, mean, color=COLORS[cond], label=LABELS[cond])
        ax.fill_between(x_pct, mean - sem, mean + sem,
                        color=COLORS[cond], alpha=0.3, edgecolor='none')
    ax.set_xlabel("% movement time (from onset)")
    ax.set_title("onset-aligned, time-normalized")

    # ---- shared formatting ----
    for i, ax in enumerate(axes):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(BASE_LINEWIDTH_PT)
        ax.spines['bottom'].set_linewidth(BASE_LINEWIDTH_PT)
        ax.tick_params(axis='both', which='major',
                       labelsize=BASE_FONTSIZE_PT,
                       width=BASE_LINEWIDTH_PT, length=3)
        ax.text(-0.12, 1.05, chr(65 + i), transform=ax.transAxes,
                fontsize=BASE_FONTSIZE_PT + 1, fontweight='bold',
                ha='right', va='bottom')

    axes[0].set_ylabel("velocity (screen units/frame)")
    axes[2].set_ylabel("velocity (screen units/frame)")

    axes[1].legend(frameon=False, loc='upper right')

    return fig


# =========================
# ========= MAIN ==========
# =========================
def run():
    traces = load_velocity_traces()
    fig = make_figure(traces)
    fig.savefig(str(OUT_DIR / OUT_PDF), bbox_inches=None)
    target_px = 2000
    dpi = target_px / fig.get_size_inches()[0]
    fig.savefig(str(OUT_DIR / OUT_PNG), dpi=dpi, bbox_inches=None)
    plt.show()


if __name__ == "__main__":
    run()