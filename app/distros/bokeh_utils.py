import numpy as np
import pandas as pd
import itertools

from bokeh.plotting import figure
from bokeh.palettes import Category10
from bokeh.models import (ColumnDataSource, CustomJS, HoverTool, Legend,
                          Select, NumeralTickFormatter)

def color_gen():
    yield from itertools.cycle(Category10[10])

def plot_lines(df, x=None, y=None, cat=None, title=None,
                x_axis_type='auto', y_axis_type='auto',
                x_label=None, y_label=None, add_tooltips=None,
                line_color='auto', line_dash='solid',
                line_width=2, plot_width=950, plot_height=600,
                tools='save, pan, box_zoom, reset, wheel_zoom',
                legend_location=None, toolbar_location=None,
                y_axis_formatter=None, palette=Category10):
    '''
       Plot multipe lines by category
    '''

    p = figure(x_axis_type=x_axis_type, y_axis_type=y_axis_type,
                plot_width=plot_width,
                plot_height=plot_height, title=title,
                toolbar_location=toolbar_location, tools=tools)

    # automatically generate colors
    color = palette

    if x_axis_type == 'datetime':
        x_tool_text = f"@{x}" + "{%m/%d/%Y}"
        x_formatter = {f"@{x}": 'datetime'}
    else:
        x_tool_text = f"@{x}"
        x_formatter = {f"@{x}": 'numeral'}

    tooltips = [(cat.title(), f"@{cat}"),
                (x.title(), x_tool_text), (y.title(), f"@{y}")]
    if add_tooltips:
        tooltips = tooltips + add_tooltips

    categories = df[cat].unique()
    lines = dict()

    for category, c in zip(categories, palette):
        data = df[df[cat] == category]

        source = ColumnDataSource(data)

        if line_color != 'auto':
            temp_color = data[line_color].head(1).values[0]
            if temp_color != 'auto':
                c = temp_color

        ld = line_dash
        if ld != 'solid':
            ld = data[line_dash].head(1).values[0]

        lines[category] = p.line(x, y, source=source, color=c,
                line_width=line_width, line_dash=ld,
                muted_color=c, muted_alpha=0.2)

        p.add_tools(HoverTool(renderers=[lines[category]],
                tooltips=tooltips, formatters=x_formatter))

    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label
    p.grid.grid_line_color = None
    p.toolbar.active_drag = None

    if y_axis_formatter:
        p.yaxis.formatter = NumeralTickFormatter(format=y_axis_formatter)

    if legend_location:
        legend = Legend(items=[(x, [lines[x]]) for x in lines],
                        location=legend_location)
        p.add_layout(legend)
        p.legend.label_text_font_size = '8pt'
        p.legend.click_policy = 'mute'

    return p


def histogram(x, density=False, bins=None, title='Histogram',
                x_label='x', y_label='y', fill_color='navy',
                hover_fill_color='grey'):
    """ plot histogram """

    # calculate bin size using Sturge’s rule
    if bins == None:
        bins = int(1 + 3.322 * np.log10(len(x)))

    hist, edges = np.histogram(x, density=density, bins=bins)

    p = figure(title=title, tools='', background_fill_color=None)

    quad = p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
                fill_color=fill_color, line_color="white", alpha=0.5,
                hover_fill_alpha=1.0, hover_fill_color=hover_fill_color)

    p.add_tools(HoverTool(renderers=[quad],
                tooltips=[(f"{x_label.title()} Range", '@left{int} to @right{int}'),
                (y_label.title(), '@top')]))

    p.y_range.start = 0
    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label
    p.grid.grid_line_color = None
    p.toolbar.logo = None
    return p


def vbar(title, x_range, counts, x_label='x', y_label='y', fill_color='navy',
                plot_width=950, plot_height=600, hover_fill_color='grey',
                user_tooltips='auto', user_tooltip_formatters='auto',
                y_axis_formatter='auto'):

    """ plot vertical bar """

    p = figure(x_range=x_range, plot_height=plot_height, plot_width=plot_width,
                title=title, toolbar_location=None, tools='')

    bar = p.vbar(x=x_range, top=counts, width=0.9,
                fill_color=fill_color, line_color='white', alpha=0.5,
                hover_fill_color=hover_fill_color, hover_fill_alpha=1.0)

    if user_tooltips == 'auto':
        tooltips = [(x_label.title(), '@x'), (y_label.title(), '@top')]
    else:
        tooltips = user_tooltips

    if user_tooltip_formatters =='auto':
        formatters = {y_label.title(): 'printf'}
    else:
        formatters = user_tooltip_formatters

    p.add_tools(HoverTool(renderers=[bar],
                tooltips=tooltips, formatters=formatters))

    if y_axis_formatter != 'auto':
        p.yaxis.formatter = NumeralTickFormatter(format=y_axis_formatter)

    p.y_range.start = 0
    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = y_label
    p.grid.grid_line_color = None
    p.toolbar.logo = None
    return p
