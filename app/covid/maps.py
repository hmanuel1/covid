"""
   Visualize map with COVID-19 cases
"""

from os.path import join
from functools import partial
import datetime as dt

import numpy as np
import pandas as pd
import geopandas as gpd

from bokeh.plotting import figure
from bokeh.models import DateSlider
from bokeh.models import (CustomJS, GeoJSONDataSource, HoverTool, Legend,
                          LinearColorMapper, Select, GroupFilter, CDSView,
                          ColumnDataSource, Button, Label)
from bokeh.layouts import column, row
from bokeh.io import curdoc
from bokeh.palettes import Purples
from bokeh.themes import Theme

from wrangler import covid_data, merge_data
from utilities import cwd


# 'client' or 'server'
SIDE = 'client'


def select_server(options, plot_width, us_settings, state_settings, legend_settings):
    """
        Select control implemented on the browser(client) side
    """

    # select control
    select = Select(value='a', options=options, max_width=plot_width - 40)

    def update(new):
        if new != 'a':
            us_settings['filter'].group = new
            us_settings['glyph'].update(
                view=CDSView(source=us_settings['source'],
                             filters=[us_settings['filter']]))

            state_settings['filter'].group = new
            state_settings['glyph'].update(
                view=CDSView(source=state_settings['source'],
                             filters=[state_settings['filter']]))

            legend_settings['filter'].group = new
            for item in legend_settings['items']:
                item[1][0].update(view=CDSView(source=legend_settings['source'],
                                               filters=[legend_settings['filter']]))
        else:
            us_settings['glyph'].update(view=us_settings['view_off'])
            state_settings['glyph'].update(view=state_settings['view_off'])

    select.on_change(partial(update, new='value'))

    return select


def select_client(options, plot_width, us_settings, state_settings, legend_settings):
    """
        Select control implemented on the serve side
    """

    # select control
    select = Select(value='a', options=options, max_width=plot_width - 40)

    us_callback = CustomJS(args=us_settings,
                           code="""
        if (cb_obj.value != 'a')
        {
            filter.group = cb_obj.value;
            glyph.view = view_on;
        }
        else
        {
            glyph.view = view_off;
        }
        source.change.emit();
        """)

    state_callback = CustomJS(args=state_settings,
                              code="""
        if (cb_obj.value != 'a')
        {
            filter.group = cb_obj.value;
            glyph.view = view_on;
        }
        else
        {
            glyph.view = view_off;
        }
        source.change.emit();
        """)

    legend_callback = CustomJS(args=legend_settings,
                               code="""
        var state = cb_obj.value;
        if (state != 'a')
        {
            filter.group = state;
        }
        source.change.emit();
        """)

    select.js_on_change('value', us_callback)
    select.js_on_change('value', state_callback)
    select.js_on_change('value', legend_callback)

    return select


def choropleth_map(state_map, us_map, palette, legend_names, **kwargs):
    """ Build Choropleth Map
        Inputs: us_map, geopandas dataframe with us state map geometry,
                county, geopandas dataframe with us counties map geometry.
                state_map, geopandas dataframe with us state map geometry.
        outputs:
    """

    figure_settings = dict(plot_height=600, plot_width=950)
    legend_settings = dict(title=None, location=None)
    misc_settings = dict(options=None)

    # uddate settings
    for key, value in kwargs.items():
        if key in figure_settings:
            figure_settings[key] = value

        if key in legend_settings:
            legend_settings[key] = value

        if key in misc_settings:
            misc_settings[key] = value

    # local variables
    srcs = dict(ugeosource=GeoJSONDataSource(geojson=us_map.to_json()),
                sgeosource=GeoJSONDataSource(geojson=state_map.to_json()),
                lsource=ColumnDataSource(state_map[['STATEFP', 'xc', 'yc']]))

    gfilter = GroupFilter(column_name='STATEFP', group='12')

    views = dict(uview_on=CDSView(source=srcs['ugeosource'], filters=[gfilter]),
                 uview_off=CDSView(source=srcs['ugeosource'], filters=[]),
                 sview_on=CDSView(
                     source=srcs['sgeosource'], filters=[gfilter]),
                 sview_off=CDSView(source=srcs['sgeosource'], filters=[]),
                 lview=CDSView(source=srcs['lsource'], filters=[gfilter]))

    def build_figure_controls():
        """
           Build map figure and controls
        """

        # all state
        plot = figure(**figure_settings,
                      toolbar_location='right', match_aspect=True,
                      tools="box_zoom, wheel_zoom, pan, reset, save")

        upatch = plot.patches(
            xs='xs', ys='ys', source=srcs['ugeosource'], view=views['uview_off'],
            fill_color=dict(field='m', transform=LinearColorMapper(palette=palette,
                                                                   low=0, high=9)),
            line_color='darkgrey', line_width=0.5)

        slines = plot.multi_line(xs='xs', ys='ys', source=srcs['sgeosource'],
                                 view=views['sview_off'],
                                 line_color='darkgrey', line_width=0.5)

        rdate = Label(x=0.35 * figure_settings['plot_width'],
                      y=0.01 * figure_settings['plot_height'],
                      x_units='screen',
                      y_units='screen',
                      text='', render_mode='css',
                      text_font_size=f"{0.10*figure_settings['plot_height']}px",
                      text_color='#eeeeee')

        plot.add_layout(rdate)

        plot.add_tools(HoverTool(renderers=[upatch],
                                 tooltips=[('County', '@NAME'),
                                           ('Cases', '@c{0,0}'),
                                           ('Deaths', '@d{0,0}'),
                                           ('Population', '@population{0,0}')]))

        if legend_settings['location']:
            items = []
            for i in reversed(range(len(palette))):
                items += [(legend_names[i], [plot.quad(top='yc', bottom='yc', left='xc',
                                                       right='xc', source=srcs['lsource'],
                                                       view=views['lview'],
                                                       visible=False,
                                                       fill_color=palette[i])])]

            plot.add_layout(Legend(items=items, **legend_settings))

        if SIDE == 'client':
            select = select_client(misc_settings['options'],
                                   figure_settings['plot_width'],
                                   dict(source=srcs['ugeosource'],
                                        filter=gfilter,
                                        view_off=views['uview_off'],
                                        view_on=views['uview_on'],
                                        glyph=upatch),
                                   dict(source=srcs['sgeosource'],
                                        filter=gfilter,
                                        view_off=views['sview_off'],
                                        view_on=views['sview_on'],
                                        glyph=slines),
                                   dict(source=srcs['lsource'],
                                        filter=gfilter))
        if SIDE == 'server':
            select = select_server(misc_settings['options'],
                                   figure_settings['plot_width'],
                                   dict(source=srcs['ugeosource'],
                                        filter=gfilter,
                                        view_off=views['uview_off'],
                                        view_on=views['uview_on'],
                                        glyph=upatch),
                                   dict(source=srcs['sgeosource'],
                                        filter=gfilter,
                                        view_off=views['sview_off'],
                                        view_on=views['sview_on'],
                                        glyph=slines),
                                   dict(source=srcs['lsource'],
                                        filter=gfilter,
                                        items=items))

        plot.axis.visible = False

        return plot, srcs['ugeosource'], select, rdate

    return build_figure_controls()


def map_slider_server(mapsource, us_map, **kwargs):
    """
        Map slider control implemented in the server side
    """

    slider_settings = dict(start=0, end=0, value=0,
                           width=100, title='Reported Date')

    # update slider setting
    for key, value in kwargs.items():
        if key in slider_settings:
            slider_settings[key] = value

    slider = DateSlider(**slider_settings)

    def update(new):
        """
            Slider callback funtion
        """

        # number of days
        day = int((slider.end - new) / (1000 * 60 * 60 * 24))

        if us_map['day'].iat[0] != day:
            us_map['c'] = us_map[f'c{day}']
            us_map['d'] = us_map[f'd{day}']
            us_map['m'] = us_map[f'm{day}']
            us_map['day'] = day
            mapsource.geojson = us_map.to_json()

    slider.on_change(partial(update, new='value'))

    return slider


def map_slider_client(mapsource, **kwargs):
    """
        Map slider control implemented in the browser (client) side
    """

    slider_settings = dict(start=0, end=0, value=0,
                           width=100, title='Reported Date')

    # update slider setting
    for key, value in kwargs.items():
        if key in slider_settings:
            slider_settings[key] = value

    slider = DateSlider(**slider_settings)

    callback = CustomJS(args=dict(source=mapsource, date=slider),
                        code="""
        var data = source.data;
        var cur_day = data['day'];

        // from DateSlider
        var day = Math.floor((date.end - date.value)/(1000*60*60*24));

        // create column name
        var ci = 'c'.concat(day.toString());
        var di = 'd'.concat(day.toString());
        var mi = 'm'.concat(day.toString());

        // change data
        if (cur_day[0] != day)
        {
            for (var i=0; i < cur_day.length; i++)
            {
                data['c'][i] = data[ci][i];
                data['d'][i] = data[di][i];
                data['m'][i] = data[mi][i];
                cur_day[0] = day;
            }
        }
        source.change.emit();
    """)

    slider.js_on_change('value', callback)

    return slider


def map_button_server(slider, rdate, width=80, height=60):
    """
        Map button control implemented in the server side
    """

    # play button
    button = Button(label='► Play', width=width, height=height)

    looop = None

    def increment_slider():
        if button.label == '► Play':
            rdate.update(text="")
            curdoc().remove_periodic_callback(looop)
        else:
            # update slider value
            temp = slider.value
            temp = temp + 1000 * 60 * 60 * 24
            if temp > slider.end:
                temp = slider.start
            slider.update(value=temp)

            # add date label to graph
            date_in_ms = temp + 1000 * 60 * 60 * 24
            rdate.update(text=dt.date.fromtimestamp(
                date_in_ms / 1000.0).strftime('%d %b %Y'))

    def update():
        if button.label == '► Play':
            button.update(label='❚❚ Pause')
            rdate.update(text=dt.date.fromtimestamp(
                slider.value / 1000.0).strftime('%d %b %Y'))
            looop = curdoc().add_periodic_callback(increment_slider, 1000)
        else:
            button.update(label='► Play')
            rdate.update(text="")
            curdoc().remove_periodic_callback(looop)

    button.on_click(update)

    return button


def map_button_client(slider, rdate, width=80, height=60):
    """
        Map button control implemented in the client side
    """

    # play button
    button = Button(label='► Play', width=width, height=height)

    # call back funtion for heat map by date
    callback = CustomJS(args=dict(button=button, slider=slider, label=rdate),
                        code="""
        function fDate(ms)
        {
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                            'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            var d = new Date(ms);
            var date = d.getDate();
            if (date < 10)
            {
                date = '0' + date;
            }
            return `${date} ${months[d.getMonth()]} ${d.getFullYear()}`
        };
        var increment_slider = function()
        {
            if (button.label == '► Play')
            {
                label.text = ""
                clearInterval(looop);
            }
            else
            {
                // update slider value
                var temp = slider.value;
                temp = temp + 1000*60*60*24;
                if (temp > slider.end)
                {
                    temp = slider.start;
                }
                slider.value = temp;

                // add date label to graph
                var d = new Date(temp + 1000*60*60*24);
                label.text = fDate(d)
            }
        };
        if (button.label == '► Play')
        {
            button.label = '❚❚ Pause';
            var looop = setInterval(increment_slider, 750, slider);
        }
        else
        {
            button.label = '► Play';
            clearInterval(looop);
        };
        """)

    # execute CustomJS on click
    button.js_on_click(callback)
    return button


def build_us_map(us_map, state_map, **kwargs):
    """
        Build the map layout with slider, select, and buttom controls
    """

    settings = dict(palette=[], levels=[], dates=[], options=[])

    # update settings
    for key, value in kwargs.items():
        if key in settings:
            settings[key] = value

    # names for custom legend
    names = []
    for level, lead_level in zip(settings['levels'], settings['levels'][1:] + [np.nan]):
        if level == 0:
            names.append(f'{level:,.0f}')
        elif not np.isinf(lead_level):
            names.append(f'{level:,.0f} to {lead_level:,.0f}')
        else:
            names.append(f'{level:,.0f}+')
            break

    def map_layout():
        """
            Build map layout with map plot and controls
        """

        # build us map with covid19 data
        plot_settings = dict(title='Cases by County:', options=settings['options'],
                             location='bottom_right', plot_height=400, plot_width=800)

        (plot, source, select, rdate) = choropleth_map(state_map, us_map,
                                                       settings['palette'],
                                                       legend_names=names,
                                                       **plot_settings)

        slider_settings = dict(start=settings['dates'][-1].date(),
                               end=settings['dates'][0].date(),
                               value=settings['dates'][0].date(),
                               width=800 - 40 - 84)

        if SIDE == 'client':
            slider = map_slider_client(mapsource=source, **slider_settings)
            button = map_button_client(slider, rdate, width=80, height=60)

        if SIDE == 'server':
            slider = map_slider_server(mapsource=source, us_map=us_map,
                                       **slider_settings)
            button = map_button_server(slider, rdate, width=80, height=60)

        return column(select, plot, row(slider, button))

    return map_layout()


STAND_ALONE = False
if STAND_ALONE:
    # read covid-19 data from file
    df = pd.read_csv(join(cwd(), 'data', 'us-counties.csv'), parse_dates=[0])
    lookup = pd.read_csv(join(cwd(), 'input', 'statefp-name-abbr.csv'))

    # get data sets
    df = covid_data(df, lookup)
    us_map_in = gpd.read_file(join(cwd(), 'shapes', 'us_map', 'us_map.shx'))
    state_map_in = gpd.read_file(
        join(cwd(), 'shapes', 'state_map', 'state_map.shx'))

    # merge covid19 data with map data
    levels_in = [0, 1, 10, 100, 250, 500, 5000, 10000, np.inf]
    us_map_in, dates_in = merge_data(df, us_map_in, levels_in, days=15)

    # create palettes
    palette_in = list(reversed(Purples[8]))

    # state drop-down options
    sel = pd.read_csv(join(cwd(), 'input', 'statefp-name-abbr.csv'),
                      dtype={'statefp': 'str'})
    sel = sel.loc[sel['statefp'].isin(us_map_in['STATEFP'].unique())].copy(deep=True)
    options_in = [('a', 'USA')] + list(zip(sel['statefp'], sel['name']))

    # build us map and fl map layouts
    settings_in = dict(palette=palette_in, levels=levels_in, dates=dates_in,
                       options=options_in)
    us_map_layout = build_us_map(us_map_in, state_map_in, **settings_in)

    curdoc().add_root(us_map_layout)
    curdoc().title = 'maps'
    curdoc().theme = Theme(filename=join(cwd(), "theme.yaml"))
