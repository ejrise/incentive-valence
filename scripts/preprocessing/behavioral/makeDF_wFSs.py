import glob
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import signal
from scipy.interpolate import interp1d
from pathlib import Path

subs=['301', '303', '304', '306', '307', '308', '309', '310', '311', '312', '313', '314', '315', '316', '317', '318', '319', '320', '321', '322', '323', '324', '325', '328', '330', '331', '332', '333', '335', '336', '337', '338', '339', '340', '341', '342', '343', '344', '345', '346', '347', '348', '349', '350', '351', '353', '354', '355', '356', '357', '358', '360', '361', '362', '364', '365', '366', '367', '368', '369', '370', '371', '372', '373', '374', '376', '377', '379']

data_dir = Path.cwd().parents[2] / "data" / "raw" / "behavioral" / "fmri_task"

# ---- SEQUENCE FILE ----
# Col 1: cue type, Col 2: pre-instruction wait (1 or 2 s), Col 3: pre-go hold (1-4 s)
# Same sequence for all subjects, all runs
SEQ_PATH = data_dir / "sequence1.csv"
seq = np.loadtxt(str(SEQ_PATH), delimiter=',', dtype=int)

sub=[]
sub_orig=[]
rt=[]
cue=[]
outcome=[]
crit=[]
init=[]
maxvel=[]
maxvelt=[]
maxacc=[]
maxacct=[]
acctrace=[]
veltrace=[]
init_x=[]
init_y=[]
init_dist=[]
quartacct_g=[]
quartacct_i=[]
post_error=[]
post_false_start=[]
wait=[]       # RENAMED from hold: this is the pre-instruction foreperiod (1 or 2 s)
hold=[]       # NEW: actual pre-go-cue hold period, binarized (1,2 = Short/False; 3,4 = Long/True)
run=[]
cue_times = []
reach_times = []
decel_times = []
reach_duration = []
decel_duration = []

XY = []
D = []
V = []
T = []

false_start = []
                        
for ind,participant in enumerate(subs):
    
    files = sorted(glob.glob(str(data_dir / (participant + '*'))))
    
    if np.shape(files)[0]!=3:
        print('error: 3 files not present for '+participant)
    else:
        for file_no,file_in in enumerate(files):
            print(f"  sub={participant}  run={file_no+1}  file={file_in}")
            with open(file_in, "rb") as fp:
                b = pickle.load(fp)
                
                # Verify trial count matches sequence
                n_trials = len(b) - 2
                assert n_trials == len(seq), \
                    f"Trial count mismatch: sub {participant} run {file_no+1}: " \
                    f"{n_trials} trials vs {len(seq)} in sequence"
                
                for trial in range(n_trials):
                    
                    sub.append(ind)
                    sub_orig.append(int(participant))
                    crit.append(b[-2]["RT_crit"])
                    run.append(file_no+1)
                    cue.append(b[trial]["cue"])
                    
                    # Pre-instruction wait period (was previously called "hold")
                    wait.append(b[trial]["start_hold"])
                    
                    # Verify sequence alignment: col 2 should match start_hold
                    assert b[trial]["start_hold"] == seq[trial, 1], \
                        f"Sequence mismatch: sub {participant} run {file_no+1} trial {trial}: " \
                        f"start_hold={b[trial]['start_hold']} != seq col2={seq[trial, 1]}"
                    
                    # Actual hold period from sequence col 3, binarized
                    # 1 or 2 s = Short (False), 3 or 4 s = Long (True)
                    hold.append(seq[trial, 2] >= 3)
                    
                    cue_times.append(b[trial]['onset_vbl'][0]-b[-2]['first_tr'])
                    
                    #trial history (if not first trial)
                    #setting this up to contrast only:
                    #post_error v post_correct
                    #post_false_start v post_correct
                    #i.e., same baseline
                    if trial>0:
                        #previous trial jumped the gun, nan for post_error
                        if b[trial-1]["jumped_gun"]==1:
                            post_false_start.append(1)
                            post_error.append(np.nan)
                        else:
                            #previous trial was correct
                            if b[trial-1]["RT"]<b[-2]["RT_crit"]:
                                post_error.append(0)
                                post_false_start.append(0)
                            else:
                                #previous trial was error, nan for jumped_the gun
                                post_error.append(1)
                                post_false_start.append(np.nan)
                    else:
                        post_false_start.append(np.nan)
                        post_error.append(np.nan)
                    
                    #If the jumped the gun we don't care about their data for that trial
                    #outcome: 0 (jumped gun), 1 (correct), 2 (too slow)
                    if b[trial]["jumped_gun"]==1:
                        false_start.append(1)
                        rt.append(np.nan)
                        outcome.append(0)
                        init.append(np.nan)
                        maxvel.append(np.nan)
                        maxacc.append(np.nan)
                        maxvelt.append(np.nan)
                        maxacct.append(np.nan)
                        veltrace.append(np.repeat(np.nan,50))
                        acctrace.append(np.repeat(np.nan,50))
                        init_x.append(np.nan)
                        init_y.append(np.nan)
                        init_dist.append(np.nan)
                        quartacct_g.append(np.nan)
                        quartacct_i.append(np.nan)
                        reach_times.append(np.nan)
                        reach_duration.append(np.nan)
                        decel_duration.append(np.nan)
                        decel_times.append(np.nan)
                    else:
                        false_start.append(0)
                        rt.append(b[trial]["RT"])
                        reach_times.append(b[trial]['reach_vbl'][0]-b[-2]['first_tr'])
                        #outcome; 1=success, 2=fail (too slow)
                        if b[trial]["RT"]<b[-2]["RT_crit"]:
                            outcome.append(1)
                        else:
                            outcome.append(2)
                            
                        #NEW code for RT investigation
                        xy=np.vstack(b[trial]["reach_cursor"])
                        XY.append(xy)
                        xy_d=np.sqrt(np.sum(np.diff(xy,axis=0)**2,axis=1))
                        t = b[trial]["reach_vbl"][1:]
                        t_new = np.linspace(t[0], t[-1], 1000)
                        f = interp1d(t, xy_d, kind='linear')
                        xy_di = f(t_new)
                        D.append(xy_di)
                        T.append(t_new)
                        t0=t_new-t_new[0]
                        init.append(t0[np.argmax(xy_di >= .01)])
                        
                        #0th derivative, displacement of reach                            
                        d=np.sqrt(np.sum((np.array(b[trial]["reach_cursor"])-np.array(b[-1]["startxy"]))**2,axis=1))
                        #1st derivative, velocity of reach
                        v=np.diff(d)
                        #2nd derivative, acceleration of reach
                        a=np.diff(v)
                        
                        #"init" is a crude movement onset variable, i.e., at what point did the cursor leave the starting position
                        # dist_test = d - b[-1]["radius"]
                        # init_ind = np.where(dist_test>0)[0][0]
                        # init.append(b[trial]["reach_vbl"][init_ind]-b[trial]["reach_vbl"][0])
                        
                        #max velocity and max acceleration
                        maxvel.append(np.max(v))
                        maxacc.append(np.max(a))
                        
                        #time of max velocity and max acceleration
                        max_vel_ind= np.where(v==np.max(v))[0][0]-1
                        max_acc_ind= np.where(a==np.max(a))[0][0]-2
                        maxvelt.append(b[trial]["reach_vbl"][max_vel_ind]-b[trial]["reach_vbl"][0])
                        maxacct.append(b[trial]["reach_vbl"][max_acc_ind]-b[trial]["reach_vbl"][0])
                        
                        #to make averagable plottable traces (given they are all different lengths)
                        #just taking the first 50 elements
                        ds_trace = np.diff(d[0:51])
                        veltrace.append(ds_trace)
                        acctrace.append(a[0:50])
                        
                        #starting position in spatial terms, i.e., where were they at the very beginning of trial
                        #can test if they drifted during the foreperiod, for e.g.
                        init_x.append(b[trial]["reach_cursor"][0][0])
                        init_y.append(b[trial]["reach_cursor"][0][1])
                        
                        #starting position in terms of distance from target, same idea
                        init_dist.append(np.sqrt(np.sum((np.array(b[trial]["reach_cursor"][0])-np.array(b[trial]["targetxy"]))**2)))
                        
                        #a slightly more robust measure of onset. in another model I figured out that 25% of the group
                        #accleeration was 0.023 units, so take the time on each trial to reach that acceleration
                        group_acc_ind = np.where(np.diff(np.diff(d))>=0.023)[0]
                        if group_acc_ind.any():
                            quartacct_g.append(b[trial]["reach_vbl"][group_acc_ind[0]-2]-b[trial]["reach_vbl"][0])
                        else:
                            quartacct_g.append(np.nan)
                        
                        #this is the same idea, but using a criterion that varies trial-by-trial, i.e., the time taken 
                        #to reach 1/4 the max acceleration as defined on that trial 
                        sorted_accs = -np.sort(-np.array(np.diff(np.diff(d))))
                        indiv_acc_thresh = sorted_accs[np.round(len(sorted_accs[sorted_accs>0])/4).astype(int)]
                        indiv_acc_ind = np.where(np.diff(np.diff(d))>indiv_acc_thresh)[0][0]                        
                        quartacct_i.append(b[trial]["reach_vbl"][indiv_acc_ind-2]-b[trial]["reach_vbl"][0])
                        
                        decel_times.append(b[trial]['reach_vbl'][max_acc_ind]-b[-2]['first_tr'])
                        reach_duration.append(b[trial]["reach_vbl"][max_acc_ind]-b[trial]["reach_vbl"][0])
                        decel_duration.append(b[trial]['reach_vbl'][-1]-b[trial]['reach_vbl'][max_acc_ind])
                        

# os.chdir(cdtmp)  # uncomment if running in original environment

#make a pandas dataframe and save to csv
pd.DataFrame({'sub':sub,
              'sub_orig':sub_orig,
              'run':run,
              'cue_t':cue_times,
              'reach_t':reach_times,
              'decel_t':decel_times,
              'decel_duration':decel_duration,
              'reach_duration':reach_duration,
              'crit':crit,
              'cue':cue,
              'outcome':outcome,
              'rt':rt,
              'init':init,
              'false_start':false_start,
              'maxvel':maxvel,
              'maxacc':maxacc,
              'maxvelt':maxvelt,
              'maxacct':maxacct,
              'init_x':init_x,
              'init_y':init_y,
              'init_dist':init_dist,
              'quartacct_g':quartacct_g,
              'quartacct_i':quartacct_i,
              'post_error':post_error,
              'post_false_start':post_false_start,
              'wait':wait,
              'hold':hold}).to_csv('IVdata_wFSs.csv',index=False)