import numpy as np
import pandas as pd
import os
import plotly.express as px


class DashData:
    """
    Графическое представление результатов оптимизации
    """

    def __init__(self, scenarios_folder_path: str = None, load_base: bool = True):
        if not scenarios_folder_path:
            self.scenarios_folder_path = os.path.join('.', 'data', 'scenarios')
        else:
            self.scenarios_folder_path = scenarios_folder_path

        self.color_discrete_map = {
            'Перемещение судна': 'DeepSkyBlue',
            'Ожидание': 'red',
            '50 лет Победы': 'brown',
            'Вайгач': 'BlueViolet',
            'Ямал': 'DarkOliveGreen',
            'Таймыр': 'Chocolate',
            'Порт назначения': 'Black',
        }
        self.ports_df = pd.DataFrame(columns=['scenario_name'])
        self.edges_df = pd.DataFrame(columns=['scenario_name'])
        self.icebreakers_df = pd.DataFrame(columns=['scenario_name'])
        self.vessels_df = pd.DataFrame(columns=['scenario_name'])
        self.velocity_df = pd.DataFrame(columns=['scenario_name'])
        self.result_departures_df = pd.DataFrame(columns=['scenario_name'])
        self.summary_stat_df = pd.DataFrame(columns=['scenario_name'])
        self.detailed_stat_df = pd.DataFrame(columns=['scenario_name'])

        self.base_map_fig = {}
        self.ports_dict = {}
        self.velocity_plot_points_figs = {}
        self.scenario_marks_mapping = {}

        # По умолчанию загружается базовый сценарий
        if load_base:
            self.upload_scenario('base')

    @property
    def category_orders(self):
        vessel_order_list = (
                self.vessels_df.sort_values(by=['date_start'], ascending=False)['vessel_name'].unique().tolist()
                + self.icebreakers_df.sort_values(by=['vessel_id'], ascending=False)['vessel_name'].unique().tolist()
        )
        return {'vessel_name': vessel_order_list}

    @property
    def scenarios_to_upload(self) -> list:
        return [
            scenario
            for scenario in os.listdir(self.scenarios_folder_path)
            if os.path.isdir(os.path.join(self.scenarios_folder_path, scenario))
        ]

    def fill_additional_data(self, scenario_name):
        self.ports_dict[scenario_name] = (
            self.ports_df[self.ports_df['scenario_name'] == scenario_name]
                .set_index(['point_id'])
                .to_dict(orient='index')
        )
        self.base_map_fig[scenario_name] = self.create_base_map_figure(scenario_name)
        self.create_velocity_objects_for_plot(scenario_name)

    def read_scenario_data_from_folder(self, scenario_name: str):
        input_folder_path = os.path.join(self.scenarios_folder_path, scenario_name, 'input')
        output_folder_path = os.path.join(self.scenarios_folder_path, scenario_name, 'output')

        with pd.ExcelFile(os.path.join(input_folder_path, 'model_data.xlsx')) as reader:
            ports_df = pd.read_excel(reader, sheet_name='points')
            edges_df = pd.read_excel(reader, sheet_name='edges')
            icebreakers_df = pd.read_excel(reader, sheet_name='icebreakers')
            vessels_df = pd.read_excel(reader, sheet_name='vessels')
        with pd.ExcelFile(os.path.join(input_folder_path, 'velocity_env.xlsx')) as reader:
            velocity_df = pd.read_excel(reader, sheet_name='Sheet1')
        with pd.ExcelFile(os.path.join(output_folder_path, 'departures.xlsx')) as reader:
            result_departures_df = pd.read_excel(reader, sheet_name='Sheet1')
        with pd.ExcelFile(os.path.join(output_folder_path, 'statistics.xlsx')) as reader:
            summary_stat_df = pd.read_excel(reader, sheet_name='Общая статистика')
            detailed_stat_df = pd.read_excel(reader, sheet_name='Частная статистика')
        self.add_edge_type(result_departures_df)

        ports_df['scenario_name'] = scenario_name
        edges_df['scenario_name'] = scenario_name
        icebreakers_df['scenario_name'] = scenario_name
        vessels_df['scenario_name'] = scenario_name
        velocity_df['scenario_name'] = scenario_name
        result_departures_df['scenario_name'] = scenario_name
        summary_stat_df['scenario_name'] = scenario_name
        detailed_stat_df['scenario_name'] = scenario_name

        result_departures_df.sort_values(by=['time_from_dt'], inplace=True)

        self.ports_df = pd.concat([self.ports_df[self.ports_df['scenario_name'] != scenario_name], ports_df])
        self.edges_df = pd.concat([self.edges_df[self.edges_df['scenario_name'] != scenario_name], edges_df])
        self.icebreakers_df = pd.concat([self.icebreakers_df[self.icebreakers_df['scenario_name'] != scenario_name], icebreakers_df])
        self.vessels_df = pd.concat([self.vessels_df[self.vessels_df['scenario_name'] != scenario_name], vessels_df])
        self.velocity_df = pd.concat([self.velocity_df[self.velocity_df['scenario_name'] != scenario_name], velocity_df])
        self.result_departures_df = pd.concat([self.result_departures_df[self.result_departures_df['scenario_name'] != scenario_name], result_departures_df])
        self.summary_stat_df = pd.concat([self.summary_stat_df[self.summary_stat_df['scenario_name'] != scenario_name], summary_stat_df])
        self.detailed_stat_df = pd.concat([self.detailed_stat_df[self.detailed_stat_df['scenario_name'] != scenario_name], detailed_stat_df])

    def upload_scenario(self, scenario_name: str):
        self.read_scenario_data_from_folder(scenario_name)
        self.fill_additional_data(scenario_name)

    def create_velocity_objects_for_plot(self, scenario_name):
        velocity_by_date = (self.velocity_df[self.velocity_df['scenario_name'] == scenario_name]
                                     .groupby('date'))
        scenario_dates = []
        scenario_ports_dict = self.ports_dict[scenario_name]
        self.velocity_plot_points_figs[scenario_name] = {}
        for date in velocity_by_date.groups.keys():
            velocity_grouped = velocity_by_date.get_group(date)
            unique_points = np.unique(velocity_grouped[['start_point_id', 'end_point_id']].values)
            unique_plot_points_df = pd.DataFrame(
                [(
                    p,
                    scenario_ports_dict[p]['point_name'],
                    scenario_ports_dict[p]['longitude'],
                    scenario_ports_dict[p]['latitude'],
                )
                 for p in unique_points],
                columns=[
                    'id',
                    'name',
                    'longitude',
                    'latitude',
                ]
            )
            velocity_fig = (
                px.scatter_mapbox(
                    unique_plot_points_df,
                    lat="latitude",
                    lon="longitude",
                    text="name",
                    zoom=2,
                    height=900,
                )
            )
            edges = []
            edges_avg_norm = []
            for edge in velocity_grouped.itertuples():
                edges += [
                    (
                        edge.start_point_id,
                        scenario_ports_dict[edge.start_point_id]['point_name'],
                        scenario_ports_dict[edge.start_point_id]['longitude'],
                        scenario_ports_dict[edge.start_point_id]['latitude'],
                    ),
                    (
                        edge.end_point_id,
                        scenario_ports_dict[edge.end_point_id]['point_name'],
                        scenario_ports_dict[edge.end_point_id]['longitude'],
                        scenario_ports_dict[edge.end_point_id]['latitude'],
                    )
                ]
                edges_avg_norm.append(edge.avg_norm)
            edges_df = pd.DataFrame(
                edges,
                columns=[
                    'id',
                    'name',
                    'longitude',
                    'latitude',
                ]
            )
            for i, (idx, edge_df) in enumerate(edges_df.groupby(edges_df.index // 2)):
                velocity_fig.add_traces(px.line_mapbox(edge_df, lat="latitude", lon="longitude").data)
                if edges_avg_norm[i] >= 19.5:
                    color = 'green'
                elif edges_avg_norm[i] >= 14.5:
                    color = 'yellow'
                elif edges_avg_norm[i] >= 9.5:
                    color = 'red'
                else:
                    color = 'black'
                velocity_fig['data'][1 + i]['line']['color'] = color

            velocity_fig.update_layout(mapbox_style="open-street-map")
            velocity_fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

            date_str = str(date.date())
            self.velocity_plot_points_figs[scenario_name][date_str] = velocity_fig
            scenario_dates.append(date_str)
        self.scenario_marks_mapping[scenario_name] = {i: date_str for i, date_str in enumerate(scenario_dates)}

    @staticmethod
    def add_edge_type(result_departures_df):
        icebreakers_departures = result_departures_df[result_departures_df['is_icebreaker'] == True]
        icebreakers_departures_dict = icebreakers_departures.groupby(['time_from_dt', 'port_from', 'port_to']).agg(
            {'vessel_name': lambda x: list(x)}).to_dict(orient='index')

        for i, row in result_departures_df.iterrows():
            if row['port_from_id'] == row['port_to_id']:
                result_departures_df.at[i, 'edge_type'] = 'Ожидание'
            elif row['is_icebreaker']:
                result_departures_df.at[i, 'edge_type'] = row['vessel_name']
            elif row['need_assistance']:
                result_departures_df.at[i, 'edge_type'] = \
                    icebreakers_departures_dict[(row['time_from_dt'], row['port_from'], row['port_to'])]['vessel_name'][
                        0]
            else:
                result_departures_df.at[i, 'edge_type'] = 'Перемещение судна'

    def create_base_map_figure(self, scenario_name):
        scenario_ports_dict = self.ports_dict[scenario_name]
        ports_df = pd.DataFrame(
            [(
                p_id,
                p['point_name'],
                p['longitude'],
                p['latitude']
            ) for p_id, p in scenario_ports_dict.items()],
            columns=[
                'id',
                'name',
                'longitude',
                'latitude',
            ]
        )
        fig = px.scatter_mapbox(
            ports_df,
            lat="latitude",
            lon="longitude",
            text="name",
            zoom=2,
            height=400,
            width=1250,
        )

        all_edges = []
        for id, edge in enumerate(self.edges_df[self.edges_df['scenario_name'] == scenario_name].itertuples()):
            all_edges += [
                (
                    id,
                    scenario_ports_dict[edge.start_point_id]['longitude'],
                    scenario_ports_dict[edge.start_point_id]['latitude']
                ),
                (
                    id,
                    scenario_ports_dict[edge.end_point_id]['longitude'],
                    scenario_ports_dict[edge.end_point_id]['latitude']
                ),
            ]

        plot_edges_df = pd.DataFrame(
            all_edges,
            columns=[
                'id',
                'longitude',
                'latitude',
            ]
        )
        for id in range(len(all_edges) // 2):
            edge_df = plot_edges_df[plot_edges_df['id'] == id]
            fig.add_traces(px.line_mapbox(edge_df, lat="latitude", lon="longitude").data)

        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig

    def add_vessel_route(self, fig, vessel_name, scenario_name):
        vessel_route_df = self.result_departures_df[
            (self.result_departures_df['vessel_name'] == vessel_name)
            & (self.result_departures_df['scenario_name'] == scenario_name)
        ]
        scenario_ports_dict = self.ports_dict[scenario_name]
        vessel_route_port_list = []
        for i, row in enumerate(vessel_route_df.itertuples()):
            port_from_lon, port_from_lat = (
                scenario_ports_dict[row.port_from_id]['longitude'],
                scenario_ports_dict[row.port_from_id]['latitude']
            )
            vessel_route_port_list.append(
                (port_from_lon, port_from_lat)
            )
            if i == len(vessel_route_df) - 1:
                port_to_lon, port_to_lat = (
                    scenario_ports_dict[row.port_to_id]['longitude'],
                    scenario_ports_dict[row.port_to_id]['latitude']
                )
                vessel_route_port_list.append(
                    (port_to_lon, port_to_lat)
                )
        vessel_route_port_df = pd.DataFrame(
            vessel_route_port_list,
            columns=[
                'longitude',
                'latitude',
            ]
        )
        fig.add_traces(
            px.line_mapbox(vessel_route_port_df, lat="latitude", lon="longitude").data
        )
        line_num = len(fig['data']) - 1
        fig['data'][line_num]['line']['width'] = 5
        fig['data'][line_num]['line']['color'] = 'red'


dash_data = DashData()
