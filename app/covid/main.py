import numpy as np
import pandas as pd
import geopandas as gpd
import datetime as dt
from os import getcwd
from os.path import dirname, join
import sys
import re

# bokeh
from bokeh import __version__
from bokeh.plotting import curdoc
from bokeh.palettes import brewer, Purples, Blues, RdPu
from bokeh.models import Panel, Tabs, Div
from bokeh.layouts import column, row, Spacer

# internal modules
from nytimes import download_nytimes
from fldem import download_fldem
from clf import classify
from arima import predict
from wrangler import covid_data, get_maps, merge_data
from distros import age_gender_histograms
from models import models_result
from maps import build_us_map
from trends import show_predictions


def refresh():
    print('downloading ny times data...', end='')
    download_nytimes()
    print('done.\ndownloading fl dem data...', end='')
    download_fldem()
    print('done.\nclassifying with fl dem data...', end='')
    classify()
    print('done.\npredicting with ny times data...', end='')
    predict()
    print('done.')


def covid():
    #  create html
    print('Bokeh Version:', __version__)

    try: __file__
    except NameError: cwd = getcwd()
    else: cwd = dirname(__file__)

    # get data sets
    df = pd.read_csv(join(cwd, 'data', 'us-counties.csv'), parse_dates=[0])
    lookup = pd.read_csv(join(cwd, 'input', 'statefp-name-abbr.csv'))

    df = covid_data(df, lookup)
    us_map = gpd.read_file(join(cwd, 'shapes', 'us_map', 'us_map.shx'))
    state_map = gpd.read_file(join(cwd, 'shapes', 'state_map', 'state_map.shx'))

    # dataset for models
    data = pd.read_csv(join(cwd, 'data', 'flclean.csv'))
    models = pd.read_csv(join(cwd, 'output', 'fl_roc_models.csv'))
    fi = pd.read_csv(join(cwd, 'output', 'fl_fi_models.csv'))

    # datasets for predictions
    cases = pd.read_csv(join(cwd, 'output', 'arima-cases.csv'), parse_dates=['date'])
    deaths = pd.read_csv(join(cwd, 'output', 'arima-deaths.csv'), parse_dates=['date'])

    # options for map drop-down menu
    sel = pd.read_csv(join(cwd, 'input', 'statefp-name-abbr.csv'),
            dtype={'statefp': 'str'})
    sel = sel.loc[sel['statefp'].isin(us_map['STATEFP'].unique())].copy(deep=True)
    options = [(x, y) for x, y in zip(sel['statefp'], sel['name'])]
    options = [('a' , 'USA')] + options

    # merge covid19 data with map data
    levels = [0, 1, 10, 100, 250, 500, 5000, 10000, np.inf]
    us_map, dates = merge_data(df, us_map, levels, days=15)

    # create palettes
    palette = list(reversed(Purples[8]))
    color = palette[2]
    hover_color = palette[4]
    trends_palette = Purples[3]

    # build us map and fl map layouts
    usmap = build_us_map(us_map, state_map, palette, levels, dates, options)

    # histograms
    histograms = age_gender_histograms(data, color, hover_color)

    # model result for florida
    modeling = models_result(models, fi, palette[2:], color, hover_color)

    # predictions based on arima since 3/15/2020
    trends = show_predictions(cases, deaths, '3/15/2020', trends_palette)

    # build layout
    headings_attr = dict(height=40,
        style={'font-size': '150%', 'color': hover_color, 'align': 'center'})

    map_heading = Div(text="<b>Map</b>", **headings_attr)
    trends_heading = Div(text="<b>Trends</b>", **headings_attr)
    hist_heading = Div(text="<b>Histograms</b>", **headings_attr)
    models_heading = Div(text="<b>Models</b>", **headings_attr)

    layout = column(
                   row(Spacer(width=10), map_heading),
                   row(Spacer(width=10), usmap),
                   row(Spacer(width=10), Spacer(height=160)),
                   row(Spacer(width=10), trends_heading),
                   row(Spacer(width=10), trends),
                   row(Spacer(width=10), Spacer(height=160)),
                   row(Spacer(width=10), hist_heading),
                   row(Spacer(width=10), histograms),
                   row(Spacer(width=10), Spacer(height=160)),
                   row(Spacer(width=10), models_heading),
                   row(Spacer(width=10), modeling),
                   row(Spacer(width=10), Spacer(height=240)))

    curdoc().add_root(layout)
    curdoc().title = 'COVID-19'

try:
    # refresh data
    if sys.argv[1] == 'refresh':
        refresh()
except IndexError:
    # run app
    covid()
