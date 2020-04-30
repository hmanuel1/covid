"""
   Visualize output of fitted models on FDEM covid-19 data
"""

from os.path import join

import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.layouts import column
from bokeh.layouts import row
from bokeh.io import curdoc
from bokeh.palettes import Purples
from bokeh.themes import Theme

from utilities import cwd, vbar


def roc(df, palette, plot_width=400, plot_height=400):
    """
        Plot ROC
    """

    figure_settings = dict(title='Receiver Operating Curve (ROC) in Florida',
                           plot_width=plot_width, plot_height=plot_height,
                           toolbar_location=None,
                           tools='save, pan, box_zoom, reset, wheel_zoom')

    # plot
    plot = figure(**figure_settings)

    lines = dict()
    for category, color in zip(df['abbrev'].unique(), palette):

        source = ColumnDataSource(df[df['abbrev'] == category])

        line_settings = dict(line_color=color, line_width=2, line_dash='solid',
                             muted_color=color, muted_alpha=0.2)

        if category == 'Random':
            line_settings = dict(line_color='black', line_width=2, line_dash='dashed',
                                 muted_color='black', muted_alpha=0.2)

        lines[category] = plot.line(x='False_Positive_Rate', y='True_Positive_Rate',
                                    source=source, **line_settings)

        plot.add_tools(HoverTool(renderers=[lines[category]],
                                 tooltips=[('Abreviation', '@abbrev'),
                                           ('False Positive Rate', '@False_Positive_Rate'),
                                           ('True Positive Rate', '@True_Positive_Rate'),
                                           ('AUC', '@auc{0.0000}'),
                                           ('LogLoss', '@logloss{0.0000}'),
                                           ('Model', '@model')]))

    legend = Legend(items=[(x, [lines[x]]) for x in lines], location='bottom_right')
    plot.add_layout(legend)

    plot.legend.click_policy = 'mute'
    plot.xaxis.axis_label = 'False Positive Rate'
    plot.yaxis.axis_label = 'True Positive Rate'

    return plot


def logloss(df, color, hover_color, plot_width=450, plot_height=250):
    """
        Plot Logloss
    """

    df.drop_duplicates(['abbrev'], inplace=True)
    df.sort_values('logloss', inplace=True)

    kwargs = dict(title='LogLoss for All Fitted Models',
                  user_tooltips=[('Model', '@x'),
                                 ('LogLoss', '@top{0.0000}')],
                  user_formatters={'Logloss': 'numeral'},
                  plot_width=plot_width, plot_height=plot_height,
                  fill_color=color, hover_fill_color=hover_color,
                  yaxis_formatter='0.0000')

    plot = vbar(x=df['abbrev'], y=df['logloss'], xlabel='Model', ylabel='LogLoss',
                **kwargs)
    return plot


def feature_importance(df, color, hover_color, plot_width=450, plot_height=250):
    """
        Plot Feature Importance
    """

    kwargs = dict(title='Feature Importance for Random Forest Model',
                  user_tooltips=[('Feature', '@x'),
                                 ('Importance', '@top{0.0%}')],
                  user_formatters={'Importance': 'numeral'},
                  plot_width=plot_width, plot_height=plot_height,
                  fill_color=color, hover_fill_color=hover_color,
                  yaxis_formatter='0%')

    plot = vbar(x=df['feature'], y=df['importance'], xlabel='Feature',
                ylabel='Importance', **kwargs)

    return plot


def models_result(df, fi, palette, color, hover_color):
    """
        Module function call to build Models Layout
    """

    layout = row(roc(df, palette, plot_width=400, plot_height=400),
                 column(logloss(df, color, hover_color,
                                plot_width=400, plot_height=200),
                        feature_importance(fi, color, hover_color,
                                           plot_width=400,
                                           plot_height=200)))
    return layout


STAND_ALONE = False
if STAND_ALONE:

    palette_in = list(reversed(Purples[8]))
    color_in = palette_in[2]
    hover_color_in = palette_in[4]

    # dataset for models
    df_in = pd.read_csv(join(cwd(), 'output', 'fl_roc_models.csv'))
    fi_in = pd.read_csv(join(cwd(), 'output', 'fl_fi_models.csv'))

    curdoc().add_root(models_result(df_in, fi_in, palette_in,
                                    color_in, hover_color_in))
    curdoc().title = 'models'
    curdoc().theme = Theme(filename=join(cwd(), "theme.yaml"))
