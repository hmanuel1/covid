"""
   Bokeh based functions for line, histogram and bar charts
"""

import os
import time

import numpy as np
from bokeh.plotting import figure
from bokeh.models import (
    HoverTool,
    NumeralTickFormatter
)

class ElapsedMilliseconds:
    """Time execution time

    Usage example:
       _ms = ElapsedMilliseconds()
       print(_ms.elapsed(), 'ms')
       ...lenthy process...
       print(_ms.elapsed(), 'ms')
    """
    def __init__(self):
        self.last_elapsed = 0
        self.last_local = int(round(time.time() * 1000))

    def elapsed(self):
        """Returns elapse time in milliseconds

        Returns:
            int -- elapsed time in milliseconds since last call
                   to this method
        """
        self.last_elapsed = int(round(time.time() * 1000)) - self.last_local
        self.last_local = int(round(time.time() * 1000))
        return self.last_elapsed

    def restart(self):
        """Restart time reference
        """
        self.last_elapsed = 0
        self.last_local = int(round(time.time() * 1000))


def cwd():
    """
        Return current working directory from __file__ or OS
    """

    try:
        __file__
    except NameError:
        cur_working_dir = os.getcwd()
    else:
        cur_working_dir = os.path.dirname(__file__)
    return cur_working_dir


def histogram(x, xlabel='x', ylabel='y', **kwargs):
    """
        plot histogram
    """

    # plot settings
    figure_settings = dict(title=None, tools='', background_fill_color=None)

    quad_settings = dict(fill_color='navy', hover_fill_color='grey',
                         line_color="white", alpha=0.5, hover_fill_alpha=1.0)

    misc_settings = dict(density=False, bins='auto')

    # update plot settings
    for key, value in kwargs.items():
        if key in figure_settings:
            figure_settings[key] = value

        if key in quad_settings:
            quad_settings[key] = value

        if key in misc_settings:
            misc_settings[key] = value

    # calculate bin size using Sturge’s rule
    if misc_settings['bins'] == 'auto':
        misc_settings['bins'] = int(1 + 3.322 * np.log10(len(x)))

    hist, edges = np.histogram(x, density=misc_settings['density'],
                               bins=misc_settings['bins'])

    plot = figure(**figure_settings)

    quad = plot.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
                     **quad_settings)

    plot.add_tools(HoverTool(renderers=[quad],
                             tooltips=[(f"{xlabel.title()} Range", '@left{int} to @right{int}'),
                                       (ylabel.title(), '@top')]))

    plot.y_range.start = 0
    plot.xaxis.axis_label = xlabel
    plot.yaxis.axis_label = ylabel

    return plot


def vbar(x, y, xlabel='x', ylabel='y', **kwargs):
    """
        Plot vertical bars
    """

    # figure and vbar settings
    figure_settings = dict(x_range=x, plot_height=600, plot_width=950,
                           title=None, toolbar_location=None, tools='')

    vbar_settings = dict(width=0.9, fill_color='navy', line_color='white',
                         alpha=0.5, hover_fill_color='grey', hover_fill_alpha=1.0)

    misc_settings = dict(yaxis_formatter='auto', user_tooltips='auto',
                         user_formatters='auto')

    # update settings
    for key, value in kwargs.items():
        if key in figure_settings:
            figure_settings[key] = value

        if key in vbar_settings:
            vbar_settings[key] = value

        if key in misc_settings:
            misc_settings[key] = value

    plot = figure(**figure_settings)

    vbar_glyph = plot.vbar(x=x, top=y, **vbar_settings)

    # tooltips
    tooltips = [(xlabel.title(), '@x'), (ylabel.title(), '@top')]
    if misc_settings['user_tooltips'] != 'auto':
        tooltips = misc_settings['user_tooltips']

    # tooltip formatters
    formatters = {ylabel.title(): 'numeral'}
    if misc_settings['user_formatters'] != 'auto':
        formatters = misc_settings['user_formatters']

    plot.add_tools(HoverTool(renderers=[vbar_glyph],
                             tooltips=tooltips,
                             formatters=formatters))

    if misc_settings['yaxis_formatter'] != 'auto':
        plot.yaxis.formatter = NumeralTickFormatter(format=misc_settings['yaxis_formatter'])

    plot.y_range.start = 0
    plot.xaxis.axis_label = xlabel
    plot.yaxis.axis_label = ylabel

    return plot
