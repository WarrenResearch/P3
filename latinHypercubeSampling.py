from summit.domain import Domain, ContinuousVariable
from summit.strategies import LHS
import numpy as np
import pandas as pd

def getHypercubeSamplingParams(numExp, inputs):
    ''' function takes a set of parameters and their bounds and 
    returns a dictionary of random experiments in the parameter space '''

    domain = Domain()

    ### create variables with designated bounds from function inputs ###
    for variable in inputs:
        bound = inputs[variable]
        domain += ContinuousVariable(name=variable, description='', bounds=bound)

    ### create LHS suggested experiments ###
    randomState = np.random.random_integers(0, 100)
    strategy = LHS(domain, random_state=np.random.RandomState(randomState))
    hypersampling = strategy.suggest_experiments(numExp)

    ### create DF to hold conditions of each experiment ###
    hypersampling_df = pd.DataFrame(hypersampling)

    ### convert each set of experimental conditions to list ###
    params_dict = {}
    for i, name in zip(range(len(hypersampling_df.columns) - 1), inputs):
        params_temp = hypersampling_df.iloc[:, i].to_list()
        params_dict[name] = params_temp
    
    params_dict["Random state value"] = randomState

    return params_dict
