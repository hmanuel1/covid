"""
    Analyze COVID-19 cases and deaths in the US.
"""

from os.path import join
import sys

from bokeh import __version__
from bokeh.plotting import curdoc
from bokeh.palettes import Greens
from bokeh.models import Div
from bokeh.layouts import column, row, Spacer
from bokeh.themes import Theme

# internal modules
from nytimes import download_nytimes
from fldem import download_fldem
from distros import age_gender_histograms
from maps import Map
from trends import show_predictions
from fits import models_result
from utilities import cwd
from database import DataBase
from wrangler import maps_to_database
from clf import (
    classify,
    IMPORTANCE_TABLE,
    MODELS_ROC_TABLE
)
from arima import (
    predict,
    ARIMA_CASES_TABLE,
    ARIMA_DEATHS_TABLE
)
from sql import (
    FLDEM_VIEW_TABLE,
    VACUUM,
    REINDEX
)


def refresh():
    """
        Refresh covid-19 data used by this app
    """
    print('refreshing database maps...', end='')
    maps_to_database()
    print('done.\ndownloading nytimes data...', end='')
    download_nytimes()
    print('done.\ndownloading fldem data...', end='')
    download_fldem()
    print('done.\nclassifying with fldem data...', end='')
    classify()
    print('done.\npredicting with nytimes data...', end='')
    predict()
    print('done.')

    _db = DataBase()
    _db.update(VACUUM)
    _db.update(REINDEX)
    _db.close()


def get_data_sets():
    """
        get data sets
    """
    _db = DataBase()

    data = _db.get_table(FLDEM_VIEW_TABLE)
    roc = _db.get_table(MODELS_ROC_TABLE)
    importance = _db.get_table(IMPORTANCE_TABLE)
    cases = _db.get_table(ARIMA_CASES_TABLE, parse_dates=['date'])
    deaths = _db.get_table(ARIMA_DEATHS_TABLE, parse_dates=['date'])

    _db.close()

    return data, roc, importance, cases, deaths

def covid():
    """
        Create Server Application
    """

    print('Bokeh Version:', __version__)

    # get all datasets for this app
    data, roc, importance, cases, deaths = get_data_sets()

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
    plot = Map(plot_width=800, plot_height=400, palette=palette['theme'])
    page['us_map'] = column(plot.controls['select'],
                            plot.plot,
                            row(plot.controls['slider'], plot.controls['button']))

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
        row(Spacer(width=10), page['us_map']),
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
