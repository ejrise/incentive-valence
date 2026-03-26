import pylink
el_tracker = pylink.EyeLink("100.1.1.1")
el_tracker.stopRecording()
el_tracker.close()