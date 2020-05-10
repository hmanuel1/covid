"""
    App to test hosting setup
"""

from os.path import dirname, join

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, MultiSelect
from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.themes import Theme

from database import DataBase


database = DataBase()
data = database.get_table('arima_cases', parse_dates=['date'])
database.close()

# x_axis_type='datetime'
plot = figure(title='test', x_axis_type='datetime')

lines = dict()
options = []
for state_id, state in zip(data['state_id'].unique(), data['state'].unique()):
    options.append((state_id, state))
    lines[state_id] = plot.line(x='x',
                                y='y',
                                source=ColumnDataSource(data=dict(x=[], y=[])),
                                visible=False,
                                name=state)

mselect = MultiSelect(value=['00'], options=options)

data.set_index('state_id', inplace=True)

def update(_attr, _old, new):
    """
        Callback function to handle select changes
    """
    for line in lines:
        if lines[line].visible and not line in new:
            lines[line].visible = False
            lines[line].data_source.data = dict(x=[], y=[])

    for line in new:
        if not lines[line].visible:
            print(line)
            source = dict(x=list(data.loc[line, 'date']),
                          y=list(data.loc[line, 'cases']))
            lines[line].data_source.data = source
            lines[line].visible = True

mselect.on_change('value', update)

top10 = data.loc[data['date'] == data['date'].max(), :]
top10 = top10.sort_values('cases', ascending=False).head(10).index.to_list()
mselect.value = top10

curdoc().add_root(column(mselect, plot))
curdoc().title = "test"
curdoc().theme = Theme(filename=join(dirname(__file__), "theme.yaml"))
