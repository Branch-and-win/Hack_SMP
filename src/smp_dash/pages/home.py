from datetime import datetime

from dash import html, dcc, callback, Output, Input, dash_table
import plotly.express as px

import dash_bootstrap_components as dbc

from src.smp_dash.data import dash_data


def get_sidebar(active_item=None):
    nav = html.Nav(id="sidebar", className="active", children=[
        html.Div(className="custom-menu", children=[
            html.Button([
                html.I(className="fa fa-bars"),
                html.Span("Toggle Menu", className="sr-only")
            ], type="button", id="sidebarCollapse", className="btn btn-primary")
        ]),
        html.Div(className="flex-column p-2 nav nav-pills", children=[
            html.A([
                html.Img(src='assets/nav.jpg', alt='', width=90, height=90, className='mx-2'),
                html.Span("СМП", className='fs-4'),
            ], className='d-flex align-items-center mb-3 mb-md-0 me-md-auto text-white text-decoration-none', href='/'),
            html.Hr(),
            dbc.NavItem(dbc.NavLink("Сводный анализ", href="/", className='text-white',
                                    active=True if active_item=='pages.home' else False)),
            dbc.NavItem(dbc.NavLink("Анализ маршрутов", href="/route_analysis", className='text-white',
                                    active=True if active_item=='pages.route_analysis' else False)),
            dbc.NavItem(dbc.NavLink("Анализ караванов", href="/assistance_analysis", className='text-white',
                                    active=True if active_item=='pages.assistance_analysis' else False)),
            dbc.NavItem(dbc.NavLink("Анализ состояния льда", href="/ice_analysis", className='text-white',
                                    active=True if active_item == 'pages.ice_analysis' else False)),
            dbc.NavItem(dbc.NavLink("Анализ лучших маршрутов", href="/best_route_analysis", className='text-white',
                                    active=True if active_item == 'pages.best_route_analysis' else False)),
            dbc.NavItem(dbc.NavLink("Загрузка сценария в дашборд", href="/upload_scenario", className='text-white',
                                    active=True if active_item == 'pages.upload_scenario' else False)),

        ])
    ])
    return nav


def build_upper_left_panel():
    return html.Div(
        id="upper-left",
        className="three columns",
        children=[
            html.Div(
                children=[
                    html.Div(
                        id="scenario-select-outer",
                        children=[
                            html.Label("Выберите сценарий:"),
                            dcc.Dropdown(
                                dash_data.result_departures_df.scenario_name.unique(),
                                'base',
                                id='home-scenario-dropdown',
                            ),
                        ],
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
            html.Br(),

            html.Div(
                id="home-upper-container",
                children=[
                    build_upper_left_panel(),
                    html.Div(
                        id="home-table-upper",
                        className="table-upper",
                        children=[
                            html.P("Сводная статистика по сценарию"),
                            html.Div(id="scenario-summary-table-container"),
                        ],
                    ),
                ],
            ),
            html.Br(),
            html.Div(
                id="home-lower-container",
                children=[
                    dcc.Graph(id='home-graph-gant'),
                    html.Br(),
                    html.P("Детальная статистика по сценарию"),
                    html.Div(id="scenario-detailed-table-container")
                ],
            ),
        html.Br(),
        html.Br()
    ])
    ]
    return layout


@callback(
    Output('home-graph-gant', 'figure'),
    Input('home-scenario-dropdown', 'value'),
)
def update_graph(scenario_name):
    print(f'Created gant {datetime.now()}')
    gant_df = dash_data.result_departures_df[
        (dash_data.result_departures_df.scenario_name == scenario_name)
    ]
    gant_fig = px.timeline(
        gant_df,
        x_start="time_from_dt",
        x_end="time_to_dt", y="vessel_name",
        color="edge_type",
        color_discrete_map=dash_data.color_discrete_map,
        category_orders=dash_data.category_orders,
        hover_data=['integer_ice', 'speed', 'max_speed', 'port_from', 'port_to']
    )
    for sctart_velocity_date in dash_data.start_planning_dates_df[
        (dash_data.start_planning_dates_df['scenario_name'] == scenario_name)
    ]['date'].unique():
        gant_fig.add_vline(x=sctart_velocity_date, line_width=2, line_color="red")
    gant_fig.update_layout(
        plot_bgcolor='WhiteSmoke'
    )
    return gant_fig


@callback(
    Output('scenario-summary-table-container', 'children'),
    Input('home-scenario-dropdown', 'value'),
)
def update_summary_table(scenario_name):
    return dash_table.DataTable(
        id="scenario-summary-table",
        columns=[{"name": i, "id": i} for i in dash_data.summary_stat_df.columns],
        data=dash_data.summary_stat_df[dash_data.summary_stat_df['scenario_name'] == scenario_name].to_dict('records'),
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


@callback(
    Output('scenario-detailed-table-container', 'children'),
    Input('home-scenario-dropdown', 'value'),
)
def update_detailed_table(scenario_name):
    return dash_table.DataTable(
        id="scenario-detailed-table",
        columns=[{"name": i, "id": i} for i in dash_data.detailed_stat_df.columns],
        data=dash_data.detailed_stat_df[dash_data.detailed_stat_df['scenario_name'] == scenario_name].to_dict('records'),
        filter_action="native",
        page_size=15,
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
