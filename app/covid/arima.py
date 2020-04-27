# %%
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from statsmodels.tsa.arima_model import ARIMA
import pmdarima as pm
from pmdarima.utils import diff
from os import getcwd
from os.path import dirname, join


def cwd():
    try: __file__
    except NameError: cwd = getcwd()
    else: cwd = dirname(__file__)
    return cwd

def arima_model(data, states, y_var, show_results=False):
    """
        Run ARIMA models in all the states in the list
    """

    results =dict(index=[], state=[], upper=[], lower=[], predict=[])
    for state in states:
        # select state data
        df = data[data['state'] == state]
        df = df.sort_values('date').reset_index(drop=True)
        df.head()

        # plot data
        if show_results:
            plt.plot(df[y_var])

        # Create Training and Test
        train = []
        train.append(0)
        for i in range(len(df)-1):
            a = df[y_var][i+1] - df[y_var][i]
            train.append(a)

        # auto arima
        model = pm.auto_arima(train, start_p=1, start_q=1,
                              test='adf',       # use adftest to find optimal 'd'
                              max_p=3, max_q=3, # maximum p and q
                              m=1,              # frequency of series
                              d=None,           # let model determine 'd'
                              seasonal=False,   # No Seasonality
                              start_P=0,
                              D=0,
                              trace=False,
                              error_action='ignore',
                              suppress_warnings=True,
                              stepwise=True)

        if show_results:
            print(model.summary())

        # Forecast
        n_periods = 15
        fc, confint = model.predict(n_periods=n_periods, return_conf_int=True)
        index_of_fc = np.arange(len(train), len(train)+n_periods)

        # replace negative values to zero
        lower = [x if x > 0 else 0 for x in confint[:, 0]]
        upper = [x if x > 0 else 0 for x in confint[:, 1]]

        # convert to cumulative begining with the last actual value
        begin = df[y_var].iat[-1]
        lower = (begin + pd.Series(lower).cumsum())
        upper = (begin + pd.Series(upper).cumsum())
        fc    = (lower + upper)/2

        # save results for this state
        results['index'] += [index_of_fc[0]-1] + list(index_of_fc)
        results['state'] += [state]*(len(index_of_fc) + 1)
        results['upper'] += [begin] + list(upper)
        results['lower'] += [begin] + list(lower)
        results['predict'] += [begin] + list(fc)

    rs = pd.DataFrame(results)
    return rs

def run_arima(data, states, y_var, show_results=False):
    # don't overide input data
    df = data.copy(deep=True)

    # run arima model
    rs = arima_model(df, states, y_var, show_results=show_results)

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
    # get covid19 state data
    data = pd.read_csv(join(cwd(), 'data', 'us-states.csv'), parse_dates=['date'])
    states = list(data['state'].unique())[:-1]

    # predict cases
    df = run_arima(data, states, 'cases', show_results=False)
    df.to_csv(join(cwd(), 'output', 'arima-cases.csv'), index=False)

    # predict deaths
    df = run_arima(data, states, 'deaths', show_results=False)
    df.to_csv(join(cwd(), 'output', 'arima-deaths.csv'), index=False)

if __name__ == "__main__":
    predict()

if False:
    # unit testing
    # get covid19 state data
    data = pd.read_csv(join(cwd(), 'data', 'us-states.csv'), parse_dates=['date'])
    states = list(data['state'].unique())[:-1]
    data = data.loc[data['state'] == 'New York',:].set_index('date')[['deaths']]

    x = [0]
    for i in range(len(data)-1):
        a = data.iloc[i+1,0]-data.iloc[i,0]
        x.append(a)

    train = x

    # auto arima
    model = pm.auto_arima(train, start_p=1, start_q=1,
                          test='adf',       # use adftest to find optimal 'd'
                          max_p=3, max_q=3, # maximum p and q
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
    n = 10
    y_pred, confidence = model.predict(n_periods=n, return_conf_int=True)
    index = np.arange(len(train), len(train)+n)
    lower =  [x[0] for x in confidence]
    upper =  [x[1] for x in confidence]

    # cumulative
    s = data.iloc[-1, 0]
    train1 = pd.Series(train).cumsum().to_list()
    y_pred1 = (s + pd.Series([x if x > 0 else 0 for x in y_pred]).cumsum()).to_list()
    lower1 = (s + pd.Series([x if x > 0 else 0 for x in lower]).cumsum()).to_list()
    upper1 = (s + pd.Series([x if x > 0 else 0 for x in upper]).cumsum()).to_list()
    y_pred1 = [(x + y)/2 for x, y in zip(upper1, lower1)]

    plt.plot(train1, color='blue')
    plt.plot(index, y_pred1, color='green')
    plt.fill_between(index,
                     lower1,
                     upper1,
                     color='k', alpha=.15)
    plt.show()
