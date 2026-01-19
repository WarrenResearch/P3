import pandas as pd
import numpy as np

# Function for calculating theoretical glass transition temperature for a defined copolymer composition based on the Fox equation
def calculateTg(weightFrac, transitionTemps):

    glassTransitionTheoreticalReciprocal = 0
    for fraction, temperature in zip(weightFrac, transitionTemps):
        glassTransitionTheoreticalReciprocal += fraction/temperature

    glassTransitionTheoretical = 1/glassTransitionTheoreticalReciprocal

    return glassTransitionTheoretical

# Function for calculating the copolymer composition required for targeting a glass transition temperature. Considers the inclusion of two additional monomers in fixed weight fractions
# as per the standard formulation provided by Synthomer, though this needs generalising for broader applications
def calculateComposition(targetTg, fixedComponentFraction, componentTg):

    w1 = (1/((1/componentTg[0]) - (1/componentTg[1])))*((1/targetTg) - ((1 - fixedComponentFraction[0] - fixedComponentFraction[1])/componentTg[1]) - (fixedComponentFraction[0]/componentTg[2]) - (fixedComponentFraction[1]/componentTg[3]))
    w2 = 1 - w1 - fixedComponentFraction[0] - fixedComponentFraction[1]

    if 0 > w1 or w1 > 1:
        print("Target Tg cannot be obtained with these monomers")
        return

    return [round(w1, 2), round(w2, 2), fixedComponentFraction[0], fixedComponentFraction[1]]