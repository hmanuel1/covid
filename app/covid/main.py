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
from trends import Trends
from arima import predict
from fits import models_result
from database import DataBase
from wrangler import maps_to_database
from utilities import (
    cwd,
    ElapsedMilliseconds
)
from clf import (
    classify,
    IMPORTANCE_TABLE,
    MODELS_ROC_TABLE
)
from sql import (
    FLDEM_VIEW_TABLE,
    VACUUM,
    REINDEX
)


TRACING = True


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


def covid():
    """
        Create Server Application
    """

    print('Bokeh Version:', __version__)

    time = ElapsedMilliseconds(log_time=TRACING)

    # get datasets
    _db = DataBase()
    data = _db.get_table(FLDEM_VIEW_TABLE)
    roc = _db.get_table(MODELS_ROC_TABLE)
    importance = _db.get_table(IMPORTANCE_TABLE)
    _db.close()

    time.log('main.get_data_set')

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

    time.log('main.histograms')

    # build us map and fl map layouts
    plot = Map(plot_width=800, plot_height=400, palette=palette['theme'])
    page['us_map'] = column(plot.controls['select'],
                            plot.plot,
                            row(plot.controls['slider'], plot.controls['button']))

    time.log('main.us_map')

    # model result for florida
    page['modeling'] = models_result(roc, importance, palette['theme'][2:],
                                     palette['color'], palette['hover'])

    time.log('main.modeling')

    # predictions based on arima since 3/15/2020
    trend = Trends(palette['trends'])
    page['trends'] = trend.layout()

    time.log('main.trends')

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


if __name__[:9] == 'bokeh_app':
    covid()

else:
    if len(sys.argv) != 2:
        sys.exit("Usage: python main.py refresh")
        if sys.argv[1] == 'refresh':
            refresh()
        else:
            sys.exit("Usage: python main.py refresh")
