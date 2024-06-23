from dash import html, dcc, callback, Output, Input, dependencies

from src.smp_dash.data import dash_data
from src.smp_dash.pages.home import get_sidebar


def build_upper_left_panel():
    return html.Div(
        id="upper-left",
        # className="ten columns",
        children=[
            html.Div(
                className="row",
                children=[
                    html.Div(
                        id="scenario-select-outer",
                        children=[
                            html.Label("Выберите сценарий:"),
                            dcc.Dropdown(
                                dash_data.result_departures_df.scenario_name.unique(),
                                'base',
                                id='ice-scenario-dropdown',
                            ),
                        ],
                        style=dict(width='33.33%'),
                    ),
                    html.Div(
                        id="ice-select-outer",
                        children=[
                            html.Label("Выберите дату прогноза интегральности льда:"),
                            dcc.Slider(
                                id='ice-slider',
                                step=1,
                            ),
                        ],
                        style=dict(width='65.33%'),
                    ),
                ],
            ),
        ],
    )

def layout():
    layout = [
        get_sidebar(__name__),
        html.Div([
            html.H1(children='Дашборд сервиса по планированию маршрутов атомных ледоколов по СМП', style={'textAlign': 'center'}, className='my-head'),

            html.Div(
                id="ice-upper-container",
                className="row",
                children=[
                    build_upper_left_panel(),
                ],
            ),
            html.Div(
                id="geo-map-loading-outer",
                children=[
                    dcc.Graph(
                        id="ice-map123",
                        figure={
                            "data": [],
                            "layout": dict(
                                plot_bgcolor="#171b26",
                                paper_bgcolor="#171b26",
                            ),
                        },
                    ),
                ],
            ),
            html.Br(),
            html.Br()
    ])
    ]
    return layout


@callback(
    dependencies.Output('ice-slider', 'min'),
    dependencies.Output('ice-slider', 'max'),
    dependencies.Output('ice-slider', 'value'),
    dependencies.Output('ice-slider', 'marks'),
    [dependencies.Input('ice-scenario-dropdown', 'value')]
)
def update_ice_dropdown(value):
    return 0, len(dash_data.scenario_marks_mapping[value]) - 1, 0, dash_data.scenario_marks_mapping[value]


@callback(
    Output('ice-map123', 'figure'),
    Input('ice-scenario-dropdown', 'value'),
    Input('ice-slider', 'value')
)
def update_ice_graph(scenario_name, mark):
    if mark is None:
        return dash_data.base_map_fig[scenario_name]
    return dash_data.velocity_plot_points_figs[scenario_name][dash_data.scenario_marks_mapping[scenario_name][mark]]
