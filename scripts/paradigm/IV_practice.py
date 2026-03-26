#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division
from psychopy import prefs
from psychopy import gui, visual, core, data, event, logging, colors
from psychopy.constants import (NOT_STARTED, STARTED, STOPPED, FINISHED)
import numpy as np
import pandas as pd
from psychopy.hardware import keyboard
from IV_functions import input_dialog, open_window, load_joystick, make_vis_stimuli, make_trialMat, first_reach, practice_home, cued_reach, delayed_reach_d, start_splash, rules_reminder
from IV_functions import ready_phase, target_onset, fore_period,  reach_phase, feedback_phase
from os import chdir
import pickle

chdir('/Users/asap1/Desktop/IV_task_fMRI')

seq=pd.read_csv('images/sequence1.csv',header=None)

par = {"expName":"IV",
    "trials":len(seq),
    "trials":100,
    "gain":1.5,
    "screen_res":(1680,1050),
    "screenW":15*2.54,
    "dist":57,
    "cue_time":0.2,
    "regular_bonus":"$0.20",
    "jackpun_bonus":"$1.60",
    "target_hold":0.8,
    "RT_crit":5,
    "feedback_time":1,
    "text_size":.05}

vis_par = {"target1xy":[-.5,.25],
    "target2xy":[.5,.25],
    "startxy":[0,-.25],
    "target_r_deg":1.2,
    "cursor_r_deg":.5,
    "joy_off":[0.00684262,0.15542522]}

expInfo = {"Participant" :"","Session" :"0", "Date":data.getDateStr()}
input_dialog(par,expInfo,visual,gui,core) #Dialog box
win,par = open_window(visual,par) #Open a window
joy = load_joystick() #Load joystick
imgComponents,cursor,vis_par,cues,feedback,bonus = make_vis_stimuli(visual,win,vis_par,par) #Make visual stimuli
trialMat,bonuses = make_trialMat(par,np,pd,par["trials"])
trial_pars = []
offset = vis_par["startxy"][1]

## First reach to the left target
img = [imgComponents[0],imgComponents[2]]
cursor = first_reach(win,img,cursor,par,vis_par,joy,core,visual,np,vis_par["target1xy"])
img = imgComponents[2]
cursor = practice_home(win,img,cursor,par,vis_par,joy,core,visual,np)

## second reach to the left target
img = [imgComponents[1],imgComponents[2]]
cursor = first_reach(win,img,cursor,par,vis_par,joy,core,visual,np,vis_par["target2xy"])
img = imgComponents[2]
cursor = practice_home(win,img,cursor,par,vis_par,joy,core,visual,np)

## cued reach to left target
cursor = cued_reach(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,cues[0],vis_par["target1xy"])
cursor = practice_home(win,imgComponents,cursor,par,vis_par,joy,core,visual,np)

## cued reach to right target
cursor = cued_reach(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,cues[0],vis_par["target2xy"])
cursor = practice_home(win,imgComponents,cursor,par,vis_par,joy,core,visual,np)

for stim_ons in [3,2,1]:
    
    # delayed cued reach to left target
    cursor = delayed_reach_d(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,cues[0],vis_par["target2xy"],3,stim_ons)
    # Return home
    cursor = practice_home(win,imgComponents,cursor,par,vis_par,joy,core,visual,np)

    # delayed cued reach to left target
    cursor = delayed_reach_d(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,cues[0],vis_par["target1xy"],3,stim_ons)
    # Return home
    cursor = practice_home(win,imgComponents,cursor,par,vis_par,joy,core,visual,np)

cursor = start_splash(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,'You will now do some practice trials. Bonuses on these trials are to teach you the rules and will not count toward your total. To begin, move cursor away from start position.')

## 10 practice trials with easier time limit
for trial in np.round(np.random.uniform(low=0,high=len(trialMat)-1,size=10)).astype(int):
    
    trial_par = {"targetxy":vis_par[trialMat.targetxy[trial]],
                "cue":trialMat.cue[trial],
                "bonus":bonuses[trialMat.cue[trial]],
                "start_hold":seq.iloc[trial,1],
                "forep":seq.iloc[trial,2],
                "jumped_gun":0}
    
    cursor,trial_par = ready_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par)
    #print(np.diff(trial_par["ready_vbl"]))
    
    cursor,trial_par = target_onset(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par,cues)
    #print(np.diff(trial_par["onset_vbl"]))
    #print(trial_par["onset_vbl"][0]-trial_par["ready_vbl"][-1])
    
    if trial_par["jumped_gun"] == 0:
        cursor,trial_par = fore_period(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par)
        #print(np.diff(trial_par["fore_vbl"]))
        #print(trial_par["fore_vbl"][0]-trial_par["onset_vbl"][-1])
    
    if trial_par["jumped_gun"] == 0:
        cursor,trial_par = reach_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par)
        #print(np.diff(trial_par["reach_vbl"]))
        #print(trial_par["reach_vbl"][0]-trial_par["fore_vbl"][-1])
    
    cursor,trial_par = feedback_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par,feedback,bonus)
    #print(np.diff(trial_par["feedb_vbl"]))
    #print(trial_par["feedb_vbl"][0]-trial_par["reach_vbl"][-1])
    
    trial_pars.append(trial_par)

## 10 practice trials with harder time limit
par["RT_crit"] = 2
for trial in np.round(np.random.uniform(low=0,high=len(trialMat)-1,size=10)).astype(int):
    
    trial_par = {"targetxy":vis_par[trialMat.targetxy[trial]],
                "cue":trialMat.cue[trial],
                "bonus":bonuses[trialMat.cue[trial]],
                "start_hold":seq.iloc[trial,1],
                "forep":seq.iloc[trial,2],
                "jumped_gun":0}
    
    cursor,trial_par = ready_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par)
    #print(np.diff(trial_par["ready_vbl"]))
    
    cursor,trial_par = target_onset(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par,cues)
    #print(np.diff(trial_par["onset_vbl"]))
    #print(trial_par["onset_vbl"][0]-trial_par["ready_vbl"][-1])
    
    if trial_par["jumped_gun"] == 0:
        cursor,trial_par = fore_period(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par)
        #print(np.diff(trial_par["fore_vbl"]))
        #print(trial_par["fore_vbl"][0]-trial_par["onset_vbl"][-1])
    
    if trial_par["jumped_gun"] == 0:
        cursor,trial_par = reach_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par)
        #print(np.diff(trial_par["reach_vbl"]))
        #print(trial_par["reach_vbl"][0]-trial_par["fore_vbl"][-1])
    
    cursor,trial_par = feedback_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par,feedback,bonus)
    #print(np.diff(trial_par["feedb_vbl"]))
    #print(trial_par["feedb_vbl"][0]-trial_par["reach_vbl"][-1])
    
    trial_pars.append(trial_par)

trial_pars.append(par)
trial_pars.append(vis_par)

import pickle
file_out="Data/"+expInfo["Participant"]+'_Session'+expInfo["Session"]+"_"+expInfo["Date"]
with open(file_out,"wb") as fp:
    pickle.dump(trial_pars, fp)

rules_reminder(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,cues,event)