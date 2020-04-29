import numpy as np
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import DateSlider
from bokeh.models import (CustomJS, GeoJSONDataSource, HoverTool, Legend,
                          LinearColorMapper, Select, GroupFilter, CDSView,
                          ColumnDataSource, Button, Label)
from bokeh.layouts import column, row
from bokeh.io import curdoc
import datetime as dt

# 'client' or 'server'
side = 'client'


def select_server(options, plot_width,
                  ugeosource, ufilter, uview_off, uview_on, upatch,
                  sgeosource, sfilter, sview_off, sview_on, slines,
                  lsource, lfilter, items):

    # select control
    select = Select(value='a', options=options, max_width=plot_width - 40)

    def update(attr, old, new):
        if new != 'a':
            ufilter.group = new
            upatch.update(view=CDSView(source=ugeosource, filters=[ufilter]))

            sfilter.group = new
            slines.update(view=CDSView(source=sgeosource, filters=[sfilter]))

            lfilter.group = new
            for item in items:
                item[1][0].update(view=CDSView(
                    source=lsource, filters=[lfilter]))
        else:
            upatch.update(view=uview_off)
            slines.update(view=sview_off)

    select.on_change('value', update)

    return select


def select_client(options, plot_width,
                  ugeosource, ufilter, uview_off, uview_on, upatch,
                  sgeosource, sfilter, sview_off, sview_on, slines,
                  lsource, lfilter):

    # select control
    select = Select(value='a', options=options, max_width=plot_width - 40)

    us_callback = CustomJS(args=dict(source=ugeosource,
                                     filter=ufilter, view_off=uview_off, view_on=uview_on, glyth=upatch),
                           code="""
        if (cb_obj.value != 'a')
        {
            filter.group = cb_obj.value;
            glyth.view = view_on;
        }
        else
        {
            glyth.view = view_off;
        }
        source.change.emit();
        """)

    state_callback = CustomJS(args=dict(source=sgeosource,
                                        filter=sfilter, view_off=sview_off, view_on=sview_on, glyth=slines),
                              code="""
        if (cb_obj.value != 'a')
        {
            filter.group = cb_obj.value;
            glyth.view = view_on;
        }
        else
        {
            glyth.view = view_off;
        }
        source.change.emit();
        """)

    legend_callback = CustomJS(args=dict(source=lsource, filter=lfilter),
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


def choropleth_map(state_map, us_map, palette, legend_location=None,
                   legend_title=None, legend_names=None, options=[],
                   plot_height=600, plot_width=950):
    """ Build Choropleth Map
        Inputs: us_map, geopandas dataframe with us state map geometry,
                county, geopandas dataframe with us counties map geometry.
                state_map, geopandas dataframe with us state map geometry.
        outputs:
    """

    # color mapper
    color_mapper = LinearColorMapper(palette=palette, low=0, high=9)

    # us data source and views
    ugeosource = GeoJSONDataSource(geojson=us_map.to_json())
    ufilter = GroupFilter(column_name='STATEFP', group='12')
    uview_on = CDSView(source=ugeosource, filters=[ufilter])
    uview_off = CDSView(source=ugeosource, filters=[])

    # state data source
    sgeosource = GeoJSONDataSource(geojson=state_map.to_json())
    sfilter = GroupFilter(column_name='STATEFP', group='12')
    sview_off = CDSView(source=sgeosource, filters=[])
    sview_on = CDSView(source=sgeosource, filters=[sfilter])

    # all state
    p = figure(plot_height=plot_height, plot_width=plot_width,
               background_fill_color='white', background_fill_alpha=1,
               toolbar_location='right', match_aspect=True,
               tools="box_zoom, wheel_zoom, pan, reset, save")

    upatch = p.patches('xs', 'ys', source=ugeosource, view=uview_off,
                       fill_color={'field': 'm', 'transform': color_mapper},
                       line_color='darkgrey', line_width=0.5)

    slines = p.multi_line('xs', 'ys', source=sgeosource, view=sview_off,
                          line_color='darkgrey', line_width=0.5)

    rdate = Label(x=0.35 * plot_width, y=0.01 * plot_height, x_units='screen',
                  y_units='screen', text='', render_mode='css',
                  text_font_size=f"{0.10*plot_height}px", text_color='#eeeeee')

    p.add_layout(rdate)

    # create hover tool
    p.add_tools(HoverTool(renderers=[upatch],
                          tooltips=[('County', '@NAME'),
                                    ('Cases', '@c{0,0}'),
                                    ('Deaths', '@d{0,0}'),
                                    ('Population', '@population{0,0}')]))

    # build custom legend
    # for custom legend
    lsource = ColumnDataSource(state_map[['STATEFP', 'xc', 'yc']])
    lfilter = GroupFilter(column_name='STATEFP', group='12')
    lview = CDSView(source=lsource, filters=[lfilter])

    if legend_location:
        items = []
        for i in reversed(range(len(palette))):
            items += [(legend_names[i], [p.quad(top='yc', bottom='yc', left='xc',
                                                right='xc', source=lsource,
                                                view=lview, visible=False,
                                                fill_color=palette[i])])]

        p.add_layout(Legend(items=items, location=legend_location,
                            background_fill_alpha=0, background_fill_color=None,
                            title=legend_title, border_line_color=None, spacing=0))

    p.legend.label_text_font_size = '8pt'
    p.min_border = 0
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.visible = False
    p.toolbar.active_drag = None
    p.toolbar.autohide = False
    p.toolbar.logo = None

    if side == 'client':
        select = select_client(options, plot_width,
                               ugeosource, ufilter, uview_off, uview_on, upatch,
                               sgeosource, sfilter, sview_off, sview_on, slines,
                               lsource, lfilter)
    if side == 'server':
        select = select_server(options, plot_width,
                               ugeosource, ufilter, uview_off, uview_on, upatch,
                               sgeosource, sfilter, sview_off, sview_on, slines,
                               lsource, lfilter, items)

    return p, ugeosource, select, rdate


def map_slider_server(mapsource, date_start, date_end, date_value, width, us_map):

    slider = DateSlider(start=date_start, end=date_end,
                        value=date_value, title='Reported Date', width=width)

    def update(attr, old, new):

        # number of days
        day = int((slider.end - new) / (1000 * 60 * 60 * 24))

        if us_map['day'].iat[0] != day:
            us_map['c'] = us_map[f'c{day}']
            us_map['d'] = us_map[f'd{day}']
            us_map['m'] = us_map[f'm{day}']
            us_map['day'] = day
            mapsource.geojson = us_map.to_json()

    slider.on_change('value', update)

    return slider


def map_slider_client(mapsource, date_start, date_end, date_value, width):

    slider = DateSlider(start=date_start, end=date_end,
                        value=date_value, title='Reported Date', width=width)

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

    # play button
    button = Button(label='► Play', width=width, height=height)

    looop = None

    def increment_slider():
        global looop

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
            d = temp + 1000 * 60 * 60 * 24
            rdate.update(text=dt.date.fromtimestamp(
                d / 1000.0).strftime('%d %b %Y'))

    def update():
        global looop

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


def build_us_map(us_map, state_map, palette, levels, dates, options):
    # names for custom legend
    names = []
    for level, lead_level in zip(levels, levels[1:] + [np.nan]):
        if level == 0:
            names.append(f'{level:,.0f}')
        elif not np.isinf(lead_level):
            names.append(f'{level:,.0f} to {lead_level:,.0f}')
        else:
            names.append(f'{level:,.0f}+')
            break

    # build us map with covid19 data
    map, source, select, rdate = choropleth_map(state_map, us_map,
                                                palette, legend_names=names,
                                                legend_title='Cases by County:',
                                                options=options,
                                                legend_location='bottom_right',
                                                plot_height=400, plot_width=800)

    if side == 'client':
        slider = map_slider_client(mapsource=source, date_start=dates[-1].date(),
                                   date_end=dates[0].date(),
                                   date_value=dates[0].date(),
                                   width=800 - 40 - 84)

        button = map_button_client(slider, rdate, width=80, height=60)

    if side == 'server':
        slider = map_slider_server(mapsource=source, date_start=dates[-1].date(),
                                   date_end=dates[0].date(), date_value=dates[0].date(),
                                   width=800 - 40 - 84, us_map=us_map)

        button = map_button_server(slider, rdate, width=80, height=60)

    layout = column(select, map, row(slider, button))
    return layout


if False:
    import numpy as np
    import geopandas as gpd
    import pandas as pd
    from os import getcwd
    from os.path import dirname, join
    from bokeh.io import curdoc
    from bokeh.palettes import Purples
    from wrangler import covid_data, merge_data

    try:
        __file__
    except NameError:
        cwd = getcwd()
    else:
        cwd = dirname(__file__)

    # read covid-19 data from file
    df = pd.read_csv(join(cwd, 'data', 'us-counties.csv'), parse_dates=[0])
    lookup = pd.read_csv(join(cwd, 'input', 'statefp-name-abbr.csv'))

    # get data sets
    df = covid_data(df, lookup)
    us_map = gpd.read_file(join(cwd, 'shapes', 'us_map', 'us_map.shx'))
    state_map = gpd.read_file(
        join(cwd, 'shapes', 'state_map', 'state_map.shx'))

    # merge covid19 data with map data
    levels = [0, 1, 10, 100, 250, 500, 5000, 10000, np.inf]
    us_map, dates = merge_data(df, us_map, levels, days=15)

    # create palettes
    palette = list(reversed(Purples[8]))

    # state drop-down options
    sel = pd.read_csv(join(cwd, 'input', 'statefp-name-abbr.csv'),
                      dtype={'statefp': 'str'})
    sel = sel.loc[sel['statefp'].isin(
        us_map['STATEFP'].unique())].copy(deep=True)
    options = [(x, y) for x, y in zip(sel['statefp'], sel['name'])]
    options = [('a', 'USA')] + options

    # build us map and fl map layouts
    usmap = build_us_map(us_map, state_map, palette, levels, dates, options)

    curdoc().add_root(usmap)
    curdoc().title = 'maps'
