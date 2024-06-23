from dash import html, dcc, callback, Output, Input, dependencies

from src.smp_dash.data import dash_data
from src.smp_dash.pages.home import get_sidebar


def build_upper_left_panel():
    return html.Div(
        id="upper-left",
        className="my-route-upper-container-left",
        children=[
            html.Div(
                # className="control-row-1",
                children=[
                    html.Div(
                        # id="scenario-select-outer",
                        children=[
                            html.Label("Выберите сценарий:"),
                            dcc.Dropdown(
                                dash_data.result_departures_df.scenario_name.unique(),
                                'base',
                                id='best-route-scenario-dropdown',
                            ),
                            html.Br(),
                            html.Label("Выберите судно:"),
                            dcc.Dropdown(
                                value='Все',
                                id='best-route-vessel-dropdown',
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )

def build_upper_right_panel():
    return html.Div(
        id="upper-left",
        className="my-route-upper-container-left",
        children=[
            html.Div(
                # className="control-row-1",
                children=[
                    html.Div(
                        # id="scenario-select-outer",
                        children=[
                            html.Label("Выберите дату:"),
                            dcc.Dropdown(
                                id='best-route-date-dropdown',
                            ),
                            html.Br(),
                            html.Label("Выберите топ маршрут:"),
                            dcc.Dropdown(
                                value='Все',
                                id='best-route-k-dropdown',
                            ),
                        ],
                    ),
                ],
            ),
        ]
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
                    build_upper_right_panel()
                ],
            ),
            html.Div(
                id="geo-map-loading-outer",
                children=[
                    dcc.Graph(
                        id="best-routes-map",
                        figure={
                            "data": [],
                            "layout": dict(
                                plot_bgcolor="#171b26",
                                paper_bgcolor="#171b26",
                            ),
                        },
                        # style={"height": "60vh"}
                    ),
                ],
            ),
            html.Br(),
            html.Br()
    ])
    ]
    return layout


# @callback(
#     dependencies.Output('ice-slider', 'min'),
#     dependencies.Output('ice-slider', 'max'),
#     dependencies.Output('ice-slider', 'value'),
#     dependencies.Output('ice-slider', 'marks'),
#     [dependencies.Input('ice-scenario-dropdown', 'value')]
# )
# def update_ice_dropdown(value):
#     return 0, len(dash_data.scenario_marks_mapping[value]) - 1, 0, dash_data.scenario_marks_mapping[value]

@callback(
    dependencies.Output('best-route-vessel-dropdown', 'options'),
    dependencies.Output('best-route-vessel-dropdown', 'value'),
    [dependencies.Input('best-route-scenario-dropdown', 'value')]
)
def update_best_route_vessel_dropdown(value):
    possible_vessels = list(dash_data.vessel_best_routes_df[dash_data.vessel_best_routes_df['scenario_name'] == value]['vessel_name'].unique())
    return (
            possible_vessels,
            possible_vessels[0]
    )


@callback(
    dependencies.Output('best-route-date-dropdown', 'options'),
    dependencies.Output('best-route-date-dropdown', 'value'),
    dependencies.Input('best-route-scenario-dropdown', 'value'),
    dependencies.Input('best-route-vessel-dropdown', 'value'),
)
def update_best_route_vessel_dropdown(scenario_name, vessel_name):
    possible_dates = list(dash_data.vessel_best_routes_df[
                                (dash_data.vessel_best_routes_df['scenario_name'] == scenario_name)
                                & (dash_data.vessel_best_routes_df['vessel_name'] == vessel_name)
                                ]['date_str'].unique())
    return (
            possible_dates,
            possible_dates[0] if len(possible_dates) else ''
    )


@callback(
    dependencies.Output('best-route-k-dropdown', 'options'),
    dependencies.Output('best-route-k-dropdown', 'value'),
    dependencies.Input('best-route-scenario-dropdown', 'value'),
    dependencies.Input('best-route-vessel-dropdown', 'value'),
    dependencies.Input('best-route-date-dropdown', 'value'),
)
def update_best_route_vessel_dropdown(scenario_name, vessel_name, date_str):
    possible_k = list(dash_data.vessel_best_routes_df[
                                (dash_data.vessel_best_routes_df['scenario_name'] == scenario_name)
                                & (dash_data.vessel_best_routes_df['vessel_name'] == vessel_name)
                                & (dash_data.vessel_best_routes_df['date_str'] == date_str)
                                ]['k'].unique())
    return (
            ['Все'] + possible_k,
            'Все'
    )


@callback(
    Output('best-routes-map', 'figure'),
    Input('best-route-scenario-dropdown', 'value'),
    Input('best-route-vessel-dropdown', 'value'),
    Input('best-route-date-dropdown', 'value'),
    Input('best-route-k-dropdown', 'value'),
)
def update_best_route_graph(scenario_name, vessel_name, date_str, k):
    return dash_data.get_vessel_best_routes(scenario_name, vessel_name, date_str, k)
