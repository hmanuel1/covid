"""
   Visualize map with COVID-19 cases
"""

from os.path import join

import numpy as np

from bokeh.plotting import figure
from bokeh.models import DateSlider
from bokeh.models import (
    CustomJS,
    GeoJSONDataSource,
    HoverTool,
    Legend,
    LinearColorMapper,
    Select,
    GroupFilter,
    CDSView,
    Button,
    Label
)
from bokeh.layouts import column, row
from bokeh.io import curdoc
from bokeh.palettes import Purples
from bokeh.themes import Theme

from database import DataBase
from utilities import cwd
from sql import (
    US_MAP_PIVOT_VIEW_TABLE,
    OPTIONS_TABLE
)
from nytimes import (
    LEVELS_TABLE,
    DATES_TABLE
)
from wrangler import STATE_MAP_TABLE


# for unit testing
UNIT_TESTING = False
TRACING = True


class Map:
    """
        Map Layout Class
    """
    def __init__(self, **kwargs):
        self.palette = kwargs.pop('palette')

        # init metadata dictionary
        self.meta = dict()

        # get data and metadata from database
        _db = DataBase()
        self.counties = _db.get_geotable(US_MAP_PIVOT_VIEW_TABLE)

        self.meta['levels'] = _db.get_table(LEVELS_TABLE)
        self.meta['dates'] = _db.get_table(DATES_TABLE, parse_dates=['date'])
        self.meta['options'] = _db.get_table(OPTIONS_TABLE)

        _cols = ['state_id', 'geometry']
        self.states = _db.get_geotable(STATE_MAP_TABLE, columns=_cols)
        _db.close()

        # format metadata
        self.meta['levels'] = list(self.meta['levels']['level'])
        self.meta['dates'] = list(self.meta['dates']['date'])

        _id, _state = self.meta['options']['id'], self.meta['options']['state']
        self.meta['options'] = list(zip(_id, _state))

        # init plot
        self.plot = figure(match_aspect=True, toolbar_location='right',
                           tools="box_zoom, wheel_zoom, pan, reset, save",
                           **kwargs)
         # hide axes
        self.plot.axis.visible = False

        # init class variables
        self.controls = dict()
        self.srcs = dict(counties=GeoJSONDataSource(geojson=self.counties.to_json()),
                         states=GeoJSONDataSource(geojson=self.states.to_json()))

        # build map
        self.plot_map()

    def __add_counties(self):
        """Add county patches to figure
        """
        # build county colors and line parameters
        _color_mapper = LinearColorMapper(palette=self.palette, low=0, high=9)
        _color = dict(field='m', transform=_color_mapper)
        _params = dict(line_color='darkgrey', fill_color=_color, line_width=0.5)
        _params['name'] = 'counties'

        # add counties to plot
        self.plot.patches(xs='xs', ys='ys', source=self.srcs['counties'], **_params)
        if TRACING:
            print('patches added')

    def __add_states(self):
        """Add state lines to figure
        """
        # build state colors and line parameters
        _params = dict(line_color='darkgrey', line_width=0.5, name='states')

        # add state to plot
        self.plot.multi_line(xs='xs', ys='ys', source=self.srcs['states'], **_params)
        if TRACING:
            print('state lines added')

    def __add_label(self):
        """ Add date label for animation
        """
        self.controls['label'] = Label(x=0.35 * self.plot.plot_width,
                                       y=0.01 * self.plot.plot_height,
                                       x_units='screen', y_units='screen',
                                       text='', render_mode='css',
                                       text_font_size=f"{0.10*self.plot.plot_height}px",
                                       text_color='#eeeeee')

        self.plot.add_layout(self.controls['label'])
        if TRACING:
            print('label added')

    def __add_hover(self):
        """Add hove tool to figure
        """
        _hover = HoverTool(renderers=self.plot.select('counties'),
                           tooltips=[('County', '@name'),
                                     ('Cases', '@c{0,0}'),
                                     ('Deaths', '@d{0,0}'),
                                     ('Population', '@pop{0,0}')])

        self.plot.add_tools(_hover)
        if TRACING:
            print('hover tool added')

    def __add_legend(self):
        """Add legend to plot
        """
        _levels = self.meta['levels']

         # names for custom legend
        _names = []
        for _level, _lead in zip(_levels, _levels[1:] + [np.nan]):
            if _level == 0:
                _names.append(f'{_level:,.0f}')

            elif not np.isinf(_lead):
                _names.append(f'{_level:,.0f} to {_lead:,.0f}')

            else:
                _names.append(f'{_level:,.0f}+')
                break

        # quad parameters
        _params = dict(top=0, bottom=0, left=0, right=0, fill_color=None,
                       visible=False)

        _items = []
        for i in reversed(range(len(self.palette))):
            _params['fill_color'] = self.palette[i]
            _items += [(_names[i], [self.plot.quad(**_params)])]

        # add lagend to plot
        self.plot.add_layout(Legend(items=_items, location='bottom_right'))
        self.plot.x_range.only_visible = True
        self.plot.y_range.only_visible = True
        if TRACING:
            print('legend added')

    def add_select(self):
        """Build select control
        """
        # select control
        self.controls['select'] = Select(value='a', options=self.meta['options'],
                                         max_width=self.plot.plot_width-40)

        # map views
        _filter = GroupFilter(column_name='state_id', group='12')
        _counties_on = CDSView(source=self.srcs['counties'], filters=[_filter])
        _counties_off = CDSView(source=self.srcs['counties'], filters=[])
        _states_on = CDSView(source=self.srcs['states'], filters=[_filter])
        _states_off = CDSView(source=self.srcs['states'], filters=[])

        _args = dict(counties_src=self.srcs['counties'], states_src=self.srcs['states'],
                     counties_glyph=self.plot.select('counties')[0],
                     states_glyph=self.plot.select('states')[0], filter=_filter,
                     counties_view_on=_counties_on, states_view_on=_states_on,
                     counties_view_off=_counties_off, states_view_off=_states_off)

        _callback = CustomJS(args=_args,
                             code="""
            if (cb_obj.value != 'a'){
                console.log(cb_obj.value);
                filter.group = cb_obj.value;
                counties_glyph.view = counties_view_on;
                states_glyph.view = states_view_on;
            }
            else{
                console.log(cb_obj.value);
                counties_glyph.view = counties_view_off;
                states_glyph.view = states_view_off;
            }
            counties_src.change.emit();
            states_src.change.emit();
            """)

        self.controls['select'].js_on_change('value', _callback)
        if TRACING:
            print('select control added')

    def add_slider(self):
        """Build slider
        """
        self.controls['slider'] = DateSlider(start=self.meta['dates'][-1].date(),
                                             end=self.meta['dates'][0].date(),
                                             value=self.meta['dates'][0].date(),
                                             width=self.plot.plot_width-40-84,
                                             title='Reported Date')

        _callback = CustomJS(args=dict(source=self.srcs['counties'],
                                       date=self.controls['slider']),
                             code="""
            // javascript code
            var data = source.data;
            var cur_day = data['day'];

            // from DateSlider
            var day = Math.floor((date.end - date.value)/(1000*60*60*24));

            // create column names
            var ci = 'c'.concat(day.toString());
            var di = 'd'.concat(day.toString());
            var mi = 'm'.concat(day.toString());

            // change data
            if (cur_day[0] != day){
                for (var i=0; i < cur_day.length; i++){
                    data['c'][i] = data[ci][i];
                    data['d'][i] = data[di][i];
                    data['m'][i] = data[mi][i];
                    cur_day[0] = day;
                }
            }
            source.change.emit();
            """)

        self.controls['slider'].js_on_change('value', _callback)
        if TRACING:
            print('slider added')

    def add_button(self):
        """Build animation button
        """
        self.controls['button'] = Button(label='► Play', width=80, height=60)

        _callback = CustomJS(args=dict(button=self.controls['button'],
                                       slider=self.controls['slider'],
                                       label=self.controls['label']),
                             code="""
            function fDate(ms){
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                                'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                var d = new Date(ms);
                var date = d.getDate();
                if (date < 10){
                    date = '0' + date;
                }
                return `${date} ${months[d.getMonth()]} ${d.getFullYear()}`
            };
            var increment_slider = function(){
                if (button.label == '► Play'){
                    label.text = ""
                    clearInterval(interval);
                }
                else{
                    // update slider value
                    var temp = slider.value;
                    temp = temp + 1000*60*60*24;
                    if (temp > slider.end){
                        temp = slider.start;
                    }
                    slider.value = temp;

                    // add date label to graph
                    var d = new Date(temp + 1000*60*60*24);
                    label.text = fDate(d)
                }
            };
            if (button.label == '► Play'){
                button.label = '❚❚ Pause';
                var interval = setInterval(increment_slider, 750, slider);
            }
            else{
                button.label = '► Play';
                clearInterval(interval);
            };
            """)

        self.controls['button'].js_on_click(_callback)
        if TRACING:
            print('play button added')

    def plot_map(self):
        """ Build map elements
        """
        self.__add_counties()
        self.__add_states()
        self.__add_hover()
        self.__add_label()
        self.__add_legend()
        self.add_select()
        self.add_slider()
        self.add_button()


if UNIT_TESTING:

    # unit test module in stand alone mode
    palette = list(reversed(Purples[8]))
    plot = Map(plot_width=800, plot_height=400, palette=palette)
    layout = column(plot.controls['select'],
                    plot.plot,
                    row(plot.controls['slider'], plot.controls['button']))

    curdoc().add_root(layout)
    curdoc().title = 'maps'
    curdoc().theme = Theme(filename=join(cwd(), "theme.yaml"))
