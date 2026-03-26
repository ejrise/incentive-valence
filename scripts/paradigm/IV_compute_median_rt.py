import glob
import os
import pickle
import numpy as np

## Enter the participant as a string below, make sure to use inverted commas, i.e.,
## 'pilot001', not pilot001. Bonus will appear in the Output below. If 4 files not 
## present for this subject, check filenames are consistent in Finder.

participant = 'fmri_pilot'
block = 0

bonus = 0
os.chdir('/Users/asap1/Desktop/IV_task_fMRI/Data')
files = glob.glob(participant+'*')
rt=[]
file_in = files[block]
with open(file_in, "rb") as fp:
    b = pickle.load(fp)
    for trial in range(len(b)-2):
        if (b[trial]["jumped_gun"]==0) & (b[trial]["outcome"]==0):
            rt.append(b[trial]["RT"])

print(np.median(np.array(rt))