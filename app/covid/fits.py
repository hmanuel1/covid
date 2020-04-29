"""
   Visualize output of fitted models on FDEM covid-19 data
"""

from os import getcwd
from os.path import dirname
from os.path import join

import pandas as pd

from bokeh.layouts import column
from bokeh.layouts import row
from bokeh.io import curdoc
from bokeh.palettes import Purples

import bokeh_utils as bu


def roc(df, palette, plot_width=400, plot_height=400):
    """
        Plot ROC
    """

    df['line_dash'] = 'solid'
    df.loc[df['model'] == 'Random', 'line_dash'] = 'dashed'
    df['line_color'] = 'auto'
    df.loc[df['model'] == 'Random', 'line_color'] = 'black'

    p = bu.plot_lines(df, x='False_Positive_Rate', y='True_Positive_Rate',
                      cat='abbrev', title='Receiver Operating Curve (ROC) in Florida',
                      line_color='line_color', line_dash='line_dash',
                      add_tooltips=[('AUC', '@auc{0.0000}'),
                                    ('LogLoss', '@logloss{0.0000}'),
                                    ('Model', '@model')],
                      x_label='False Positive Rate', y_label='True Positive Rate',
                      legend_location='bottom_right', plot_width=plot_width,
                      plot_height=plot_height, palette=palette)
    return p


def logloss(df, color, hover_color, plot_width=450, plot_height=250):
    """
        Plot Logloss
    """

    df.drop_duplicates(['abbrev'], inplace=True)
    df.sort_values('logloss', inplace=True)

    p = bu.vbar('LogLoss for All Fitted Models',
                x_range=df['abbrev'], counts=df['logloss'],
                x_label='Model', y_label='LogLoss',
                user_tooltips=[('Model', '@x'), ('LogLoss', '@top{0.0000}')],
                user_tooltip_formatters={'Logloss': 'numeral'},
                plot_width=plot_width, plot_height=plot_height,
                fill_color=color,
                hover_fill_color=hover_color, y_axis_formatter='0.0000')
    return p


def feature_importance(df, color, hover_color, plot_width=450, plot_height=250):
    """
        Plot Feature Importance
    """

    p = bu.vbar('Feature Importance for Random Forest Model',
                x_range=df['feature'], counts=df['importance'],
                x_label='Feature', y_label='Importance',
                user_tooltips=[('Feature', '@x'),
                               ('Importance', '@top{0.0%}')],
                user_tooltip_formatters={'Importance': 'numeral'},
                plot_width=plot_width, plot_height=plot_height,
                fill_color=color,
                hover_fill_color=hover_color, y_axis_formatter='0%')
    return p


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

    try:
        __file__
    except NameError:
        cwd = getcwd()
    else:
        cwd = dirname(__file__)

    # dataset for models
    df_in = pd.read_csv(join(cwd, 'output', 'fl_roc_models.csv'))
    fi_in = pd.read_csv(join(cwd, 'output', 'fl_fi_models.csv'))

    curdoc().add_root(models_result(df_in, fi_in, palette_in,
                                    color_in, hover_color_in))
    curdoc().title = 'models'
