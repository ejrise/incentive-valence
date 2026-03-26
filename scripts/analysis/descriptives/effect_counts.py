# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 15:57:24 2026

@author: neilm
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Count subjects showing faster (smaller) median init for
jackpot vs standard and robber vs standard.
"""
import numpy as np
import pandas as pd
from pathlib import Path

try:
    _SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    _SCRIPT_DIR = Path.cwd()

CSV_PATH = _SCRIPT_DIR / ".." / ".." / ".." / "data" / "preprocessed" / "behavioral" / "IVdata_wFSs.csv"

def run():
    df = pd.read_csv(CSV_PATH)

    # Recode cue 3 -> 0 (standard)
    df.loc[df['cue'] == 3, 'cue'] = 0

    # Drop false starts
    df = df[df['false_start'] == 0].copy()
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['init'])

    # Per-subject median init by cue
    subj = df.groupby(['sub_orig', 'cue'])['init'].median().unstack()

    n = len(subj)
    jp_faster = subj[1] < subj[0]
    rb_faster = subj[2] < subj[0]

    print(f"n = {n}")
    print(f"Jackpot faster than Standard: {jp_faster.sum()}/{n}")
    print(f"Robber  faster than Standard: {rb_faster.sum()}/{n}")

    both    = ( jp_faster &  rb_faster).sum()
    jp_only = ( jp_faster & ~rb_faster).sum()
    rb_only = (~jp_faster &  rb_faster).sum()
    neither = (~jp_faster & ~rb_faster).sum()

    print(f"\nCross-tabulation:")
    print(f"  Both faster:        {both}")
    print(f"  Jackpot only:       {jp_only}")
    print(f"  Robber only:        {rb_only}")
    print(f"  Neither:            {neither}")
    print(f"\nAny incentive effect: {both + jp_only + rb_only}/{n}")

if __name__ == "__main__":
    run()