from PyQt5 import QtWidgets
import numpy as np
import pandas as pd
import datetime
import time
import DLS_handler
import threading

class conventionalEP(QtWidgets.QWidget):
    def __init__(self, parent, main):
        super(conventionalEP, self).__init__(parent)
       
        self.main = main

    def startEP(self):
        expThread = threading.Thread(target=self.runScript)
        expThread.start()
 
 #### Newest script for running optimisations ####
    def runScript(self, strategy="TSEMO"):
        expID = self.main.methodHandler.experimentIDLineEdit.text()
        expIndex = self.main.methodHandler.expIndex
        parameters = self.main.methodHandler.variablesDict
        if self.main.methodHandler.optimisationFlag:
            sampleStrategy = int(self.main.methodHandler.sampleStrategyText.text()) # If an optimisation, sample according to the defined strategy (every x reactions)
        else: 
            sampleStrategy = 1 # Else sample every reaction
        reactionsCounter = 0
        sampleLoopCounter = 0
        experimentLog = {}
        if self.main.methodHandler.optimisationFlag:
            optimisationSummary = self.main.methodHandler.optimisationSummary
        
        ### Extract parameters
        volumeCSTR = parameters.get("volumeCSTR")
        numberCSTRs = parameters.get("numberCSTRs")
        volumeReactor2 = parameters.get("volumeReactor2")
        deadVolume = parameters.get("deadVolume")[0]
        cleanRate = parameters.get("cleanRate")[0]
        cleanTime = parameters.get("cleanTime")[0]
        cleanVolume = parameters.get("cleanVolume")[0]
        nEmulsionFeeds = parameters.get("numEmulsionFeeds")
        nEmulsionFeedsActive = max(nEmulsionFeeds)

        ### Name all equipment
        seedPump = self.main.controller.pump1
        monomerAPump = self.main.controller.pump2
        monomerBPump = self.main.controller.pump3
        Aq1Pump = self.main.controller.pump4
        Aq2Pump = self.main.controller.pump5
        DLSpump = self.main.controller.pump10
        solventPump = self.main.controller.pump6

        solventValve = self.main.controller.valve1
        emulsionValve = self.main.controller.valve2
        outletValve = self.main.controller.valve3
        DLSValve = self.main.controller.valve4
        self.DLS = DLS_handler.StoppedFlowDLS(self, main=self.main)

        ### Get flowrates for pre-programmed conditions (OFAAT, DoE, LHC or first optimisation experiment)
        v_seed = self.main.methodHandler.flowRates.get("v_seed")
        v_Aq1 = self.main.methodHandler.flowRates.get("v_Aq1")
        v_Aq2 = self.main.methodHandler.flowRates.get("v_Aq2")
        v_monomerA = self.main.methodHandler.flowRates.get("v_monomerA")
        v_monomerB = self.main.methodHandler.flowRates.get("v_monomerB")

        ######################
        ###   PREPARATION  ###
        ######################

        ''' Start main script '''
        print(f'Starting experiment at {str(datetime.datetime.now())}')
        logEvent = f"Starting experiment {str(expID)}"
        logEventTime = str(datetime.datetime.now())
        experimentLog["Event"] = list([logEvent])
        experimentLog["Time"] = list([logEventTime])

        outletValve.valveHome() # set outlet to waste
        emulsionValve.valveHome() # set emulsion valve to waste
        solventValve.valveHome() # set solvent to surfactant position

        ''' Run solvent pump '''
        solventPump.setFlowrateText.setText(str(cleanRate))
        solventPump.setFlowrate()
        solventPump.start()
        
        print('Priming emulsion feeds...')
        ''' Prime emulsion feeds with surfactant solution (10 s for each) '''
        for i in range(2, int(nEmulsionFeedsActive) + 2):
            emulsionValve.valveSwitch(position=i)
            time.sleep(5)
        for i in reversed(range(2, int(nEmulsionFeedsActive) + 2)):
            emulsionValve.valveSwitch(position=i)
            time.sleep(5)

        solventPump.stop()

        ''' Update waste volume available '''
        volumePriming = 2*20*nEmulsionFeedsActive*(cleanRate/60)
        self.main.methodHandler.wasteVolumeAvailable = self.main.methodHandler.wasteVolumeAvailable - volumePriming
        self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))

        emulsionValve.distributionModeCheckbox.setChecked(True) # Activate distribution mode on emulsion feed valve

        ''' Write script/loop here '''
        #######################
        ### PROGRAMMED LOOP ###
        #######################
        for i in expIndex.astype(int):
            reactionsCounter+=1
            ''' define sample ID '''
            sampleID = f'{expID}-{str(reactionsCounter)}'

            ''' First calculate the total flow rates, time required to steady-state, and waste volume space required '''
            total_flowrate_i = v_seed[i] + v_Aq1[i] + v_Aq2[i] + v_monomerA[i]
            time_SS = 3*((volumeCSTR[i]*numberCSTRs[i]) + volumeReactor2[i] + deadVolume)/total_flowrate_i # Time to reach steady state (min)

            wasteVolumeReaction = time_SS*total_flowrate_i # Waste volume generated from getting to steady state (mL)
            wasteVolumeCleaningStep = cleanVolume # Waste volume generated from a single cleaning step (3 reactor volumes)
            wasteVolumeRequired = wasteVolumeReaction + 3*wasteVolumeCleaningStep # Total volume of waste generated in the i'th experiment (mL)

            if wasteVolumeRequired > self.main.methodHandler.wasteVolumeAvailable:
                self.main.methodHandler.pauseExperiment = True
                self.main.methodHandler.dialogueLabel.setText("WARNING - waste bottle too full to complete\nthe next experiment, please empty it to continue")
                self.main.methodHandler.dialogueLabel.setHidden(False)
                self.main.methodHandler.ackButton.setHidden(False)
                while self.main.methodHandler.pauseExperiment:
                    time.sleep(1)
                self.main.methodHandler.wasteVolumeAvailable = 980 # Assumes waste bottle has been emptied and resets to full capacity
            
            ''' Update waste bottle volume available '''
            self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))

            ''' Prepare emulsion at fast flow rate before starting reaction and start filling reactor with seed '''
            print(f'Preparing emulsion for {sampleID}')
            emulsionValve.valveHome()
            seedPump.setFlowrateText.setText(str(np.round(10*v_seed[i], 5)))
            Aq1Pump.setFlowrateText.setText(str(np.round(10*v_Aq1[i], 4)))
            Aq2Pump.setFlowrateText.setText(str(np.round(10*v_Aq2[i], 4)))
            monomerAPump.setFlowrateText.setText(str(np.round(10*v_monomerA[i], 4)))
            monomerBPump.setFlowrateText.setText(str(np.round(10*v_monomerB[i], 4)))

            seedPump.setFlowrate()
            Aq1Pump.setFlowrate()
            Aq2Pump.setFlowrate()
            monomerAPump.setFlowrate()
            monomerBPump.setFlowrate()

            seedPump.start()
            Aq1Pump.start()
            Aq2Pump.start()
            monomerAPump.start()
            monomerBPump.start()

            emulsionValve.valveHome()

            ''' Calculate and start timer to prepare emulsion (3 CSTR volumes at preparation flow rate) '''
            preparationTime = 60*3*volumeCSTR[i]/(10*(v_Aq1[i] + v_Aq2[i] + v_monomerA[i]))
            startPreparationTime = datetime.datetime.now()
            while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startPreparationTime).seconds < preparationTime:
                time.sleep(1)

            logEvent = f"Starting reaction {sampleID}"
            logEventTime = datetime.datetime.now()
            experimentLog["Event"].append(logEvent)
            experimentLog["Time"].append(str(logEventTime))

            if self.main.methodHandler.manualStop:
                break

            ''' Set flow rates '''
            seedPump.setFlowrateText.setText(str(v_seed[i]))
            Aq1Pump.setFlowrateText.setText(str(v_Aq1[i]))
            Aq2Pump.setFlowrateText.setText(str(v_Aq2[i]))
            monomerAPump.setFlowrateText.setText(str(v_monomerA[i]))
            monomerBPump.setFlowrateText.setText(str(v_monomerB[i]))

            seedPump.setFlowrate()
            Aq1Pump.setFlowrate()
            Aq2Pump.setFlowrate()
            monomerAPump.setFlowrate()
            monomerBPump.setFlowrate()

            emulsionValve.nFeedsLineEdit.setText(str(nEmulsionFeeds[i])) # Set number of feeds for emulsion distribution
            emulsionValve.startDistribution()
            
            print(f"Starting synthesis, steady state expected at {str(datetime.datetime.now() + datetime.timedelta(seconds=60*time_SS))}")

            '''Wait for steady state'''
            start_exp_time = datetime.datetime.now()
            while not self.main.methodHandler.stopThread and (datetime.datetime.now() - start_exp_time).seconds < 60*time_SS:
                self.main.methodHandler.wasteVolumeAvailable = self.main.methodHandler.wasteVolumeAvailable - (wasteVolumeReaction/(60*time_SS))
                self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))
                time.sleep(1)
            if self.main.methodHandler.manualStop:
                break
            
            if self.main.methodHandler.optimisationFlag and reactionsCounter%sampleStrategy == 0: # Sample every x reactions if running an optimisation where x = sampleStrategy
                print(f"Collecting product sample for {sampleID}")
                print(f'Sampler switched to port {((reactionsCounter/sampleStrategy) - (sampleLoopCounter*7) + 1)}')
                outletValve.valveSwitch(position=int((reactionsCounter/sampleStrategy) - (sampleLoopCounter*7) + 1)) # Start collecting sample by switching to next sample position

                '''Calculate and start timer to collect defined amount of sample'''
                sampleTime = 60*parameters.get("volumeSample")[i]/total_flowrate_i
                startSampleTime = datetime.datetime.now()
                logEvent = f"Sample collection for {sampleID} started"
                logEventTime = str(datetime.datetime.now())
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))
                print(f'At steady state, start sampling until {str(startSampleTime + datetime.timedelta(seconds=sampleTime))}')
                while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startSampleTime).seconds < sampleTime:
                    time.sleep(1)
                logEvent = f"Sample collection for {sampleID} completed"
                logEventTime = datetime.datetime.now()
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))
            elif not self.main.methodHandler.optimisationFlag: # If not an optimisation, just sample every experiment
                print(f"Collecting product sample for {sampleID}")
                print(f'Sampler switched to port {((reactionsCounter/sampleStrategy) - (sampleLoopCounter*7) + 1)}')
                outletValve.valveSwitch(position=((reactionsCounter/sampleStrategy) - (sampleLoopCounter*7) + 1)) # Start collecting sample by switching to next sample position

                '''Calculate and start timer to collect defined amount of sample'''
                sampleTime = 60*parameters.get("volumeSample")[i]/total_flowrate_i
                startSampleTime = datetime.datetime.now()
                logEvent = f"Sample collection for {sampleID} started"
                logEventTime = datetime.datetime.now()
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))
                print(f'At steady state, start sampling until {str(startSampleTime + datetime.timedelta(seconds=sampleTime))}')
                while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startSampleTime).seconds < sampleTime:
                    time.sleep(1)
                logEvent = f"Sample collection for {sampleID} completed"
                logEventTime = datetime.datetime.now()
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))
            if self.main.methodHandler.manualStop:
                break
            
            '''Start DLS analysis - extract sample, dilute, and pause flow'''
            print("Sampling for DLS")
            self.DLS.sampleAndScan(concentration=parameters.get("w_f")[i], flowRate=total_flowrate_i, sampleID=sampleID)
            logEvent = f"DLS sample {sampleID} extracted"
            logEventTime = datetime.datetime.now()
            experimentLog["Event"].append(logEvent)
            experimentLog["Time"].append(str(logEventTime))
            ''' Sample collected, start cleaning cycle '''
            outletValve.valveHome()

            seedPump.stop()
            Aq1Pump.stop()
            Aq2Pump.stop()
            monomerAPump.stop()
            monomerBPump.stop()

            ''' Clean with surfactant solution including emulsion feeds '''
            solventPump.start()

            print('Starting cleaning stage 1 ...')
            startClean1Time = datetime.datetime.now()
            logEvent = f"Cleaning with surfactant solution after reaction {sampleID}"
            logEventTime = startClean1Time
            experimentLog["Event"].append(logEvent)
            experimentLog["Time"].append(str(logEventTime))
            while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startClean1Time).seconds < 60*cleanTime:
                self.main.methodHandler.wasteVolumeAvailable = self.main.methodHandler.wasteVolumeAvailable - (wasteVolumeCleaningStep/(60*cleanTime))
                self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))
                time.sleep(1)

            if self.main.methodHandler.manualStop:
                break

            if self.DLS.DLSDataCollected == 1: # Check if DLS data has been saved and add size value to optimisationSummary
                newSize = self.DLS.particleSize
                optimisationSummary["Particle_size"].append(newSize)
                logEvent = f"DLS data saved for {sampleID}"
                logEventTime = datetime.datetime.now()
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))
            else: 
                print("Warning: no DLS data collected for this experiment")
                newSize = 55
                optimisationSummary["Particle_size"].append(newSize)
                logEvent = f"DLS data saved for {sampleID}"
                logEventTime = datetime.datetime.now()
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))

            # Update the values of the optimisation objectives which are equal to the minimised inputs
            for key in self.main.methodHandler.inputsDict.keys():
                optimisationSummary[f'{key}_min'].append(optimisationSummary[key][-1])

            ''' Clean with solvent '''
            emulsionValve.stopDistribution()
            emulsionValve.valveSwitch(position=2) # Send solvent into CSTR 1
            solventValve.valveSwitch(position=2) # Switch solvent inlet

            print('Starting cleaning stage 2 ...')
            startClean2Time = datetime.datetime.now()
            logEvent = "Cleaning with solvent after reaction " + sampleID
            logEventTime = startClean2Time
            experimentLog["Event"].append(logEvent)
            experimentLog["Time"].append(str(logEventTime))
            while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startClean2Time).seconds < 60*cleanTime:
                self.main.methodHandler.wasteVolumeAvailable = self.main.methodHandler.wasteVolumeAvailable - (wasteVolumeCleaningStep/(60*cleanTime))
                self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))
                time.sleep(1)

            if self.main.methodHandler.manualStop:
                break

            ''' Rinse with surfactant solution '''
            solventValve.valveHome() # Switch to surfactant solution

            print('Starting cleaning stage 3 ...')
            startClean3Time = datetime.datetime.now()
            logEvent = f"Refilling with surfactant solution after reaction {sampleID}"
            logEventTime = startClean3Time
            experimentLog["Event"].append(logEvent)
            experimentLog["Time"].append(str(logEventTime))
            while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startClean3Time).seconds < 60*cleanTime:
                self.main.methodHandler.wasteVolumeAvailable = self.main.methodHandler.wasteVolumeAvailable - (wasteVolumeCleaningStep/(60*cleanTime))
                self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))
                time.sleep(1)

            solventPump.stop()
            
            if self.main.methodHandler.manualStop:
                break

            if not self.main.methodHandler.stopThread and (reactionsCounter) % (7*sampleStrategy) == 0:
                self.main.methodHandler.pauseExperiment = True
                self.main.methodHandler.dialogueLabel.setText("Experiment paused, clean sample bottles and press OK to continue")
                self.main.methodHandler.dialogueLabel.setHidden(False)
                self.main.methodHandler.ackButton.setHidden(False)
                sampleLoopCounter += 1 # iterate sampleLoopCounter so the next experiment takes the sample in the correct sampling port
                while self.main.methodHandler.pauseExperiment:
                    time.sleep(1)

            self.main.methodHandler.optIterations +=1 # Iterate the optimisation iterations to keep track of the total number of experiments which make up the optimisation

        print("Finished pre-programmed experiments")
        
        ######################
        ### OPTIMISER LOOP ###
        ######################
        if self.main.methodHandler.optimisationFlag:
            print("Beginning optimisation")

            while not self.main.methodHandler.stopThread and self.main.methodHandler.optIterations < self.main.methodHandler.maxIterations:
                reactionsCounter+=1
                ''' define sample ID '''
                sampleID = f'{expID}-{str(reactionsCounter)}'

                newVars = self.main.methodHandler.getNewConditions(current_dataSet=optimisationSummary) # Requests a new set of experiments from the methodHandler, with a call to the algorithm and subequently a new set of calculated flow rates
                v_seed = newVars["v_seed"][-1]
                v_Aq1 = newVars["v_Aq1"][-1]
                v_Aq2 = newVars["v_Aq2"][-1]
                v_monomerA = newVars["v_monomerA"][-1]
                nEmulsionFeeds = newVars["numEmulsionFeeds"][-1]

                ''' First calculate the total flow rates, time required to steady-state, and waste volume space required '''
                total_flowrate_i = v_seed + v_Aq1 + v_Aq2 + v_monomerA
                time_SS = 3*((volumeCSTR[0]*numberCSTRs[0]) + volumeReactor2[0] + deadVolume)/total_flowrate_i # Time to reach steady state (min)

                wasteVolumeReaction = time_SS*total_flowrate_i # Waste volume generated from getting to steady state (mL)
                wasteVolumeCleaningStep = cleanVolume # Waste volume generated from a single cleaning step (3 reactor volumes)
                wasteVolumeRequired = wasteVolumeReaction + 3*wasteVolumeCleaningStep # Total volume of waste generated in the i'th experiment (mL)

                if wasteVolumeRequired > self.main.methodHandler.wasteVolumeAvailable:
                    self.main.methodHandler.pauseExperiment = True
                    self.main.methodHandler.dialogueLabel.setText("WARNING - waste bottle too full to complete\nthe next experiment, please empty it to continue")
                    self.main.methodHandler.dialogueLabel.setHidden(False)
                    self.main.methodHandler.ackButton.setHidden(False)
                    while self.main.methodHandler.pauseExperiment:
                        time.sleep(1)
                    self.main.methodHandler.wasteVolumeAvailable = 980 # Assumes waste bottle has been emptied and resets to full capacity
                
                ''' Update waste bottle volume available '''
                self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))

                ''' Prepare emulsion at fast flow rate before starting reaction and start filling reactor with seed '''
                print(f'Preparing emulsion for {sampleID}')
                emulsionValve.valveHome()
                seedPump.setFlowrateText.setText(str(np.round(10*v_seed, 5)))
                Aq1Pump.setFlowrateText.setText(str(np.round(10*v_Aq1, 4)))
                Aq2Pump.setFlowrateText.setText(str(np.round(10*v_Aq2, 4)))
                monomerAPump.setFlowrateText.setText(str(np.round(10*v_monomerA, 4)))
                monomerBPump.setFlowrateText.setText(str(np.round(10*v_monomerB, 4)))

                seedPump.setFlowrate()
                Aq1Pump.setFlowrate()
                Aq2Pump.setFlowrate()
                monomerAPump.setFlowrate()
                monomerBPump.setFlowrate()

                seedPump.start()
                Aq1Pump.start()
                Aq2Pump.start()
                monomerAPump.start()
                monomerBPump.start()

                emulsionValve.valveHome()

                ''' Calculate and start timer to prepare emulsion (3 CSTR volumes at preparation flow rate) '''
                preparationTime = 60*3*volumeCSTR[0]/(10*(v_Aq1 + v_Aq2 + v_monomerA))
                startPreparationTime = datetime.datetime.now()
                while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startPreparationTime).seconds < preparationTime:
                    time.sleep(1)

                logEvent = "Starting reaction " + sampleID
                logEventTime = datetime.datetime.now()
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))

                if self.main.methodHandler.manualStop:
                    break

                ''' Set flow rates '''
                seedPump.setFlowrateText.setText(str(v_seed))
                Aq1Pump.setFlowrateText.setText(str(v_Aq1))
                Aq2Pump.setFlowrateText.setText(str(v_Aq2))
                monomerAPump.setFlowrateText.setText(str(v_monomerA))
                monomerBPump.setFlowrateText.setText(str(v_monomerB))

                emulsionValve.nFeedsLineEdit.setText(str(nEmulsionFeeds)) # Set number of feeds for emulsion distribution
                emulsionValve.startDistribution()
                
                print(f"Starting synthesis, steady state expected at {str(datetime.datetime.now() + datetime.timedelta(seconds=60*time_SS))}")

                '''Wait for steady state'''
                start_exp_time = datetime.datetime.now()
                while not self.main.methodHandler.stopThread and (datetime.datetime.now() - start_exp_time).seconds < 60*time_SS:
                    self.main.methodHandler.wasteVolumeAvailable = self.main.methodHandler.wasteVolumeAvailable - (wasteVolumeReaction/(60*time_SS))
                    self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))
                    time.sleep(1)
                if self.main.methodHandler.manualStop:
                    break
                
                if self.main.methodHandler.optimisationFlag and reactionsCounter%sampleStrategy == 0: # Sample every x reactions if running an optimisation where x = sampleStrategy
                    print(f"Collecting product sample for {sampleID}")
                    print(f'Sampler switched to port {((reactionsCounter/sampleStrategy) - (sampleLoopCounter*7) + 1)}')
                    outletValve.valveSwitch(position=((reactionsCounter/sampleStrategy) - (sampleLoopCounter*7) + 1)) # Start collecting sample by switching to next sample position

                    '''Calculate and start timer to collect defined amount of sample'''
                    sampleTime = 60*parameters.get("volumeSample")[i]/total_flowrate_i
                    startSampleTime = datetime.datetime.now()
                    logEvent = f"Sample collection for {sampleID} started"
                    logEventTime = datetime.datetime.now()
                    experimentLog["Event"].append(logEvent)
                    experimentLog["Time"].append(str(logEventTime))
                    print(f'At steady state, start sampling until {str(startSampleTime + datetime.timedelta(seconds=sampleTime))}')
                    while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startSampleTime).seconds < sampleTime:
                        time.sleep(1)
                    logEvent = f"Sample collection for {sampleID} completed"
                    logEventTime = datetime.datetime.now()
                    experimentLog["Event"].append(logEvent)
                    experimentLog["Time"].append(str(logEventTime))
                elif not self.main.methodHandler.optimisationFlag: # If not an optimisation, just sample every experiment
                    print(f"Collecting product sample for {sampleID}")
                    print(f'Sampler switched to port {((reactionsCounter/sampleStrategy) - (sampleLoopCounter*7) + 1)}')
                    outletValve.valveSwitch(position=((reactionsCounter/sampleStrategy) - (sampleLoopCounter*7) + 1)) # Start collecting sample by switching to next sample position

                    '''Calculate and start timer to collect defined amount of sample'''
                    sampleTime = 60*parameters.get("volumeSample")[i]/total_flowrate_i
                    startSampleTime = datetime.datetime.now()
                    logEvent = f"Sample collection for {sampleID} started"
                    logEventTime = datetime.datetime.now()
                    experimentLog["Event"].append(logEvent)
                    experimentLog["Time"].append(str(logEventTime))
                    print(f'At steady state, start sampling until {str(startSampleTime + datetime.timedelta(seconds=sampleTime))}')
                    while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startSampleTime).seconds < sampleTime:
                        time.sleep(1)
                    logEvent = f"Sample collection for {sampleID} completed"
                    logEventTime = datetime.datetime.now()
                    experimentLog["Event"].append(logEvent)
                    experimentLog["Time"].append(str(logEventTime))
                if self.main.methodHandler.manualStop:
                    break
                
                '''Start DLS analysis - extract 
                sample, dilute, and pause flow'''
                print("Sampling for DLS")
                self.DLS.sampleAndScan(concentration=parameters.get("w_f")[i], flowRate=total_flowrate_i, sampleID=sampleID)
                logEvent = f"DLS sample {sampleID} extracted"
                logEventTime = datetime.datetime.now()
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))

                ''' Sample collected, start cleaning cycle '''
                outletValve.valveHome()
                seedPump.stop()
                Aq1Pump.stop()
                Aq2Pump.stop()
                monomerAPump.stop()
                monomerBPump.stop()

                ''' Clean with surfactant solution including emulsion feeds '''
                solventPump.start()

                print('Starting cleaning stage 1 ...')
                startClean1Time = datetime.datetime.now()
                logEvent = "Cleaning with surfactant solution after reaction " + sampleID
                logEventTime = startClean1Time
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))
                while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startClean1Time).seconds < 60*cleanTime:
                    self.main.methodHandler.wasteVolumeAvailable = self.main.methodHandler.wasteVolumeAvailable - (wasteVolumeCleaningStep/(60*cleanTime))
                    self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))
                    time.sleep(1)

                if self.main.methodHandler.manualStop:
                    break

                if self.DLS.DLSDataCollected == 1: # Check if DLS data has been saved and add size value to optimisationSummary
                    newSize = self.DLS.particleSize
                    optimisationSummary["Particle_size"].append(newSize)
                    logEvent = f"DLS data saved for {sampleID}"
                    logEventTime = datetime.datetime.now()
                    experimentLog["Event"].append(logEvent)
                    experimentLog["Time"].append(str(logEventTime))
                else: 
                    print("Warning: no DLS data collected for this experiment")
                    newSize = 0
                    optimisationSummary["Particle_size"].append(newSize)
                    logEvent = f"DLS data saved for {sampleID}"
                    logEventTime = datetime.datetime.now()
                    experimentLog["Event"].append(logEvent)
                    experimentLog["Time"].append(str(logEventTime))

                # Update the values of the optimisation objectives which are equal to the minimised inputs
                for key in self.main.methodHandler.inputsDict.keys():
                    optimisationSummary[f'{key}_min'].append(optimisationSummary[key][-1])

                ''' Clean with solvent '''
                emulsionValve.stopDistribution()
                emulsionValve.valveSwitch(position=2) # Send solvent into CSTR 1
                solventValve.valveSwitch(position=2) # Switch solvent inlet

                print('Starting cleaning stage 2 ...')
                startClean2Time = datetime.datetime.now()
                logEvent = "Cleaning with solvent after reaction " + sampleID
                logEventTime = startClean2Time
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))
                while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startClean2Time).seconds < 60*cleanTime:
                    self.main.methodHandler.wasteVolumeAvailable = self.main.methodHandler.wasteVolumeAvailable - (wasteVolumeCleaningStep/(60*cleanTime))
                    self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))
                    time.sleep(1)

                if self.main.methodHandler.manualStop:
                    break

                ''' Rinse with surfactant solution '''
                solventValve.valveHome() # Switch to surfactant solution

                print('Starting cleaning stage 3 ...')
                startClean3Time = datetime.datetime.now()
                logEvent = f"Refilling with surfactant solution after reaction {sampleID}"
                logEventTime = startClean3Time
                experimentLog["Event"].append(logEvent)
                experimentLog["Time"].append(str(logEventTime))
                while not self.main.methodHandler.stopThread and (datetime.datetime.now() - startClean3Time).seconds < 60*cleanTime:
                    self.main.methodHandler.wasteVolumeAvailable = self.main.methodHandler.wasteVolumeAvailable - (wasteVolumeCleaningStep/(60*cleanTime))
                    self.main.methodHandler.wasteVolumeCounter.setText(str(round(self.main.methodHandler.wasteVolumeAvailable, 1)))
                    time.sleep(1)

                solventPump.stop()
                
                if self.main.methodHandler.manualStop:
                    break

                if not self.main.methodHandler.stopThread and (reactionsCounter) % (7*sampleStrategy) == 0:
                    self.main.methodHandler.pauseExperiment = True
                    self.main.methodHandler.dialogueLabel.setText("Experiment paused, clean sample bottles and press OK to continue")
                    self.main.methodHandler.dialogueLabel.setHidden(False)
                    self.main.methodHandler.ackButton.setHidden(False)
                    sampleLoopCounter += 1 # iterate sampleLoopCounter so the next experiment takes the sample in the correct sampling port
                    while self.main.methodHandler.pauseExperiment:
                        time.sleep(1)

                pd.DataFrame(optimisationSummary).to_excel(f'{self.main.methodHandler.savePath}-optimisationSummary.xlsx') # Save optimisation summary to save folder

                self.main.methodHandler.optIterations +=1

            print("COMPLETED")
            print(experimentLog)
            pd.DataFrame.from_dict(experimentLog).to_excel(f'{self.main.methodHandler.savePath}-experimentLog.xlsx') # Save experiment log to save folder
