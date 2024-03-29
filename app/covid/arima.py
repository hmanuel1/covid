"""
   Fit ARIMA model to cases and deaths for each US State
"""

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import pmdarima as pm

from database import DataBase
from sql import STATES_VIEW_TABLE


# output - database
ARIMA_CASES_TABLE = 'arima_cases'
ARIMA_DEATHS_TABLE = 'arima_deaths'


def arima_model(data, y_var):
    """Perform ARIMA and return results

    Arguments:
        data {DataFrame} -- data for model
        y_var {String} -- column name for independent variable 'ŷ'

    Returns:
        DataFrame -- prediction and confidence intervals
    """
    results = dict(index=[], state_id=[], state=[], upper=[], lower=[], predict=[])

    for state_id, state in zip(data['state_id'].unique(), data['state'].unique()):
        # select state data
        data_state = data[data['state'] == state]
        data_state = data_state.sort_values('date').reset_index(drop=True)

        # Create Training and Test
        train = []
        train.append(0)
        for i in range(len(data_state) - 1):
            x = data_state[y_var][i + 1] - data_state[y_var][i]
            train.append(x)

        # auto arima
        model = pm.auto_arima(train, start_p=1, start_q=1,
                              test='adf',       # use adftest to find optimal 'd'
                              max_p=3, max_q=3,  # maximum p and q
                              m=1,              # frequency of series
                              d=None,           # let model determine 'd'
                              seasonal=False,   # No Seasonality
                              start_P=0,
                              D=0,
                              trace=False,
                              error_action='ignore',
                              suppress_warnings=True,
                              stepwise=True)

        # Forecast
        _, confint = model.predict(n_periods=15, return_conf_int=True)
        index_of_fc = np.arange(len(train), len(train) + 15)

        # replace negative values to zero
        lower = [x if x > 0 else 0 for x in confint[:, 0]]
        upper = [x if x > 0 else 0 for x in confint[:, 1]]

        # convert to cumulative begining with the last actual value
        lower = (data_state[y_var].iat[-1] + pd.Series(lower).cumsum())
        upper = (data_state[y_var].iat[-1] + pd.Series(upper).cumsum())

        # save results for this state
        results['index'] += [index_of_fc[0] - 1] + list(index_of_fc)
        results['state_id'] += [state_id] * (len(index_of_fc) + 1)
        results['state'] += [state] * (len(index_of_fc) + 1)
        results['upper'] += [data_state[y_var].iat[-1]] + list(upper)
        results['lower'] += [data_state[y_var].iat[-1]] + list(lower)
        results['predict'] += [data_state[y_var].iat[-1]] + list((lower + upper) / 2)

    return pd.DataFrame(results)


def run_arima(data, y_var, show_results=False):
    """Call ARIMA function and add predicted results to original data

    Arguments:
        data {DataFrame} -- ny times cumulative covid19 cases and deaths
        y_var {String} -- column name of predicted variable 'ŷ'

    Keyword Arguments:
        show_results {bool} -- plot model results (default: {False})

    Returns:
        DataFrame -- prediction results
    """
    result = data.copy(deep=True)

    # run arima model
    arima = arima_model(result, y_var)

    # merge prediction with data and plotted
    arima['start'] = arima['state'].map(data.groupby(['state']).min()['date'])
    arima['date'] = arima['start'] + pd.to_timedelta(arima['index'], 'days')
    arima['actual'] = np.nan

    cols = ['date', 'state_id', 'state', 'actual', 'upper', 'lower', 'predict']
    arima = arima[cols].copy(deep=True)

    result = result.rename(columns={y_var: 'actual'})
    result['upper'] = np.nan
    result['lower'] = np.nan
    result['predict'] = np.nan
    result = pd.concat([result, arima], axis=0, ignore_index=True)

    if show_results:
        for state in ['Florida', 'Georgia', 'Alabama', 'New York']:
            result_state = result[result['state'] == state]
            plt.plot(result_state['date'], result_state['actual'], color='blue')
            plt.plot(result_state['date'], result_state['predict'], color='green')
            plt.fill_between(result_state['date'],
                             result_state['lower'],
                             result_state['upper'],
                             color='k', alpha=.15)
        plt.show()

    return result


def predict():
    """main module function to predict covid19 cases and deaths

    Inputs from databae:
        US_STATES_TABLE {database table} -- nytimes covid19 data

    Outputs to database:
        ARIMA_CASES_TABLE {database table} -- cases[predict, upper, lower]
        ARIMA_DEATHS_TABLE {database table } -- deaths[predict, upper, lower]
    """
    _db = DataBase()
    data = _db.get_table(STATES_VIEW_TABLE, parse_dates=['date'])
    _db.close()

    # predict cases
    result = run_arima(data, 'cases')

    # only data after 3/15/2020
    slicer = result['date'] > pd.to_datetime('3/15/2020')
    result = result.loc[slicer, :].copy(deep=True)
    result.sort_values(['date', 'state'], inplace=True)
    result = result.round(0)

    _db = DataBase()
    _db.add_table(ARIMA_CASES_TABLE, data=result, index=False)
    _db.close()

    # predict deaths
    result = run_arima(data, 'deaths')

     # only data after 3/15/2020
    slicer = result['date'] > pd.to_datetime('3/15/2020')
    result = result.loc[slicer, :].copy(deep=True)
    result.sort_values(['date', 'state'], inplace=True)
    result = result.round(0)

    _db = DataBase()
    _db.add_table(ARIMA_DEATHS_TABLE, data=result, index=False)
    _db.close()


if __name__ == "__main__":
    predict()
