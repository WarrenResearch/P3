import glob
import pandas as pd
import numpy as np
from pymoo.indicators.hv import Hypervolume

findDir = 'insert path to data'
saveDir = 'insert path to save data'
    
fileCounter = 0
hyperVolumesDict = {}
for file in glob.glob(findDir + r'\*.xlsx'):
    fileCounter += 1
    currentData = pd.read_excel(file)
    numExps = currentData.shape[0]
    utopian = np.array([0.01, 0.02, 0.0])
    nadir = np.array([0.05, 0.2086, 1])

    surfConc = np.array(currentData.get("Surfactant_concentration"))
    seedFrac = np.array(currentData.get("Seed_fraction"))
    sizeFunc = np.array(currentData.get("Size function for 150"))

    objectiveSpace = []
    for x, y, z in zip(surfConc, seedFrac, sizeFunc):
        F = list([x, y, z])
        objectiveSpace.append(F)
    objectiveSpace = np.array(objectiveSpace)

    metric = Hypervolume(ref_point= np.array([0.05, 0.2086, 1]),
                        norm_ref_point=True,
                        zero_to_one=True,
                        nds=True,
                        ideal=utopian,
                        nadir=nadir)

    objectiveArray = np.array([]).reshape(0, 3)
    hv = []
    iterationList = []
    iteration = 0
    for i in range(0, len(objectiveSpace)):
        objectiveArray = np.vstack((objectiveArray, objectiveSpace[i]))
        hv_temp = metric.do(objectiveArray)
        hv.append(hv_temp)
        iteration += 1
        iterationList.append(iteration)
    
    hyperVolumesDict[str(fileCounter)] = hv
    hyperVolumesSummary = pd.DataFrame.from_dict(hyperVolumesDict)

    hyperVolumeTot = 0
    hyperVolumeAveList = []
    for exp in range(numExps):
        hyperVolumeTot = sum(hyperVolumesSummary.iloc[exp, :])
        hyperVolumeAveList.append(hyperVolumeTot/len(hyperVolumesSummary.columns))

hyperVolumesDict["AVERAGE"] = hyperVolumeAveList
hyperVolumesSummary = pd.DataFrame.from_dict(hyperVolumesDict)
hyperVolumesSummary.to_excel(f'{saveDir}\Hypervolumes\hv-summary-150nm.xlsx')