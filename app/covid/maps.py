"""
   Visualize map with COVID-19 cases
"""

from os.path import join

import numpy as np
import pandas as pd
import geopandas as gpd

from bokeh.plotting import figure
from bokeh.models import DateSlider
from bokeh.models import (CustomJS, GeoJSONDataSource, HoverTool, Legend,
                          LinearColorMapper, Select, GroupFilter, CDSView,
                          Button, Label)
from bokeh.layouts import column, row
from bokeh.io import curdoc
from bokeh.palettes import Purples
from bokeh.themes import Theme

from wrangler import covid_data, merge_data
from utilities import cwd


class Map:
    """
        Map Layout Class
    """

    def __init__(self, **kwargs):

        # needs at least width and height
        self.palette = kwargs.pop('palette')

        # read county shapes
        _path = join(cwd(), 'shapes', 'us_map', 'us_map.shx')
        _counties = gpd.read_file(_path)

        # read state shapes
        _path = join(cwd(), 'shapes', 'state_map', 'state_map.shx')
        _states = gpd.read_file(_path)

        # get covid data
        _path = join(cwd(), 'data', 'us-counties.csv')
        _data = pd.read_csv(_path, parse_dates=[0])
        _path = join(cwd(), 'input', 'statefp-name-abbr.csv')
        _data = covid_data(_data, pd.read_csv(_path))

        # merge covid data and county shapes
        self.levels = [0, 1, 10, 100, 250, 500, 5000, 10000, np.inf]
        _counties, self.dates = merge_data(_data, _counties,
                                           self.levels, 15)

        # states options
        _path = join(cwd(), 'input', 'statefp-name-abbr.csv')
        self.options = pd.read_csv(_path, dtype={'statefp': 'str'})
        _sel = self.options['statefp'].isin(_counties['STATEFP'].unique())
        _sel = self.options[_sel].copy(deep=True)
        self.options = [('a', 'USA')] + list(zip(_sel['statefp'], _sel['name']))

        # init plot
        self.plot = figure(match_aspect=True, toolbar_location='right',
                           tools="box_zoom, wheel_zoom, pan, reset, save",
                           **kwargs)
         # hide axes
        self.plot.axis.visible = False

        # init class variables
        self.controls = dict()
        self.srcs = dict(count=GeoJSONDataSource(geojson=_counties.to_json()),
                         stat=GeoJSONDataSource(geojson=_states.to_json()))

        # build map
        self.plot_map()

    def __add_counties(self):
        """ add us counties to plot """

        # build county colors and line parameters
        _color_mapper = LinearColorMapper(palette=self.palette, low=0, high=9)
        _color = dict(field='m', transform=_color_mapper)
        _params = dict(line_color='darkgrey', fill_color=_color, line_width=0.5)
        _params['name'] = 'counties'

        # add counties to plot
        self.plot.patches(xs='xs', ys='ys', source=self.srcs['count'], **_params)

    def __add_states(self):
        """ add us states to plot """

        # build state colors and line parameters
        _params = dict(line_color='darkgrey', line_width=0.5, name='states')

        # add state to plot
        self.plot.multi_line(xs='xs', ys='ys', source=self.srcs['stat'], **_params)

    def __add_label(self):
        """ add date label for animation """

        self.controls['label'] = Label(x=0.35 * self.plot.plot_width,
                                       y=0.01 * self.plot.plot_height,
                                       x_units='screen', y_units='screen',
                                       text='', render_mode='css',
                                       text_font_size=f"{0.10*self.plot.plot_height}px",
                                       text_color='#eeeeee')

        self.plot.add_layout(self.controls['label'])

    def __add_hover(self):
        """ add hover tool to plot """
        _hover = HoverTool(renderers=self.plot.select('counties'),
                           tooltips=[('County', '@NAME'),
                                     ('Cases', '@c{0,0}'),
                                     ('Deaths', '@d{0,0}'),
                                     ('Population', '@population{0,0}')])

        self.plot.add_tools(_hover)

    def __add_legend(self):
        """ add date label """

         # names for custom legend
        _names = []
        for _level, _lead in zip(self.levels, self.levels[1:] + [np.nan]):
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

    def add_select(self):
        """ add state selection """

        # select control
        self.controls['select'] = Select(value='a', options=self.options,
                                         max_width=self.plot.plot_width-40)

        # map views
        _filter = GroupFilter(column_name='STATEFP', group='12')
        _counties_on = CDSView(source=self.srcs['count'], filters=[_filter])
        _counties_off = CDSView(source=self.srcs['count'], filters=[])
        _states_on = CDSView(source=self.srcs['stat'], filters=[_filter])
        _states_off = CDSView(source=self.srcs['stat'], filters=[])

        _args = dict(counties_src=self.srcs['count'], states_src=self.srcs['stat'],
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

    def add_slider(self):
        """ add slider """
        self.controls['slider'] = DateSlider(start=self.dates[-1].date(),
                                             end=self.dates[0].date(),
                                             value=self.dates[0].date(),
                                             width=self.plot.plot_width-40-84,
                                             title='Reported Date')

        _callback = CustomJS(args=dict(source=self.srcs['count'],
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

    def add_button(self):
        """ add button """
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
                    clearInterval(looop);
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
                var looop = setInterval(increment_slider, 750, slider);
            }
            else{
                button.label = '► Play';
                clearInterval(looop);
            };
            """)

        self.controls['button'].js_on_click(_callback)

    def plot_map(self):
        """ plot map elements """
        self.__add_counties()
        self.__add_states()
        self.__add_hover()
        self.__add_label()
        self.__add_legend()
        self.add_select()
        self.add_slider()
        self.add_button()

STAND_ALONE = False
if STAND_ALONE:

    # unit test module in stand alone mode
    palette = list(reversed(Purples[8]))
    plot = Map(plot_width=800, plot_height=400, palette=palette)
    layout = column(plot.controls['select'],
                    plot.plot,
                    row(plot.controls['slider'], plot.controls['button']))

    curdoc().add_root(layout)
    curdoc().title = 'maps'
    curdoc().theme = Theme(filename=join(cwd(), "theme.yaml"))
