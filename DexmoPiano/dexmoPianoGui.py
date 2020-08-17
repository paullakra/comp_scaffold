from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import subprocess
import shutil
import time
import os

import dexmoOutput
import fileIO
import midiGen
from optionsWindow import optionsWindowClass
import threadHandler


# directory/filename strings
outputDir = './output/'
tempDir = './output/temp/'
inputMidiStrs = [tempDir + 'output.mid', tempDir + 'output-m.mid']
outputLyStr = tempDir + 'output-midi.ly'
outputPngStr = tempDir + 'output-midi.png'

GuidanceModeList = ["None", "At every note", "At every note (note C-G)", "Individual"]
guidanceMode = "At every note"
maxNotePerBar = 1
numberOfBars = 5
bpm = 120
noteValuesList = [1, 1/2, 1/4, 1/8]
pitchesList = [60, 62]
twoHandsBool = False
#outFiles = [inputMidiStr, outputSubdir + 'output-m.mid']

errors = []
changetask = []

midiSaved = False
currentMidi = None

# starts only metronome output and haptic impulse from dexmo for every note
def startTask():
    global currentMidi, midiSaved, errors

    timestr = getCurrentTimestamp()

    # use MIDI file with metronome staff
    targetNotes, actualNotes, errorvalue = threadHandler.startThreads(inputMidiStrs[1], guidanceMode)

    if not midiSaved:
        saveMidiAndXML(targetNotes)
        midiSaved = True

    # create entry containing actual notes in XML
    fileIO.createTrialEntry(outputDir, currentMidi, timestr, guidanceMode, actualNotes)
    ###TODO: remove (testing)
    fileIO.printXML(outputDir + currentMidi + ".xml", True)


    #errorvalue = threadHandler.get_errors()
    errors.append(abs(errorvalue))
    add_error_plot()

# starts Demo with sound output and haptic impulse from dexmo for every note
def startDemo():
    # use MIDI file with metronome staff
    dexmoOutput.play_demo(inputMidiStrs[1], guidanceMode)

# save midi and XML file to output folder
def saveMidiAndXML(targetNotes):
    global currentMidi

    timestr = getCurrentTimestamp()

    # MIDI
    print("\nMIDI SAVED:", timestr)    ###TODO: Delete
    currentMidi = timestr
    shutil.move(inputMidiStrs[0], outputDir + timestr + '.mid')

    # XML
    currOptions = [bpm, numberOfBars, maxNotePerBar, noteValuesList, pitchesList, twoHandsBool]
    fileIO.createXML(outputDir, timestr, currOptions, targetNotes)
    

def getCurrentTimestamp():
    return time.strftime("%Y%m%d-%H%M%S")

def getTimeSortedMidiFiles():
    ll=os.listdir(outputDir)
    files=[x.split('.')[0] for x in ll if '.mid' in x]
    for i in files:
        i = time.strftime(i)
    files.sort()
    return files

# generate new midiFile and Notesheet and displays it
# dont generate new task if user opened a midi file
def nextTask(userSelectedTask=False, userSelectedLocation=inputMidiStrs[0]):
    global midiSaved, currentMidi
    if userSelectedTask == False:
        midiGen.generateMidi(bpm=bpm,
                             noteValues=noteValuesList,
                             notesPerBar=list(range(1, maxNotePerBar + 1)),
                             noOfBars=numberOfBars,
                             pitches=pitchesList,
                             twoHands=twoHandsBool,
                             outFiles=inputMidiStrs)

        subprocess.run(['midi2ly', inputMidiStrs[0], '--output=' + outputLyStr],
                       stderr=subprocess.DEVNULL)
        currentMidi = None
        midiSaved = False

    else:
        subprocess.run(['midi2ly', userSelectedLocation, '--output=' + outputLyStr],
                       stderr=subprocess.DEVNULL)

    subprocess.run(['lilypond', '--png', '-o', tempDir, outputLyStr],
                   stderr=subprocess.DEVNULL)
    clearFrame()
    load_notesheet(outputPngStr)

    check_dexmo_connected(mainWindow=True)
    load_taskButtons()

    # if task is changed remember trial to show in visualisation
    if errors:
        changetask.append(len(errors))

    add_error_plot()

# load next midi task again
def nextSavedTask(goToTask=False):
    global midiSaved, currentMidi, errors, changetask
    if currentMidi == None:
        return False

    files = getTimeSortedMidiFiles()
    # if actual is already the newest or there are no midis there is no next task
    if len(files) < 1 or (files.index(currentMidi)+1)  == len(files):
        return False

    newMidi = files[files.index(currentMidi)+1]

    if (goToTask == True):
        #TODO: delete? and add errors from xml in GUI
        errors = []
        changetask = []

        midiSaved = True
        currentMidi = newMidi
        nextTask(userSelectedTask=True,userSelectedLocation= outputDir + newMidi + '.mid')

# load previous midi task again
def previousTask(goToTask= False):
    global midiSaved, currentMidi, errors, changetask

    files = getTimeSortedMidiFiles()
    # if there are no midi files return false
    if len(files) < 1:
        return False

    # if actual is already the oldest there is no previous task
    if(currentMidi != None):
        if files.index(currentMidi) == 0:
            return False

    # if actual task is already saved, use second newest to go back
    if midiSaved:
        newMidi = files[files.index(currentMidi) -1]
    else:
        newMidi = files[len(files) -1]

    if (goToTask == True):
        #TODO: delete? and add errors from xml in GUI
        errors = []
        changetask = []

        midiSaved = True
        currentMidi = newMidi
        nextTask(userSelectedTask=True,userSelectedLocation= outputDir + newMidi + '.mid')

# check if dexmo is connected and change possible guidance modes
def check_dexmo_connected(mainWindow):
    #TODO: Why is dexmo_port not declared global here?
    if (dexmo_port.get() == "None"):
        global GuidanceModeList, guidanceMode
        GuidanceModeList = ["None"]
        guidanceMode = "None"
        if(mainWindow):
            add_Dexmo_Warning()

# loads notesheet for actual task
def load_notesheet(png):
    global background
    background = Image.open(png)
    background = background.convert("RGBA")
    #width, height = background.size

    img = ImageTk.PhotoImage(background)
    panel = Label(root, image=img)
    panel.image = img
    panel.place(x=170, y=0, width=835, height=1181)

# delete saved midis and XMLs from last programm run
def deleteOldFiles():
    files = os.listdir(outputDir)
    for item in files:
        if item.endswith('.mid') or item.endswith('.xml'):
            os.remove(os.path.join(outputDir, item))

##_______________________________OPTIONS______________________________________##
def specifyTask():
    global bpm, numberOfBars, maxNotePerBar, noteValuesList, pitchesList, twoHandsBool, errors, changetask
    
    values = bpm, numberOfBars, maxNotePerBar, noteValuesList, pitchesList, twoHandsBool
    options.changeParameter()

    newValues = options.get_data()
    # if parameters changed, delete errors to start a new diagram
    if values != newValues:
        errors = []
        changetask = []
    bpm, numberOfBars, maxNotePerBar, noteValuesList, pitchesList, twoHandsBool = newValues

##_____________________________ERROR-PLOT_____________________________________##
#TODO: add error plot with saved xml errors, if previous or next task is choosen
def add_error_plot():
    Label(root, text=" Error visualization:").place(x=1200, y=10, width=150, height=20)

    fig = Figure(figsize=(9, 6), facecolor="white")
    axis = fig.add_subplot(111)
    np.linspace(0, 10, 1000)

    xvalues = []
    for i in range(len(errors)):
        xvalues.append(i + 1)
    axis.plot(xvalues, errors, label="General error", marker='o')

    if (changetask):
        for i in changetask:
            axis.axvline(x=i + 0.5, color="black")
            axis.text(i + 0.5, 4.05, "new task", rotation=45, fontsize=8)

    axis.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    # axis.set_xticks(xvalues)
    axis.set_yticks([0, 1, 2, 3])
    axis.set_ylim(0, 4)
    axis.set_xlabel("Trials")
    axis.set_ylabel("Error")
    # axis.legend()
    axis.grid()

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas._tkcanvas.place(x=1050, y=30, width=400, height=400)

    global checkbox, details
    details = BooleanVar()
    details.set(False)
    checkbox = Checkbutton(root, text='show error details', command=add_error_details, var=details)
    checkbox.place(x=1050, y=440)

def add_error_details():
    fig = Figure(figsize=(9, 6), facecolor="white")
    axis = fig.add_subplot(111)
    x = np.linspace(0, 10, 1000)

    xvalues = []
    for i in range(len(errors)):
        xvalues.append(i + 1)
    axis.plot(xvalues, errors, label="General error", marker='o')

    if (changetask):
        for i in changetask:
            axis.axvline(x=i + 0.5, color="black")
            axis.text(i + 0.5, 4.05, "new task", rotation=45, fontsize=8)

    axis.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    # axis.set_xticks(xvalues)
    axis.set_yticks([0, 1, 2, 3])
    axis.set_ylim(0, 4)
    axis.set_xlabel("Trials")
    axis.set_ylabel("Error")

    axis.plot(x, np.sin(x), "-r", label="Tempo")
    axis.plot(x, np.cos(x), "-g", label="Notes")
    axis.plot(x, np.tan(x), "--y", label="etc")

    axis.legend(loc='upper right')
    axis.grid()

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas._tkcanvas.place(x=1050, y=30, width=400, height=400)

    global checkbox, details
    details = BooleanVar()
    details.set(True)
    checkbox = Checkbutton(root, text='show error details', command=add_error_plot, var=details)
    checkbox.place(x=1050, y=440)
##____________________________________________________________________________##

# create warning if Dexmo is not plugged in
def add_Dexmo_Warning():
    Label(root, text=" Warning: \n No Dexmo connected, \n no guidance possible.",
              fg="red").place(x=10, y=300, width=150, height=70)

# create button for demo, practicing, next task, back to start menu, guidance mode
def load_taskButtons():
    global currentMidi
    Button(root, text='Start Task', command=startTask).place(x=10, y=100, height=50, width=150)
    Button(root, text='Start Demo', command=startDemo).place(x=10, y=160, height=50, width=150)

    ##  GUIDANCE Mode
    l = Label(root, text=" Guidance mode:")
    l.place(x=10, y=210, width=150, height=70)
    guidance = StringVar(root)
    guidance.set(guidanceMode)
    guideopt = OptionMenu(root, guidance, *GuidanceModeList, command=set_guidance)
    guideopt.place(x=10, y=260, width=150, height=30)

    Button(root, text='Generate new Task', command=nextTask).place(x=10, y=400, height=50, width=150)
    Button(root, text='Specify next Task', command=specifyTask).place(x=10, y=460, height=25, width=150)
    Button(root, text='Open Midi file', command=openfile).place(x=10, y=520, height=25, width=150)

    ## next and previous tasks buttons
    if (nextSavedTask() == False):
        Button(root, text='Next Task >>', command=nextSavedTask, state=DISABLED).place(x=10, y=800, height=50, width=150)
    else:
        Button(root, text='Next Task >>', command=lambda: nextSavedTask(True)).place(x=10, y=800, height=50, width=150)

    files = getTimeSortedMidiFiles()
    if currentMidi != None:
        currMidiIdx = files.index(currentMidi) +1
        l2 = Label(root, text=" Midi File " + str(currMidiIdx) + " of " + str(len(files)))
        l2.place(x=10, y=860, width=150, height=20)

    if (previousTask() == False):
        Button(root, text='<< Previous Task', command=previousTask, state=DISABLED).place(x=10, y=880, height=50, width=150)
    else:
        Button(root, text='<< Previous Task', command=lambda: previousTask(True)).place(x=10, y=880, height=50, width=150)
    ## Back to Menu
    Button(root, text='Back to Menu', command=backToMenu).place(x=10, y=940, height=50, width=150)

# set guidance for task
def set_guidance(guidance):
    global guidanceMode
    guidanceMode = guidance

# open midi file user can choose
def openfile():
    nextTask(userSelectedTask=True, userSelectedLocation=filedialog.askopenfilename(filetypes=[("Midi files", ".midi .mid")]))

# load start menu with button for first task and exit button
def load_Startmenu():
    Button(root, text='Start first task', command=nextTask).place(x=675, y=440, height=50, width=150)
    Button(root, text='Quit', command=quit).place(x=675, y=500, height=50, width=150)
    choose_ports()

# destroy all widgets from frame
def clearFrame():
    for widget in root.winfo_children():
        widget.destroy()

# go back to start menu
def backToMenu():
    clearFrame()
    load_Startmenu()

# quit "Piano with dexmo"
def quit():
    root.destroy()

# choose sound, dexmo and inport ports in startmenu
def choose_ports():
    global dexmo_port

    # CONSTANTS
    X_POS = 660
    X_DIFF = 10
    Y_DIFF = 40
    TEXT_HEIGHT = 50
    FIELD_HEIGHT = 25
    WIDTH = 200

    def createPortButton(portText, findStr, yPos, portList, setFunc):
        # place button label (text)
        l = Label(root, text = portText + " port:")
        l.place(x=X_POS, y=yPos, height=TEXT_HEIGHT, width=WIDTH)

        # match port
        midiPort = StringVar(root)
        matching = [s for s in portList if findStr in s.lower()]
        if matching:
            midiPort.set(matching[0])
        else:
            midiPort.set("None")

        setFunc(midiPort.get())

        # place drop-down menu
        options = OptionMenu(root, midiPort, *portList, command=setFunc)
        options.place(x=X_POS-X_DIFF, y=yPos+Y_DIFF, height=FIELD_HEIGHT, width=WIDTH)

        return midiPort

    # choose outport for (lego)dexmo etc
    outports, inports = dexmoOutput.get_midi_interfaces()
    outports.append("None")
    inports.append("None")

    # create port buttons with automatic portname choice (if possible) 
    dexmo_port = createPortButton("Dexmo output", "dexmo", 600, outports, dexmoOutput.set_dexmo)
    sound_port = createPortButton("Sound output", "qsynth", 680, outports, dexmoOutput.set_sound_outport)
    input_port = createPortButton("Piano input", "vmpk", 760, inports, threadHandler.set_inport)



##_____________________________START LOOP HERE________________________________##

# create file output folder if it does not already exist
subprocess.run(['mkdir', '-p', tempDir], stderr=subprocess.DEVNULL)
# Create a window and title
root = Tk()
root.title("Piano with Dexmo")

deleteOldFiles()
load_Startmenu()
# Set the resolution of window
root.geometry("1500x1000")

# initialize keyboard input thread (done here to avoid multiple instances)
threadHandler.initInputThread()

check_dexmo_connected(mainWindow=False)
options = optionsWindowClass(root=root, bpm=bpm, numberOfBars=numberOfBars, maxNoteperBar=maxNotePerBar,
                             noteValuesList=noteValuesList, pitchesList=pitchesList, twoHandsBool=twoHandsBool)

root.mainloop()
