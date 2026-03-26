import glob
import os
import pickle
import numpy as np

## Enter the participant as a string below, make sure to use inverted commas, i.e.,
## 'pilot001', not pilot001. Bonus will appear in the Output below. If 4 files not 
## present for this subject, check filenames are consistent in Finder.

participant = '356'

bonus = 0
os.chdir('/Users/asap1/Desktop/IV_task_fMRI/Data')
files = glob.glob(participant+'*')

files = [f for f in files if "Session0" not in f]

for file_in in files:
    #print(file_in)
    with open(file_in, "rb") as fp:
        b = pickle.load(fp)
    #print(b[-2]["RT_crit"])
    for trial in range(len(b)-2):
        if b[trial]["jumped_gun"]==0:
            
            if ((b[trial]["cue"] == 0) | (b[trial]["cue"] == 3)):
                if b[trial]["RT"]<b[-2]["RT_crit"]:
                    bonus = bonus + 0.20
                    
            if (b[trial]["cue"] == 1):
                if b[trial]["RT"]<b[-2]["RT_crit"]:
                    bonus = bonus + 1.60
                    
            if (b[trial]["cue"] == 2):
                if b[trial]["RT"]>b[-2]["RT_crit"]:
                    bonus = bonus - 1.6
#print('bonus: $'+str(bonus))

bonus = np.round(bonus,decimals=2)

if np.shape(files)[0]!=3:
    print('error: 3 files not present for this participant')
else:
    print('bonus: $'+str(bonus))