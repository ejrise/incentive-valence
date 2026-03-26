#!/usr/bin/env python
# -*- coding: utf-8 -*- bonus

from __future__ import absolute_import, division
from psychopy import prefs
from psychopy import gui, visual, core, data, event, logging, colors
from psychopy.constants import (NOT_STARTED, STARTED, STOPPED, FINISHED)
import numpy as np
import pandas as pd
from psychopy.hardware import keyboard
from IV_functions import (input_dialog, open_window, load_joystick, make_vis_stimuli, find_pupil,
                            make_trialMat, ready_phase, target_onset, fore_period, reach_phase, feedback_phase,
                            start_splash, bonus_screen,iti_phase, get_serial_port, wait4tr_start, config_eyetracker)
from os import chdir, path
import pickle
import pylink
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

chdir('/Users/asap1/Desktop/IV_task_fMRI')

par = {"expName":"IV",
    "screen_res":(1680,1050),
    "screenW":15*2.54,
    "feedback_time":1,
    "cue_time":0.2,
    "dist":57}

expInfo=1

win,par = open_window(visual,par) #Open a window
el_tracker = find_pupil(pylink,expInfo,EyeLinkCoreGraphicsPsychoPy,win,visual,path,event)
el_tracker.close()
