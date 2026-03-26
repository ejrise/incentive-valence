#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 16:54:06 2022

@author: nmd
"""

import glob
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import signal
from pathlib import Path

try:
    _SCRIPT_DIR = Path(__file__).resolve().parent
except NameError:
    _SCRIPT_DIR = Path.cwd()

_REPO_ROOT = (_SCRIPT_DIR / ".." / ".." / ".." / "..").resolve()

df = pd.read_csv(_REPO_ROOT / "data" / "preprocessed" / "behavioral" / "IVdata_wFSs.csv")

df.loc[df.cue==3,'cue']=0
#df = df[df['cue_cont'].notna() & (df['cue_cont'] != 0)]
#df = df[df['reach_cont'].notna() & (df['reach_cont'] != 0)]
df = df[df['init'].notna() & (df['init'] != 0)]
df = df[df['maxvel'].notna() & (df['maxvel'] != 0)]

df['short']=((df.reach_t-df.cue_t)<1.5).astype(int)
df['hold_time']=(df.reach_t-df.cue_t)
df['reach_onset']=df.reach_t + df.init
df['RT']=df.init.values


#adjust RT to account for latency differences with short and long holds. each RT is now expressed as a delta from the hold-lengh-specific median
def subtract_median(group):
    # Calculate the median RT for the group
    median_RT = group['RT'].median()
    # Subtract the median RT from each RT in the group
    group['adj_RT'] = group['RT'] - median_RT
    return group
# Group the data by 'sub_orig', 'run', 'short', and apply the custom function
df = df.groupby(['sub_orig', 'run', 'short']).apply(subtract_median)

def logn(data):
    min_value = np.min(data) 
    shift = -min_value + 1 if min_value < 0 else 0
    transformed_data = np.log(data + shift + 1)
    return transformed_data


def make_output_dir(dirpath):
    from os.path import abspath,isdir
    from os import makedirs
    dirpath0 = abspath(dirpath)

    # Check if directory already exists
    if not isdir(dirpath0):
        makedirs(dirpath0)
        
def demean(x):
    y=x-x.mean()
    return y

def make_event_file(times,durations,heights,file_out,out_dir,run):
    out_string = out_dir + '/run' +str(run)+'_'+file_out+'.txt'
    out_data = np.array([times,durations,heights]).T
    dur_form = '%i'
    hei_form = '%i'
    if np.mean(durations==1)!=1:
        dur_form = '%1.4f'
    if np.mean(heights==1)!=1:
        hei_form = '%1.4f'
    out_form = '%1.4f '+dur_form+' '+hei_form
    np.savetxt(out_string, out_data, fmt=out_form,delimiter=' ')

def check_array_for_nan_inf(arr, message):
    if np.isnan(arr).any() or np.isinf(arr).any():
        print(message)

subs = np.unique(df.sub_orig)          
            
for e in [0]:
    
    for ind,participant in enumerate(subs):
        
        out_dir = str(_SCRIPT_DIR / str(participant))
        make_output_dir(out_dir)
        
        L2_RT = []
        #L2_RT2 = []
        
        for run in [1,2,3]:
            
            run_df = df.loc[(df.sub_orig==participant)&(df.run==run)].reset_index(drop=True)
            
            for cue in [0,1,2]:
                
                n_trials = np.sum(run_df.cue==cue)
                
                vigor = run_df.loc[run_df.cue==cue,'init'].values
                stick_height = np.ones(n_trials)
                stick_width = np.ones(n_trials)*.1
                inst_cues = run_df.loc[run_df.cue==cue,'cue_t']
                go_cues = run_df.loc[run_df.cue==cue,'reach_t']
                
                check_array_for_nan_inf(inst_cues,'weird no. in inst cues')
                check_array_for_nan_inf(go_cues,'weird no. in go cues')
                
                make_event_file(inst_cues,stick_width,stick_height,'cue'+str(cue),out_dir,run)#inst cue, activation
                make_event_file(go_cues,vigor,stick_height,'RT'+str(cue),out_dir,run)#go cue, dur
            
            n_trials = len(run_df)
            stick_height = np.ones(n_trials)
            stick_width = np.ones(n_trials)*.1    
                
            go_cues = run_df['reach_t']
            make_event_file(go_cues,stick_width,stick_height,'go',out_dir,run)#inst cue, activation
            
            reach_times = run_df['reach_onset']
            reach_durations = run_df['rt'].values-run_df['RT'].values
            check_array_for_nan_inf(reach_times,'weird no. in cue_times')
            make_event_file(reach_times,reach_durations,np.ones(len(reach_times)),'reach',out_dir,run)
            
            hold_times = run_df['cue_t']+.200
            hold_durations = run_df['hold_time'].values-.200
            check_array_for_nan_inf(hold_times,'weird no. in cue_times')
            make_event_file(hold_times,hold_durations,np.ones(len(hold_times)),'hold',out_dir,run)