from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox
import pandas as pd
import seedAmountScreen
import surfactantScreen
import nFeedsScreen
import monomerScreen
import OFAATbuilder
import numpy as np
import threading
import datetime
# import latinHypercubeSampling
import time
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import flowrateCalculator
import DoEbuilder
import conventionalEP
import glassTransitionPredictor
import glob
import optimiser

class ExperimentMethod(QtWidgets.QWidget):
    def __init__(self, parent, main):
        super(ExperimentMethod, self).__init__(parent)

        self.main = main

        # Initialise each possible experimental method - each method calculates parameters slightly differently
        self.surfactantScreener = surfactantScreen.surfactantScreener(self, main=self.main)
        self.seedAmountScreener = seedAmountScreen.seedAmountScreener(self, main=self.main)
        self.nFeedsScreener = nFeedsScreen.nFeedsScreener(self, main=self.main)
        self.monomerScreener = monomerScreen.monomerScreener(self, main=self.main)
        self.conventionalEPHandler = conventionalEP.conventionalEP(self, main=self.main)
        
        # Set the master layout of the Method tab onto which all widgets are placed
        self.Layout = QtWidgets.QGridLayout()
        self.setLayout(self.Layout)
        
        ###################################### Method builder box ##############################################

        # Main groupBox for all input and calculated experimental parameters
        self.methodBuilderBox = QtWidgets.QGroupBox("Method builder")
        self.methodBuilderBox.setMaximumSize(680, 910)
        self.methodBuilderBox.setContentsMargins(10, 5, 10, 5)
        methodBuilderLayout = QtWidgets.QGridLayout()
        self.methodBuilderBox.setLayout(methodBuilderLayout)

        ################################## Polymerisation selector box #########################################

        # Create groupBox for selecting the type of polymerisation for the experiment and add grid layout
        self.polymerisationSelectorBox = QtWidgets.QGroupBox("Polymerisation selector")
        self.polymerisationSelectorBox.setMaximumSize(250, 100)
        self.polymerisationSelectorLayout = QtWidgets.QGridLayout()
        self.polymerisationSelectorBox.setLayout(self.polymerisationSelectorLayout)

        # Create a checkBox for each type of polymerisation available and setAutoExclusive so only one can be selected at a time
        self.conventionalEmulsionCheckBox = QtWidgets.QCheckBox("Seeded free-radical emulsion")
        self.conventionalEmulsionCheckBox.setAutoExclusive(True)
        self.conventionalEmulsionCheckBox.setChecked(True)

        # Add checkBoxes to layout
        self.polymerisationSelectorLayout.addWidget(self.conventionalEmulsionCheckBox, 0, 0)

        # Connect checkBox clicks to widget re-formatting function
        self.conventionalEmulsionCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.variableSelectorBox))

        ##################################### Method selector box ##############################################

        # Create groupBox for selecting the type of experiment to run and add grid layout
        methodSelectorBox = QtWidgets.QGroupBox("Select method type")
        methodSelectorBox.setMaximumSize(150, 100)
        methodBoxLayout = QtWidgets.QGridLayout()
        methodSelectorBox.setLayout(methodBoxLayout)

        # Create checkBoxes for each type of experiment and setAutoExclusive so only one can be selected at a time
        self.OFAATCheckBox = QtWidgets.QCheckBox("OFAAT")
        self.OFAATCheckBox.setAutoExclusive(True)
        self.DoECheckBox = QtWidgets.QCheckBox("DoE")
        self.DoECheckBox.setAutoExclusive(True)
        self.TSEMOCheckBox = QtWidgets.QCheckBox("TSEMO")
        self.TSEMOCheckBox.setAutoExclusive(True)

        # Add checkBoxes to layout
        methodBoxLayout.addWidget(self.OFAATCheckBox, 0, 0)
        methodBoxLayout.addWidget(self.DoECheckBox, 1, 0)
        methodBoxLayout.addWidget(self.TSEMOCheckBox, 2, 0)

        # Connect checkBox clicks to widget re-formatting function
        self.OFAATCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.variableSelectorBox))
        self.DoECheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.variableSelectorBox))
        self.TSEMOCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.variableSelectorBox))
        self.OFAATCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.propertyTargetingBox))
        self.DoECheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.propertyTargetingBox))
        self.TSEMOCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.propertyTargetingBox))

        ###################################### Variable selector box ############################################

        # Create groupBox to contain all variable fields
        self.variableSelectorBox = QtWidgets.QGroupBox("Define variables")
        self.variableSelectorBox.resize(300, 400)
        self.variableSelectorLayout = QtWidgets.QGridLayout()
        self.variableSelectorBox.setLayout(self.variableSelectorLayout)

        ########### Common variables #############
        self.reactor1VolumeLabel = QtWidgets.QLabel("CSTR volume (mL)")
        self.reactor1VolumeText = QtWidgets.QLineEdit("1.5")

        self.nCSTRsLabel = QtWidgets.QLabel("Number of CSTRs")
        self.nCSTRsText = QtWidgets.QLineEdit("5")

        self.reactor2VolumeLabel = QtWidgets.QLabel("Reactor 2 volume (mL)")
        self.reactor2VolumeText = QtWidgets.QLineEdit("5")

        self.sampleVolumeLabel = QtWidgets.QLabel("Sample volume (mL)")
        self.sampleVolumeText = QtWidgets.QLineEdit("5")

        self.monomerRatioText = QtWidgets.QLineEdit("1.0")
        self.monomerRatioText1 = QtWidgets.QLineEdit("Min A")
        self.monomerRatioText2 = QtWidgets.QLineEdit("Max A")
        self.monomerDensityLabel = QtWidgets.QLabel("Monomer density [g/mL]")
        self.monomerDensityText = QtWidgets.QLineEdit("0.9015")
        self.monomerDensityLabel1 = QtWidgets.QLabel("Monomer A density [g/mL]")
        self.monomerDensityText1 = QtWidgets.QLineEdit("Density A")
        self.monomerDensityLabel2 = QtWidgets.QLabel("Monomer B density [g/mL]")
        self.monomerDensityText2 = QtWidgets.QLineEdit("Density B")

        self.residenceTimeLabel = QtWidgets.QLabel("Residence time (CSTRs) [min]")
        self.residenceTimeText = QtWidgets.QLineEdit("50")

        self.productConcLabel = QtWidgets.QLabel("Product concentration [g/g]")
        self.productConcentrationText = QtWidgets.QLineEdit("0.3")
        self.productConcentrationText1 = QtWidgets.QLineEdit("Min")
        self.productConcentrationText2 = QtWidgets.QLineEdit("Max")

        self.numExpsLabel = QtWidgets.QLabel("Number of experiments")
        self.numExpsText = QtWidgets.QLineEdit("0")        

        ########### Conventional emulsion polymerisation variables ##############
        # Core variables #
        self.seedConcentrationLabel = QtWidgets.QLabel("Seed concentration [w/w]")
        self.seedConcentrationText = QtWidgets.QLineEdit("0.094")

        self.w_eMaxLabel = QtWidgets.QLabel("Max emulsion concentration [w/w]")
        self.w_eMaxText = QtWidgets.QLineEdit("0.7")

        # Optional variables #
        self.surfactantRatioCheckBox = QtWidgets.QCheckBox("Surfactant concentration [g/mL]")
        self.surfactantRatioText = QtWidgets.QLineEdit("0.025")
        self.surfactantRatioText1 = QtWidgets.QLineEdit("Min")
        self.surfactantRatioText2 = QtWidgets.QLineEdit("Max")

        self.seedAmountText = QtWidgets.QLineEdit("0.05")
        self.seedAmountText1 = QtWidgets.QLineEdit("Min R value")
        self.seedAmountText2 = QtWidgets.QLineEdit("Max R value")

        self.numFeedsText = QtWidgets.QLineEdit("4")
        self.numFeedsText1 = QtWidgets.QLineEdit("Min")
        self.numFeedsText2 = QtWidgets.QLineEdit("Max")

        self.monomerRatioCheckBox = QtWidgets.QCheckBox("Monomer ratio [g/g]")
        self.seedAmountCheckBox = QtWidgets.QCheckBox("Seed fraction [g/g]")
        self.feedRateCheckBox = QtWidgets.QCheckBox("Emulsion feeds")

        self.calculateParamsBtn = QtWidgets.QPushButton("\nCalculate parameters\n")
        self.calculateParamsBtn.setStyleSheet(
            "background-color: #e9e9e9;" 
            "color: black;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #6e6e6e;"
            "font-size: 10pt"
        )

        self.variableSelectorLayout.addWidget(self.reactor1VolumeLabel, 0, 0)
        self.variableSelectorLayout.addWidget(self.reactor1VolumeText, 0, 1)
        self.variableSelectorLayout.addWidget(self.nCSTRsLabel, 1, 0)
        self.variableSelectorLayout.addWidget(self.nCSTRsText, 1, 1)
        self.variableSelectorLayout.addWidget(self.reactor2VolumeLabel, 2, 0)
        self.variableSelectorLayout.addWidget(self.reactor2VolumeText, 2, 1)
        self.variableSelectorLayout.addWidget(self.sampleVolumeLabel, 3, 0)
        self.variableSelectorLayout.addWidget(self.sampleVolumeText, 3, 1)
        self.variableSelectorLayout.addWidget(self.w_eMaxLabel, 4, 0)
        self.variableSelectorLayout.addWidget(self.w_eMaxText, 4, 1)
        self.variableSelectorLayout.addWidget(self.monomerDensityLabel, 5, 0)
        self.variableSelectorLayout.addWidget(self.monomerDensityText, 5, 1)
        self.variableSelectorLayout.addWidget(self.residenceTimeLabel, 6, 0)
        self.variableSelectorLayout.addWidget(self.residenceTimeText, 6, 1)
        self.variableSelectorLayout.addWidget(self.productConcLabel, 7, 0)
        self.variableSelectorLayout.addWidget(self.productConcentrationText, 7, 1)
        self.variableSelectorLayout.addWidget(self.productConcentrationText1, 7, 1)
        self.variableSelectorLayout.addWidget(self.productConcentrationText2, 7, 2)
        self.variableSelectorLayout.addWidget(self.seedConcentrationLabel, 12, 0)
        self.variableSelectorLayout.addWidget(self.seedConcentrationText, 12, 1)
        self.variableSelectorLayout.addWidget(self.surfactantRatioCheckBox, 15, 0)
        self.variableSelectorLayout.addWidget(self.surfactantRatioText, 15, 1)
        self.variableSelectorLayout.addWidget(self.surfactantRatioText1, 15, 1)
        self.variableSelectorLayout.addWidget(self.surfactantRatioText2, 15, 2)
        self.variableSelectorLayout.addWidget(self.monomerRatioCheckBox, 16, 0)
        self.variableSelectorLayout.addWidget(self.monomerRatioText, 16, 1)
        self.variableSelectorLayout.addWidget(self.monomerRatioText1, 16, 1)
        self.variableSelectorLayout.addWidget(self.monomerDensityText1, 17, 1)
        self.variableSelectorLayout.addWidget(self.monomerRatioText2, 16, 2)
        self.variableSelectorLayout.addWidget(self.monomerDensityText2, 17, 2)
        self.variableSelectorLayout.addWidget(self.seedAmountCheckBox, 18, 0)
        self.variableSelectorLayout.addWidget(self.seedAmountText, 18, 1)
        self.variableSelectorLayout.addWidget(self.seedAmountText1, 18, 1)
        self.variableSelectorLayout.addWidget(self.seedAmountText2, 18, 2)
        self.variableSelectorLayout.addWidget(self.feedRateCheckBox, 19, 0)
        self.variableSelectorLayout.addWidget(self.numFeedsText, 19, 1)
        self.variableSelectorLayout.addWidget(self.numFeedsText1, 19, 1)
        self.variableSelectorLayout.addWidget(self.numFeedsText2, 19, 2)
        self.variableSelectorLayout.addWidget(self.numExpsLabel, 26, 0)
        self.variableSelectorLayout.addWidget(self.numExpsText, 26, 1)
        self.variableSelectorLayout.addWidget(self.calculateParamsBtn, 27, 0, 1, 2)

        self.surfactantRatioCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.variableSelectorBox))
        self.monomerRatioCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.variableSelectorBox))
        self.seedAmountCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.variableSelectorBox))
        self.feedRateCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.variableSelectorBox))

        self.calculateParamsBtn.clicked.connect(self.buildExperiment)
        
        # Rest widget by default until method selections are made
        for label in self.variableSelectorBox.findChildren(QtWidgets.QLabel):
            label.setHidden(True)
        for lineEdit in self.variableSelectorBox.findChildren(QtWidgets.QLineEdit):
            lineEdit.setHidden(True)
        for checkBox in self.variableSelectorBox.findChildren(QtWidgets.QCheckBox):
            checkBox.setHidden(True)

        ################################# Property targeting box #########################################
            
        # Create groupBox to contain all 'optimisable' properties
        self.propertyTargetingBox = QtWidgets.QGroupBox("Select optimisation targets")
        self.propertyTargetingBox.resize(300, 400)
        self.propertyTargetingLayout = QtWidgets.QGridLayout()
        self.propertyTargetingBox.setLayout(self.propertyTargetingLayout)

        self.particleSizeCheckBox = QtWidgets.QCheckBox("Particle size [nm]")
        self.particleSizeText = QtWidgets.QLineEdit("Size target")
        self.particleSizeMappingCheckBox = QtWidgets.QCheckBox("Enable size mapping (Flip-Flop)")

        self.surfactantConcentrationObjectiveCheckBox = QtWidgets.QCheckBox("Minimise surfactant [g/mL]")

        self.seedFractionObjectiveCheckBox = QtWidgets.QCheckBox("Minimise seed [g/g]")

        self.TgCheckBox = QtWidgets.QCheckBox("Tg (\u00b0C)")
        self.TgText = QtWidgets.QLineEdit("Tg target")
        self.TgPolymer1Text = QtWidgets.QLineEdit("Tg polymer 1")
        self.TgPolymer2Text = QtWidgets.QLineEdit("Tg polymer 2")
        self.fractionFixedCopolymer1Label = QtWidgets.QLabel("Fixed copolymer 1 conc [w/w]")
        self.fractionFixedCopolymer1Text = QtWidgets.QLineEdit("0.01")
        self.fractionFixedCopolymer2Label = QtWidgets.QLabel("Fixed copolymer 2 conc [w/w]")
        self.fractionFixedCopolymer2Text = QtWidgets.QLineEdit("0.02")
        self.TgFixedCopolymer1Label = QtWidgets.QLabel("Fixed copolymer 1 Tg [\u00b0C]")
        self.TgFixedCopolymer1Text = QtWidgets.QLineEdit("106")
        self.TgFixedCopolymer2Label = QtWidgets.QLabel("Fixed copolymer 2 Tg [\u00b0C]")
        self.TgFixedCopolymer2Text = QtWidgets.QLineEdit("228")
        self.calculateMonomerCompositionBtn = QtWidgets.QPushButton("Calculate monomer composition")
        self.monomerCompositionLabel1 = QtWidgets.QLabel("Monomer composition: ")
        self.monomerCompositionLabel2 = QtWidgets.QLabel()
        self.calculateMonomerCompositionBtn.setStyleSheet("background-color: #e9e9e9;" 
            "color: black;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #6e6e6e;"
            "font-size: 10pt")
        self.calculateMonomerCompositionBtn.setFixedSize(200, 50)

        self.trainingDataBrowseButton = QtWidgets.QPushButton('Select training data folder')
        self.trainingDataBrowseButton.setStyleSheet(
            "background-color: #e9e9e9;" 
            "color: black;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #6e6e6e"
        )
        self.trainingDataBrowseButton.clicked.connect(self.searchTrainingData)
        self.trainingDataBrowseButton.setFixedSize(200, 50)
        self.trainingDataPathText = QtWidgets.QLineEdit()

        self.maxIterationsLabel = QtWidgets.QLabel("Max iterations")
        self.maxIterationsText = QtWidgets.QLineEdit("30")

        self.sampleStrategyLabel = QtWidgets.QLabel("Sample every __ experiments")
        self.sampleStrategyText = QtWidgets.QLineEdit("3")

        self.propertyTargetingLayout.addWidget(self.particleSizeCheckBox, 0, 0)
        self.propertyTargetingLayout.addWidget(self.particleSizeText, 0, 1)
        self.propertyTargetingLayout.addWidget(self.particleSizeMappingCheckBox, 1, 0)
        self.propertyTargetingLayout.addWidget(self.surfactantConcentrationObjectiveCheckBox, 2, 0)
        self.propertyTargetingLayout.addWidget(self.seedFractionObjectiveCheckBox, 3, 0)
        self.propertyTargetingLayout.addWidget(self.TgCheckBox, 4, 0)
        self.propertyTargetingLayout.addWidget(self.TgText, 4, 1)
        self.propertyTargetingLayout.addWidget(self.TgPolymer1Text, 5, 1)
        self.propertyTargetingLayout.addWidget(self.TgPolymer2Text, 6, 1)
        self.propertyTargetingLayout.addWidget(self.fractionFixedCopolymer1Label, 7, 0)
        self.propertyTargetingLayout.addWidget(self.fractionFixedCopolymer1Text, 7, 1)
        self.propertyTargetingLayout.addWidget(self.fractionFixedCopolymer2Label, 8, 0)
        self.propertyTargetingLayout.addWidget(self.fractionFixedCopolymer2Text, 8, 1)
        self.propertyTargetingLayout.addWidget(self.TgFixedCopolymer1Label, 9, 0)
        self.propertyTargetingLayout.addWidget(self.TgFixedCopolymer1Text, 9, 1)
        self.propertyTargetingLayout.addWidget(self.TgFixedCopolymer2Label, 10, 0)
        self.propertyTargetingLayout.addWidget(self.TgFixedCopolymer2Text, 10, 1)
        self.propertyTargetingLayout.addWidget(self.calculateMonomerCompositionBtn, 11, 0, 1, 2)
        self.propertyTargetingLayout.addWidget(self.monomerCompositionLabel1, 12, 0)
        self.propertyTargetingLayout.addWidget(self.monomerCompositionLabel2, 13, 0)
        self.propertyTargetingLayout.addWidget(self.trainingDataBrowseButton, 14, 0, 1, 2)
        self.propertyTargetingLayout.addWidget(self.trainingDataPathText, 15, 0, 1, 2)
        self.propertyTargetingLayout.addWidget(self.maxIterationsLabel, 16, 0)
        self.propertyTargetingLayout.addWidget(self.maxIterationsText, 16, 1)
        self.propertyTargetingLayout.addWidget(self.sampleStrategyLabel, 17, 0)
        self.propertyTargetingLayout.addWidget(self.sampleStrategyText, 17, 1)

        self.propertyTargetingBox.setHidden(True)

        for label in self.propertyTargetingBox.findChildren(QtWidgets.QLabel):
            label.setHidden(True)
        for lineEdit in self.propertyTargetingBox.findChildren(QtWidgets.QLineEdit):
            lineEdit.setHidden(True)
        for checkBox in self.propertyTargetingBox.findChildren(QtWidgets.QCheckBox):
            checkBox.setHidden(True)
        self.calculateMonomerCompositionBtn.setHidden(True)
        self.trainingDataBrowseButton.setHidden(True)

        self.particleSizeCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.propertyTargetingBox))
        self.particleSizeMappingCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.propertyTargetingBox))
        self.TgCheckBox.clicked.connect(lambda: self.formatWidget(groupBox=self.propertyTargetingBox))
        self.calculateMonomerCompositionBtn.clicked.connect(self.calculateMonomerComposition)

        ###################################### Cleaning box ##############################################

        cleaningBox = QtWidgets.QGroupBox("Cleaning")
        cleaningBox.resize(300, 150)
        cleaningBox.setMaximumWidth(300) 
        self.cleaningBoxLayout = QtWidgets.QGridLayout()
        cleaningBox.setLayout(self.cleaningBoxLayout)

        self.cleaningRateLabel = QtWidgets.QLabel("Cleaning flow rate [mL/min]")
        self.cleaningRateText = QtWidgets.QLineEdit("5")
        self.cleaningRateText.setMaximumWidth(50)

        self.cleaningVolumesLabel = QtWidgets.QLabel("Number of reactor volumes")
        self.cleaningVolumesText = QtWidgets.QLineEdit("2")
        self.cleaningVolumesText.setMaximumWidth(50)

        self.samplesNumberLabel = QtWidgets.QLabel("Number of samples")
        self.samplesNumberText = QtWidgets.QLineEdit("7")
        self.samplesNumberText.setMaximumWidth(50)

        self.cleanSampleTubesButton = QtWidgets.QPushButton("\nClean autosampler\n")
        self.cleanSampleTubesButton.setStyleSheet(
            "background-color: #e9e9e9;" 
            "color: black;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #6e6e6e;"
            "font-size: 10pt"
        )

        self.emptyWasteButton = QtWidgets.QPushButton("\nWaste bottle emptied\n")
        self.emptyWasteButton.setStyleSheet(
            "background-color: #e9e9e9;" 
            "color: black;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #6e6e6e;"
            "font-size: 10pt"
        )

        self.wasteVolumeCounterLabel = QtWidgets.QLabel("Waste container volume\navailable (mL):")
        self.wasteVolumeCounterLabel.setStyleSheet(
            "font-size: 10pt"
        )
        self.wasteVolumeCounter = QtWidgets.QLabel()
        self.wasteVolumeCounter.setStyleSheet(
            "font-size: 10pt"
        )

        self.cleaningBoxLayout.addWidget(self.cleaningRateLabel, 0, 0)
        self.cleaningBoxLayout.addWidget(self.cleaningRateText, 0, 1)
        self.cleaningBoxLayout.addWidget(self.cleaningVolumesLabel, 1, 0)
        self.cleaningBoxLayout.addWidget(self.cleaningVolumesText, 1, 1)
        self.cleaningBoxLayout.addWidget(self.samplesNumberLabel, 2, 0)
        self.cleaningBoxLayout.addWidget(self.samplesNumberText, 2, 1)
        self.cleaningBoxLayout.addWidget(self.cleanSampleTubesButton, 3, 0, 1, 2)
        self.cleaningBoxLayout.addWidget(self.emptyWasteButton, 4, 0, 1, 2)
        self.cleaningBoxLayout.addWidget(self.wasteVolumeCounterLabel, 5, 0, QtCore.Qt.AlignTop)
        self.cleaningBoxLayout.addWidget(self.wasteVolumeCounter, 6, 0, 1, 2, QtCore.Qt.AlignTop)

        self.Layout.addWidget(cleaningBox, 0, 2, 5, 1)

        self.cleanSampleTubesButton.clicked.connect(self.startSamplerCleaning)
        self.emptyWasteButton.clicked.connect(self.wasteEmptied)

        ###################################### Calculated variables ############################################

        calcVarBox = QtWidgets.QGroupBox("Calculated variables")
        calcVarBox.setMaximumSize(680, 250)
        calcVarBoxLayout = QtWidgets.QGridLayout()
        calcVarBox.setLayout(calcVarBoxLayout)

        self.parametersTable = QtWidgets.QTableWidget()
        self.parametersTable.setMinimumWidth(600)

        ####################################### Save directory box #############################################

        self.directoryLineEdit = QtWidgets.QLineEdit()
        self.directoryLineEdit.setMaximumSize(300, 50)
        self.directoryBrowseButton = QtWidgets.QPushButton('Browse file locations')
        self.directoryBrowseButton.setMaximumSize(120, 50)
        self.directoryBrowseButton.setStyleSheet(
            "background-color: #e9e9e9;" 
            "color: black;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #6e6e6e"
        )
        self.directoryBrowseButton.clicked.connect(self.searchDirectories)
        self.experimentIDLineEdit = QtWidgets.QLineEdit()
        self.experimentIDLineEdit.setMaximumSize(120, 50)
        self.experimentIDLineEdit.setText(str(datetime.date.today()))
        self.setDataPathButton = QtWidgets.QPushButton('Set data path')
        self.setDataPathButton.setMaximumSize(100, 50)
        self.setDataPathButton.setStyleSheet(
            "background-color: #e9e9e9;" 
            "color: black;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #6e6e6e"
        )
        self.setDataPathButton.clicked.connect(self.setDataPath)
        self.directoryBox = QtWidgets.QGroupBox('Set save location')
        self.directoryBox.setMaximumSize(680, 50)
        directoryBoxLayout = QtWidgets.QHBoxLayout()
        self.directoryBox.setLayout(directoryBoxLayout)
        directoryBoxLayout.addWidget(self.directoryLineEdit, QtCore.Qt.AlignTop)
        directoryBoxLayout.addWidget(self.directoryBrowseButton, QtCore.Qt.AlignTop)
        directoryBoxLayout.addWidget(self.experimentIDLineEdit, QtCore.Qt.AlignTop)
        directoryBoxLayout.addWidget(self.setDataPathButton, QtCore.Qt.AlignTop)

        self.savePathCreated = 0 # Used to track if a save file has been created to store metadata and results

        ####################################### Dialogue widget ################################################

        # Used for displaying messages to the user

        self.dialogueLabel = QtWidgets.QLabel()
        self.ackButton = QtWidgets.QPushButton("OK")
        self.ackButton.setFixedSize(60, 30)
        self.ackButton.setStyleSheet(
            "background-color: #e9e9e9;" 
            "color: black;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #6e6e6e;"
            "font-size: 10pt"
        )
        self.dialogueLabel.setHidden(True)
        self.dialogueLabel.setStyleSheet(
            "background-color: #fcfc03;"
            "font-size: 10pt;"
            "border-radius: 5px"
        )
        self.ackButton.setHidden(True)        

        ####################################### Add methodBuilder widgets #############################################

        self.runButton = QtWidgets.QPushButton("\nStart experiment\n")
        self.runButton.setStyleSheet(
            "background-color: #0996D4;" 
            "color: white;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #2d5e86;"
            "font-size: 10pt")
        self.runButton.setFixedSize(200, 50)
        self.stopButton = QtWidgets.QPushButton("\nStop experiment\n")
        self.stopButton.setStyleSheet(
            "background-color: #d27b79;"
            "color: white;"
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #862f2d;"
            "font-size: 10pt")
        self.stopButton.setFixedSize(200, 50)
        methodBuilderLayout.addWidget(self.directoryBox, 0, 0, 1, 6, QtCore.Qt.AlignTop)
        methodBuilderLayout.addWidget(methodSelectorBox, 1, 0, 1, 2, QtCore.Qt.AlignTop)
        methodBuilderLayout.addWidget(self.polymerisationSelectorBox, 1, 2, 1, 2, QtCore.Qt.AlignTop)
        methodBuilderLayout.addWidget(self.variableSelectorBox, 2, 0, 2, 4, QtCore.Qt.AlignTop)
        methodBuilderLayout.addWidget(self.propertyTargetingBox, 2, 4, QtCore.Qt.AlignTop)
        methodBuilderLayout.addWidget(self.runButton, 5, 1, 1, 2, QtCore.Qt.AlignTop)
        methodBuilderLayout.addWidget(self.stopButton, 5, 3, 1, 2, QtCore.Qt.AlignTop)
        methodBuilderLayout.addWidget(self.dialogueLabel, 6, 1, 1, 3, QtCore.Qt.AlignTop)
        methodBuilderLayout.addWidget(self.ackButton, 6, 4, 1, 2, QtCore.Qt.AlignTop)
        self.Layout.addWidget(self.methodBuilderBox, 0, 0, 11, 1, QtCore.Qt.AlignTop)

        self.runButton.clicked.connect(self.startExperiment)
        self.stopButton.clicked.connect(self.stopExperimentManual)
        self.ackButton.clicked.connect(self.unpauseExperiment)

        ######################################## Method graph widget ############################################

        self.methodGraphBox = QtWidgets.QGroupBox("Experimental design")
        self.methodGraphLayout = QtWidgets.QGridLayout()
        self.methodGraphBox.setLayout(self.methodGraphLayout)
        self.Layout.addWidget(self.methodGraphBox, 0, 1, 5, 1)
        self.methodGraphLayout.addWidget(self.parametersTable, 0, 0, 2, 2, QtCore.Qt.AlignLeft)
        self.nGraph = 0 # To track number of times experimental graph has been constructed - if first time running the app, n = 0. Prevents multiple graphs being displayed

        ######################################## Platform diagram widget #########################################

        self.diaGroupBox = QtWidgets.QGroupBox("Experimental set-up")
        self.diaGroupBoxLayout = QtWidgets.QGridLayout()
        self.diaGroupBox.setLayout(self.diaGroupBoxLayout)
        diagramLoc = r'C:\Users\pm15pmp\Miniconda3\envs\MPSR\polymer_platform\231219_Pcubed\Conventional-EP.jpg'
        self.diagram = QtGui.QPixmap(diagramLoc)
        self.diaLabel = QtWidgets.QLabel(self)
        self.diaLabel.setPixmap(self.diagram)
        self.diaLabel.setScaledContents(True)
        self.diaLabel.setFixedSize(1100, 475)
    
        self.diaGroupBoxLayout.addWidget(self.diaLabel, 0, 4, 1000, 1000)
  
        self.Layout.addWidget(self.diaGroupBox, 5, 1, 6, 5)

    def calculateMonomerComposition(self):
        targetTg = float(self.TgText.text()) + 273
        polymer1Tg = float(self.TgPolymer1Text.text()) + 273
        polymer2Tg = float(self.TgPolymer2Text.text()) + 273
        fixedPolymer1Fraction = float(self.fractionFixedCopolymer1Text.text())
        fixedPolymer2Fraction = float(self.fractionFixedCopolymer2Text.text())
        fixedPolymer1Tg = float(self.TgFixedCopolymer1Text.text()) + 273
        fixedPolymer2Tg = float(self.TgFixedCopolymer2Text.text()) + 273

        transitionTemps = [polymer1Tg, polymer2Tg, fixedPolymer1Tg, fixedPolymer2Tg]
        fixedComponentFractions = [fixedPolymer1Fraction, fixedPolymer2Fraction]

        monomerComposition = glassTransitionPredictor.calculateComposition(targetTg, fixedComponentFractions, transitionTemps)
        self.monomerCompositionLabel2.setText(str(monomerComposition[0]) + ', '
                                                 + str(monomerComposition[1]) + ', '
                                                 + str(monomerComposition[2]) + ', '
                                                 + str(monomerComposition[3]))

    def formatWidget(self, groupBox):
        self.resetWidget(groupBox)
        self.runButton.setText("Start experiment")
        self.reactor1VolumeLabel.setHidden(False)
        self.reactor1VolumeText.setHidden(False)
        self.nCSTRsLabel.setHidden(False)
        self.nCSTRsText.setHidden(False)
        self.reactor2VolumeLabel.setHidden(False)
        self.reactor2VolumeText.setHidden(False)
        self.sampleVolumeLabel.setHidden(False)
        self.sampleVolumeText.setHidden(False)
        self.numExpsLabel.setHidden(False)
        self.numExpsText.setHidden(False)
        self.propertyTargetingBox.setHidden(True)
        self.calculateMonomerCompositionBtn.setHidden(True)
        self.numExpsLabel.setText("Number of experiments")

        if self.DoECheckBox.isChecked():
            self.numExpsLabel.setHidden(True)
            self.numExpsText.setHidden(True)

        if self.TSEMOCheckBox.isChecked():
            self.propertyTargetingBox.setHidden(False)
            self.trainingDataBrowseButton.setHidden(False)
            self.trainingDataPathText.setHidden(False)
            self.maxIterationsLabel.setHidden(False)
            self.maxIterationsText.setHidden(False)
            self.sampleStrategyLabel.setHidden(False)
            self.sampleStrategyText.setHidden(False)
            self.numExpsLabel.setText("Number of LHC experiments")
            self.runButton.setText("Start optimisation")
            for checkBox in self.propertyTargetingBox.findChildren(QtWidgets.QCheckBox):
                checkBox.setHidden(False)
                self.particleSizeMappingCheckBox.setHidden(True)
            if self.TgCheckBox.isChecked():
                self.TgText.setHidden(False)
                self.TgPolymer1Text.setHidden(False)
                self.TgPolymer2Text.setHidden(False)
                self.TgFixedCopolymer1Label.setHidden(False)
                self.TgFixedCopolymer1Text.setHidden(False)
                self.TgFixedCopolymer2Label.setHidden(False)
                self.TgFixedCopolymer2Text.setHidden(False)
                self.fractionFixedCopolymer1Label.setHidden(False)
                self.fractionFixedCopolymer1Text.setHidden(False)
                self.fractionFixedCopolymer2Label.setHidden(False)
                self.fractionFixedCopolymer2Text.setHidden(False)
                self.calculateMonomerCompositionBtn.setHidden(False)
                self.monomerCompositionLabel1.setHidden(False)
                self.monomerCompositionLabel2.setHidden(False)
            
            if self.particleSizeCheckBox.isChecked():
                self.particleSizeText.setHidden(False)
                self.particleSizeMappingCheckBox.setHidden(False)

            if self.particleSizeMappingCheckBox.isChecked():
                self.particleSizeText.setHidden(True) 
                
        if self.OFAATCheckBox.isChecked():
            self.surfactantRatioCheckBox.setAutoExclusive(True)
            self.monomerRatioCheckBox.setAutoExclusive(True)
            self.seedAmountCheckBox.setAutoExclusive(True)
            self.feedRateCheckBox.setAutoExclusive(True)
        else:
            self.surfactantRatioCheckBox.setAutoExclusive(False)
            self.monomerRatioCheckBox.setAutoExclusive(False)
            self.seedAmountCheckBox.setAutoExclusive(False)
            self.feedRateCheckBox.setAutoExclusive(False)
            
    ######################################### Free-radical emulsion formatting #########################################

        if self.conventionalEmulsionCheckBox.isChecked():
            self.residenceTimeText.setHidden(False)
            self.w_eMaxLabel.setHidden(False)
            self.w_eMaxText.setHidden(False)
            self.productConcLabel.setHidden(False)
            self.productConcentrationText.setHidden(False)
            self.seedConcentrationLabel.setHidden(False)
            self.seedConcentrationText.setHidden(False)
            self.monomerDensityLabel.setHidden(False)
            self.monomerDensityText.setHidden(False)
            self.residenceTimeLabel.setHidden(False)
            self.surfactantRatioCheckBox.setHidden(False)
            self.surfactantRatioText.setHidden(False)
            self.monomerRatioCheckBox.setHidden(False)
            self.monomerRatioText.setHidden(False)
            self.monomerDensityLabel.setHidden(False)
            self.monomerDensityText.setHidden(False)
            self.seedAmountCheckBox.setHidden(False)
            self.seedAmountText.setHidden(False)
            self.feedRateCheckBox.setHidden(False)
            self.numFeedsText.setHidden(False)
        else:
            self.surfactantRatioCheckBox.setChecked(False)
            self.monomerRatioCheckBox.setChecked(False)
            self.seedAmountCheckBox.setChecked(False)
            self.feedRateCheckBox.setChecked(False)

        if self.surfactantRatioCheckBox.isChecked():
            self.surfactantRatioText1.setHidden(False)
            self.surfactantRatioText2.setHidden(False)
            self.surfactantRatioText.setHidden(True)

        if self.monomerRatioCheckBox.isChecked():
            self.monomerRatioText1.setHidden(False)
            self.monomerRatioText2.setHidden(False)
            self.monomerDensityText1.setHidden(False)
            self.monomerDensityText2.setHidden(False)
            self.monomerRatioText.setHidden(True)
            self.monomerDensityLabel.setHidden(True)
            self.monomerDensityText.setHidden(True)

        if self.seedAmountCheckBox.isChecked():
            self.seedAmountText1.setHidden(False)
            self.seedAmountText2.setHidden(False)
            self.w_eMaxText.setHidden(False)
            self.seedAmountText.setHidden(True)

        if self.feedRateCheckBox.isChecked():
            self.numFeedsText1.setHidden(False)
            self.numFeedsText2.setHidden(False)
            self.numFeedsText.setHidden(True)

    def resetWidget(self, groupBox):
        for label in groupBox.findChildren(QtWidgets.QLabel):
            label.setHidden(True)
        for lineEdit in groupBox.findChildren(QtWidgets.QLineEdit):
            lineEdit.setHidden(True)
        for checkBox in groupBox.findChildren(QtWidgets.QCheckBox):
            checkBox.setHidden(True)

    def buildExperiment(self):

        # Make sure a method has been selected:
        if not (self.OFAATCheckBox.isChecked() or self.DoECheckBox.isChecked() or self.TSEMOCheckBox.isChecked()):
            print('Please select a method')

        ### Catch issues with more than one variable being selected for an OFAAT experiment
        variableCounter = 0
        for checkBox in self.variableSelectorBox.findChildren(QtWidgets.QCheckBox):
            if checkBox.isChecked():
                variableCounter = variableCounter + 1
        if self.OFAATCheckBox.isChecked() and variableCounter > 1:
            print("Too many variables selected for OFAAT experiment - please just choose one")
            return

        '''First collect all the experimental parameters from user inputs - error handling to
        ignore problems with trying to read default text like "min" and "max" in hidden lineEdits'''

        # Get common fixed parameters from user inputs #
        volumeCSTR = [float(self.reactor1VolumeText.text())] # Volume of a single CSTR
        numberCSTRs = [int(self.nCSTRsText.text())] # Number of CSTRs in cascade
        volumeReactor2 = [float(self.reactor2VolumeText.text())]
        deadVolume = [1] # Volume of tubing between reactor outlet and sampling valve [mL]
        volumeSample = [float(self.sampleVolumeText.text())] # Specify amount of sample to collect
        densityAq = [1] # Density of aqueous solution (assuming water)
        densityMonomer = [float(self.monomerDensityText.text())] # Density of monomer if composition is kept constant [g/mL]
        densityProduct = [1] # Density of final product (assuming density of water for now)
        numExp = int(self.numExpsText.text()) # Number of experiments to run/samples to take
        cleanRate = [float(self.cleaningRateText.text())] # Flow rate for solvent washing
        cleanTime = [float(self.cleaningVolumesText.text())*((volumeCSTR[0]*numberCSTRs[0]) + volumeReactor2[0])/cleanRate[0]] # Time taken to clean between reactions (min)
        cleanVolume = [cleanRate[0]*cleanTime[0]] # Volume of material used for each cleaning step (mL)
        flushTime = 2*((volumeCSTR[0]*numberCSTRs[0]) + volumeReactor2[0])/cleanRate[0] # Time taken to flush reactor after experiment

        # Get common variable parameters from user inputs #
        w_f = [float(self.productConcentrationText.text())] # Specify final product concentration [w/w]
        try:
            w_fMin = [float(self.productConcentrationText1.text())] # Minimum product concentration [w/w]
            w_fMax = [float(self.productConcentrationText2.text())] # Maximum product concentration [w/w]
        except(ValueError): pass

        tau = [float(self.residenceTimeText.text())] # Residence time - for seeded processes this is the average RT of a single seed particle [min]

        densityInitiator = [1] # Density of initiator solution [g/mL]
        
        monomerAFraction = [float(self.monomerRatioText.text())]
        try:
            monomerAFractionMin = [float(self.monomerRatioText1.text())] # Minimum fraction [w/w] of monomer 'A' (value between 0.0 and 1.0)
            monomerAFractionMax = [float(self.monomerRatioText2.text())] # Maximum fraction [w/w] of monomer 'A' (value between 0.0 and 1.0)
            densityMonomerA = [float(self.monomerDensityText1.text())] # Density of monomer 'A' [g/mL]
            densityMonomerB = [float(self.monomerDensityText2.text())] # Density of monomer 'B' [g/mL]
        except(ValueError): 
            densityMonomerA = [float(self.monomerDensityText.text())]
            densityMonomerB = [0]

        # Get fixed parameters specific to conventional emulsion polymerisation #
        w_s = [float(self.seedConcentrationText.text())] # Specify seed concentration [w/w]
        densitySeed = [1] # Density of latex seed (assuming density of water, can be measured before exp)

        # Get variable parameters specific to conventional emulsion polymerisation #
        surfactantRatio = [float(self.surfactantRatioText.text())] # Surfactant concentration in emulsion if amount is kept constant [w/w]
        w_Aq = [float(self.surfactantRatioText.text())] # Minimum surfactant concentration [g/g]
        w_Aq1 = w_Aq # If surfactant concentration not varied, w_Aq1 takes w_Aq value
        w_Aq2 = [0]

        try:
            surfactantRatioMin = [float(self.surfactantRatioText1.text())] # Minimum bound of surfactant concentration in emulsion [w/w]
            surfactantRatioMax = [float(self.surfactantRatioText2.text())] # Maximum bound of surfactant concentration in emulsion [w/w]
        except(ValueError): pass

        densitySurfactant = [1] # Density of surfactant solution [g/mL]
        seedFrac = [float(self.seedAmountText.text())] # Seed fraction if kept constant (ratio of seed solids to total solids content of product)
        try:
            seedFracMin = [float(self.seedAmountText1.text())] # Minimum seed fraction (ratio of seed solids to total solids content of product)
            seedFracMax = [float(self.seedAmountText2.text())] # Maximum seed fracion (ratio of seed solids to total solids content of product)
        except(ValueError): pass    

        numEmulsionFeeds = [int(self.numFeedsText.text())] # Number of emulsion feeds if kept constant
        try:
            numEmulsionFeedsMin = [int(self.numFeedsText1.text())] # Minimum number of emulsion feeds (proxy for emulsion feed rate)
            numEmulsionFeedsMax = [int(self.numFeedsText2.text())] # Maximum number of emulsion feeds (proxy for emulsion feed rate)
        except(ValueError): pass

        '''Next part of the function collects all the selected parameters (names 
        and bounds) into lists ready to be handled by the chosen method'''

        self.parameterNames = [] # Blank list to hold the names (str) of the varied parameters involved in the experiment
        self.parameterBounds = [] # Blank list to hold the min/max of each selected parameter [min, max]

        # If OFAAT method selected, build an index list to loop over based on the number of experiments required
        if self.OFAATCheckBox.isChecked():
            expIndex = np.linspace(0, numExp - 1, num=numExp)
        
        # For each possible variable, check if it has been selected and either a) run a OFAAT calculation or b) add the name 
        # and bounds to the experiment builder lists above     

        if self.surfactantRatioCheckBox.isChecked():
            surfactantRatioBounds = surfactantRatioMin + surfactantRatioMax
            w_Aq1 = [float(self.surfactantRatioText1.text())] # Minimum bound of surfactant concentration in emulsion [w/w]
            w_Aq2 = [float(self.surfactantRatioText2.text())] # Maximum bound of surfactant concentration in emulsion [w/w]

            # if self.OFAATCheckBox.isChecked():
            #     parameters = 0# >>call function for varying surfactant concentration
            # else:
            self.parameterNames.append("Surfactant_concentration")
            self.parameterBounds.append(surfactantRatioBounds)

        if self.monomerRatioCheckBox.isChecked():
            monomerRatioBounds = monomerAFractionMin + monomerAFractionMax

            # if self.OFAATCheckBox.isChecked():
            #     parameters = 0# >>call function for varying monomer ratio
            # else:
            self.parameterNames.append("Monomer-A-fraction")
            self.parameterBounds.append(monomerRatioBounds)

        if self.seedAmountCheckBox.isChecked():
            seedAmountBounds = seedFracMin + seedFracMax

            # if self.OFAATCheckBox.isChecked():
            #     parameters = 0# >>call function for varying seed amount
            # else:
            self.parameterNames.append("Seed_fraction")
            self.parameterBounds.append(seedAmountBounds)

        if self.feedRateCheckBox.isChecked():
            emulsionFeedsBounds = numEmulsionFeedsMin + numEmulsionFeedsMax

            # if self.OFAATCheckBox.isChecked():
            #     parameters = 0# >>call function for varying number of feeds
            # else:
            self.parameterNames.append("Emulsion-feeds")
            self.parameterBounds.append(emulsionFeedsBounds)

        '''Now pass the lists of varied parameters to the relevant experiment builder (DoE or LHS) to return a
        dataFrame containing experimental conditions for a series of pre-programmed experiments'''

        if self.OFAATCheckBox.isChecked():
            expDesign = OFAATbuilder.buildOFAAT(self.parameterBounds, self.parameterNames, numExp)

        if self.DoECheckBox.isChecked():
            if len(self.parameterNames) == 1:
                print("Please select more variables for DoE experiment")
                return
            expDesign = DoEbuilder.buildCC(self.parameterBounds, self.parameterNames)

        if self.TSEMOCheckBox.isChecked():

            self.optIterations = 0 # Tracks the total number of experimental iterations (including training data)
            self.maxIterations = int(self.maxIterationsText.text())
            self.inputsDict = {}
            for variable, bounds in zip(self.parameterNames, self.parameterBounds):
                self.inputsDict[variable] = bounds

            self.objectivesDict = {} # Build a dictionary for passing objective variables to the algorithm
            if self.particleSizeCheckBox.isChecked():
                particleSizeBounds = [0, 1000] # Arbitrary broad bounds of particle size
                if self.particleSizeMappingCheckBox.isChecked():
                    strategy = "FLIPFLOP" # 'FLIPFLOP' strategy is employed when we want to map particle sizes whilst min/max-ing other objectives, this alternates between minimising and maximising the particle size objective
                    self.sizeKey = "Particle_size"
                    self.sizeTarget=None
                else:
                    strategy = "MIN"
                    self.sizeTarget = self.particleSizeText.text()
                    self.sizeKey = "Size_function" # For targeting a specific size we need to convert particle size to a function we can minimise, not sure exactly how to handle this for now
                self.objectivesDict[(self.sizeKey, strategy)] = particleSizeBounds
            
            if self.surfactantConcentrationObjectiveCheckBox.isChecked():
                surfactantConcBounds = [surfactantRatioMax[0], surfactantRatioMax[0]]
                self.objectivesDict[("Surfactant_concentration_min", "MIN")] = surfactantConcBounds # Always want to minimise surfactant concentration by default

            if self.seedFractionObjectiveCheckBox.isChecked():
                seedFractionBounds = [seedFracMin[0], seedFracMax[0]]
                self.objectivesDict[("Seed_fraction_min", "MIN")] = seedFractionBounds # Always want to minimise seed fraction by default
        
            allVariables=[] # Put all inputs and objectives in a list, used for checking that the training data provides all the required information
            for var in list(self.inputsDict.keys()):
                allVariables.append(var)
            for obj in list(self.objectivesDict.keys()):
                allVariables.append(obj[0])
            
            self.trainingDataQ=False
            if not self.trainingDataPathText.text()=='': # If training data lineEdit is not blank (i.e. training data has been given)
                self.trainingDataQ=True # Update trainingDataQuery to true so the optimiser knows to use training data
                self.trainingDataPath = self.trainingDataPathText.text()
                countFiles = 0
                for file in glob.glob(self.trainingDataPath + r"\*.xlsx"): # Counts all files in the training data directory, must be exactly 1 excel sheet of training data
                    countFiles+=1
                self.nonExclusiveTrainingDataMsgBox = QMessageBox()
                self.nonExclusiveTrainingDataMsgBox.setStandardButtons(QMessageBox.Ok)
                if countFiles > 1:
                    self.nonExclusiveTrainingDataMsgBox.setWindowTitle("Too many files in specified directory")
                    self.nonExclusiveTrainingDataMsgBox.setText("Tried to read more than one file in the specified directory, please\nput the training data in its own folder and reselect the path")
                    self.nonExclusiveTrainingDataMsgBox.exec()
                elif countFiles < 1:
                    self.nonExclusiveTrainingDataMsgBox.setWindowTitle("No files found in current directory")
                    self.nonExclusiveTrainingDataMsgBox.setText("No files found in the specified directory, please check the location\nof your training data and that it is .xlsx format")
                    self.nonExclusiveTrainingDataMsgBox.exec()
                if self.nonExclusiveTrainingDataMsgBox.clickedButton() is self.nonExclusiveTrainingDataMsgBox.button(QMessageBox.Ok):
                    return
                else:
                    self.trainingDatadf = pd.read_excel(file)
                    self.trainingDataDict = self.trainingDatadf.to_dict(orient='list') # convert the training data excel file to a dictionary
                self.optIterations = self.trainingDatadf.shape[0] # Update the total number of experimental iterations to include the training data

                # Check that all the variables in the training data match the selected inputs and objectives of the current experiment
                for key_to_check in allVariables:
                    try:
                        check = self.trainingDataDict[key_to_check]
                    except KeyError:
                        self.missingVariableMsgBox = QMessageBox()
                        self.missingVariableMsgBox.setStandardButtons(QMessageBox.Ok)
                        self.missingVariableMsgBox.setWindowTitle("Selected variable does not exist in training data")
                        self.missingVariableMsgBox.setText("Either an input or objective variable is missing from the training data, please match\nthe training data with the inputs and objectives you are using")
                        self.missingVariableMsgBox.exec()
                        if self.missingVariableMsgBox.clickedButton() is self.missingVariableMsgBox.button(QMessageBox.Ok):
                            return
                expDesign = optimiser.getNextExperiment(self.inputsDict, 
                                                        self.objectivesDict,
                                                        self.optIterations,
                                                        current_dataSet=self.trainingDataDict)
            
            # Get LHC sampling experiments or request training data
            if int(self.numExpsText.text()) > 0:
                self.LHCQ = True # Set LHCQ true if the user has specified to run LHC experiments
                # self.expDesignDict = latinHypercubeSampling.getHypercubeSamplingParams(numExp, self.inputsDict)
                expDesign = pd.DataFrame(self.expDesignDict)
            elif not self.trainingDataQ:
                self.LHCQ = False # Set LHCQ false if the user has NOT specified to run LHC experiments
                self.noLHCMsgBox = QMessageBox()
                self.noLHCMsgBox.setWindowTitle("No LHC experiments planned")
                self.noLHCMsgBox.setText("You have selected to run zero LHC experiments, either provide your own training data\nor continue and the algorithm will run its own LHC")
                self.noLHCMsgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                self.noLHCMsgBox.setDefaultButton(QMessageBox.Cancel)
                self.noLHCMsgBox.exec()
                if self.noLHCMsgBox.standardButton(self.noLHCMsgBox.clickedButton()) == QMessageBox.Ok:
                    expDesign = optimiser.getNextExperiment(self.inputsDict, 
                                                            self.objectivesDict, 
                                                            iteration=self.optIterations)
                if self.noLHCMsgBox.clickedButton() is self.noLHCMsgBox.button(QMessageBox.Cancel):
                    return

            if self.trainingDataQ: # If training data is provided, add the expDesign (from initial conditions or LHC) to it
                self.optimisationSummary = self.trainingDataDict # Store the training data in a new 'optimisation summmary' which holds the input and objective variables
                for key in expDesign:
                    self.optimisationSummary[key].extend(expDesign[key]) # Append the new input variables from the expDesign to the optimisation summary
            else: # Otherwise, create a blank optimisation summary and fill it in with the expDesign
                self.optimisationSummary = {}
                for var in allVariables:
                    self.optimisationSummary[var] = []
                for key in expDesign:
                    if key in self.optimisationSummary:
                        self.optimisationSummary[key].extend(expDesign[key])
                    
            expDesign = pd.DataFrame(expDesign)

        '''Use the experimental design to build lists for each variable with n elements based on the
        'shape' of expDesign. Having each variable as a list (even a list of the same repeating value)
        allows the pump flow rates to be calculated in the calculateFlowrates function for any future
        combination of varied experimental parameters'''

        numExp = pd.DataFrame.from_dict(expDesign).shape[0]
        self.expIndex = np.linspace(0, numExp - 1, numExp)
        self.variablesDict = {}
        for n in range(0, numExp-1):
            ### Core variables ###
            volumeCSTR.append(volumeCSTR[0])
            numberCSTRs.append(numberCSTRs[0])
            volumeReactor2.append(volumeReactor2[0])
            deadVolume.append(deadVolume[0])
            volumeSample.append(volumeSample[0])
            densityInitiator.append(densityInitiator[0])
            densityAq.append(densityAq[0])
            densityProduct.append(densityProduct[0])
            tau.append(tau[0])
            w_f.append(w_f[0])
            monomerAFraction.append(monomerAFraction[0])
            densityMonomer.append(densityMonomer[0])
            densityMonomerA.append(densityMonomerA[0])
            densityMonomerB.append(densityMonomerB[0])
            cleanRate.append(cleanRate[0])
            cleanTime.append(cleanTime[0])
            cleanVolume.append(cleanVolume[0])
            
            ### Conventional emulsion polymerisation variables ###
            w_s.append(w_s[0])
            densitySurfactant.append(densitySurfactant[0])
            densitySeed.append(densitySeed[0])
            w_Aq1.append(w_Aq1[0])
            w_Aq2.append(w_Aq2[0])
            w_Aq.append(w_Aq[0])
            surfactantRatio.append(surfactantRatio[0])
            seedFrac.append(seedFrac[0])
            numEmulsionFeeds.append(numEmulsionFeeds[0])

        '''Now build a dict of parameter key-words and their list of values, and recreate the lists of 
        those parameters that are varied by substituting them to the values specified by the experimental design'''
        
        self.variablesDict = {
            'volumeCSTR' : volumeCSTR,
            'numberCSTRs' : numberCSTRs,
            'volumeReactor2' : volumeReactor2,
            'deadVolume' : deadVolume,
            'volumeSample' : volumeSample,
            'densityInitiator' : densityInitiator,
            'densityAq' : densityAq,
            'densityProduct' : densityProduct,
            'tau' : tau,
            'w_f' : w_f,
            'monomerAFraction' : monomerAFraction,
            'densityMonomer' : densityMonomer,
            'densityMonomerA' : densityMonomerA,
            'densityMonomerB' : densityMonomerB,
            'w_s' : w_s,
            'densitySurfactant' : densitySurfactant,
            'densitySeed' : densitySeed,
            'surfactantRatio' : surfactantRatio,
            'Surfactant_concentration' : w_Aq,
            'w_Aq1' : w_Aq1,
            'w_Aq2' : w_Aq2,
            'Seed_fraction' : seedFrac,
            'numEmulsionFeeds' : numEmulsionFeeds,
            'cleanRate' : cleanRate,
            'cleanTime' : cleanTime,
            'cleanVolume' : cleanVolume
        }

        '''Substitute the 'default' values of the manipulated variables for the lists defined by the experimental design'''

        for columnName in expDesign:

            if columnName == "Random state value": # Collect the random state value for building the latin hypercube and then drop it from the DF. This will make it accessible in the experiment summary but not interfere with plotting/formatting
                randomStateValue = expDesign[columnName].to_list()
                self.variablesDict["Random state value"] = randomStateValue
                expDesign.drop(columns="Random state value", inplace=True, axis=1)

            if columnName == 'Surfactant_concentration':
                surfactantRatio = expDesign[columnName].to_list()
                self.variablesDict["Surfactant_concentration"] = list(np.round(surfactantRatio, 3))

            if columnName == 'Monomer-A-fraction':
                monomerAFraction = expDesign[columnName].to_list()
                self.variablesDict["monomerAFraction"] = list(np.round(monomerAFraction, 3))

                densityMonomer = [] # Calculate sequence of monomer densities as the weighted average of the two monomers in their defined ratio
                for i in monomerAFraction:
                    densityMonomer_temp = np.round((i*densityMonomerA[0] + (1 - i)*densityMonomerB[0]), 3)
                    densityMonomer.append(densityMonomer_temp)
                
                self.variablesDict["densityMonomerA"] = densityMonomerA
                self.variablesDict["densityMonomerB"] = densityMonomerB
                self.variablesDict["densityMonomer"] = densityMonomer

            if columnName == 'Seed_fraction':
                seedFrac = expDesign[columnName].to_list()
                self.variablesDict["Seed_fraction"] = list(np.round(seedFrac, 3))

            if columnName == 'Emulsion-feeds':
                numEmulsionFeeds = expDesign[columnName].to_list()
                self.variablesDict["numEmulsionFeeds"] = numEmulsionFeeds

        '''Now pass the dict to the appropriate calculator'''

        if self.conventionalEmulsionCheckBox.isChecked():
            self.flowRates = flowrateCalculator.calculateFlowrates(
                'conventional',
                self.variablesDict,
                numExp, 
                )

            self.main.controller.pump1.setHidden(False)
            self.main.controller.pump2.setHidden(False)
            self.main.controller.pump4.setHidden(False)
            self.main.controller.pump5.setHidden(False)
            self.main.controller.pump6.setHidden(False)
            self.main.controller.pump10.setHidden(False)            
            if self.monomerRatioCheckBox.isChecked():
                self.main.controller.pump3.setHidden(False)

        self.variablesDict.update(self.flowRates)
        
        '''After creating the experimental design, the following code is used to display the table and graph in the GUI'''

        if self.conventionalEmulsionCheckBox.isChecked():
            
            self.v_seed = self.flowRates.get('v_seed')
            self.v_Aq1 = self.flowRates.get('v_Aq1')
            self.v_Aq2 = self.flowRates.get('v_Aq2')
            self.v_monomerA = self.flowRates.get('v_monomerA')
            self.v_monomerB = self.flowRates.get('v_monomerB')
     
        # Build parameters table for reference
            self.parametersTable.setRowCount(10)
            self.parametersTable.setColumnCount(numExp)
            self.parametersTable.setVerticalHeaderLabels(
                ['Surfactant concentration (g/g)',
                'Monomer A fraction (g/g)', 
                'Seed fraction (g/g)',
                'Emulsion feeds',
                'Seed flow rate (mL/min)',
                'Aq-1 flow rate (mL/min)',
                'Aq-2 flow rate (mL/min)',
                'Monomer A flow rate (mL/min)',
                'Monomer B flow rate (mL/min)'])
            
            for i in self.expIndex.astype(int):
                tablew_Aq = QtWidgets.QTableWidgetItem(str(round(surfactantRatio[i], 4)))
                tableMA_fraction = QtWidgets.QTableWidgetItem(str(round(monomerAFraction[i], 4)))
                tableR_s = QtWidgets.QTableWidgetItem(str(round(seedFrac[i], 4)))
                tablenFeeds = QtWidgets.QTableWidgetItem(str(numEmulsionFeeds[i]))
                tablev_seed = QtWidgets.QTableWidgetItem(str(round(self.v_seed[i], 4)))
                tablev_Aq1 = QtWidgets.QTableWidgetItem(str(round(self.v_Aq1[i], 4)))
                tablev_Aq2 = QtWidgets.QTableWidgetItem(str(round(self.v_Aq2[i], 4)))
                tablev_monomerA = QtWidgets.QTableWidgetItem(str(round(self.v_monomerA[i], 4)))
                tablev_monomerB = QtWidgets.QTableWidgetItem(str(round(self.v_monomerB[i], 4)))
                self.parametersTable.setItem(0, i, tablew_Aq)
                self.parametersTable.setItem(1, i, tableMA_fraction)
                self.parametersTable.setItem(2, i, tableR_s)
                self.parametersTable.setItem(3, i, tablenFeeds)
                self.parametersTable.setItem(4, i, tablev_seed)
                self.parametersTable.setItem(5, i, tablev_Aq1)
                self.parametersTable.setItem(6, i, tablev_Aq2)
                self.parametersTable.setItem(7, i, tablev_monomerA)
                self.parametersTable.setItem(8, i, tablev_monomerB)

            self.parametersTable.resizeColumnsToContents()

        self.parametersTable.resizeColumnsToContents()

        if not self.nGraph == 0: # Clear old graph if one has already been displayed
            plt.close(self.fig)
            self.methodGraphLayout.removeWidget(self.canvas)
            self.methodGraphLayout.removeWidget(self.toolbar)

        self.nGraph = 1 # Lets the function know that this isn't the first time displaying a graph to clear the old graph
        self.fig = plt.figure()
        self.fig.clear()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(canvas=self.canvas)
        self.methodGraphLayout.addWidget(self.toolbar, 0, 3, QtCore.Qt.AlignTop)
        self.methodGraphLayout.addWidget(self.canvas, 1, 3, QtCore.Qt.AlignTop)

        # Create a dictionary of 'var(i) : parameterName' used for plotting the design in GUI #
        expDesign_vars = {}
        for i, name in zip(range(len(self.parameterNames)), self.parameterNames):
            var_name = "var%d" % i
            expDesign_vars[var_name] = name
        designColumns = list(expDesign.columns)

        if len(designColumns) <= 2:
            self.ax = self.fig.add_subplot(111)
            self.fig.subplots_adjust(left=0.2, bottom=0.15)
        elif len(designColumns) == 3:
            self.ax = self.fig.add_subplot(111, projection='3d')
            self.fig.subplots_adjust(bottom=0.2)

        plotArgs = []
        if self.OFAATCheckBox.isChecked():
            plotArgs.append(expDesign.index)
        for i in designColumns:
            newPlotArg = [expDesign[i]]
            plotArgs.append(newPlotArg)

        if len(designColumns) < 4:
            self.ax.scatter(*plotArgs, c='#0996D4', marker='o')
            x_variable = expDesign_vars.get("var0")
            y_variable = expDesign_vars.get("var1")
            if self.OFAATCheckBox.isChecked():
                x_variable = "Reaction number"
                y_variable = expDesign_vars.get("var0")
            self.ax.set_xlabel(x_variable)
            self.ax.set_ylabel(y_variable)
            if len(designColumns) == 3:
                z_variable = expDesign_vars.get("var2")
                self.ax.set_zlabel(z_variable)

    def startExperiment(self):
        self.startMsgBox = QMessageBox()
        self.startMsgBox.setWindowTitle("Confirm waste bottle emptied")
        self.startMsgBox.setText("Confirm you have emptied the waste bottle - do not continue the experiment without doing so")
        self.startMsgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.startMsgBox.setDefaultButton(QMessageBox.Cancel)
        self.startMsgBox.exec()
        if self.startMsgBox.standardButton(self.startMsgBox.clickedButton()) == QMessageBox.Ok:
            self.wasteVolumeAvailable = 980 # Resets the volume available in the waste bottle to 980 mL (2% margin of safety)
            self.wasteVolumeCounter.setText(str(round(self.wasteVolumeAvailable, 1)))
        if self.startMsgBox.clickedButton() is self.startMsgBox.button(QMessageBox.Cancel):
            return
        self.saveSummaryData()
        self.stopThread = False
        self.manualStop = False
        self.runButton.setStyleSheet(
            "background-color: #8fd9a7;" 
            "color: black;" 
            "border-radius:5px;"
            "border: 1px solid;"
            "border-color: #002b0e;"
            "font-size: 10pt"
        )
        self.runButton.setText("\nExperiment in progress...\n")

        self.optimisationFlag=0
        # If OFAAT selected:
        if self.OFAATCheckBox.isChecked():
            # If surfactant concentration selected:
            if self.surfactantRatioCheckBox.isChecked():
                print('Starting surfactant screen experiment')
            if self.monomerRatioCheckBox.isChecked():
                print('Starting monomer fraction screening experiment')
            if self.seedAmountCheckBox.isChecked():
                print('Starting seed fraction screening experiment')
            if self.feedRateCheckBox.isChecked():
                print('Starting feed-rate screening experiment')

        if self.DoECheckBox.isChecked():
            print('Starting DoE experiment')        

        if self.TSEMOCheckBox.isChecked():
            self.optimisationFlag=1

        if self.conventionalEmulsionCheckBox.isChecked():
            self.conventionalEPHandler.startEP()

    def stopExperiment(self):
        self.stopThread = True
        self.manualStop = False

    def stopExperimentManual(self):
        # Stop an experiment with manual flag true (doesn't immediately start cleaning reactor)
        self.stopThread = True
        self.manualStop = True
        print('Experiment aborted by user at ' + str(datetime.datetime.now()))
        self.main.methodHandler.runButton.setChecked(False)
        self.main.methodHandler.runButton.setText('\nStart experiment\n')
        self.main.methodHandler.runButton.setStyleSheet(
        "background-color: #0996D4;" 
        "color: white;" 
        "border-radius:5px;"
        "border: 1px solid;"
        "border-color: #2d5e86;"
        "font-size: 10pt"
        )

    def unpauseExperiment(self):
        self.pauseExperiment = False
        self.dialogueLabel.setHidden(True)
        self.ackButton.setHidden(True)

    def startSamplerCleaning(self):
        self.sampleCleanThread = threading.Thread(target=self.cleanSampler)
        self.sampleCleanThread.start()
        self.stopCleanThread = False
    
    def stopSamplerCleaning(self):
        self.sampleCleanThread.join()
        self.stopCleanThread = True

    def cleanSampler(self):
        # Script for conveniently cleaning all sample ports
        solventPump = self.main.controller.pump6
        solventValve = self.main.controller.valve1
        emulsionValve = self.main.controller.valve2
        outletValve = self.main.controller.valve3
        nSamples = int(self.samplesNumberText.text())

        while not self.stopCleanThread:

            emulsionValve.valveSwitch(5)
            solventPump.start()

            for i in range(2, nSamples + 2):
                outletValve.valveSwitch(i)
                portTimerStart = datetime.datetime.now()
                while not self.stopCleanThread and (datetime.datetime.now() - portTimerStart).seconds < 45:
                    time.sleep(1)
                
                if i == (nSamples - 1):
                    solventValve.valveSwitch(position='B')
            
            for i in reversed(range(2, nSamples + 2)):
                outletValve.valveSwitch(i)
                portTimerStart = datetime.datetime.now()
                while not self.stopCleanThread and (datetime.datetime.now() - portTimerStart).seconds < 45:
                    time.sleep(1)
            break
        print("Sampler cleaning finished")
        return
    
    def wasteEmptied(self):
        self.wasteMsgBox = QMessageBox()
        self.wasteMsgBox.setWindowTitle("Confirm waste bottle emptied")
        self.wasteMsgBox.setText("Confirm you have emptied the waste bottle - do not continue the experiment without doing so")
        self.wasteMsgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.wasteMsgBox.setDefaultButton(QMessageBox.Cancel)
        self.wasteMsgBox.exec()
        if self.wasteMsgBox.standardButton(self.wasteMsgBox.clickedButton()) == QMessageBox.Ok:
            print("Waste bottle volume reset")
            self.wasteVolumeAvailable = 980 # Resets the volume available in the waste bottle to 980 mL (2% margin of safety)
            return
        if self.wasteMsgBox.clickedButton() is self.wasteMsgBox.button(QMessageBox.Cancel):
            return

    def searchDirectories(self):
        self.activeFolder = QtWidgets.QFileDialog.getExistingDirectory(self, caption='Select save folder')
        print(self.activeFolder)
        self.directoryLineEdit.setText(self.activeFolder)

    def searchTrainingData(self):
        self.trainingDataFolder = QtWidgets.QFileDialog.getExistingDirectory(self, caption='Select training data folder')
        self.trainingDataPathText.setText(self.trainingDataFolder)

    def setDataPath(self):
        self.saveFolder = (str(self.directoryLineEdit.text()) + '/')
        self.savePath = (self.saveFolder + self.experimentIDLineEdit.text())
        print("savePath: " + str(self.savePath))
        self.savePathCreated = 1

    def saveSummaryData(self):
        # Saves a summary of the experimental conditions in pre-programmed experiments (OFAAT and DoE) into the save path #
        self.expSummary = pd.DataFrame(self.variablesDict)
        summarySavePath = (self.savePath + '-summary.csv')
        pd.DataFrame(self.expSummary).to_csv(summarySavePath)
        print("Summary data saved")

    def getNewConditions(self, current_dataSet=None, strategy="TSEMO"):
        if strategy=="TSEMO":
            newConditions = optimiser.getNextExperiment(self.inputsDict, # inputs dictionary is defined by the method handler when parameters are calculated
                                                             self.objectivesDict, # objectives dictionary is defined by the method handler when parameters are calculated
                                                             self.optIterations, # number of total experimental iterations is held in the method handler
                                                             current_dataSet=current_dataSet) # current_dataSet can be updated externally and new conditions returned here
            
            for key in newConditions:
                newExpCount = len(newConditions[key]) # Count how many new experiments were added (usually 1 but gives room to request multiple suggested experiments)
                pass
            for key in self.variablesDict:
                if key in newConditions:
                    self.variablesDict[key].extend(newConditions[key]) # If the keyword (input variable) exists in the newConditions dict, append the new value(s) to the corresponding list in
                    self.optimisationSummary[key].extend(newConditions[key])
                elif not key in self.flowRates:
                    for i in range(newExpCount): # Else, count how many new conditions were added, and extend the constant variables (V_CSTR, nCSTRs etc.) with their first/default value
                        self.variablesDict[key].append(self.variablesDict[key][0])
                

            if self.conventionalEmulsionCheckBox.isChecked():
                newFlowRates = flowrateCalculator.calculateFlowrates('conventional',
                                                                        self.variablesDict,
                                                                        type="optimisation")                
                for key in newFlowRates:
                    self.variablesDict[key].extend(newFlowRates[key])
            return self.variablesDict
        
        
