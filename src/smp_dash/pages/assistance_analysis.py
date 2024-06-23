from datetime import datetime

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
                            html.Label("Выберите сценарий:"),
                            dcc.Dropdown(
                                dash_data.result_departures_df.scenario_name.unique(),
                                'base',
                                id='assistance-scenario-dropdown',
                            ),
                            html.Br(),
                            html.Label("Выберите ледокол:"),
                            dcc.Dropdown(
                                list(dash_data.icebreakers_discrete_map.keys()),
                                value=list(dash_data.icebreakers_discrete_map.keys()),
                                id='assistance-icebreaker-dropdown',
                                multi=True,
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
                id="route-upper-container",
                className="route-upper-block",
                children=[
                    build_upper_left_panel(),
                    # html.Div(className='spacer'),
                    html.Div(
                        id="geo-map-outer",
                        className="my-route-upper-container-right",
                        children=[
                            html.P(
                                id="map-title",
                                children="Карта сбора караванов в СМП",
                            ),
                            html.Div(
                                id="assistance-map-loading-outer",
                                children=[
                                    dcc.Loading(
                                        id="loading",
                                        children=[
                                            dcc.Graph(
                                                id="assistance-map",
                                                figure={
                                                    "data": [],
                                                    "layout": dict(
                                                        plot_bgcolor="#171b26",
                                                        paper_bgcolor="#171b26",
                                                    ),
                                                },
                                            ),
                                        ]
                                    )
                                ],
                            ),
                        ]
                    ),
                ],
            ),
            html.Br(),
            html.Div(
                id="geo-map-loading-outer",
                children=[
                    html.Br(),
                    html.P("Детальные данные о проводках ледоколами"),
                    html.Div(id='assistance-graph-gant')
                ],
            ),
            html.Br()
        ])
    ]
    return layout


@callback(
    Output('assistance-map', 'figure'),
    Input('assistance-scenario-dropdown', 'value'),
    Input('assistance-icebreaker-dropdown', 'value'),
)
def update_assistance_graph(scenario_name, icebreaker_names):
    fig = dash_data.get_assistance_plot(scenario_name, icebreaker_names)
    return fig


# @callback(
#     Output("assistance-graph-gant", "figure"),
#     [
#         Input("assistance-map", "selectedData"),
#         Input('assistance-scenario-dropdown', 'value'),
#         Input('assistance-icebreaker-dropdown', 'value'),
#     ],
# )
def update_assistance_gant(point_select, scenario_name, icebreaker_names):
    if icebreaker_names is None:
        icebreaker_names = []
    if point_select is None:
        gant_df = dash_data.result_departures_df[
            (dash_data.result_departures_df.scenario_name == scenario_name)
            & (dash_data.result_departures_df.edge_type.isin(icebreaker_names))
        ]
    else:
        point_ids = [point['customdata'] for point in point_select['points'] if 'customdata' in point]
        gant_df = dash_data.result_departures_df[
            (dash_data.result_departures_df.scenario_name == scenario_name)
            & (dash_data.result_departures_df.edge_type.isin(icebreaker_names))
            & (dash_data.result_departures_df.port_from_id.isin(point_ids))
        ]

    gant_fig = px.timeline(
        gant_df,
        x_start="time_from_dt",
        x_end="time_to_dt",
        y="vessel_name",
        color="edge_type",
        color_discrete_map=dash_data.color_discrete_map,
        category_orders=dash_data.category_orders,
        hover_data=['integer_ice', 'speed', 'max_speed', 'port_from', 'port_to']
    )
    return gant_fig

@callback(
    Output('assistance-graph-gant', 'children'),
    [
        Input("assistance-map", "selectedData"),
        Input('assistance-scenario-dropdown', 'value'),
        Input('assistance-icebreaker-dropdown', 'value'),
    ],
)
def update_summary_table(point_select, scenario_name, icebreaker_names):
    assistance_df = dash_data.get_assistance_df(scenario_name, icebreaker_names, point_select)[
        ['port_from', 'port_to', 'time_from_dt', 'edge_type', 'assistance_count', 'vessel_names']
    ]
    assistance_df['time_from_str'] = assistance_df['time_from_dt'].apply(lambda dt: datetime.strftime(dt, '%d-%m-%Y %H-%M'))
    assistance_df.sort_values(by=['assistance_count', 'time_from_dt'], ascending=[False, True], inplace=True)
    assistance_df.drop(['time_from_dt'], axis=1, inplace=True)
    rename_dict = {
        'port_from': 'Порт начала проводки',
        'port_to': 'Порт окончания проводки',
        'time_from_str': 'Дата начала проводки',
        'edge_type': 'Ледокол, осуществляющий проводку',
        'assistance_count': 'Количество судов под проводкой',
        'vessel_names': 'Список судов под проводкой'
    }
    assistance_df.rename(columns=rename_dict, inplace=True)
    assistance_df = assistance_df[list(rename_dict.values())]
    return dash_table.DataTable(
        id="scenario-summary-table",
        columns=[{"name": i, "id": i} for i in assistance_df.columns],
        data=assistance_df.to_dict('records'),
        # filter_action="native",
        page_size=10,
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
