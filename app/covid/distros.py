"""
    Visualize histograms of cases and deaths by age and gender
"""

from os.path import join

import pandas as pd
from bokeh.layouts import gridplot
from bokeh.io import curdoc
from bokeh.palettes import Purples
from bokeh.themes import Theme

from utilities import cwd, histogram, vbar


def age_cases_histogram(df, color, hover_color):
    """
        Plot distribution of cases among age groups
    """

    kwargs = dict(title='Age Distribution of Cases in Florida', fill_color=color,
                  hover_fill_color=hover_color)

    plot = histogram(x=df['age'].values, xlabel='Age', ylabel='Cases', **kwargs)

    return plot


def age_deaths_histogram(df, color, hover_color):
    """
        Plot distribution of deaths among age groups
    """

    kwargs = dict(title='Age Distribution of Deaths in Florida', fill_color=color,
                  hover_fill_color=hover_color)

    plot = histogram(x=df[df['died'] == 1]['age'], xlabel='Age', ylabel='Deaths', **kwargs)

    return plot


def gender_cases_histogram(df, color, hover_color):
    """
        Plot distribution of cases by gender
    """

    x = ['Male', 'Female']
    y = [df['Male'].sum(), len(df) - df['Male'].sum()]

    kwargs = dict(title='Gender Distribution of Cases in Florida', fill_color=color,
                  hover_fill_color=hover_color)

    plot = vbar(x=x, y=y, xlabel='Gender', ylabel='Cases', **kwargs)

    return plot


def gender_deaths_histogram(df, color, hover_color):
    """
        Plot distribution of deaths by gender
    """

    df_died = df[df['died'] == 1]
    x = ['Male', 'Female']
    y = [df_died['Male'].sum(), len(df_died) - df_died['Male'].sum()]

    kwargs = dict(title='Gender Distribution of Deaths in Florida', fill_color=color,
                  hover_fill_color=hover_color)

    plot = vbar(x=x, y=y, xlabel='Gender', ylabel='Deaths', **kwargs)

    return plot


def age_gender_histograms(df, color, hover_color):
    """
        Build layout with all distributions
    """

    layout = gridplot([age_cases_histogram(df, color, hover_color),
                       age_deaths_histogram(df, color, hover_color),
                       gender_cases_histogram(df, color, hover_color),
                       gender_deaths_histogram(df, color, hover_color)],
                      ncols=2, plot_width=400,
                      plot_height=250,
                      toolbar_location=None)
    return layout

STAND_ALONG = False
if STAND_ALONG:

    palette_in = list(reversed(Purples[8]))

    # dataset for models)
    df_in = pd.read_csv(join(cwd(), 'data', 'flclean.csv'))

    curdoc().add_root(age_gender_histograms(df_in, palette_in[2], palette_in[4]))
    curdoc().title = "distros"
    curdoc().theme = Theme(filename=join(cwd(), "theme.yaml"))
