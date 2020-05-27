"""
   Bokeh based functions for line, histogram and bar charts
"""

import os
import time

import numpy as np
from bokeh import __version__ as bokeh_release_ver
from bokeh.plotting import figure
from bokeh.models import (
    HoverTool,
    NumeralTickFormatter
)


LOADER = """
    #loader {
      position: absolute;
      left: 20%;
      top: 30%;
      z-index: 1000;
      border: 16px solid #f3f3f3;
      border-top: 16px solid #3498db;
      border-radius: 50%;
      width: 120px;
      height: 120px;
      animation: spin 2s linear infinite;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
"""

PRELOADER = """
    <script type="text/javascript">
      function preloader(){
        document.getElementById("loading").style.display = "none";
        document.getElementById("content").style.display = "block";
      }
      window.onload = preloader;
    </script>
"""


class ElapsedMilliseconds:
    """Time execution time

    Usage example 1:
       time = ElapsedMilliseconds()
       ...lenthy process...
       print(time.elapsed(), 'ms')

    Usage example 2:
       time = ElapsedMilliseconds(log_time=True)
       ...lenthy process...
       time.log('your custom log msg')
    """
    def __init__(self, log_time=False):
        self.last_elapsed = 0
        self.last_local = int(round(time.time() * 1000))
        self.log_time = log_time

    def elapsed(self):
        """Returns elapse time in milliseconds

        Returns:
            int -- elapsed time in milliseconds since last call
                   to this method
        """
        self.last_elapsed = int(round(time.time() * 1000)) - self.last_local
        self.last_local = int(round(time.time() * 1000))
        return self.last_elapsed

    def log(self, module='', function='', process=''):
        """Print elapsed time since last call

        Keyword Arguments:
            module {String} -- module name (default: {''})
            function {String} -- function name (default: {''})
            process {String} -- process name (default: {''})
        """
        if self.log_time:
            print(f"{module}:{function}:{process}:{self.elapsed()}ms")

    def restart(self):
        """Restart time reference
        """
        self.last_elapsed = 0
        self.last_local = int(round(time.time() * 1000))


def cwd():
    """Return current working directory if running from bokeh server,
       jupiter or python.

    Returns:
        String -- path to current working directory
    """
    try:
        __file__
    except NameError:
        cur_working_dir = os.getcwd()
    else:
        cur_working_dir = os.path.dirname(__file__)
    return cur_working_dir


def histogram(x, xlabel='x', ylabel='y', **kwargs):
    """Plot histogram

    Arguments:
        x {list, array, or series} -- data to plot histogram

    Keyword Arguments:
        xlabel {String} -- x axis label (default: {'x'})
        ylabel {String} -- y axis label (default: {'y'})

    Returns:
        Bokeh figure -- plot
    """
    # plot settings
    figure_settings = dict(title=None, tools='')

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
                                       (ylabel.title(), '@top{0,0}')]))

    plot.y_range.start = 0
    plot.xaxis.axis_label = xlabel
    plot.yaxis.axis_label = ylabel

    return plot


def vbar(x, y, xlabel='x', ylabel='y', **kwargs):
    """Plot histogram

    Arguments:
        x {list, array, or series} -- x data for vertical bars
        y {list, array, or series} -- y data for vertical bars

    Keyword Arguments:
        xlabel {String} -- x axis label (default: {'x'})
        ylabel {String} -- y axis label (default: {'y'})

    Returns:
        Bokeh figure -- plot

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
    tooltips = [(xlabel.title(), '@x'), (ylabel.title(), '@top{0,0}')]
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
