"""
    Analyze COVID-19 cases and deaths in the US.
"""

from os.path import join
import sys

import numpy as np
import pandas as pd
import geopandas as gpd

from bokeh import __version__
from bokeh.plotting import curdoc
from bokeh.palettes import Greens
from bokeh.models import Div
from bokeh.layouts import column, row, Spacer
from bokeh.themes import Theme

# internal modules
from nytimes import download_nytimes
from fldem import download_fldem
from clf import classify
from arima import predict
from wrangler import covid_data, merge_data
from distros import age_gender_histograms
from maps import build_us_map
from trends import show_predictions
from fits import models_result
from utilities import cwd


def refresh():
    """
        Refresh covid-19 data used by this appp
    """

    print('downloading ny times data...', end='')
    download_nytimes()
    print('done.\ndownloading fl dem data...', end='')
    download_fldem()
    print('done.\nclassifying with fl dem data...', end='')
    classify()
    print('done.\npredicting with ny times data...', end='')
    predict()
    print('done.')


def get_data_sets():
    """
        get data sets
    """

    df = pd.read_csv(join(cwd(), 'data', 'us-counties.csv'), parse_dates=[0])
    lookup = pd.read_csv(join(cwd(), 'input', 'statefp-name-abbr.csv'))

    df = covid_data(df, lookup)
    us_map = gpd.read_file(join(cwd(), 'shapes', 'us_map', 'us_map.shx'))
    state_map = gpd.read_file(
        join(cwd(), 'shapes', 'state_map', 'state_map.shx'))

    # dataset for models
    data = pd.read_csv(join(cwd(), 'data', 'flclean.csv'))
    roc = pd.read_csv(join(cwd(), 'output', 'fl_roc_models.csv'))
    importance = pd.read_csv(join(cwd(), 'output', 'fl_fi_models.csv'))

    # datasets for predictions
    cases = pd.read_csv(
        join(cwd(), 'output', 'arima-cases.csv'), parse_dates=['date'])
    deaths = pd.read_csv(
        join(cwd(), 'output', 'arima-deaths.csv'), parse_dates=['date'])

    # options for map drop-down menu
    sel = pd.read_csv(join(cwd(), 'input', 'statefp-name-abbr.csv'),
                      dtype={'statefp': 'str'})
    sel = sel.loc[sel['statefp'].isin(
        us_map['STATEFP'].unique())].copy(deep=True)
    options = [('a', 'USA')] + list(zip(sel['statefp'], sel['name']))

    return df, us_map, state_map, data, roc, importance, options, cases, deaths

def covid():
    """
        Create Serve Application
    """

    print('Bokeh Version:', __version__)

    # get all datasets for this app
    df, us_map, state_map, data, roc, importance, options, cases, deaths = get_data_sets()

    # merge covid19 data with map data
    levels = [0, 1, 10, 100, 250, 500, 5000, 10000, np.inf]
    us_map, dates = merge_data(df, us_map, levels, days=15)

    # create palettes
    palette = dict()
    palette['theme'] = list(reversed(Greens[8]))
    palette['color'] = palette['theme'][2]
    palette['hover'] = palette['theme'][4]
    palette['trends'] = Greens[3]

    # hold page layouts
    page = dict()

    # histograms
    page['histograms'] = age_gender_histograms(data, palette['color'],
                                               palette['hover'])

    # build us map and fl map layouts
    page['usmap'] = build_us_map(us_map=us_map, state_map=state_map,
                                 palette=palette['theme'], levels=levels,
                                 dates=dates, options=options)

    # model result for florida
    page['modeling'] = models_result(roc, importance, palette['theme'][2:],
                                     palette['color'], palette['hover'])

    # predictions based on arima since 3/15/2020
    page['trends'] = show_predictions(cases, deaths, '3/15/2020', palette['trends'])

    # build layout
    headings_attr = dict(height=40,
                         style={'font-size': '150%',
                                'color': palette['hover'],
                                'align': 'center'})

    layout = column(
        row(Spacer(width=10), Div(text="<b>Map</b>", **headings_attr)),
        row(Spacer(width=10), page['usmap']),
        row(Spacer(width=10), Spacer(height=160)),
        row(Spacer(width=10), Div(text="<b>Trends</b>", **headings_attr)),
        row(Spacer(width=10), page['trends']),
        row(Spacer(width=10), Spacer(height=160)),
        row(Spacer(width=10), Div(text="<b>Histograms</b>", **headings_attr)),
        row(Spacer(width=10), page['histograms']),
        row(Spacer(width=10), Spacer(height=160)),
        row(Spacer(width=10), Div(text="<b>Models</b>", **headings_attr)),
        row(Spacer(width=10), page['modeling']),
        row(Spacer(width=10), Spacer(height=240)))

    curdoc().add_root(layout)
    curdoc().title = 'COVID-19'
    curdoc().theme = Theme(filename=join(cwd(), "theme.yaml"))


try:
    # refresh data
    if sys.argv[1] == 'refresh':
        refresh()
except IndexError:
    # run app
    covid()
