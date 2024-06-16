from dash import Dash, html, dcc, callback, Output, Input, dependencies, dash_table
import plotly.graph_objects as go
import plotly.express as px

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
                            html.Label("Выберите сценарий"),
                            dcc.Dropdown(
                                dash_data.result_departures_df.scenario_name.unique(),
                                'base',
                                id='route-scenario-dropdown',
                            ),
                            html.Br(),
                            html.Label("Выберите судно:"),
                            dcc.Dropdown(
                                value='Все',
                                id='route-vessel-dropdown',
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
                # html.Div(className='parent', children=[
                #     dcc.Graph(id='plot1', className='plot'),
                #     html.Div(className='spacer'),
                #     dcc.Graph(id='plot2', className='plot'),
                # ]),

            html.Div(
                id="route-upper-container",
                className="route-upper-block",
                children=[
                    build_upper_left_panel(),
                    html.Div(className='spacer'),
                    html.Div(
                        id="geo-map-outer",
                        className="my-route-upper-container-right",
                        children=[
                            html.P(
                                id="map-title",
                                children="Карта движения судна в СМП",
                            ),
                            html.Div(
                                id="route-lower-container1",
                                children=[
                                    dcc.Graph(
                                        id="route-map",
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
                        ]
                    ),
                ],
            ),
            html.Div(
                id="table-container",
                className="table-container",
                children=[
                    html.Div(
                        id="table-upper",
                        children=[
                            html.P("Детальная статистика по маршруту судна"),
                            html.Div(id="route-detailed-stat-container"),
                        ],
                    ),
                ],
            ),
            html.Br(),
            html.Div(
                id="geo-map-loading-outer",
                children=[
                    dcc.Graph(id='route-graph-gant')
                ],
            ),
            html.Br()
    ])
    ]
    return layout


@callback(
    dependencies.Output('route-vessel-dropdown', 'options'),
    dependencies.Output('route-vessel-dropdown', 'value'),
    [dependencies.Input('route-scenario-dropdown', 'value')]
)
def update_vessel_dropdown(value):
    possible_vessels = list(dash_data.result_departures_df[dash_data.result_departures_df['scenario_name'] == value]['vessel_name'].unique())
    return (
            possible_vessels,
            possible_vessels[0]
    )


@callback(
    Output('route-graph-gant', 'figure'),
    Output('route-map', 'figure'),
    Input('route-scenario-dropdown', 'value'),
    Input('route-vessel-dropdown', 'value')
)
def update_route_graph(scenario_name, vessel_name):
    if vessel_name != 'Пусто':
        route_fig = go.Figure(dash_data.base_map_fig[scenario_name])
        dash_data.add_vessel_route(route_fig, vessel_name, scenario_name)
        gant_df = dash_data.result_departures_df[
            (dash_data.result_departures_df.scenario_name == scenario_name)
            & (dash_data.result_departures_df.vessel_name == vessel_name)
        ]
    else:
        route_fig = dash_data.base_map_fig[scenario_name]
        gant_df = dash_data.result_departures_df[
            (dash_data.result_departures_df.vessel_name == '____UNREAL_VALUE_____')
        ]
    gant_fig = px.timeline(gant_df, x_start="time_from_dt", x_end="time_to_dt", y="vessel_name",
                       color="edge_type", color_discrete_map=dash_data.color_discrete_map, category_orders=dash_data.category_orders,
                           hover_data=['integer_ice', 'speed', 'max_speed', 'port_from', 'port_to'])
    return gant_fig, route_fig


@callback(
    Output('route-detailed-stat-container', 'children'),
    Input('route-scenario-dropdown', 'value'),
    Input('route-vessel-dropdown', 'value'),
)
def update_summary_table(scenario_name, vessel_name):
    return dash_table.DataTable(
        id="route-detailed-table",
        columns=[{"name": i, "id": i} for i in dash_data.detailed_stat_df.columns],
        data=dash_data.detailed_stat_df[
            (dash_data.detailed_stat_df['scenario_name'] == scenario_name)
            & (dash_data.detailed_stat_df['vessel_name'] == vessel_name)
            ].to_dict('records'),
        # filter_action="native",
        page_size=5,
        style_table={'overflowX': 'auto'},
        style_cell={
            "background-color": "#242a3b",
            "color": "white",
            'height': 'auto',
            'whiteSpace': 'normal',
            'minWidth': '90px', 'width': '90px', 'maxWidth': '90px',
        },
        style_as_list_view=False,
        style_header={"background-color": "#1f2536", "padding": "0px 5px"},
    )