import numpy as np
import pandas as pd

def buildOFAAT(bounds, variable, numExp):
    
    vals = np.linspace(bounds[0][0], bounds[0][1], numExp)

    if variable=="Emulsion-feeds":
        vals = np.round(np.linspace(bounds[0][0], bounds[0][1], numExp), 0)
    
    OFAAT_dict = {}
    for variable, bound in zip(variable, bounds):
        new_dict_item = {variable : bound}
        OFAAT_dict = {**OFAAT_dict, **new_dict_item}

    OFAAT_dict = {variable: vals}
    expDesign = pd.DataFrame.from_dict(OFAAT_dict)
    return expDesign