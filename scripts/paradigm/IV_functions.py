def input_dialog(par,expInfo,visual,gui,core):
    #dlg window specs
    dlg_win = visual.Window([800,600],fullscr=False, screen=0, 
        winType='pyglet', allowGUI=True, allowStencil=False,
        monitor='testMonitor', color=[0,0,0], colorSpace='rgb',
        blendMode='avg', useFBO=True, units='height')
        
    #Input dialogue
    dlg = gui.DlgFromDict(dictionary=expInfo, title=par["expName"], order=["Participant","Session","Date"])
    if dlg.OK == False:
        core.quit()
        
    dlg_win.close()
    
    return expInfo

def open_window(visual,par):
    #window specs
    win = visual.Window(size=par["screen_res"],fullscr=True, screen=0, 
        winType='pyglet', allowGUI=True, allowStencil=False,
        monitor='testMonitor', color=[0,0,0], colorSpace='rgb',
        blendMode='avg', useFBO=True, units='height',checkTiming=True)
    par["ifi"] = win.monitorFramePeriod
    par["ifi"]=par["ifi"]/2
    par["feedback_time"]=par["feedback_time"]-par["ifi"]
    par["cue_time"]=par["cue_time"]-par["ifi"]
    win.mouseVisible = False
    
    return win,par

def load_joystick():
    from psychopy.hardware import joystick
    nJoys = joystick.getNumJoysticks()
    print("nJOys = ", nJoys)
    id = 0
    joy = joystick.Joystick(id)
    nAxes = joy.getNumAxes()
    
    return joy

def make_vis_stimuli(visual,win,vis_par,par):
    
    import numpy as np
    
    pix_per_deg = (np.tan(np.radians(1))*par["dist"]) * (par["screen_res"][0]/par["screenW"])
    
    H_per_deg = pix_per_deg/par["screen_res"][1]
    
    vis_par["radius"] = vis_par["target_r_deg"]*H_per_deg
    
    target1 = visual.Circle(win=win, radius=vis_par["radius"], edges=99, lineWidth=0, fillColor="white", pos=vis_par["target1xy"], size=1)
    target2 = visual.Circle(win=win, radius=vis_par["radius"], edges=99, lineWidth=0, fillColor="white", pos=vis_par["target2xy"], size=1)
    start = visual.Circle(win=win, radius=vis_par["radius"], edges=99, lineWidth=0, fillColor="white", pos=vis_par["startxy"], size=1)
    cursor = visual.Circle(win=win, radius=vis_par["cursor_r_deg"]*H_per_deg, edges=99, lineWidth=0, fillColor=[0,0,1], pos=[0,0], size=1)
    jackpot = visual.ImageStim(win=win,pos=[0,0],image="images/jackpot.png")
    punishment = visual.ImageStim(win=win,pos=[0,0],image="images/punishment.png")
    neutral1 = visual.ImageStim(win=win,pos=[0,0],image="images/neutral1.png")
    neutral2 = visual.ImageStim(win=win,pos=[0,0],image="images/neutral2.png")
    
    success = visual.TextStim(win=win,text='SUCCESS!',pos=[0,.05],color=[0,1,0],bold=True,height=par["text_size"])
    too_slow = visual.TextStim(win=win,text='TOO SLOW!',pos=[0,.05],color=[1,0,0],bold=True,height=par["text_size"])
    premature = visual.TextStim(win=win,text='MOVED TOO SOON!',pos=[0,.05],color=[1,0,0],bold=True,height=par["text_size"])
    
    bonus = visual.TextStim(win=win,text='test',pos=[0,-.05],color=[0,1,0],bold=True,height=par["text_size"])
    
    imgComponents = [target1,target2,start] #Combine all static images in a list
    cues = [neutral1,jackpot,punishment,neutral2] #And all cues in another
    feedback = [success,too_slow,premature]
    
    return imgComponents,cursor,vis_par,cues,feedback,bonus
    
def make_trialMat(par,np,pd,numTrials):
    targetxy = np.repeat("target1xy",numTrials)
    targetxy[np.random.rand(numTrials)<.5]="target2xy"
    
    from random import randint
    cue=[randint(0,3) for p in range(0,numTrials)]
    forep=[randint(1,2)-par["ifi"] for p in range(0,numTrials)]
    
    trialMat = pd.DataFrame({"targetxy":targetxy,
                            "cue":cue,
                            "forep":forep})
                           
    bonuses = ["regular_bonus","jackpun_bonus","jackpun_bonus","regular_bonus"]
    return trialMat,bonuses

def iti_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par):
    
    offset = vis_par["startxy"][1]
    
    for i in imgComponents:
        i.setAutoDraw(False)
    
    cursor.setAutoDraw(False)
    
    timer = core.CountdownTimer(2)
    continueRoutine = True
    
    iti_vbl=[]
    
    while continueRoutine:
        
        vbl = win.flip()
        iti_vbl.append(vbl)
        
        if timer.getTime()<par["ifi"]:
            continueRoutine = False
            trial_par["iti_vbl"]=iti_vbl
    
    return cursor, trial_par

def ready_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par):
    
    offset = vis_par["startxy"][1]
    
    for i in imgComponents:
        i.setAutoDraw(True)
    
    timer = core.Clock()
    timer.add(-1)
    last_state = 0
    continueRoutine = True
    
    ready_vbl=[]
    ready_cursor=[]
    
    while continueRoutine:
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
        
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        
        if ((dist_to_start<vis_par["radius"]) & (last_state==0)):
            timer = core.CountdownTimer(trial_par["start_hold"])
            last_state=1
        elif ((dist_to_start>vis_par["radius"]) & (last_state==1)):
            timer = core.Clock()
            timer.add(-1)
            last_state=0
        
        cursor.setPos(cursor_pos)
        cursor.setAutoDraw(True)
        vbl = win.flip()
        ready_vbl.append(vbl)
        ready_cursor.append(cursor_pos)
        
        if timer.getTime()<par["ifi"]:
            continueRoutine = False
            trial_par["ready_vbl"]=ready_vbl
            trial_par["ready_cursor"]=ready_cursor
    
    return cursor, trial_par

def target_onset(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par,cues):
    
    offset = vis_par["startxy"][1]
    
    for i in imgComponents:
        i.setAutoDraw(True)
    
    timer = core.Clock()
    
    continueRoutine = True
    
    onset_vbl=[]
    onset_cursor=[]
    
    while continueRoutine:
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
        
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        
        cursor.setPos(cursor_pos)
        cursor.setAutoDraw(True)
        
        cues[trial_par["cue"]].setPos(trial_par["targetxy"])
        cues[trial_par["cue"]].setAutoDraw(True)
        
        vbl = win.flip()
        onset_vbl.append(vbl)
        onset_cursor.append(cursor_pos)
        
        if dist_to_start>vis_par["radius"]:
            trial_par["jumped_gun"]=1
            continueRoutine = False
            trial_par["onset_vbl"]=onset_vbl
            trial_par["onset_cursor"]=onset_cursor
        
        if timer.getTime()>par["cue_time"]:
            cues[trial_par["cue"]].setAutoDraw(False)
            cursor.setAutoDraw(False)
            continueRoutine = False
            trial_par["onset_vbl"]=onset_vbl
            trial_par["onset_cursor"]=onset_cursor
    
    return cursor, trial_par

def fore_period(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par):
    
    offset = vis_par["startxy"][1]
    
    for i in imgComponents:
        i.setAutoDraw(True)
    
    timer = core.Clock()
    
    continueRoutine = True
    
    fore_vbl=[]
    fore_cursor=[]
    
    while continueRoutine:
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
        
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        
        vbl = win.flip()
        fore_vbl.append(vbl)
        fore_cursor.append(cursor_pos)
        
        if dist_to_start>vis_par["radius"]:
            trial_par["jumped_gun"]=1
            continueRoutine = False
            trial_par["fore_vbl"]=fore_vbl
            trial_par["fore_cursor"]=fore_cursor
        
        if timer.getTime()>trial_par["forep"]:
            continueRoutine = False
            trial_par["fore_vbl"]=fore_vbl
            trial_par["fore_cursor"]=fore_cursor
    
    return cursor, trial_par

def reach_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par):
    
    offset = vis_par["startxy"][1]
    
    for i in imgComponents:
        i.setAutoDraw(True)
    
    timer = core.Clock()
    timer.add(-1)
    last_state = 0
    continueRoutine = True
    
    reach_vbl=[]
    reach_cursor=[]
    
    while continueRoutine:
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
        
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        
        dist_to_targ = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(trial_par["targetxy"]))**2))
        
        if ((dist_to_targ<vis_par["radius"]) & (last_state==0)):
            timer = core.CountdownTimer(par["target_hold"])
            last_state=1
        elif ((dist_to_targ>vis_par["radius"]) & (last_state==1)):
            timer = core.Clock()
            timer.add(-1)
            last_state=0
        
        cursor.setPos(cursor_pos)
        cursor.setAutoDraw(True)
        
        vbl = win.flip()
        reach_vbl.append(vbl)
        reach_cursor.append(cursor_pos)
        
        if timer.getTime()<par["ifi"]:
            continueRoutine = False
            trial_par["reach_vbl"]=reach_vbl
            trial_par["reach_cursor"]=reach_cursor
            trial_par["RT"] = vbl-reach_vbl[0]
            #print(str(trial_par["RT"]))
    
    return cursor,trial_par

def feedback_phase(win,imgComponents,cursor,par,vis_par,joy,core,np,trial_par,feedback,bonus):
    
    offset = vis_par["startxy"][1]
    
    for i in imgComponents:
        i.setAutoDraw(True)
    
    timer = core.Clock()
    
    #if they jumped the gun
    if ((trial_par["jumped_gun"] == 1) & (trial_par["cue"]==2)):
        outcome = 2
        bonus.setText('SUBTRACTED FROM BONUS: '+par["jackpun_bonus"])
        bonus.setColor([1,0,0])
        cursor.setColor([1,0,0])
    
    if ((trial_par["jumped_gun"] == 1) & (trial_par["cue"]!=2)):
        outcome = 2
        bonus.setText('BONUS UNCHANGED')
        bonus.setColor([-1,-1,-1])
        cursor.setColor([1,0,0])
    
    if trial_par["jumped_gun"] == 0:
        if trial_par["RT"] < par["RT_crit"]:
            outcome = 0 #success
            if trial_par["cue"]!=2:
                bonus.setText('ADDED TO BONUS: '+par[trial_par["bonus"]])
                bonus.setColor([0,1,0])
                cursor.setColor([0,1,0])
            else:
                bonus.setText('BONUS UNCHANGED')
                bonus.setColor([-1,-1,-1])
                cursor.setColor([0,1,0])
        else:
            outcome = 1 #fail
            if trial_par["cue"]==2:
                bonus.setText('SUBTRACTED FROM BONUS: '+par[trial_par["bonus"]])
                bonus.setColor([1,0,0])
                cursor.setColor([1,0,0])
            else:
                bonus.setText('BONUS UNCHANGED')
                bonus.setColor([-1,-1,-1])
                cursor.setColor([1,0,0])
    
    trial_feedback = feedback[outcome]
    
    continueRoutine = True
    
    feedb_vbl=[]
    feedb_cursor=[]
    
    while continueRoutine:
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
        
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        
        cursor.setPos(cursor_pos)
        cursor.setAutoDraw(True)
        trial_feedback.setAutoDraw(True)
        bonus.setAutoDraw(True)
        
        vbl = win.flip()
        feedb_vbl.append(vbl)
        feedb_cursor.append(cursor_pos)
        
        if timer.getTime()>par["feedback_time"]:
            trial_feedback.setAutoDraw(False)
            bonus.setAutoDraw(False)
            cursor.setColor([0,0,1])
            continueRoutine = False
            trial_par["feedb_vbl"]=feedb_vbl
            trial_par["feedb_cursor"]=feedb_cursor
    
    return cursor, trial_par

def first_reach(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,targ):
    offset = vis_par["startxy"][1]
    home_text = visual.TextStim(win=win,text='Use joystick to move the cursor to the target above and hold it there for one second',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    move_text = visual.TextStim(win=win,text='Move to target',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    hold_text = visual.TextStim(win=win,text='Hold',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    
    timer = core.Clock()
    timer.add(-1)
    continueRoutine = True
    last_state=0
    
    while continueRoutine:
        
        for i in imgComponents:
            i.draw()
    
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
    
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        dist_to_targ = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(targ))**2))
        cursor.setPos(cursor_pos)
        cursor.draw()
        
        if (dist_to_start<vis_par["radius"]):
            last_state=0
            timer = core.Clock()
            timer.add(-1)
            home_text.draw()
        elif (dist_to_targ<vis_par["radius"]):
            if last_state==0:
                timer = core.CountdownTimer(1)
                last_state=1
            hold_text.draw()
        else:
            last_state=0
            timer = core.Clock()
            timer.add(-1)
            move_text.draw()
        
        vbl = win.flip()
        
        if timer.getTime()<0:
            continueRoutine = False
    return cursor

def practice_home(win,imgComponents,cursor,par,vis_par,joy,core,visual,np):
    
    offset = vis_par["startxy"][1]
    home_text0 = visual.TextStim(win=win,text='Success',pos=[0,.10],color=[1,1,1],bold=False,height=.03)
    home_text1 = visual.TextStim(win=win,text='Move the cursor back to the start position and hold for one second',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    hold_text = visual.TextStim(win=win,text='Hold',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    
    timer = core.Clock()
    timer.add(-1)
    continueRoutine = True
    last_state=0
    
    while continueRoutine:
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
        
        if isinstance(imgComponents,list):
            for i in imgComponents:
                i.draw()
        else:
            imgComponents.draw()
        
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        dist_to_targ = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["target1xy"]))**2))
        cursor.setPos(cursor_pos)
        cursor.draw()
        
        if (dist_to_start>vis_par["radius"]):
            last_state=0
            timer = core.Clock()
            timer.add(-1)
            home_text0.draw()
            home_text1.draw()
        else:
            if last_state==0:
                timer = core.CountdownTimer(1)
                last_state=1
            hold_text.draw()
        
        vbl = win.flip()
        
        if timer.getTime()<0:
            continueRoutine = False
    
    return cursor

def cued_reach(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,cue,targ):
    
    cue.setPos(targ)
    
    offset = vis_par["startxy"][1]
    home_text = visual.TextStim(win=win,text='Move the cursor to the target indicated by the face and hold it there for one second',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    move_text = visual.TextStim(win=win,text='Move to target',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    hold_text = visual.TextStim(win=win,text='Hold',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    
    timer = core.Clock()
    timer.add(-1)
    continueRoutine = True
    last_state=0
    
    while continueRoutine:
        
        for i in imgComponents:
            i.draw()
        
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
    
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        dist_to_targ = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(targ))**2))
        cursor.setPos(cursor_pos)
        cursor.draw()
        
        if (dist_to_start<vis_par["radius"]):
            last_state=0
            timer = core.Clock()
            timer.add(-1)
            home_text.draw()
            cue.draw()
        elif (dist_to_targ<vis_par["radius"]):
            if last_state==0:
                timer = core.CountdownTimer(1)
                last_state=1
            hold_text.draw()
        else:
            last_state=0
            timer = core.Clock()
            timer.add(-1)
            move_text.draw()
        
        vbl = win.flip()
        
        if timer.getTime()<0:
            continueRoutine = False
    return cursor

def delayed_reach(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,cue,targ,wait_period,stim_onset):
    
    offset = vis_par["startxy"][1]
    home_text = visual.TextStim(win=win,text='Wait for the face',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    cue.setPos(targ)
    x = joy.getX()
    y = joy.getY()+vis_par["joy_off"][1]
    cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
    cursor.setPos(cursor_pos)
    
    ##WAIT FOR FACE
    continueRoutine=True
    timer = core.CountdownTimer(wait_period)
    while continueRoutine:
        for i in imgComponents:
            i.draw()
        home_text.draw()
        cursor.draw()
        vbl = win.flip()
        if timer.getTime()<0:
            continueRoutine=False
    
    home_text = visual.TextStim(win=win,text='Wait for the cursor',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    
    ##FACE APPEARS
    continueRoutine=True
    timer = core.CountdownTimer(stim_onset)
    while continueRoutine:
        for i in imgComponents:
            i.draw()
        home_text.draw()
        cue.draw()
        vbl = win.flip()
        if timer.getTime()<0:
            continueRoutine=False
    
    move_text = visual.TextStim(win=win,text='Move to target',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    hold_text = visual.TextStim(win=win,text='Hold',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    
    #REACH
    timer = core.Clock()
    timer.add(-1)
    continueRoutine = True
    last_state=0
    while continueRoutine:
        
        for i in imgComponents:
            i.draw()
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
    
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        dist_to_targ = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(targ))**2))
        cursor.setPos(cursor_pos)
        cursor.draw()
        
        if (dist_to_targ<vis_par["radius"]):
            if last_state==0:
                timer = core.CountdownTimer(1)
                last_state=1
            hold_text.draw()
        else:
            last_state=0
            timer = core.Clock()
            timer.add(-1)
            move_text.draw()
        
        vbl = win.flip()
        
        if timer.getTime()<0:
            continueRoutine = False
    return cursor

def delayed_reach_d(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,cue,targ,wait_period,stim_onset):
    
    offset = vis_par["startxy"][1]
    home_text = visual.TextStim(win=win,text='Wait for the face',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    cue.setPos(targ)
    x = joy.getX()
    y = joy.getY()+vis_par["joy_off"][1]
    cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
    cursor.setPos(cursor_pos)
    
    ##WAIT FOR FACE
    continueRoutine=True
    timer = core.CountdownTimer(wait_period)
    while continueRoutine:
        for i in imgComponents:
            i.draw()
        home_text.draw()
        cursor.draw()
        vbl = win.flip()
        if timer.getTime()<0:
            continueRoutine=False
            
    
    home_text = visual.TextStim(win=win,text='Wait for the cursor',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    
    ##FACE APPEARS
    continueRoutine=True
    timer = core.CountdownTimer(stim_onset)
    while continueRoutine:
        for i in imgComponents:
            i.draw()
        home_text.draw()
        cue.draw()
        vbl = win.flip()
        if timer.getTime()<0:
            continueRoutine=False
    
    ##WAIT FOR CURSOR
    continueRoutine=True
    timer = core.CountdownTimer(stim_onset)
    while continueRoutine:
        for i in imgComponents:
            i.draw()
        home_text.draw()
        vbl = win.flip()
        if timer.getTime()<0:
            continueRoutine=False
    
    move_text = visual.TextStim(win=win,text='Move to target',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    hold_text = visual.TextStim(win=win,text='Hold',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    
    #REACH
    timer = core.Clock()
    timer.add(-1)
    continueRoutine = True
    last_state=0
    while continueRoutine:
        
        for i in imgComponents:
            i.draw()
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
    
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        dist_to_targ = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(targ))**2))
        cursor.setPos(cursor_pos)
        cursor.draw()
        
        if (dist_to_targ<vis_par["radius"]):
            if last_state==0:
                timer = core.CountdownTimer(1)
                last_state=1
            hold_text.draw()
        else:
            last_state=0
            timer = core.Clock()
            timer.add(-1)
            move_text.draw()
        
        vbl = win.flip()
        
        if timer.getTime()<0:
            continueRoutine = False
    return cursor

def start_splash(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,msg):
    
    msg0_text = visual.TextStim(win=win,text=msg,pos=[0,.10],color=[1,1,1],bold=False,height=.03)
    msg1_text = visual.TextStim(win=win,text='trials will begin when you return to start position',pos=[0,-.10],color=[1,1,1],bold=False,height=.03)
    
    offset = vis_par["startxy"][1]
    
    timer = core.Clock()
    timer.add(-1)
    continueRoutine = True
    last_state=0
    
    while continueRoutine:
        
        for i in imgComponents:
            i.draw()
    
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
    
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        cursor.setPos(cursor_pos)
        cursor.draw()
        
        vbl = win.flip()
        
        if (dist_to_start<vis_par["radius"]):
            last_state=0
            msg0_text.draw()
            msg1_text.draw()
        else:
            continueRoutine=False
    
    timer = core.Clock()
    timer.add(-1)
    continueRoutine = True
    last_state=0
    
    while continueRoutine:
        
        x = joy.getX()
        y = joy.getY()+vis_par["joy_off"][1]
        
        if isinstance(imgComponents,list):
            for i in imgComponents:
                i.draw()
        else:
            imgComponents.draw()
        
        cursor_pos =  [x*par["gain"],-y*par["gain"] + offset]
        dist_to_start = np.sqrt(np.sum(np.array(np.array(cursor_pos)-np.array(vis_par["startxy"]))**2))
        cursor.setPos(cursor_pos)
        cursor.draw()
        
        vbl = win.flip()
        
        if (dist_to_start>vis_par["radius"]):
            last_state=0
            timer = core.Clock()
            timer.add(-1)
            msg1_text.draw()
        else:
            continueRoutine = False
    
    return cursor

def rules_reminder(win,imgComponents,cursor,par,vis_par,joy,core,visual,np,cues,event):
    
    continueRoutine=True
    
    jack_x=-0.5
    pun_x=0.5
    norm_x=0
    
    texty1 = -.4
    texty2 = -.45
    
    msg0_text = visual.TextStim(win=win,text='Training complete',pos=[0,.20],color=[1,1,1],bold=False,height=.03)
    msg1_text = visual.TextStim(win=win,text='Different faces will impact your bonus differently. Review reward rules below',pos=[0,.10],color=[1,1,1],bold=False,height=.03)
    msg2_text = visual.TextStim(win=win,text='Ask experimenter any questions now',pos=[0,0],color=[1,1,1],bold=False,height=.03)
    
    bonus0a_text = visual.TextStim(win=win,text='Success: +$1.60',pos=[jack_x,texty1],color=[0,1,0],bold=True,height=.03)
    bonus0b_text = visual.TextStim(win=win,text='Too slow: no change',pos=[jack_x,texty2],color=[-1,-1,-1],bold=True,height=.03)
    
    bonus1a_text = visual.TextStim(win=win,text='Success: +$0.20',pos=[norm_x,texty1],color=[0,1,0],bold=True,height=.03)
    bonus1b_text = visual.TextStim(win=win,text='Too slow: no change',pos=[norm_x,texty2],color=[-1,-1,-1],bold=True,height=.03)
    
    bonus2a_text = visual.TextStim(win=win,text='Success: no change',pos=[pun_x,texty1],color=[-1,-1,-1],bold=True,height=.03)
    bonus2b_text = visual.TextStim(win=win,text='Too slow: -$1.60',pos=[pun_x,texty2],color=[1,0,0],bold=True,height=.03)
    
    bonus_texts = [bonus0a_text,bonus0b_text,bonus1a_text,bonus1b_text,bonus2a_text,bonus2b_text]
    
    for i in imgComponents:
        i.setAutoDraw(False)
    cursor.setAutoDraw(False)
    
    while continueRoutine:
        
        vbl = win.flip()
        
        cues[0].setPos([norm_x-.12,-.25])
        cues[3].setPos([norm_x+.12,-.25])
        cues[1].setPos([jack_x,-.25])
        cues[2].setPos([pun_x,-.25])
        
        cues[0].setSize([.25,.25])
        cues[3].setSize([.25,.25])
        cues[1].setSize([.25,.25])
        cues[2].setSize([.25,.25])
        
        for i in cues:
            i.draw()
            
        for i in bonus_texts:
            i.draw()
        
        msg0_text.draw()
        msg1_text.draw()
        msg2_text.draw()
        
        key = event.getKeys()
        
        if any(key):
            continueRoutine=False

def bonus_screen(win,par,vis_par,core,visual,np,event,expInfo,imgComponents,cursor):
    import glob
    import os
    import pickle
    bonus = 0
    os.chdir('/Users/asap1/Desktop/IV_task/Data')
    files = glob.glob(expInfo["Participant"]+'*')
    for file_in in files:
        with open(file_in, "rb") as fp:
            b = pickle.load(fp)
            for trial in range(len(b)-2):
                if b[trial]["jumped_gun"]==0:
                    
                    if ((b[trial]["cue"] == 0) | (b[trial]["cue"] == 3)):
                        if b[trial]["RT"]<par["RT_crit"]:
                            bonus = bonus + 0.10
                            
                    if (b[trial]["cue"] == 1):
                        if b[trial]["RT"]<par["RT_crit"]:
                            bonus = bonus + 0.80
                            
                    if (b[trial]["cue"] == 2):
                        if b[trial]["RT"]>par["RT_crit"]:
                            bonus = bonus - 0.80
    
    msg0_text = visual.TextStim(win=win,text='Experiment finished!',pos=[0,.10],color=[1,1,1],bold=False,height=.03)
    
    bonus = np.round(bonus,decimals=2)
    
    if np.shape(files)[0]==4:
        msg1_text = visual.TextStim(win=win,text='You earned a bonus of $'+str(bonus),pos=[0,.0],color=[1,1,1],bold=False,height=.03)
    else:
        msg1_text = visual.TextStim(win=win,text='The experimenter will calculate your bonus',pos=[0,.0],color=[1,1,1],bold=False,height=.03)
    
    msg0_text.draw()
    msg1_text.draw()
    
    for i in imgComponents:
        i.setAutoDraw(False)
    cursor.setAutoDraw(False)
    
    vbl = win.flip()
    
    continueRoutine=True
    while continueRoutine:
        key = event.getKeys()
        if any(key):
            continueRoutine=False

def get_serial_port():
    import glob
    files = glob.glob("/dev/tty.*")
    addr = [v for v in files if "serial" in v]
    if len(addr)==1:
        return(addr)

def wait4tr_start(serial_port,core):
    import serial
    ser = serial.Serial(serial_port, 19200, stopbits=1)
    x = ser.read()
    print(x)
    first_tr = core.getTime()
    ser.close()
    return(first_tr)

def config_eyetracker(pylink,expInfo,EyeLinkCoreGraphicsPsychoPy,win,visual,path,event):
    el_tracker = pylink.EyeLink("100.1.1.1")
    edf_file=expInfo["Participant"]+'_'+expInfo["Session"]+".EDF"
    scn_width, scn_height = win.size
    el_coords = "screen_pixel_coords = 0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendCommand(el_coords)
    dv_coords = "DISPLAY_COORDS  0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendMessage(dv_coords)
    el_tracker.sendCommand("calibration_type = HV5")
    genv = EyeLinkCoreGraphicsPsychoPy(el_tracker,win)
    print(genv)
    fore_col = (-1,-1,-1)
    back_col = win.color
    genv.setCalibrationColors(fore_col,back_col)
    genv.setTargetType('picture')
    genv.setPictureTarget(path.join('images', 'fixTarget.bmp'))
    pylink.openGraphicsEx(genv)
    
    task_msg = 'Next we will start calibration for the eye tracker. Please make eye movements with the cross displayed on the screen'
    task_msg = task_msg + '\nNow, press ENTER twice to calibrate tracker'
    
    msg = visual.TextStim(win, task_msg,
        color=genv.getForegroundColor(),wrapWidth=1680/2)
    win.flip()
    msg.draw()
    win.flip()
    event.waitKeys()
    
    el_tracker.doTrackerSetup()
    el_tracker.exitCalibration()
    
    return el_tracker,edf_file

def find_pupil(pylink,expInfo,EyeLinkCoreGraphicsPsychoPy,win,visual,path,event):
    el_tracker = pylink.EyeLink("100.1.1.1")
    scn_width, scn_height = win.size
    el_coords = "screen_pixel_coords = 0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendCommand(el_coords)
    dv_coords = "DISPLAY_COORDS  0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendMessage(dv_coords)
    el_tracker.sendCommand("calibration_type = HV5")
    genv = EyeLinkCoreGraphicsPsychoPy(el_tracker,win)
    print(genv)
    fore_col = (-1,-1,-1)
    back_col = win.color
    genv.setCalibrationColors(fore_col,back_col)
    genv.setTargetType('picture')
    genv.setPictureTarget(path.join('images', 'fixTarget.bmp'))
    pylink.openGraphicsEx(genv)
    
    task_msg = 'Next we will start calibration for the eye tracker. Please make eye movements with the cross displayed on the screen'
    task_msg = task_msg + '\nNow, press ENTER twice to calibrate tracker'
    
    msg = visual.TextStim(win, task_msg,
        color=genv.getForegroundColor(),wrapWidth=1680/2)
    win.flip()
    msg.draw()
    win.flip()
    event.waitKeys()
    
    el_tracker.doTrackerSetup()
    el_tracker.exitCalibration()
    
    return el_tracker