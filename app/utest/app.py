"""Embed Bokeh plot with Flask

Returns:
    html -- web page
"""
import os

import pprint

from flask import (
    Flask,
    render_template,
    request
)
from bokeh.embed import components
from bokeh.plotting import figure


app = Flask(__name__)


# main app plot
def create_figure():
    """Test Figure

    Returns:
        figure-- bokeh figure
    """
    x = [1, 2, 3, 5]
    y = [6, 7, 8, 9]
    plot = figure()
    plot.line(x=x, y=y)
    return plot

# Index page
@app.route('/')
def index():
    """Embed bokeh app with Flask

    Returns:
        Flask rendered html -- flask rendered html
    """
    # Determine the selected feature
    command = request.args.get('command')

    print(command)

    # create the plot
    plot = create_figure()

    # embed plot into html via bokeh flask render
    script, div = components(plot)

    return render_template('index.html', script=script, div=div, title='Test')

print("User's Environment variable:")
pprint.pprint(dict(os.environ), width=1)

# with debug=True, flask server will auto-reload
# when there are code changes
if __name__ == '__main__':
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)
