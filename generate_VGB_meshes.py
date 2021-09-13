# -*- coding: utf-8 -*-
import sys
import re
import numpy as np

sourceFile=sys.argv[1]

step = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
extraTemp = float(sys.argv[3]) if len(sys.argv) > 3 else 3

# Read the printer.cfg
with open(sourceFile, "r") as f:
    lines = f.readlines()

destFile = sourceFile[:-4] + '_NEW.cfg'

parsingCOLD = False
parsingCOLDindex = 0

parsingHOT = False
parsingHOTindex = 0

parsingTEST = False
parsingTESTindex = 0

parsing = False
parsingPreamble = True

preamble = list()
COLD = list()
HOT = list()
TEST = list()
TESTtemp = 999
postamble = list()

#get the structure of a bed_mesh section without the point values
for lIndex in range(len(lines)):
    oline = lines[lIndex]
    parts = oline.split('#*#', 1)
    if len(parts) > 1:
        if parsing:
            if "\t" in parts[1]:
                parsingPreamble = False
                continue
            if parsingPreamble:
                preamble.append(oline)
            else:
                postamble.append(oline)
        command = parts[1].strip()
        stringMatch = re.search ('bed_mesh', command)
        if not parsing and stringMatch:
            #print("started parsing!")
            parsing = True
        elif parsing and stringMatch:
            #print("stopped parsing!")
            parsing = False
            postamble.pop()
            break

#get cold, hot and test (if present) mesh points
for lIndex in range(len(lines)):
    oline = lines[lIndex]
    parts = oline.split('#*#', 1)
    if parsingCOLD and lIndex > parsingCOLDindex + 2:
        if not "tension" in parts[1]:
            row = [float(i) for i in parts[1].strip().split(', ')]
            COLD.append(row)
        else:
            parsingCOLD = False
    if parsingHOT and lIndex > parsingHOTindex + 2:
        if not "tension" in parts[1]:
            row = [float(i) for i in parts[1].strip().split(', ')]
            HOT.append(row)
        else:
            parsingHOT = False
    if parsingTEST and lIndex > parsingTESTindex + 2:
        if not "tension" in parts[1]:
            row = [float(i) for i in parts[1].strip().split(', ')]
            TEST.append(row)
        else:
            parsingTEST = False
    if len(parts) > 1:
        command = parts[1].strip()
        stringMatchCOLD = re.search ('bed_mesh COLD', command)
        stringMatchHOT = re.search ('bed_mesh HOT', command)
        stringMatchTEST = re.search ('bed_mesh TEST', command)
        if stringMatchCOLD:
            parsingCOLD = True
            parsingCOLDindex = lIndex
            COLDtemp = float(command.split("[bed_mesh COLD")[1].replace("]",""))
        elif stringMatchHOT:
            parsingHOT = True
            parsingHOTindex = lIndex
            HOTtemp = float(command.split("[bed_mesh HOT")[1].replace("]",""))
        elif stringMatchTEST:
            parsingTEST = True
            parsingTESTindex = lIndex
            TESTtemp = float(command.split("[bed_mesh TEST")[1].replace("]",""))

#calculate per-point expansion coefficient
deltaT = HOTtemp - COLDtemp
deltaZ = np.array(HOT) - np.array(COLD)
coeffs = deltaZ/deltaT

#linearly generate new meshes every <step> °C with some tolerance
multiplier = pow(10,len(str(TESTtemp))) #hacky way of ensuring consistent numbers -> integers only
degrees = np.arange(COLDtemp*multiplier-extraTemp*multiplier, HOTtemp*multiplier+extraTemp*multiplier, step*multiplier)
degrees = degrees / multiplier

newMeshes = list()

for i in degrees:
    newMeshFC = COLD + coeffs*(i-COLDtemp)
    newMeshes.append(newMeshFC)
    #compare mesh if similar temp as test mesh exists
    if np.abs(i-TESTtemp)<step/1.5:
        print("Testing! " + str(i) + " and " + str(TESTtemp))
        print("Absolute error:")
        error = np.array(TEST) - newMeshFC;
        print(error)
        MSE = np.mean(np.power(error,2))
        print("MSE: " + str(MSE))
        print("Maximum absolute error is " + str(np.round(np.max(np.abs(error)),5)) + " mm (" + str(np.round(np.max(np.abs(error))*1000,2)) + " microns)")

#add new meshes to the new printer.cfg
with open(destFile, "w") as f:
    for lIndex in range(len(lines)):
        f.write(lines[lIndex])
    f.write("#*#\n")
    #now add the new meshes
    for index, mesh in enumerate(newMeshes):
        f.write("#*# [bed_mesh " + str(degrees[index]) + "]\n")
        #write preamble
        for line in preamble:
            f.write(line)
        #write points
        for line in mesh:
            lineChar = np.char.mod('%f', line)
            f.write("#*# \t" + str(', '.join(lineChar)) + "\n")
        #write postamble
        for line in postamble:
            f.write(line)
