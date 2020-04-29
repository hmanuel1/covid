"""
    Visualize histograms of cases and deaths by age and gender
"""

from os import getcwd
from os.path import dirname, join

import pandas as pd
from bokeh.layouts import gridplot
from bokeh.io import curdoc
from bokeh.palettes import Purples

import bokeh_utils as bu


def age_cases_histogram(df, color, hover_color):
    """
        Plot distribution of cases among age groups
    """

    x = df['age'].values
    p = bu.histogram(x, density=False,
                     title='Age Distribution of Cases in Florida',
                     x_label='Age', y_label='Cases', fill_color=color,
                     hover_fill_color=hover_color)
    return p


def age_deaths_histogram(df, color, hover_color):
    """
        Plot distribution of deaths among age groups
    """

    x = df[df['died'] == 1]['age'].values
    p = bu.histogram(x, density=False,
                     title='Age Distribution of Deaths in Florida',
                     x_label='Age', y_label='Deaths', fill_color=color,
                     hover_fill_color=hover_color)
    return p


def gender_cases_histogram(df, color, hover_color):
    """
        Plot distribution of cases by gender
    """

    counts = [df['Male'].sum(), len(df) - df['Male'].sum()]
    x_range = ['Male', 'Female']
    p = bu.vbar('Gender Distribution of Cases in Florida',
                x_range, counts, x_label='Gender', y_label='Cases',
                fill_color=color, hover_fill_color=hover_color)
    return p


def gender_deaths_histogram(df, color, hover_color):
    """
        Plot distribution of deaths by gender
    """

    df = df[df['died'] == 1]
    counts = [df['Male'].sum(), len(df) - df['Male'].sum()]
    x_range = ['Male', 'Female']
    p = bu.vbar('Gender Distribution of Deaths in Florida',
                x_range, counts, x_label='Gender', y_label='Deaths',
                fill_color=color, hover_fill_color=hover_color)
    return p


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

    try:
        __file__
    except NameError:
        cwd = getcwd()
    else:
        cwd = dirname(__file__)

    # dataset for models)
    df_in = pd.read_csv(join(cwd, 'data', 'flclean.csv'))

    curdoc().add_root(age_gender_histograms(df_in, palette_in[2], palette_in[4]))
    curdoc().title = "distros"
