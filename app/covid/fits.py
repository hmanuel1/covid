"""
   Visualize output of fitted models on FDEM covid-19 data
"""

from os.path import join

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.layouts import column
from bokeh.layouts import row
from bokeh.io import curdoc
from bokeh.palettes import Purples
from bokeh.themes import Theme

from utilities import cwd, vbar
from database import DataBase
from clf import (
    MODELS_ROC_TABLE,
    IMPORTANCE_TABLE
)


THEME = join(cwd(), 'theme.yaml')


def roc(data, palette, plot_width=400, plot_height=400):
    """Plot ROC curve for all the models

    Arguments:
        data {DataFrame} -- data with model roc values
        palette {list} -- rgb color palette

    Keyword Arguments:
        plot_width {int} -- plot with (default: {400})
        plot_height {int} -- plot height (default: {400})

    Returns:
        Bokeh Figure Object -- plot instance
    """
    figure_settings = dict(title='Receiver Operating Curve (ROC) in Florida',
                           plot_width=plot_width, plot_height=plot_height,
                           toolbar_location=None,
                           tools='save, pan, box_zoom, reset, wheel_zoom')

    # plot
    plot = figure(**figure_settings)

    lines = dict()
    for category, color in zip(data['model'].unique(), palette):

        source = ColumnDataSource(data[data['model'] == category])

        line_settings = dict(line_color=color, line_width=2, line_dash='solid',
                             muted_color=color, muted_alpha=0.2)

        if category == 'Random':
            line_settings = dict(line_color='black', line_width=2, line_dash='dashed',
                                 muted_color='black', muted_alpha=0.2)

        lines[category] = plot.line(x='fpr', y='tpr',
                                    source=source, **line_settings)

        plot.add_tools(HoverTool(renderers=[lines[category]],
                                 tooltips=[('Model', '@model'),
                                           ('False Pos Rate',
                                            '@fpr'),
                                           ('True Pos Rate',
                                            '@tpr'),
                                           ('AUC', '@auc{0.0000}'),
                                           ('LogLoss', '@logloss{0.0000}')]))

    legend = Legend(items=[(x, [lines[x]])
                           for x in lines], location='bottom_right')
    plot.add_layout(legend)

    plot.legend.click_policy = 'mute'
    plot.xaxis.axis_label = 'False Positive Rate'
    plot.yaxis.axis_label = 'True Positive Rate'

    return plot


def logloss(data, color, hover_color, plot_width=450, plot_height=250):
    """LogLoss bar chart for all models

    Arguments:
        data {DataFrame} -- data with logloss for all the models
        color {rgb color} -- bar fill color
        hover_color {rgb color} -- bar fill color when hovering over

    Keyword Arguments:
        plot_width {int} -- plot width (default: {450})
        plot_height {int} -- plot height (default: {250})

    Returns:
        Bokeh Figure Object -- plot instance
    """
    data.drop_duplicates(['model'], inplace=True)
    data.sort_values('logloss', inplace=True)

    kwargs = dict(title='LogLoss for All Fitted Models',
                  user_tooltips=[('Model', '@x'),
                                 ('LogLoss', '@top{0.0000}')],
                  user_formatters={'Logloss': 'numeral'},
                  plot_width=plot_width, plot_height=plot_height,
                  fill_color=color, hover_fill_color=hover_color,
                  yaxis_formatter='0.0000')

    plot = vbar(x=data['model'], y=data['logloss'], xlabel='Model',
                ylabel='LogLoss', **kwargs)
    return plot


def feature_importance(data, color, hover_color, plot_width=450, plot_height=250):
    """Plot feature importance from Random Forest Model

    Arguments:
        data {DataFrame} -- data with feature importance
        color {rgb color} -- bar fill color
        hover_color {rgb color} -- bar fill color when hovering over

    Keyword Arguments:
        plot_width {int} -- plot width (default: {450})
        plot_height {int} -- plot height (default: {250})

    Returns:
        Bokeh Figure Object -- plot instance
    """
    kwargs = dict(title='Feature Importance for Random Forest Model',
                  user_tooltips=[('Feature', '@x'),
                                 ('Importance', '@top{0.0%}')],
                  user_formatters={'Importance': 'numeral'},
                  plot_width=plot_width, plot_height=plot_height,
                  fill_color=color, hover_fill_color=hover_color,
                  yaxis_formatter='0%')

    plot = vbar(x=data['feature'], y=data['importance'], xlabel='Feature',
                ylabel='Importance', **kwargs)

    return plot


def models_result(data, importance, palette, color, hover_color):
    """Module main function to plot roc, logloss and feature importance

    Arguments:
        data {DataFrame} -- data with roc and logloss
        importance {DataFrame} -- data with feature importance
        palette {list} -- rgb color palette
        color {rgb color} -- bar fill color
        hover_color {rgb color} -- bar fill color when hovering over

    Returns:
        [type] -- [description]
    """
    layout = row(roc(data, palette, plot_width=400, plot_height=400),
                 column(logloss(data, color, hover_color,
                                plot_width=400, plot_height=200),
                        feature_importance(importance, color, hover_color,
                                           plot_width=400,
                                           plot_height=200)))
    return layout


if __name__[:9] == 'bokeh_app':
    print('unit testing...')

    palette_in = list(reversed(Purples[8]))
    color_in = palette_in[2]
    hover_color_in = palette_in[4]

    # dataset for models
    database = DataBase()
    data_roc = database.get_table(MODELS_ROC_TABLE)
    data_fi = database.get_table(IMPORTANCE_TABLE)
    database.close()

    curdoc().add_root(models_result(data_roc, data_fi, palette_in,
                                    color_in, hover_color_in))
    curdoc().title = 'models'
    curdoc().theme = Theme(filename=THEME)
