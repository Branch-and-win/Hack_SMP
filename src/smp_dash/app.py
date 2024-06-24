import dash
from dash import Dash
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from flask import Flask
from src.smp_dash.pages import home, ice_analysis, route_analysis, upload_scenario, best_route_analysis, \
    assistance_analysis

load_figure_template(["darkly"])

app = Flask(__name__, instance_relative_config=True)
dash_app = Dash(
    __name__,
    server=app,
    use_pages=True,
    assets_folder='assets',
    external_stylesheets=[dbc.themes.DARKLY]
)
dash.register_page(
    'pages.home',
    path='/',
    title='Сводный анализ',
    name='Сводный анализ',
    layout=home.layout
)
dash.register_page(
    'pages.route_analysis',
    path='/route_analysis',
    title='Анализ маршрутов',
    name='Анализ маршрутов',
    layout=route_analysis.layout
)
dash.register_page(
    'pages.assistance_analysis',
    path='/assistance_analysis',
    title='Анализ караванов',
    name='Анализ караванов',
    layout=assistance_analysis.layout
)
dash.register_page(
    'pages.ice_analysis',
    path='/ice_analysis',
    title='Анализ состояния льда',
    name='Анализ состояния льда',
    layout=ice_analysis.layout
)
dash.register_page(
    'pages.best_route_analysis',
    path='/best_route_analysis',
    title='Анализ лучших маршрутов',
    name='Анализ лучших маршрутов',
    layout=best_route_analysis.layout
)
dash.register_page(
    'pages.upload_scenario',
    path='/upload_scenario',
    title='Загрузка сценария в дашборд',
    name='Загрузка сценария в дашборд',
    layout=upload_scenario.layout
)

with app.app_context():
    dash_app.layout = dash.page_container

if __name__ == "__main__":
    app.run(host='0.0.0.0')
