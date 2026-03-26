#!/usr/bin/env python
# coding: utf-8

import numpy as np
import json
from pprint import pprint
from scipy.stats import rankdata
import sys
import os
import glob

dir="/path/to/sub/folders/"
subjects = ["sub-01", "sub-02", etc]

for sub in subjects:
    outdir1=os.path.join(dir, sub)
    outdir=os.path.join(outdir1,"slicetime")
    pprint(outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    currfn = glob.glob(outdir1 + "/func/*_task-rest_echo-1_bold.json") #make sure this json is correct for all subs 
    currfn=currfn[0]
    print(currfn)
    data = json.load(open(currfn))
    pprint(data)
    sliceTimes=data['SliceTiming']
    sliceOrder=rankdata(sliceTimes).astype(int)
    fn=outdir + '/slicetimeorder.txt'
    np.savetxt(fn,sliceOrder.astype(int),fmt='%i')
