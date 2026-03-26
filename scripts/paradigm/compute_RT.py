import glob
import os
import pickle
import numpy as np

subs = ['asap02','asap03','asap04','asap05','asap06','asap07','asap08','asap09','asap10','asap12','asap13','asap16','asap18','pilot001','pilot002']
os.chdir('/Users/asap1/Desktop/IV_task/Data')

rt=[]

for participant in subs:
    
    sub_rt=[]
    
    files = glob.glob(participant+'*')
    
    if np.shape(files)[0]!=4:
        print('error: 4 files not present for '+participant)
    else:
        for file_in in files:
            with open(file_in, "rb") as fp:
                b = pickle.load(fp)
                
                for trial in range(len(b)-2):
                    if b[trial]["jumped_gun"]==0:
                        if b[trial]["RT"]<b[-2]["RT_crit"]:
                            
                            sub_rt.append(b[trial]["RT"])
                            
        print(np.shape(sub_rt))
        print(np.median(sub_rt))
        rt.append(np.median(sub_rt))
print(np.mean(rt))



