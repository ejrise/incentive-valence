#!/usr/bin/env python
# -*- coding: utf-8 -*- bonus

from __future__ import absolute_import, division
from psychopy import prefs
from psychopy import gui, visual, core, data, event, logging, colors
from psychopy.constants import (NOT_STARTED, STARTED, STOPPED, FINISHED)
import numpy as np
import pandas as pd
from psychopy.hardware import keyboard
from IV_functions import (input_dialog, open_window, load_joystick, make_vis_stimuli,
                            make_trialMat, ready_phase, target_onset, fore_period, reach_phase, feedback_phase,
                            start_splash, bonus_screen,iti_phase, get_serial_port, wait4tr_start, config_eyetracker)
from os import chdir, path
import pickle
import pylink
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

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
    "RT_crit":1.87,
    "feedback_time":1,
    "text_size":.05}

vis_par = {"target1xy":[-.5,.25],
    "target2xy":[.5,.25],
    "startxy":[0,-.25],
    "target_r_deg":1.2,
    "cursor_r_deg":.5,
    "joy_off":[0.00684262,0.15542522]}

expInfo = {"Participant" :"","Session" :"", "Date":data.getDateStr()}
input_dialog(par,expInfo,visual,gui,core) #Dialog box
win,par = open_window(visual,par) #Open a window

el_tracker,edf_file = config_eyetracker(pylink,expInfo,EyeLinkCoreGraphicsPsychoPy,win,visual,path,event)

el_tracker.openDataFile(edf_file)
el_tracker.startRecording(1, 1, 1, 1)

##WILL NOW WAIT FOR SCANNER TRIGGER

serial_port = get_serial_port()
first_tr = wait4tr_start(serial_port[0],core)
par["first_tr"]=first_tr

joy = load_joystick() #Load joystick

imgComponents,cursor,vis_par,cues,feedback,bonus = make_vis_stimuli(visual,win,vis_par,par) #Make visual stimuli

trialMat,bonuses = make_trialMat(par,np,pd,par["trials"])

trial_pars = []

cursor = start_splash(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,'to begin, move cursor away from start position')

for trial in range(0,par["trials"]):
    
    trial_par = {"targetxy":vis_par[trialMat.targetxy[trial]],
                "cue":seq.iloc[trial,0]-1,
                "bonus":bonuses[seq.iloc[trial,0]-1],
                "start_hold":seq.iloc[trial,1],
                "forep":seq.iloc[trial,2],
                "jumped_gun":0}
    
    cursor,trial_par = iti_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par)
    
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

if expInfo["Session"]=='4':
    bonus_screen(win,par,vis_par,core,visual,np,event,expInfo,imgComponents,cursor)

local_edf='/Users/asap1/Desktop/IV_task_fMRI/eyeData/'+edf_file
el_tracker.receiveDataFile(edf_file, local_edf)
el_tracker.closeDataFile()
el_tracker.stopRecording()
el_tracker.close()
