from summit.domain import *
from summit.strategies import TSEMO
from summit.utils.dataset import DataSet
import pandas as pd

def getNextExperiment(inputs, objectives, iteration, current_dataSet=None):
    '''
    Function takes input variables and objectives as dict of {"parameter name" : [minBound, maxBound]}
    
    For objective variables, the dict keys must be tuples indicating whether the objective is to be maximised
    or minimised, i.e. {("parameter name", "MIN") : [minBound, maxBound]}

    current_dataSet is the previous experimental data passed as a dict of {"parameter name" : [value1, value2, ... valuen]}
    
    iteration (usually used to count the number of iterations for a given optimisation), lets the objective be 'FLIPFLOPed'
    alternately to switch an objective, i.e. in the case where a maximisation and minimisation maps out an objective space
    
    '''
    if iteration%2:
        maximize_FLIPFLOP = 1
    else:
        maximize_FLIPFLOP = 0

    domain = Domain()
    for variable in inputs:
        bound = inputs[variable]
        domain += ContinuousVariable(name=str(variable), description='', bounds=bound)

    for objective in objectives:
        bound = objectives[objective]
        if objective[1] == "MIN":
            maximize=False
        elif objective[1] == "MAX":
            maximize=True
        elif objective[1] == "FLIPFLOP":
            maximize=maximize_FLIPFLOP
        domain += ContinuousVariable(name=str(objective[0]), description='', bounds=bound, is_objective=True, maximize=maximize)

    print(f"Getting new reaction conditions for experiment {iteration}...")
    df = pd.DataFrame(data=current_dataSet)
    previous_data = DataSet.from_df(df)
    strategy = TSEMO(domain)
    next_experiments = strategy.suggest_experiments(1, previous_data)
    next_experiments_df = pd.DataFrame(next_experiments)
    parameter_names = list(inputs.keys())
    params_dict = {}
    for i, name in zip(range(len(next_experiments_df.columns) - 1), parameter_names):
        params_temp = round(next_experiments_df.iloc[:, i], 5).to_list()
        params_dict[name] = params_temp
    return params_dict