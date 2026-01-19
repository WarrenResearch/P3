import numpy as np
from types import SimpleNamespace

def calculateFlowrates(method, parameters, numExp=1, type="standard"):
    expIndex = np.linspace(0, numExp - 1, numExp)
###### For generalisation, take an argument for the type of polymerisation used and run the calculation for each type ######## e.g. if type=conventionalEmulsion: do these calcs...
    
    vars = SimpleNamespace(**parameters) # Convert all dict items from variables argument to variables (as lists so need indexing when used)
    # calculate a list of emulsion concentrations
    w_emulsion = []
    for r, f in zip(vars.Seed_fraction, vars.w_f):
        w_emulsion_temp = (f*vars.w_s[0]*(1 - r))/(vars.w_s[0] - f*r)
        w_emulsion.append(w_emulsion_temp)

    # subsequently calculate the emulsion densities (weighted average of monomer and aqueous phase densities)
    densityEmulsion = [] 
    for e, m in zip(w_emulsion, vars.densityMonomer):
        densityEmulsion_temp = m*e + (1-e)*vars.densityAq[0]
        densityEmulsion.append(densityEmulsion_temp)
   
    v_seed = []
    v_emulsion = []
    v_total = []
    v_monomers = []
    v_monomerA = []
    v_monomerB = []
    v_Aq = []
    v_Aq1 = []
    v_Aq2 = []

    for i in expIndex.astype(int):
        if type=="optimisation": # If optimisation experiment, we want to keep all variables in the provided 'parameters' dictionary and only find the new flowrates for the last set of conditions
            i=-1
        emulsionFeedsIndex = np.linspace(1, vars.numEmulsionFeeds[i], int(vars.numEmulsionFeeds[i]))
        summation = 0
        for f in emulsionFeedsIndex:
            summation_temp = 1/(1 + ((vars.densitySeed[i]/densityEmulsion[i])*((vars.w_s[i]/(vars.w_f[i]*vars.Seed_fraction[i])) - 1))*(1-((vars.numEmulsionFeeds[i]-f)/vars.numEmulsionFeeds[i])))
            summation = summation + summation_temp
        A = (vars.densitySeed[i]/densityEmulsion[i])*((vars.w_s[i]/(vars.w_f[i]*vars.Seed_fraction[i])) - 1)
        B = (vars.numberCSTRs[i] - vars.numEmulsionFeeds[i])/(1 + A)
        v_seed_temp = round(((vars.volumeCSTR[i]/vars.tau[i])*(summation + B)), 4)
        v_seed.append(v_seed_temp)
        v_emulsion_temp = ((vars.densitySeed[i]*v_seed_temp)/densityEmulsion[i])*((vars.w_s[i]/(vars.w_f[i]*vars.Seed_fraction[i])) - 1)
        v_emulsion.append(v_emulsion_temp)
        v_total_temp = v_seed_temp + v_emulsion_temp
        v_total.append(v_total_temp)
        
        v_monomers_temp = (v_emulsion[i]*densityEmulsion[i]*(vars.Surfactant_concentration[i] - w_emulsion[i]))/(vars.densityMonomer[i]*(vars.Surfactant_concentration[i] - 1))
        v_monomers.append(v_monomers_temp)

        v_monomerA_temp = round((vars.densityMonomer[i]*v_monomers[i]*vars.monomerAFraction[i]/vars.densityMonomerA[i]), 4)
        v_monomerA.append(v_monomerA_temp)
        
        if vars.densityMonomerB[i] == 0: # Conditional to avoid divide by zero error if monomer ratio not varied
            v_monomerB_temp = 0
            v_monomerB.append(v_monomerB_temp)
        else:
            v_monomerB_temp = round((vars.densityMonomer[i]*v_monomers[i]*(1-vars.monomerAFraction[i])/vars.densityMonomerB[i]), 4)
            v_monomerB.append(v_monomerB_temp)
        
        v_Aq_temp = round((((densityEmulsion[i]*v_emulsion[i])-(vars.densityMonomer[i]*v_monomers[i]))/(vars.densityAq[i])), 4)
        v_Aq.append(v_Aq_temp)

        v_Aq1_temp = round(((vars.densityAq[i]*v_Aq[i]*(vars.Surfactant_concentration[i] - vars.w_Aq2[i]))/(vars.densityAq[i]*(vars.w_Aq1[i] - vars.w_Aq2[i]))), 4)
        v_Aq1.append(v_Aq1_temp)

        v_Aq2_temp = round(((vars.densityAq[i]*v_Aq[i]*(vars.Surfactant_concentration[i] - vars.w_Aq1[i]))/(vars.densityAq[i]*(vars.w_Aq2[i] - vars.w_Aq1[i]))), 4)
        v_Aq2.append(v_Aq2_temp)

    flowRatesDict = {
        'v_seed' : v_seed,
        'v_Aq1' : v_Aq1,
        'v_Aq2' : v_Aq2,
        'v_monomerA' : v_monomerA,
        'v_monomerB' : v_monomerB
    }
    return flowRatesDict