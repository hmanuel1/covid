import numpy as np
import pandas as pd

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, CustomJS, Select, Range1d
from bokeh.io import show, output_file, save
from bokeh.layouts import row

x = [0, 2, 4]
y1 = [4, np.nan, 0]
y2 = [8, 20, np.nan]

import numpy as np
import pandas as pd

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Select
from bokeh.io import curdoc
from bokeh.layouts import row, column

x = [0, 2, 4]
y1 = [4, 10, 20]
y2 = [8, 20, 40]

source = ColumnDataSource(data=dict(x=x, y1=y1, y2=y2))

lines = dict()

p = figure()
lines['line1'] = p.line('x', 'y1', source=source, visible=False)
lines['line2'] = p.line('x', 'y2', source=source, visible=True)

select = Select(value='line1', options=['line1', 'line2'])

def update_plot(attr, old, new):
    lines[old].visible = not lines[old].visible
    lines[new].visible = not lines[new].visible

select.on_change('value', update_plot)

# add to document
curdoc().add_root(column(select, p))
curdoc().title = "test"
