"""
    this module is just for unit testing with Bokeh serve
    Application will be run with Flask in `appflask.py`.

    To test this app execute the following command:
        bokeh serve --show appbokeh.py
"""

from os.path import join

from bokeh.io import curdoc
from bokeh.themes import Theme

from applayout import covid_app
from utilities import cwd

# unit testing
layout = covid_app()
curdoc().add_root(layout)
curdoc().title = 'COVID-19'
curdoc().theme = Theme(filename=join(cwd(), "theme.yaml"))
