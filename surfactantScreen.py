# Function/script for screening surfactant concentration written for OFAAT experiments

# Takes two input arguments of controller and methodHandler. Controller is the instance of platformControl
# created in the GUI initialisation, methodHandler is the method builder used to instantiate the method (may not be fully accurate)
from PyQt5 import QtWidgets, QtCore, QtSerialPort
import threading
import numpy as np
import datetime
import time

class surfactantScreener(QtWidgets.QWidget):
    def __init__(self, parent, main):
        super(surfactantScreener, self).__init__(parent)
        
        self.main = main

        # self.pumpSeed = self.controller.pump1
        # self.pumpMonomer = self.controller.pump2
        # self.pumpAq1 = self.controller.pump4
        # self.pumpAq2 = self.controller.pump5
        # self.pumpSolvent = self.controller.pump6

        # self.valveSolvent = self.controller.valve1
        # self.valveEmulsion = self.controller.valve2
        # self.valveOutlet = self.controller.valve3

    def startExperiment(self):
        # Start experiment thread here with call to run script
        self.experimentThread = threading.Thread(target=self.runScript)
        self.experimentThread.start()
        self.stopThread = False

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
                self.pumpSeed.setFlowrateText.setText(str(np.round(10*self.v_seed, 4)))
                self.pumpAq1.setFlowrateText.setText(str(np.round(10*self.v_Aq1_seq[i], 4)))
                self.pumpAq2.setFlowrateText.setText(str(np.round(10*self.v_Aq2_seq[i], 4)))
                self.pumpMonomer.setFlowrateText.setText(str(np.round(10*self.v_monomer_seq[i], 4)))

                self.pumpSeed.setFlowrate()
                self.pumpAq1.setFlowrate()
                self.pumpAq2.setFlowrate()
                self.pumpMonomer.setFlowrate()
                self.pumpSeed.start()
                self.pumpAq1.start()
                self.pumpAq2.start()
                self.pumpMonomer.start()

                # Calculate and start time to prepare emulsion (3 CSTR volumes at preparation flow rate)
                preparationTime = 60*3*self.V_CSTR/(10*self.v_Aq1_seq[i] + 10*self.v_Aq2_seq[i] + 10*self.v_monomer_seq[i])
                startPreparationTime = datetime.datetime.now()
                while not self.stopThread and (datetime.datetime.now() - startPreparationTime).seconds < preparationTime:
                    time.sleep(1)

                # Reduce flow rates to reaction flow rates and begin distributing emulsion to CSTRs
                self.pumpSeed.setFlowrateText.setText(str(np.round(self.v_seed, 4)))
                self.pumpAq1.setFlowrateText.setText(str(np.round(self.v_Aq1_seq[i], 4)))
                self.pumpAq2.setFlowrateText.setText(str(np.round(self.v_Aq2_seq[i], 4)))
                self.pumpMonomer.setFlowrateText.setText(str(np.round(self.v_monomer_seq[i], 4)))
                
                self.pumpSeed.setFlowrate()
                self.pumpAq1.setFlowrate()
                self.pumpAq2.setFlowrate()
                self.pumpMonomer.setFlowrate()

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
                sampleTime = 60*self.V_sample/(self.v_seed + self.v_Aq1_seq[i] + self.v_Aq2_seq[i] + self.v_monomer_seq[i]) # Time to collect sample at current flow rate
                startSampleTime = datetime.datetime.now()
                print('At steady state, start sampling until ' + str(startSampleTime + datetime.timedelta(seconds=sampleTime)))
                while not self.stopThread and (datetime.datetime.now() - startSampleTime).seconds < sampleTime:
                    time.sleep(1)

                # Sample collected, start cleaning cycle
                self.valveOutlet.valveHome()
                self.pumpSeed.stop()
                self.pumpAq1.stop()
                self.pumpAq2.stop()
                self.pumpMonomer.stop()

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
                    self.pumpAq1.stop()
                    self.pumpAq2.stop()
                    self.pumpMonomer.stop()
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
            self.pumpAq1.stop()
            self.pumpAq2.stop()
            self.pumpMonomer.stop()

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
    w_Aq1, 
    w_Aq2, 
    M_density, 
    S_density, 
    Aq_density,
    E_density, 
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
        self.w_Aq_seq = np.linspace(w_Aq1, w_Aq2, numExp) # Series of targeted surfactant concentrations between min and max
        self.nEmulsionFeeds = nEmulsionFeeds
        self.cleanRate = cleanRate
        self.cleanTime = cleanTime

        #### Calculation of seed flow rate to target an average seed residence time for i emulsion feeds in n CSTRs ####
        emulsionFeedsIndex = np.linspace(1, self.nEmulsionFeeds, num=self.nEmulsionFeeds)
        summation = 0
        for i in emulsionFeedsIndex:
            summation_temp = 1/(1 + ((S_density/E_density)*((w_s/(w_f*R_s)) - 1))*(1-((self.nEmulsionFeeds-i)/self.nEmulsionFeeds)))
            summation = summation + summation_temp

        A = (S_density/E_density)*((w_s/(w_f*R_s)) - 1)
        B = (nCSTRs - self.nEmulsionFeeds)/(1 + A)
        self.v_seed = (V_CSTR/tau)*(summation + B)
        self.v_emulsion = ((S_density*self.v_seed)/E_density)*((w_s/(w_f*R_s)) - 1)
        self.v_total = self.v_seed + self.v_emulsion
        self.w_emulsion = (w_f*(E_density*self.v_emulsion + S_density*self.v_seed) - (w_s*S_density*self.v_seed))/(E_density*self.v_emulsion)
        
        self.v_monomer_seq = np.array([])
        self.v_Aq_seq = np.array([])
        self.v_Aq1_seq = np.array([])
        self.v_Aq2_seq = np.array([])

        for i in self.w_Aq_seq:
            v_monomer = (E_density*self.v_emulsion*(self.w_emulsion - i))/(M_density*(1 - i))
            self.v_monomer_seq = np.append(self.v_monomer_seq, v_monomer)

            v_Aq = (E_density*self.v_emulsion*(1 - self.w_emulsion))/(Aq_density*(1 - i))
            self.v_Aq_seq = np.append(self.v_Aq_seq, v_Aq)
    
        for x, y in zip(self.v_Aq_seq, self.w_Aq_seq):
            v_Aq1 = (Aq_density*x*(y - w_Aq2))/(Aq_density*(w_Aq1 - w_Aq2))
            self.v_Aq1_seq = np.append(self.v_Aq1_seq, v_Aq1)

            v_Aq2 = (Aq_density*x*(y - w_Aq1))/(Aq_density*(w_Aq2 - w_Aq1))
            self.v_Aq2_seq = np.append(self.v_Aq2_seq, v_Aq2)

        #### Calculate required volumes ####
        Vol_seed = 0 # Volume of seed required to perform series of experiments
        Vol_seed_waste = 0 # Volume of seed contributing to waste volume
        Vol_monomer = 0 # Volume of monomer mixture required to perform series of experiments
        Vol_monomer_prep = 0 # Volume of monomer mixture required during emulsion preparation
        Vol_monomer_waste = 0 # Volume of monomer contributing to waste volume
        Vol_Aq1 = 0 # Volume of Aq1 required to perform series of experiments
        Vol_Aq1_prep = 0 # Volume of Aq1 required during emulsion preparation
        Vol_Aq1_waste = 0 # Volume of Aq1 contributing to waste volume
        Vol_Aq2 = 0 # Volume of Aq2 required to perform series of experiments
        Vol_Aq2_prep = 0 # Volume of Aq2 required during emulsion preparation
        Vol_Aq2_waste = 0 # Volume of Aq2 contributing to waste volume
        for x, y, z in zip(self.v_monomer_seq, self.v_Aq1_seq, self.v_Aq2_seq):
            sampleTime_exp = self.V_sample/(x + y + z + self.v_seed) # Get the time taken to sample for each experiment in the series (total flow rates vary)
            preparationTime = 3*V_CSTR/(10*x + 10*y + 10*z) # Emulsion prepared at 10 x flow rate for convenince (3 CSTR volumes)
            Vol_seed_exp = self.v_seed*(self.reactionTime + sampleTime_exp + 3*self.V_reactor2/(x + y + z + self.v_seed)) # Required seed volume is the amount used during reaction + amount used during sampling
            Vol_seed_prep = self.v_seed*10*preparationTime
            Vol_seed = Vol_seed + Vol_seed_exp + Vol_seed_prep
            Vol_seed_waste_exp = y*self.reactionTime
            Vol_seed_waste = Vol_seed_waste + Vol_seed_waste_exp

            Vol_monomer_exp = x*(self.reactionTime + sampleTime_exp + 3*self.V_reactor2/(x + y + z + self.v_seed)) # Same for required monomer volume...
            Vol_monomer_prep = 10*x*preparationTime
            Vol_monomer = Vol_monomer + Vol_monomer_prep + Vol_monomer_exp
            Vol_monomer_waste_exp = x*self.reactionTime + x*3*(self.V_reactor2/(x + y + z + self.v_seed))
            Vol_monomer_waste = Vol_monomer_waste + Vol_monomer_waste_exp

            Vol_Aq1_exp = y*(self.reactionTime + sampleTime_exp + 3*self.V_reactor2/(x + y + z + self.v_seed)) # ...and required Aq1 volume...
            Vol_Aq1_prep = 10*y*preparationTime
            Vol_Aq1 = Vol_Aq1 + Vol_Aq1_prep + Vol_Aq1_exp
            Vol_Aq1_waste_exp = y*self.reactionTime + y*3*(self.V_reactor2/(x + y + z + self.v_seed))
            Vol_Aq1_waste = Vol_Aq1_waste + Vol_Aq1_waste_exp

            Vol_Aq2_exp = z*(self.reactionTime + sampleTime_exp + 3*self.V_reactor2/(x + y + z + self.v_seed)) # ...and required Aq2 volume.
            Vol_Aq2_prep = 10*z*preparationTime
            Vol_Aq2 = Vol_Aq2 + Vol_Aq2_prep + Vol_Aq2_exp
            Vol_Aq2_waste_exp = z*self.reactionTime + z*3*(self.V_reactor2/(x + y + z + self.v_seed))
            Vol_Aq2_waste = Vol_Aq2_waste + Vol_Aq2_waste_exp
        
        V_waste = Vol_seed_waste + Vol_monomer_waste + Vol_Aq1_waste + Vol_Aq2_waste + 3.5*numExp*cleanRate*cleanTime + cleanTime*cleanRate + flushTime*cleanRate + 1*cleanRate
        
        # Build parameters table for reference
        self.main.methodHandler.methodBuilderBox.setMinimumWidth(600)
        self.main.methodHandler.parametersTable.setRowCount(8)
        self.main.methodHandler.parametersTable.setColumnCount(numExp)
        self.main.methodHandler.parametersTable.setVerticalHeaderLabels(
            ['Surfactant concentration (g/g)',
            'Seed flow rates (mL/min)', 
            'Aq-1 flow rates (mL/min)',
            'Aq-2 flow rates (mL/min)',
            'Monomer flow rates (mL/min)',
            'Number of feeds',
            'Seed ratio',
            'Emulsion concentration (% w/w)'])
        for i in self.expIndex.astype(int):
            w_Aq = QtWidgets.QTableWidgetItem(str(np.round(self.w_Aq_seq[i], 4)))
            v_seed = QtWidgets.QTableWidgetItem(str(np.round(self.v_seed, 4)))
            v_Aq1 = QtWidgets.QTableWidgetItem(str(np.round(self.v_Aq1_seq[i], 4)))
            v_Aq2 = QtWidgets.QTableWidgetItem(str(np.round(self.v_Aq2_seq[i], 4)))
            v_monomer = QtWidgets.QTableWidgetItem(str(np.round(self.v_monomer_seq[i], 4)))
            nFeeds = QtWidgets.QTableWidgetItem(str(self.nEmulsionFeeds))
            R_seed = QtWidgets.QTableWidgetItem(str(R_s))
            w_emulsion = QtWidgets.QTableWidgetItem(str(np.round(self.w_emulsion, 4)))
            self.main.methodHandler.parametersTable.setItem(0, i, w_Aq)
            self.main.methodHandler.parametersTable.setItem(1, i, v_seed)
            self.main.methodHandler.parametersTable.setItem(2, i, v_Aq1)
            self.main.methodHandler.parametersTable.setItem(3, i, v_Aq2)
            self.main.methodHandler.parametersTable.setItem(4, i, v_monomer)
            self.main.methodHandler.parametersTable.setItem(5, i, nFeeds)
            self.main.methodHandler.parametersTable.setItem(6, i, R_seed)
            self.main.methodHandler.parametersTable.setItem(7, i, w_emulsion)

        self.main.methodHandler.parametersTable.resizeColumnsToContents()
        # self.main.methodHandler.methodBuilderBox.setMinimumWidth(750)
