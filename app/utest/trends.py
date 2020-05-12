"""
    Visualize trends of COVID-19 cases and deaths
"""
# %%
from os.path import join

from bokeh.io import curdoc
from bokeh.palettes import Purples
from bokeh.layouts import gridplot, row
from bokeh.plotting import figure
from bokeh.themes import Theme
from bokeh.models import (
    ColumnDataSource,
    MultiSelect,
    NumeralTickFormatter,
    HoverTool,
    Legend,
    Title
)

from database import DataBase
from utilities import (
    cwd,
    ElapsedMilliseconds
)


ARIMA_CASES_TABLE = 'arima_cases'
ARIMA_DEATHS_TABLE = 'arima_deaths'


TRACING = True

class LinePlot:
    """Line plot for covid19 cases and deaths by state
    """
    def __init__(self, table):
        # data
        _db = DataBase()
        self.data = _db.get_table(table, parse_dates=['date'])
        _db.close()

        # options
        _ids = self.data['state_id'].unique()
        _states = self.data['state'].unique()
        self.options = list(zip(_ids, _states))

        self.data.set_index('state_id', inplace=True)

        self.plot = None

        # glyphs
        self.actual = dict()
        self.predict = dict()
        self.lower = dict()
        self.upper = dict()
        self.area = dict()

    def _add_figure(self):
        _args = dict(x_axis_type='datetime', tools='save')
        self.plot = figure(**_args)
        self.plot.xaxis.ticker.desired_num_ticks = 10
        self.plot.yaxis.formatter = NumeralTickFormatter(format='0,0')
        self.plot.xaxis.axis_label = 'x'
        self.plot.yaxis.axis_label = 'y'

    def _add_lines(self):
        _args = dict(x='x', y='y', source=None, name=None, visible=False)
        for _id, _state, in self.options:
            _args['name'] = _state

            _args['source'] = ColumnDataSource(data=dict(x=[], y=[]))
            self.actual[_id] = self.plot.line(**_args)

            _args['source'] = ColumnDataSource(data=dict(x=[], y=[]))
            self.predict[_id] = self.plot.line(**_args)

            _args['source'] = ColumnDataSource(data=dict(x=[], y=[]))
            self.lower[_id] = self.plot.line(**_args)

            _args['source'] = ColumnDataSource(data=dict(x=[], y=[]))
            self.upper[_id] = self.plot.line(**_args)

    def _add_hover(self):
        for _id, _state, in self.options:
            _renderers = [self.actual[_id], self.predict[_id]]
            _renderers += [self.upper[_id], self.lower[_id]]
            _hover = HoverTool(renderers=_renderers,
                               toggleable=False,
                               tooltips=[('State', '$name'),
                                         ('Date', '$x{%m/%d/%Y}'),
                                         ('Count', '$y{0,0}')],
                               formatters={'$x': 'datetime'})
            self.plot.add_tools(_hover)

    def _add_area(self):
        for _id, _state, in self.options:
            _source = ColumnDataSource(data=dict(x=[], y1=[], y2=[]))
            _area_args = dict(x='x', y1='y1', y2='y2', source=_source,
                              name=_state, visible=False)
            self.area[_id] = self.plot.varea(**_area_args)

    def _add_legend(self):
        _actual_renderer = self.actual[self.options[0][0]]
        _predict_render = self.predict[self.options[0][0]]
        _area_renderer = self.area[self.options[0][0]]

        _legend = Legend(items=[('Actual', [_actual_renderer]),
                                ('Predicted', [_predict_render]),
                                ('95% Conf.', [_area_renderer])],
                         location='top_left')

        self.plot.add_layout(_legend)

    def color_actual(self, line_color='navy', line_dash='solid'):
        """Color actual line and change line dash style in all states

        Keyword Arguments:
            line_color {rgb color} -- rgb color (default: {'navy'})
            line_dash {'solid', 'dashed'} -- line style (default: {'solid'})
        """
        for _id, _, in self.options:
            self.actual[_id].glyph.line_color = line_color
            self.actual[_id].glyph.line_dash = line_dash

    def color_predict(self, line_color='red', line_dash='dashed'):
        """Color predict line and change line dash style in all states

        Keyword Arguments:
            line_color {rgb color} -- rgb color (default: {'navy'})
            line_dash {'solid', 'dashed'} -- line style (default: {'dashed'})
        """
        for _id, _, in self.options:
            self.predict[_id].glyph.line_color = line_color
            self.predict[_id].glyph.line_dash = line_dash

    def color_interval(self, line_color='navy', line_dash='solid'):
        """Color interval lines and change line dash style in all states

        Keyword Arguments:
            line_color {rgb color} -- rgb color (default: {'navy'})
            line_dash {'solid', 'dashed'} -- line style (default: {'solid'})
        """
        for _id, _, in self.options:
            self.lower[_id].glyph.line_color = line_color
            self.lower[_id].glyph.line_dash = line_dash

            self.upper[_id].glyph.line_color = line_color
            self.upper[_id].glyph.line_dash = line_dash

    def color_area(self, fill_color='grey', fill_alpha=0.25):
        """Color interval area fill color and fill alpha in all states

        Keyword Arguments:
            fill_color {rgb color} -- rgb color (default: {'grey'})
            fill_alpha {float} -- fill alpha (default: {0.25})
        """
        for _id, _, in self.options:
            self.area[_id].glyph.fill_color = fill_color
            self.area[_id].glyph.fill_alpha = fill_alpha

    def color_palette(self, palette=Purples[3]):
        """Color lines and interval area in all states

        Keyword Arguments:
            palette {list} -- list of rgb color (default: {Purples[3]})
        """
        self.color_actual(line_color=palette[0])
        self.color_predict(line_color=palette[0])
        self.color_interval(line_color=palette[1])
        self.color_area(fill_color=palette[2])

    def title(self, title=None):
        """Plot title

        Keyword Arguments:
            title {String} -- plot title (default: {None})
        """
        self.plot.title = Title(text=title)

    def axis_label(self, xlabel='x', ylabel='y'):
        """Set x and y axis labels

        Keyword Arguments:
            xlabel {str} -- x axis label (default: {'x'})
            ylabel {str} -- y axis label (default: {'y'})
        """
        self.plot.xaxis.axis_label = xlabel
        self.plot.yaxis.axis_label = ylabel

    def render_figure(self):
        """Render figure, glyphs and color glyphs with default colors
        """
        self._add_figure()
        self._add_lines()
        self._add_area()
        self._add_hover()
        self._add_legend()
        self.color_actual()
        self.color_predict()
        self.color_interval()
        self.color_area()

class Trends:
    """Trends layout
    """
    def __init__(self, palette=Purples[3]):
        time = ElapsedMilliseconds(log_time=TRACING)

        self.cases = LinePlot(ARIMA_CASES_TABLE)
        self.cases.render_figure()
        self.cases.title("Cumulative Cases by State")
        self.cases.axis_label('Date', 'Cases')
        self.cases.color_palette(palette)

        time.log('trends:state cases')

        self.deaths = LinePlot(ARIMA_DEATHS_TABLE)
        self.deaths.render_figure()
        self.deaths.title("Cumulative Deaths by State")
        self.deaths.axis_label('Date', 'Deaths')
        self.deaths.color_palette(palette)

        time.log('trends:state deaths')

        self.multiselect = None
        self._add_multiselect()
        self.multiselect.value = ['12', '34', '36']

        time.log('trends:render default states')

    def _add_multiselect(self):
        self.multiselect = MultiSelect(title='States:', value=['01'],
                                       options=self.cases.options)
        self.multiselect.max_width = 180
        self.multiselect.min_height = 500 - 40
        self.multiselect.on_change('value', self._callback_cases)
        self.multiselect.on_change('value', self._callback_deaths)

    def _callback_cases(self, _attr, _old, new):
        for _id, _ in list(self.multiselect.options):
            if self.cases.actual[_id].visible:
                self.cases.actual[_id].visible = False
                self.cases.predict[_id].visible = False
                self.cases.lower[_id].visible = False
                self.cases.upper[_id].visible = False
                self.cases.area[_id].visible = False

                self.cases.actual[_id].data_source.data = dict(x=[], y=[])
                self.cases.predict[_id].data_source.data = dict(x=[], y=[])
                self.cases.lower[_id].data_source.data = dict(x=[], y=[])
                self.cases.upper[_id].data_source.data = dict(x=[], y=[])
                self.cases.area[_id].data_source.data = dict(x=[], y1=[], y2=[])

        for _id in new:
            if not self.cases.actual[_id].visible:
                _slice = self.cases.data.loc[_id, :]
                _x = _slice['date'].to_list()

                _y = _slice['actual'].to_list()
                self.cases.actual[_id].data_source.data = dict(x=_x, y=_y)

                _y = _slice['predict'].to_list()
                self.cases.predict[_id].data_source.data = dict(x=_x, y=_y)

                _y1 = _slice['lower'].to_list()
                self.cases.lower[_id].data_source.data = dict(x=_x, y=_y1)

                _y2 = _slice['upper'].to_list()
                self.cases.upper[_id].data_source.data = dict(x=_x, y=_y2)

                self.cases.area[_id].data_source.data = dict(x=_x, y1=_y1, y2=_y2)

                self.cases.actual[_id].visible = True
                self.cases.predict[_id].visible = True
                self.cases.lower[_id].visible = True
                self.cases.upper[_id].visible = True
                self.cases.area[_id].visible = True

    def _callback_deaths(self, _attr, _old, new):
        for _id, _ in list(self.multiselect.options):
            if self.deaths.actual[_id].visible:
                self.deaths.actual[_id].visible = False
                self.deaths.predict[_id].visible = False
                self.deaths.lower[_id].visible = False
                self.deaths.upper[_id].visible = False
                self.deaths.area[_id].visible = False

                self.deaths.actual[_id].data_source.data = dict(x=[], y=[])
                self.deaths.predict[_id].data_source.data = dict(x=[], y=[])
                self.deaths.lower[_id].data_source.data = dict(x=[], y=[])
                self.deaths.upper[_id].data_source.data = dict(x=[], y=[])
                self.deaths.area[_id].data_source.data = dict(x=[], y1=[], y2=[])

        for _id in new:
            if not self.deaths.actual[_id].visible:
                _slice = self.deaths.data.loc[_id, :]
                _x = _slice['date'].to_list()

                _y = _slice['actual'].to_list()
                self.deaths.actual[_id].data_source.data = dict(x=_x, y=_y)

                _y = _slice['predict'].to_list()
                self.deaths.predict[_id].data_source.data = dict(x=_x, y=_y)

                _y1 = _slice['lower'].to_list()
                self.deaths.lower[_id].data_source.data = dict(x=_x, y=_y1)

                _y2 = _slice['upper'].to_list()
                self.deaths.upper[_id].data_source.data = dict(x=_x, y=_y2)

                self.deaths.area[_id].data_source.data = dict(x=_x, y1=_y1, y2=_y2)

                self.deaths.actual[_id].visible = True
                self.deaths.predict[_id].visible = True
                self.deaths.lower[_id].visible = True
                self.deaths.upper[_id].visible = True
                self.deaths.area[_id].visible = True

    def layout(self):
        """Build trend layout

        Returns:
            Bokeh Layout -- layout with cases, deaths and state selection
        """
        _graphs = gridplot([self.cases.plot, self.deaths.plot], ncols=1,
                           plot_width=800 - self.multiselect.max_width - 40,
                           plot_height=250, toolbar_location='right',
                           toolbar_options=dict(logo=None))

        _layout = row(self.multiselect, _graphs)

        return _layout


if __name__[:9] == 'bokeh_app':
    print('unit testing...')

    trend = Trends(palette=Purples[3])

    curdoc().add_root(trend.layout)
    curdoc().title = "trends"
    curdoc().theme = Theme(filename=join(cwd(), "theme.yaml"))
