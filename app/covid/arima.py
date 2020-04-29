"""
   Fit ARIMA model to cases and deaths for each US State
"""
from os import getcwd
from os.path import dirname, join
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import pmdarima as pm

# pylint: disable=invalid-name

def cwd():
    """
       Return current working directiory from __file__ or OS
    """

    try:
        __file__
    except NameError:
        current_working_dir = getcwd()
    else:
        current_working_dir = dirname(__file__)
    return current_working_dir


def arima_model(data, states, y_var):
    """
        Run ARIMA models in all the states in the list
    """

    results = dict(index=[], state=[], upper=[], lower=[], predict=[])
    for state in states:
        # select state data
        df = data[data['state'] == state]
        df = df.sort_values('date').reset_index(drop=True)

        # Create Training and Test
        train = []
        train.append(0)
        for i in range(len(df) - 1):
            x = df[y_var][i + 1] - df[y_var][i]
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
        lower = (df[y_var].iat[-1] + pd.Series(lower).cumsum())
        upper = (df[y_var].iat[-1] + pd.Series(upper).cumsum())

        # save results for this state
        results['index'] += [index_of_fc[0] - 1] + list(index_of_fc)
        results['state'] += [state] * (len(index_of_fc) + 1)
        results['upper'] += [df[y_var].iat[-1]] + list(upper)
        results['lower'] += [df[y_var].iat[-1]] + list(lower)
        results['predict'] += [df[y_var].iat[-1]] + list((lower + upper) / 2)

    return pd.DataFrame(results)


def run_arima(data, states, y_var, show_results=False):
    """
       Run ARIMA model
    """

    df = data.copy(deep=True)

    # run arima model
    rs = arima_model(df, states, y_var)

    # merge prediction with data and plotted
    rs['start'] = rs['state'].map(data.groupby(['state']).min()['date'])
    rs['date'] = rs['start'] + pd.to_timedelta(rs['index'], 'days')
    rs = rs[['date', 'state', 'upper', 'lower', 'predict']].copy(deep=True)
    rs[y_var] = np.nan

    df['upper'], df['lower'], df['predict'] = np.nan, np.nan, np.nan
    df = pd.concat([df, rs], axis=0, ignore_index=True)

    if show_results:
        for state in ['Florida', 'Georgia', 'Alabama', 'New York']:
            a = df[df['state'] == state]
            plt.plot(a['date'], a[y_var], color='blue')
            plt.plot(a['date'], a['predict'], color='green')
            plt.fill_between(a['date'],
                             a['lower'],
                             a['upper'],
                             color='k', alpha=.15)
        plt.show()

    cols = ['date', 'state', y_var, 'predict', 'lower', 'upper']
    return df[cols]


def predict():
    """
    get covid19 state data
    """

    data = pd.read_csv(join(cwd(), 'data', 'us-states.csv'),
                       parse_dates=['date'])
    states = list(data['state'].unique())[:-1]

    # predict cases
    df = run_arima(data, states, 'cases')
    df.to_csv(join(cwd(), 'output', 'arima-cases.csv'), index=False)

    # predict deaths
    df = run_arima(data, states, 'deaths')
    df.to_csv(join(cwd(), 'output', 'arima-deaths.csv'), index=False)


if __name__ == "__main__":
    predict()
