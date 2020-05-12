"""Print Hello, <name> in web browser

Returns:
    html -- web page
"""


from flask import (
    Flask,
    render_template,
    request
)
from bokeh.embed import components
from bokeh.layouts import row

from trends import Trends

app = Flask(__name__)



# main app plot
def create_figure():
    """Plot histogram of Iris feature

    Arguments:
        feature_name {String} -- iris feature name
        var2 {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    trend = Trends()

    return row(trend.multiselect, trend.cases.plot, trend.deaths.plot)


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

    return render_template('index.html', script=script, div=div)

# with debug=True, flask server will auto-reload
# when there are code changes
if __name__ == '__main__':
    app.run(port=5000, debug=True)
