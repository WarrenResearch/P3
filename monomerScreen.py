# Function/script for screening surfactant concentration written for OFAAT experiments

# Takes two input arguments of controller and methodHandler. Controller is the instance of platformControl
# created in the GUI initialisation, methodHandler is the method builder used to instantiate the method (may not be fully accurate)
from PyQt5 import QtWidgets, QtCore, QtSerialPort
import threading
import numpy as np
import datetime
import time

class monomerScreener(QtWidgets.QWidget):
    def __init__(self, parent, main):
        super(monomerScreener, self).__init__(parent)
        
        self.main=main

        # self.pumpSeed = self.controller.pump1
        # self.pumpMA = self.controller.pump2
        # self.pumpMB = self.controller.pump3
        # self.pumpAq = self.controller.pump4
        # self.pumpSolvent = self.controller.pump6

        # self.valveSolvent = self.controller.valve1
        # self.valveEmulsion = self.controller.valve2
        # self.valveOutlet = self.controller.valve3

    def startExperiment(self):
        # Start experiment thread here with call to run script
        self.experimentThread = threading.Thread(target=self.runScript)
        self.experimentThread.start()
        self.stopThread = False
        print(self.stopThread)

    def runScript(self):
        # Script for running the experiment goes here using parameters calculated in calculateParameters fcn #
        print('Starting experiment at ' + str(datetime.datetime.now()))
    
        self.valveOutlet.valveHome() # set outlet to waste
        self.valveEmulsion.valveHome() # set emulsion valve to waste
        self.valveSolvent.valveSwitch(position='A') # set solvent to surfactant position

        # Run solvent pump
        self.pumpSolvent.setFlowrateText.setText(str(self.cleanRate))
        self.pumpSolvent.setFlowrate()
        self.pumpSolvent.start()
        
        print('Priming emulsion feeds...')
        # Prime emulsion feeds with surfactant solution (10 s for each)
        for i in range(2, int(self.nEmulsionFeeds) + 2):
            self.valveEmulsion.valveSwitch(i)
            time.sleep(10)
        for i in reversed(range(2, int(self.nEmulsionFeeds) + 2)):
            self.valveEmulsion.valveSwitch(i)
            time.sleep(10)

        self.pumpSolvent.stop()

        self.valveEmulsion.distributionModeCheckBox.setChecked(True) # Activate distribution mode on emulsion feed valve
        self.valveEmulsion.nFeedsLineEdit.setText(str(self.nEmulsionFeeds)) # Set number of feeds for emulsion distribution

        while not self.stopThread:
            for i in self.expIndex.astype(int):

                # Prepare emulsion at fast flow rate before starting reaction and start filling reactor with seed
                print('Preparing emulsion...')
                self.valveEmulsion.valveHome()
                self.pumpSeed.setFlowrateText.setText(str(np.round(10*self.v_seed_seq[i], 4)))
                self.pumpMA.setFlowrateText.setText(str(np.round(10*self.v_MA_seq[i], 4)))
                self.pumpMB.setFlowrateText.setText(str(np.round(10*self.v_MB_seq[i], 4)))
                self.pumpAq.setFlowrateText.setText(str(np.round(10*self.v_Aq_seq[i], 4)))

                self.pumpSeed.setFlowrate()
                self.pumpMA.setFlowrate()
                self.pumpMB.setFlowrate()
                self.pumpAq.setFlowrate()
                self.pumpSeed.start()
                self.pumpMA.start()
                self.pumpMB.start()
                self.pumpAq.start()

                # Calculate and start time to prepare emulsion (3 CSTR volumes at preparation flow rate)
                preparationTime = 60*3*self.V_CSTR/(10*self.v_MA_seq[i] + 10*self.v_MB_seq[i] + 10*self.v_Aq_seq[i])
                startPreparationTime = datetime.datetime.now()
                while not self.stopThread and (datetime.datetime.now() - startPreparationTime).seconds < preparationTime:
                    time.sleep(1)

                # Reduce flow rates to reaction flow rates and begin distributing emulsion to CSTRs
                self.pumpSeed.setFlowrateText.setText(str(np.round(self.v_seed_seq[i], 4)))
                self.pumpMA.setFlowrateText.setText(str(np.round(self.v_MA_seq[i], 4)))
                self.pumpMB.setFlowrateText.setText(str(np.round(self.v_MB_seq[i], 4)))
                self.pumpAq.setFlowrateText.setText(str(np.round(self.v_Aq_seq[i], 4)))
                
                self.pumpSeed.setFlowrate()
                self.pumpMA.setFlowrate()
                self.pumpMB.setFlowrate()
                self.pumpAq.setFlowrate()

                self.valveEmulsion.startDistribution()

                # Calculate and start time to run reaction to steady state
                startSteadyStateTime = datetime.datetime.now()
                residenceTime = self.tau + self.V_reactor2/(self.v_seed + self.v_Aq1_seq[i] + self.v_Aq2_seq[i] + self.v_monomer_seq[i]) # Total residence time = CSTRs RT + tube RT
                reactionTime = 3*residenceTime # 3 reactor volumes until steady state
                print('Reaction started, steady-state expected at ' + str(startSteadyStateTime + datetime.timedelta(seconds=60*reactionTime)))
                while not self.stopThread and (datetime.datetime.now() - startSteadyStateTime).seconds < 60*reactionTime:
                    time.sleep(1)

                self.valveOutlet.valveSwitch(i + 2) # Start collecting sample by switching to next sample position

                # Calculate and start time to collect defined amount of sample
                sampleTime = 60*self.V_sample/(self.v_seed_seq + self.v_MA_seq[i] + self.v_MB_seq[i] + self.v_Aq_seq[i]) # Time to collect sample at current flow rate
                startSampleTime = datetime.datetime.now()
                print('At steady state, start sampling until ' + str(startSampleTime + datetime.timedelta(seconds=sampleTime)))
                while not self.stopThread and (datetime.datetime.now() - startSampleTime).seconds < sampleTime:
                    time.sleep(1)

                # Sample collected, start cleaning cycle
                self.valveOutlet.valveHome()
                self.pumpSeed.stop()
                self.pumpMA.stop()
                self.pumpMB.stop()
                self.pumpAq.stop()

                # Clean with surfactant solution including emulsion feeds
                self.pumpSolvent.start()
                startClean1Time = datetime.datetime.now()
                print('Sample collected, cleaning started, next experiment starting at ' + str(startClean1Time + datetime.timedelta(seconds=3.5*60*self.cleanTime)))
                print('Starting cleaning stage 1 ...')
                while not self.stopThread and (datetime.datetime.now() - startClean1Time).seconds < 60*self.cleanTime:
                    time.sleep(1)

                # Clean with solvent
                self.valveEmulsion.stopDistribution()
                time.sleep(1)
                self.valveEmulsion.valveSwitch(port=2) # Send solvent into CSTR 1
                time.sleep(1)
                self.valveSolvent.valveSwitch(position='B') # Switch solvent inlet
                print('Starting cleaning stage 2 ...')
                startClean2Time = datetime.datetime.now()
                while not self.stopThread and (datetime.datetime.now() - startClean2Time).seconds < 60*1.5*self.cleanTime:
                    time.sleep(1)

                # Rinse with surfactant solution
                self.valveSolvent.valveSwitch(position='A') # Switch to surfactant solution
                print('Starting cleaning stage 3 ...')
                startClean3Time = datetime.datetime.now()
                while not self.stopThread and (datetime.datetime.now() - startClean3Time).seconds < 60*self.cleanTime:
                    time.sleep(1)

                self.pumpSolvent.stop()

                # If stopThread == True during experiment loop, stop pumps, close experiment thread, and break loops
                if self.stopThread:
                    self.pumpSeed.stop()
                    self.pumpMA.stop()
                    self.pumpMB.stop()
                    self.pumpAq.stop()
                    self.experimentThread.join()
                    print('Experiment stopped by user at ' + str(datetime.datetime.now()))
                    print('Experiment thread closed')
                    self.manualStop = True
                    break

            break

        # After exiting experiment loop
        # Check if loop was broken by user, if so, expected manual actions to deal with reactor, if not:
        if not self.manualStop:
            # Final flushing cycle to give reactor an extra clean
            self.pumpSeed.stop()
            self.pumpMA.stop()
            self.pumpMB.stop()
            self.pumpAq.stop()

            self.pumpSolvent.start()
            self.valveSolvent.valveSwitch(position='B') # Switches to solvent
            self.valveEmulsion.startDistribution()

            # Final clean with solvent including emulsion feed tubes
            print('Reagent pumps stopped, flushing with solvent...')
            startFlush1Time = datetime.datetime.now()
            while not self.stopThread and (datetime.datetime.now() - startFlush1Time).seconds < 60*self.cleanTime:
                time.sleep(1)

            self.valveEmulsion.stopDistribution()
            self.valveEmulsion.valveSwitch(port=2)
            self.valveSolvent.valveSwitch(position='A')

            # Flushes with surfactant through CSTR 1
            startFlush2Time = datetime.datetime.now()
            while not self.stopThread and (datetime.datetime.now() - startFlush2Time).seconds < 60*self.cleanTime:
                time.sleep(1)

            self.valveEmulsion.startDistribution()

            # Rinse emulsion feeds lines with surfactant
            finalFlushTime = datetime.datetime.now()
            while not self.stopThread and (datetime.datetime.now() - finalFlushTime).seconds < 60:
                time.sleep(1)

            self.valveEmulsion.stopDistribution()
            self.pumpSolvent.stop()
            self.experimentThread.join()
            print('EXPERIMENT COMPLETED :)')

            self.runExpButton.setChecked(False)
            self.runExpButton.setText('\n \nRUN EXPERIMENT \n \n')
            self.runExpButton.repaint()

    def calculateParameters(self, 
    V_CSTR, 
    nCSTRs, 
    V_reactor2,
    tau, 
    nEmulsionFeeds,
    V_sample, 
    w_f, 
    w_s, 
    R_s, 
    w_Aq,
    MA_ratioMin,
    MA_ratioMax,
    MA_density,
    MB_density,
    S_density, 
    Aq_density,
    numExp, 
    cleanRate, 
    cleanTime, 
    flushTime):
    ### Function takes user inputs and calculates required conditions to complete the sequence of experiments ###
        # Define surfactantScreener attributes from function call
        self.tau = tau
        self.reactionTime = 3*tau
        self.V_CSTR = V_CSTR
        self.V_reactor2 = V_reactor2
        self.V_sample = V_sample
        self.expIndex = np.linspace(0, numExp - 1, num=numExp) # Index to track reaction number during sequence of experiments
        self.nEmulsionFeeds = nEmulsionFeeds
        self.cleanRate = cleanRate
        self.cleanTime = cleanTime

        #### Calculation of seed flow rate to target an average seed residence time for i emulsion feeds in n CSTRs ####
        m_ratio_seq = np.linspace(MA_ratioMin, MA_ratioMax, numExp) # Series of targeted surfactant concentrations between min and max 
        m_density_seq = np.array([])
        for i in m_ratio_seq:
            m_density = i*MA_density + (1-i)*MB_density
            m_density_seq = np.append(m_density_seq, m_density)

        w_emulsion = (w_f*w_s*(1-R_s))/(w_s - (w_f*R_s))
        #### Calculation of seed flow rate to target an average seed residence time for i emulsion feeds in n CSTRs ####

        E_density_seq = np.array([])
        self.v_seed_seq = np.array([])
        self.v_emulsion_seq = np.array([])
        self.v_total_seq = np.array([])

        for d in m_density_seq:
            E_density = d*w_emulsion + (1-w_emulsion)
            E_density_seq = np.append(E_density_seq, E_density)
            emulsionFeedsIndex = np.linspace(1, self.nEmulsionFeeds, num=self.nEmulsionFeeds)
            summation = 0
            for i in emulsionFeedsIndex:
                summation_temp = 1/(1 + ((S_density/E_density)*((w_s/(w_f*R_s)) - 1))*(1-((self.nEmulsionFeeds-i)/self.nEmulsionFeeds)))
                summation = summation + summation_temp
            A = (S_density/E_density)*((w_s/(w_f*R_s)) - 1)
            B = (nCSTRs - self.nEmulsionFeeds)/(1 + A)
            v_seed = (self.V_CSTR/self.tau)*(summation + B)
            self.v_seed_seq = np.append(self.v_seed_seq, v_seed)
            v_emulsion = ((S_density*v_seed)/E_density)*((w_s/(w_f*R_s)) - 1)
            self.v_emulsion_seq = np.append(self.v_emulsion_seq, v_emulsion)
            v_total = v_seed + v_emulsion
            self.v_total_seq = np.append(self.v_total_seq, v_total)
            w_emulsion = (w_f*(E_density*v_emulsion + S_density*v_seed) - (w_s*S_density*v_seed))/(E_density*v_emulsion)

        self.v_M_seq = np.array([])
        self.v_MA_seq = np.array([])
        self.v_MB_seq = np.array([])
        self.v_Aq_seq = np.array([])

        for i, a, v in zip(m_density_seq, E_density_seq, self.v_emulsion_seq):
            v_M = (v*a*(w_Aq - w_emulsion))/(i*(w_Aq - 1))
            self.v_M_seq = np.append(self.v_M_seq, v_M)
        
        for i, a, b in zip(m_density_seq, self.v_M_seq, m_ratio_seq):
            v_MA = i*a*b/MA_density
            self.v_MA_seq = np.append(self.v_MA_seq, v_MA)
        
        for i, a, b in zip(m_density_seq, self.v_M_seq, m_ratio_seq):
            v_MB = i*a*(1-b)/MB_density
            self.v_MB_seq = np.append(self.v_MB_seq, v_MB)
        
        for i, a, b, c in zip(m_density_seq, self.v_M_seq, E_density_seq, self.v_emulsion_seq):
            v_Aq = ((b*c)-(i*a))/(Aq_density)
            self.v_Aq_seq = np.append(self.v_Aq_seq, v_Aq)
        
        #### VOLUME CALCULATIONS ###

        # Vol_seed = reactionTime*numExp*v_seed + sampleTime*numExp*v_seed # Required seed volume

        Vol_seed_array = np.array([])
        Vol_MA_array = np.array([])
        Vol_MB_array = np.array([])
        Vol_Aq_array = np.array([])
        Vol_seed = 0
        Vol_MA = 0
        Vol_MB = 0
        Vol_Aq = 0

        for i in self.expIndex.astype(int):
            reactionTime = 3*(self.tau + (self.V_reactor2/self.v_total_seq[i]))
            sampleTime = self.V_sample/self.v_total_seq[i]
            prepTime = 3*self.V_CSTR/10*self.v_emulsion_seq[i]

            Vol_seed_temp = (reactionTime + sampleTime + 10*prepTime)*self.v_seed_seq[i]
            Vol_seed_array = np.append(Vol_seed_array, Vol_seed_temp)
            Vol_seed = Vol_seed + Vol_seed_array[i]

            Vol_MA_temp = (reactionTime + sampleTime + 10*prepTime)*self.v_MA_seq[i]
            Vol_MA_array = np.append(Vol_MA_array, Vol_MA_temp)
            Vol_MA = Vol_MA + Vol_MA_array[i]

            Vol_MB_temp = (reactionTime + sampleTime + 10*prepTime)*self.v_MB_seq[i]
            Vol_MB_array = np.append(Vol_MB_array, Vol_MB_temp)
            Vol_MB = Vol_MB + Vol_MB_array[i]

            Vol_Aq_temp = (reactionTime + sampleTime + 10*prepTime)*self.v_Aq_seq[i]
            Vol_Aq_array = np.append(Vol_Aq_array, Vol_Aq_temp)
            Vol_Aq = Vol_Aq + Vol_Aq_array[i]

        V_waste = Vol_seed + Vol_MA + Vol_MB + Vol_Aq + flushTime*self.cleanRate + (numExp - 1)*self.cleanTime*self.cleanRate

        
        # Build parameters table for reference
        self.methodHandler.methodBuilderBox.setMinimumWidth(600)
        self.methodHandler.parametersTable.setRowCount(9)
        self.methodHandler.parametersTable.setColumnCount(numExp)
        self.methodHandler.parametersTable.setVerticalHeaderLabels(
            ['Monomer A fraction (g/g)',
            'Surfactant concentration (g/g)',
            'Seed flow rates (mL/min)', 
            'Aq flow rates (mL/min)',
            'Monomer A flow rates (mL/min)',
            'Monomer B flow rates (mL/min)',
            'Number of feeds',
            'Seed ratio',
            'Emulsion concentration (% w/w)'])
        for i in self.expIndex.astype(int):
            MA_fraction = QtWidgets.QTableWidgetItem(str(np.round(m_ratio_seq[i], 4)))
            w_Aqueous = QtWidgets.QTableWidgetItem(str(np.round(w_Aq, 4)))
            v_seed = QtWidgets.QTableWidgetItem(str(np.round(self.v_seed_seq[i], 4)))
            v_Aq = QtWidgets.QTableWidgetItem(str(np.round(self.v_Aq_seq[i], 4)))
            v_MA = QtWidgets.QTableWidgetItem(str(np.round(self.v_MA_seq[i], 4)))
            v_MB = QtWidgets.QTableWidgetItem(str(np.round(self.v_MB_seq[i], 4)))
            nFeeds = QtWidgets.QTableWidgetItem(str(self.nEmulsionFeeds))
            R_seed = QtWidgets.QTableWidgetItem(str(R_s))
            w_e = QtWidgets.QTableWidgetItem(str(np.round(w_emulsion, 4)))
            self.methodHandler.parametersTable.setItem(0, i, MA_fraction)
            self.methodHandler.parametersTable.setItem(1, i, w_Aqueous)
            self.methodHandler.parametersTable.setItem(2, i, v_seed)
            self.methodHandler.parametersTable.setItem(3, i, v_Aq)
            self.methodHandler.parametersTable.setItem(4, i, v_MA)
            self.methodHandler.parametersTable.setItem(5, i, v_MB)
            self.methodHandler.parametersTable.setItem(6, i, nFeeds)
            self.methodHandler.parametersTable.setItem(7, i, R_seed)
            self.methodHandler.parametersTable.setItem(8, i, w_e)

        self.methodHandler.parametersTable.resizeColumnsToContents()
        self.methodHandler.methodBuilderBox.setMinimumWidth(750)
