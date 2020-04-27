import numpy as np
import pandas as pd

from bokeh.plotting import figure
from bokeh.models import Select, GroupFilter, CDSView, ColumnDataSource, Range1d
from bokeh.layouts import column, row
from bokeh.io import curdoc, show

x = [0, 1, 2, 3, 4, 5]
y = [6, 7, 8, 9, 10, 11]
c = ['a', 'a', 'b', 'b', 'c', 'c']

df = pd.DataFrame({'x': x,'y': y, 'c':c})
source = ColumnDataSource(data=dict(x=[], y=[], c=[]))

# default x and y range
pad = 0.025
xmin = df['x'].min() - pad*(df['x'].max() - df['x'].min())
xmax = df['x'].max() + pad*(df['x'].max() - df['x'].min())
ymin = df['y'].min() - pad*(df['y'].max() - df['y'].min())
ymax = df['y'].max() + pad*(df['y'].max() - df['y'].min())

p = figure(x_range=(xmin, xmax), y_range=(ymin, ymax))
line = p.line('x', 'y', source=source)
circle = p.circle('x', 'y', source=source)

select = Select(value='-', options=['-', 'a', 'b', 'c'])

def update(attr, old, new):
    if new != '-':
        s = df[df['c'] == new]
        source.data.update(dict(x=s['x'], y= s['y'], c=s['c']))

        _xmin = s['x'].min() - pad*(s['x'].max() - s['x'].min())
        _xmax = s['x'].max() + pad*(s['x'].max() - s['x'].min())
        p.x_range.update(start=_xmin, end=_xmax)

        _ymin = s['y'].min() - pad*(s['y'].max() - s['y'].min())
        _ymax = s['y'].max() + pad*(s['y'].max() - s['y'].min())
        p.y_range.update(start=_ymin, end=_ymax)
    else:
        source.data.update(dict(x=[], y=[], c=[]))
        p.x_range.update(start=xmin, end=xmax)
        p.y_range.update(start=ymin, end=ymax)

select.on_change('value', update)

curdoc().add_root(column(select, p))
curdoc().title = 'test'
