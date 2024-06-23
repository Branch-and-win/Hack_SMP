from dash import Dash, html, dcc, callback, Output, Input, dependencies, dash_table
import plotly.graph_objects as go
import plotly.express as px

from src.smp_dash.data import dash_data
from src.smp_dash.pages.home import get_sidebar


def build_upper_left_panel():
    return html.Div(
        id="assistance-upper-left",
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
                id="assistance-upper-container",
                className="route-upper-block",
                children=[
                    build_upper_left_panel(),
                ]
            ),

            html.Div(
                id="assistance-map-loading-outer",
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
                        style={"height": "60vh"}
                    ),
                ],
            ),
            html.Br(),
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