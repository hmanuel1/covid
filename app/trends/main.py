# %%
import numpy as np
import pandas as pd
from bokeh.io import show, output_file
from bokeh.palettes import Purples
from bokeh.layouts import gridplot, column, row
from bokeh.plotting import figure
from bokeh.models import (ColumnDataSource, Select, CustomJS,
                        GroupFilter, CDSView, MultiSelect,
                        NumeralTickFormatter, HoverTool, Legend,
                        WheelZoomTool, PanTool, HoverTool, SaveTool,
                        BoxZoomTool, ResetTool)

def cases_trends(df, y_var, palette=Purples[3], title=None, plot_width=600,
        plot_height=600):
    # state category
    cats = sorted(list(df['state'].unique()))

    # plot
    p = figure(x_axis_type='datetime', plot_width=plot_width,
            plot_height=plot_height, title=title)

    source = dict()
    ly_var = dict()
    lpredi = dict()
    lupper = dict()
    llower = dict()
    vareaf = dict()
    for cat in cats:
        source[cat] = ColumnDataSource(df[df['state'] == cat])

        ly_var[cat] = p.line('date', y_var, source=source[cat],
            line_color= palette[0], visible=False)

        p.add_tools(HoverTool(renderers=[ly_var[cat]], toggleable=False,
            tooltips=[('State', '@state'), ('Date', '@date{%m/%d/%Y}'),
            (y_var.title(), f"@{y_var}"+"{0,0}")],
            formatters={'@date': 'datetime'}))

        lpredi[cat] = p.line('date', 'predict', source=source[cat],
            line_color=palette[0], line_dash='dashed', visible=False)

        p.add_tools(HoverTool(renderers=[lpredi[cat]], toggleable=False,
            tooltips=[('State', '@state'), ('Date', '@date{%m/%d/%Y}'),
            (f"Predicted {y_var.title()}", '@predict{0,0}')],
            formatters={'@date': 'datetime'}))

        lupper[cat] = p.line('date', 'upper', source=source[cat],
            line_color=palette[1], visible=False)

        p.add_tools(HoverTool(renderers=[lupper[cat]], toggleable=False,
            tooltips=[('State', '@state'), ('Date', '@date{%m/%d/%Y}'),
            ('Upper 95% Limit', '@upper{0,0}')],
            formatters={'@date': 'datetime'}))

        llower[cat] = p.line('date', 'lower', source=source[cat],
            line_color=palette[1], visible=False)

        p.add_tools(HoverTool(renderers=[llower[cat]], toggleable=False,
            tooltips=[('State', '@state'), ('Date', '@date{%m/%d/%Y}'),
            ('Lower 95% Limit', '@lower{0,0}')],
            formatters={'@date': 'datetime'}))

        vareaf[cat] = p.varea(x='date', y1='lower', y2='upper',
            fill_color=palette[2], source=source[cat], fill_alpha=0.5, visible=False)

    # build legend
    items = [('Actual', [ly_var[cat]]),
            ('Predicted', [lpredi[cat]]),
            ('95% Confidence', [vareaf[cat]])]

    p.add_layout(Legend(items=items, location='top_left',
            background_fill_alpha=0, background_fill_color=None,
            border_line_color=None, label_text_font_size='8pt'))

    p.xaxis.ticker.desired_num_ticks = 10
    p.y_range.only_visible = True
    p.yaxis.axis_label = y_var.title()
    p.xaxis.axis_label = 'Date'
    p.grid.grid_line_color = None
    p.toolbar.active_drag = None
    p.toolbar.logo = None
    p.yaxis.formatter = NumeralTickFormatter(format='0,0')

    out = dict(ly_var=ly_var, lpredi=lpredi, lupper=lupper, llower=llower,
            vareaf=vareaf, sources=source, cats=cats)

    return p, out


def multi_select_client(value, glyphs):
    """ multi state select """

    mselect = MultiSelect(title='States:', value=value,
            options=glyphs[0]['cats'])

    callbacks = []
    for i, glyph in enumerate(glyphs):
        callbacks.append(CustomJS(args=dict(source=glyph['sources'],
            y_var=glyph['ly_var'], predi=glyph['lpredi'],
            upper=glyph['lupper'], lower=glyph['llower'],
            varea=glyph['vareaf'], mselect=mselect),
            code = '''
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
    """ multi state select """

    mselect = MultiSelect(title='States:', value=value,
            options=glyphs[0]['cats'])

    def callback(attrname, old, new):
        for glyph in glyphs:
            source = glyph['sources']
            y_var = glyph['ly_var']
            predi = glyph['lpredi']
            upper = glyph['lupper']
            lower = glyph['llower']
            varea = glyph['vareaf']

            for option in mselect.options:
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


def render_cases(df, y_var, date, palette=Purples[3]):
    df = df[df['date'] > pd.to_datetime(date)]

    # select top 10 state by number of cases
    top10 = df.groupby('state').max()[[y_var]]
    top10 = top10.sort_values(y_var, ascending=False)
    top10 = list(top10.index)[:10]

    # render lines
    p, out = cases_trends(df, y_var, palette,
                title=f"Cumulative {y_var.title()} by State",
                plot_width=600, plot_height=300)
    return p, top10, out


def show_predictions(cases, deaths, start_date, palette=Purples[3]):
    p_cases, top10_cases, out_cases = render_cases(cases,
        'cases', start_date, palette)
    p_deaths, top10_deaths, out_deaths = render_cases(deaths,
        'deaths', start_date, palette)

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
    mselect = multi_select_server(value=top10_cases,
            glyphs=[out_cases, out_deaths])
    mselect.max_width = 180
    mselect.min_height = 500-40

    graphs = gridplot([p_cases, p_deaths], ncols=1,
            plot_width=800-mselect.max_width-40,
            plot_height=250, toolbar_location='right',
            toolbar_options=dict(logo=None))

    layout = row(mselect, graphs)
    return  layout

from os import getcwd
from os.path import dirname, join
from bokeh.io import curdoc

palette = Purples[3]

try: __file__
except NameError: cwd = getcwd()
else: cwd = dirname(__file__)

cases = pd.read_csv(join(cwd, 'output', 'arima-cases.csv'), parse_dates=['date'])
deaths = pd.read_csv(join(cwd, 'output', 'arima-deaths.csv'), parse_dates=['date'])

layout = show_predictions(cases=cases, deaths=deaths,
        start_date='3/15/2020', palette=palette)

curdoc().add_root(layout)
curdoc().title = "trends"
