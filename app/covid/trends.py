"""
    Visualize trends of COVID-19 cases and deaths
"""

from os.path import join

import pandas as pd

from bokeh.io import curdoc
from bokeh.palettes import Purples
from bokeh.layouts import gridplot, row
from bokeh.plotting import figure
from bokeh.themes import Theme
from bokeh.models import (
    ColumnDataSource,
    CustomJS,
    MultiSelect,
    NumeralTickFormatter,
    HoverTool,
    Legend
)

from utilities import cwd
from database import DataBase
from arima import (
    ARIMA_CASES_TABLE,
    ARIMA_DEATHS_TABLE
)


SIDE = 'client'


def cases_trends(data, y_var, palette=Purples[3], **kwargs):
    """Plot covid19 case trend

    Arguments:
        data {DataFrame} -- data with covid case trend
        y_var {String} -- predicted variable column name

    Keyword Arguments:
        palette {list} -- rgb color palette (default: {Purples[3]})

    Returns:
        Bokeh Figure Object -- plot instance
        dict -- instances of plot elements (e.g. lines, datasources) for animation
    """
    figure_settings = dict(title=None, plot_width=600, plot_height=600,
                           x_axis_type='datetime', tools='save, box_zoom, reset')

    for key, value in kwargs.items():
        if key in figure_settings:
            figure_settings[key] = value

    # plot
    plot = figure(**figure_settings)

    source = dict()
    ly_var = dict()
    lpredi = dict()
    lupper = dict()
    llower = dict()
    vareaf = dict()
    for cat in sorted(list(data['state'].unique())):
        source[cat] = ColumnDataSource(data[data['state'] == cat])

        ly_var[cat] = plot.line(x='date', y=y_var, source=source[cat],
                                line_color=palette[0], visible=False)

        plot.add_tools(HoverTool(renderers=[ly_var[cat]], toggleable=False,
                                 tooltips=[('State', '@state'), ('Date', '@date{%m/%d/%Y}'),
                                           (y_var.title(), f"@{y_var}" + "{0,0}")],
                                 formatters={'@date': 'datetime'}))

        lpredi[cat] = plot.line(x='date', y='predict', source=source[cat],
                                line_color=palette[0], line_dash='dashed', visible=False)

        plot.add_tools(HoverTool(renderers=[lpredi[cat]], toggleable=False,
                                 tooltips=[('State', '@state'), ('Date', '@date{%m/%d/%Y}'),
                                           (f"Predicted {y_var.title()}", '@predict{0,0}')],
                                 formatters={'@date': 'datetime'}))

        lupper[cat] = plot.line(x='date', y='upper', source=source[cat],
                                line_color=palette[1], visible=False)

        plot.add_tools(HoverTool(renderers=[lupper[cat]], toggleable=False,
                                 tooltips=[('State', '@state'), ('Date', '@date{%m/%d/%Y}'),
                                           ('Upper 95% Limit', '@upper{0,0}')],
                                 formatters={'@date': 'datetime'}))

        llower[cat] = plot.line(x='date', y='lower', source=source[cat],
                                line_color=palette[1], visible=False)

        plot.add_tools(HoverTool(renderers=[llower[cat]], toggleable=False,
                                 tooltips=[('State', '@state'), ('Date', '@date{%m/%d/%Y}'),
                                           ('Lower 95% Limit', '@lower{0,0}')],
                                 formatters={'@date': 'datetime'}))

        vareaf[cat] = plot.varea(x='date', y1='lower', y2='upper',
                                 fill_color=palette[2], source=source[cat],
                                 fill_alpha=0.5, visible=False)

    # legend
    plot.add_layout(Legend(items=[('Actual', [ly_var[data['state'].iat[0]]]),
                                  ('Predicted', [lpredi[data['state'].iat[0]]]),
                                  ('95% Confidence', [vareaf[data['state'].iat[0]]])],
                           location='top_left'))

    plot.xaxis.ticker.desired_num_ticks = 10
    plot.yaxis.axis_label = y_var.title()
    plot.xaxis.axis_label = 'Date'
    plot.yaxis.formatter = NumeralTickFormatter(format='0,0')

    return plot, dict(ly_var=ly_var, lpredi=lpredi, lupper=lupper, llower=llower,
                      vareaf=vareaf, sources=source,
                      cats=sorted(list(data['state'].unique())))


def multi_select_client(value, glyphs):
    """Multi-select control for state selection with client browser animation

    Arguments:
        value {list} -- starting selection options
        glyphs {list} -- bokeh glyph elements

    Returns:
        Bokeh Multi-select Object -- multi-select object instance
    """
    mselect = MultiSelect(title='States:', value=value,
                          options=glyphs[0]['cats'])

    callbacks = []
    for i, glyph in enumerate(glyphs):
        callbacks.append(CustomJS(args=dict(source=glyph['sources'],
                                            y_var=glyph['ly_var'], predi=glyph['lpredi'],
                                            upper=glyph['lupper'], lower=glyph['llower'],
                                            varea=glyph['vareaf'], mselect=mselect),
                                  code='''
            var selections = cb_obj.value;
            var options = mselect.options;
            for (var i=0; i < options.length; i++)
            {
                y_var[options[i]].visible = false;
                predi[options[i]].visible = false;
                upper[options[i]].visible = false;
                lower[options[i]].visible = false;
                varea[options[i]].visible = false;
                source[options[i]].change.emit();
            }
            for (var i=0; i < selections.length; i++)
            {
                y_var[selections[i]].visible = true;
                predi[selections[i]].visible = true;
                upper[selections[i]].visible = true;
                lower[selections[i]].visible = true;
                varea[selections[i]].visible = true;
                source[selections[i]].change.emit();
            }
            '''))
        mselect.js_on_change('value', callbacks[i])

    return mselect


def multi_select_server(value, glyphs):
    """Multi-select control for state selection with server driven animation

    Arguments:
        value {list} -- starting selection options
        glyphs {list} -- bokeh glyph elements

    Returns:
        Bokeh Multi-select Object -- multi-select object instance
    """
    mselect = MultiSelect(title='States:', value=value,
                          options=glyphs[0]['cats'])

    def callback(_attr, _old, new):
        """
           Call back function to select trend line for
           selected states.
        """

        for glyph in glyphs:
            y_var = glyph['ly_var']
            predi = glyph['lpredi']
            upper = glyph['lupper']
            lower = glyph['llower']
            varea = glyph['vareaf']

            for option in list(mselect.options):
                y_var[option].visible = False
                predi[option].visible = False
                upper[option].visible = False
                lower[option].visible = False
                varea[option].visible = False

            for selection in new:
                y_var[selection].visible = True
                predi[selection].visible = True
                upper[selection].visible = True
                lower[selection].visible = True
                varea[selection].visible = True

    mselect.on_change('value', callback)

    return mselect


def render_cases(data, y_var, date, palette=Purples[3]):
    """Select top 10 states by cases and make their plots visible

    Arguments:
        data {DataFrame} -- cases data
        y_var {String} -- predicted variable
        date {TimeStamp} -- date

    Keyword Arguments:
        palette {list} -- rgb color palette (default: {Purples[3]})

    Returns:
        Bokeh Figure Object -- plot instance
        list -- top-10 states by cases count
    """
    data = data[data['date'] > pd.to_datetime(date)]

    # select top 10 state by number of cases
    top10 = data.groupby('state').max()[[y_var]]
    top10 = top10.sort_values(y_var, ascending=False)
    top10 = list(top10.index)[:10]

    # render lines
    kwargs = dict(title=f"Cumulative {y_var.title()} by State",
                  plot_width=600, plot_height=300)

    plot, out = cases_trends(data, y_var, palette, **kwargs)

    return plot, top10, out


def show_predictions(cases, deaths, start_date, palette=Purples[3]):
    """Main module function to plot cases, deaths and add select control

    Arguments:
        cases {DataFrame} -- arima model prediction of cases by state
        deaths {DataFrame} -- arima model prediction of deaths by state
        start_date {date} -- date to show at startup

    Keyword Arguments:
        palette {list} -- rgb color palette (default: {Purples[3]})

    Returns:
        Bokeh Layout Object -- layout instance
    """
    p_cases, top10_cases, out_cases = render_cases(cases, 'cases', start_date, palette)
    p_deaths, _, out_deaths = render_cases(deaths, 'deaths', start_date, palette)

    # show top 10 states by cases
    for cat in top10_cases:
        out_cases['ly_var'][cat].visible = True
        out_cases['lpredi'][cat].visible = True
        out_cases['lupper'][cat].visible = True
        out_cases['llower'][cat].visible = True
        out_cases['vareaf'][cat].visible = True

        out_deaths['ly_var'][cat].visible = True
        out_deaths['lpredi'][cat].visible = True
        out_deaths['lupper'][cat].visible = True
        out_deaths['llower'][cat].visible = True
        out_deaths['vareaf'][cat].visible = True

    # add multiselect
    if SIDE == 'server':
        mselect = multi_select_server(value=top10_cases,
                                      glyphs=[out_cases, out_deaths])

    if SIDE == 'client':
        mselect = multi_select_client(value=top10_cases,
                                      glyphs=[out_cases, out_deaths])

    mselect.max_width = 180
    mselect.min_height = 500 - 40

    graphs = gridplot([p_cases, p_deaths], ncols=1,
                      plot_width=800 - mselect.max_width - 40,
                      plot_height=250, toolbar_location='right',
                      toolbar_options=dict(logo=None))

    return row(mselect, graphs)


if __name__[:9] == 'bokeh_app':
    print('unit testing...')

    palette_in = Purples[3]

    database = DataBase()
    cases_in = database.get_table(ARIMA_CASES_TABLE, parse_dates=['date'])
    deaths_in = database.get_table(ARIMA_DEATHS_TABLE, parse_dates=['date'])
    database.close()

    layout = show_predictions(cases=cases_in, deaths=deaths_in,
                              start_date='3/15/2020', palette=palette_in)

    curdoc().add_root(layout)
    curdoc().title = "trends"
    curdoc().theme = Theme(filename=join(cwd(), "theme.yaml"))
