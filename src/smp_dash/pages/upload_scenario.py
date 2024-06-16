from dash import html, dcc, callback, Output, Input

from src.smp_dash.data import dash_data
from src.smp_dash.pages.home import get_sidebar


def layout():
    layout = [
        get_sidebar(__name__),
        html.H1(children='СМП', style={'textAlign': 'center'}),
        html.Div(
            className="upload-upper-menu",
            children=[
                html.Div(
                    id="upload-select-scenario-outer",
                    children=[
                        html.Label("Выберите сценарий для загрузки"),
                        dcc.Dropdown(
                            dash_data.scenarios_to_upload,
                            id='upload-select-scenario-dropdown',
                            clearable=True,
                        ),
                    ],
                    style=dict(width='33.33%'),
                ),
                html.Button(
                    'Загрузить',
                    id='upload-select-scenario-button',
                    n_clicks=0,
                    style=dict(width='33.33%'),
                ),
            ]
        ),
        html.Br(),
        html.Div(
            className="upload-upper-menu",
            children=[
                html.Label("Лог загрузки сценария:"),
                html.Br(),
                dcc.Textarea(
                    id='upload-log-text',
                    value='',
                    style={'width': '40%', 'height': 300},
                ),
            ]
        ),
    ]
    return layout


@callback(
    Output('upload-log-text', 'value'),
    Input('upload-select-scenario-button', 'n_clicks'),
    Input('upload-select-scenario-dropdown', 'value'),
)
def upload_new_sceanrio(n_clicks, scenario_name):
    if n_clicks > 0:
        try:
            dash_data.upload_scenario(scenario_name)
        except Exception as e:
            return (
                f'{n_clicks}: Не удалось загрузить сценарий {scenario_name}\n',
                str(e)
            )
        return f'{n_clicks}: Сценарий {scenario_name} успешно загружен'
    return ''
