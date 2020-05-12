"""Visualize histograms of cases and deaths by age and gender
"""

from os.path import join

from bokeh.layouts import gridplot
from bokeh.io import curdoc
from bokeh.palettes import Purples
from bokeh.themes import Theme

from utilities import (
    cwd,
    histogram,
    vbar
)
from database import DataBase
from sql import FLDEM_VIEW_TABLE


THEME = join(cwd(), "theme.yaml")


def age_cases_histogram(data, color, hover_color):
    """Plot histogram of covid19 cases by age

    Arguments:
        data {DataFrame} -- data to plot histogram
        color {rgb color} -- color of histogram bars
        hover_color {rgb color} -- color of histogram bar when hovering over

    Returns:
        Bokeh Figure Object -- plot object
    """
    kwargs = dict(title='Age Distribution of Cases in Florida', fill_color=color,
                  hover_fill_color=hover_color)
    plot = histogram(x=data['age'].values, xlabel='Age', ylabel='Cases', **kwargs)

    return plot


def age_deaths_histogram(data, color, hover_color):
    """Plot histogram of covid19 deaths by age

    Arguments:
        data {DataFrame} -- data to plot histogram
        color {rgb color} -- color of histogram bars
        hover_color {rgb color} -- color of histogram bar when hovering over

    Returns:
        Bokeh Figure Object -- plot object
    """
    kwargs = dict(title='Age Distribution of Deaths in Florida', fill_color=color,
                  hover_fill_color=hover_color)
    plot = histogram(x=data[data['died'] == 1]['age'], xlabel='Age',
                     ylabel='Deaths', **kwargs)

    return plot


def gender_cases_histogram(data, color, hover_color):
    """Plot histogram of covid19 cases by gender

    Arguments:
        data {DataFrame} -- data to plot histogram
        color {rgb color} -- color of histogram bars
        hover_color {rgb color} -- color of histogram bar when hovering over

    Returns:
        Bokeh Figure Object -- plot object
    """
    x = ['Male', 'Female']
    y = [data['gender'].sum(), len(data) - data['gender'].sum()]

    kwargs = dict(title='Gender Distribution of Cases in Florida', fill_color=color,
                  hover_fill_color=hover_color)
    plot = vbar(x=x, y=y, xlabel='Gender', ylabel='Cases', **kwargs)

    return plot


def gender_deaths_histogram(data, color, hover_color):
    """Plot histogram of covid19 deaths by gender

    Arguments:
        data {DataFrame} -- data to plot histogram
        color {rgb color} -- color of histogram bars
        hover_color {rgb color} -- color of histogram bar when hovering over

    Returns:
        Bokeh Figure Object -- plot object
    """
    died = data[data['died'] == 1]
    x = ['Male', 'Female']
    y = [died['gender'].sum(), len(died) - died['gender'].sum()]

    kwargs = dict(title='Gender Distribution of Deaths in Florida', fill_color=color,
                  hover_fill_color=hover_color)
    plot = vbar(x=x, y=y, xlabel='Gender', ylabel='Deaths', **kwargs)

    return plot


def age_gender_histograms(data, color, hover_color):
    """Plot histograms
        1) cases by age
        2) deaths by age
        3) cases by gender
        4) deaths by gender

    Arguments:
        data {DataFrame} -- data to plot histogram
        color {rgb color} -- color of histogram bars
        hover_color {rgb color} -- color of histogram bar when hovering over

    Returns:
        Bokeh layout Object -- layout
    """
    layout = gridplot([age_cases_histogram(data, color, hover_color),
                       age_deaths_histogram(data, color, hover_color),
                       gender_cases_histogram(data, color, hover_color),
                       gender_deaths_histogram(data, color, hover_color)],
                      ncols=2, plot_width=400,
                      plot_height=250,
                      toolbar_location=None)
    return layout


if __name__[:9] == 'bokeh_app':
    print('unit testing...')

    palette_in = list(reversed(Purples[8]))

    # dataset for models)
    database = DataBase()
    data_in = database.get_table(FLDEM_VIEW_TABLE)
    database.close()

    curdoc().add_root(age_gender_histograms(data_in, palette_in[2], palette_in[4]))
    curdoc().title = "distros"
    curdoc().theme = Theme(filename=THEME)
