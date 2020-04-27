import pandas as pd
from bokeh.layouts import gridplot
import bokeh_utils as bu
import re


def age_cases_histogram(df, color, hover_color):
    x = df['age'].values
    p = bu.histogram(df['age'], density=False,
                title='Age Distribution of Cases in Florida',
                x_label='Age', y_label='Cases', fill_color=color,
                hover_fill_color=hover_color)
    return p

def age_deaths_histogram(df, color, hover_color):
    x = df[df['died'] == 1]['age'].values
    p = bu.histogram(x, density=False,
                title='Age Distribution of Deaths in Florida',
                x_label='Age', y_label='Deaths', fill_color=color,
                hover_fill_color=hover_color)
    return p

def gender_cases_histogram(df, color, hover_color):
    counts = [df['Male'].sum(), len(df) - df['Male'].sum()]
    x_range = ['Male', 'Female']
    p = bu.vbar('Gender Distribution of Cases in Florida',
                x_range, counts, x_label='Gender', y_label='Cases',
                fill_color=color, hover_fill_color=hover_color)
    return p

def gender_deaths_histogram(df, color, hover_color):
    df = df[df['died'] == 1]
    counts = [df['Male'].sum(), len(df) - df['Male'].sum()]
    x_range = ['Male', 'Female']
    p = bu.vbar('Gender Distribution of Deaths in Florida',
                x_range, counts, x_label='Gender', y_label='Deaths',
                fill_color=color, hover_fill_color=hover_color)
    return p

def age_gender_histograms(df, color, hover_color):
    p1 = age_cases_histogram(df, color, hover_color)
    p2 = age_deaths_histogram(df, color, hover_color)
    p3 = gender_cases_histogram(df, color, hover_color)
    p4 = gender_deaths_histogram(df, color, hover_color)

    layout = gridplot([p1, p2, p3, p4], ncols=2, plot_width=400,
                plot_height=250, toolbar_location=None)
    return layout

if False:
    import pandas as pd
    from os import getcwd
    from os.path import dirname, join
    from bokeh.io import curdoc
    from bokeh.palettes import Purples

    palette = list(reversed(Purples[8]))
    color = palette[2]
    hover_color = palette[4]

    try: __file__
    except NameError: cwd = getcwd()
    else: cwd = dirname(__file__)

    # dataset for models)
    df = pd.read_csv(join(cwd, 'data', 'flclean.csv'))

    curdoc().add_root(age_gender_histograms(df, color, hover_color))
    curdoc().title = "distros"
