import os

import plotly.express as px
import pandas as pd


class ModelDash:
    """
    Графическое представление результатов оптимизации
    """

    def __init__(self, input_folder_path: str, output_folder_path: str):
        self.input_folder_path = input_folder_path
        self.output_folder_path = output_folder_path

        with pd.ExcelFile(os.path.join(input_folder_path, 'model_data.xlsx')) as reader:
            self.ports_df = pd.read_excel(reader, sheet_name='points')
            self.edges_df = pd.read_excel(reader, sheet_name='edges')
            self.icebreakers_df = pd.read_excel(reader, sheet_name='icebreakers')
            self.vessels_df = pd.read_excel(reader, sheet_name='vessels')
        with pd.ExcelFile(os.path.join(output_folder_path, 'departures.xlsx')) as reader:
            self.result_departures_df = pd.read_excel(reader, sheet_name='Sheet1')

        self.ports_dict = self.ports_df.set_index('point_id').to_dict(orient='index')

    def plot_results(self):
        """
        Отрисовка результатов оптимизации
        """
        print('Подготовка картинок с результатами')

        self.result_departures_df.sort_values(by=['time_from'], inplace=True)

        icebreakers_departures = self.result_departures_df[self.result_departures_df['is_icebreaker'] == True]
        icebreakers_departures_dict = icebreakers_departures.groupby(['time_from_dt', 'port_from', 'port_to']).agg(
            {'vessel_name': lambda x: list(x)}).to_dict(orient='index')
        self.result_departures_df['edge_type'] = self.result_departures_df.apply(
            lambda x: icebreakers_departures_dict[(x['time_from_dt'], x['port_from'], x['port_to'])]['vessel_name'][0] if (
                    x['need_assistance'] is True or x['is_icebreaker'] is True) else '', axis=1)
        for i, row in self.result_departures_df.iterrows():

            if row['port_from_id'] == row['port_to_id']:
                self.result_departures_df.at[i, 'edge_type'] = 'Ожидание'
            elif row['is_icebreaker']:
                self.result_departures_df.at[i, 'edge_type'] = row['vessel_name']
            elif row['need_assistance']:
                self.result_departures_df.at[i, 'edge_type'] = \
                icebreakers_departures_dict[(row['time_from_dt'], row['port_from'], row['port_to'])]['vessel_name'][0]
            else:
                self.result_departures_df.at[i, 'edge_type'] = 'Перемещение судна'

        ports_df = pd.DataFrame(
            [(
                p.point_id,
                p.point_name,
                p.longitude,
                p.latitude
            ) for p in self.ports_df.itertuples()],
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
            zoom=1,
            height=960,
            width=1820,
        )
        always_visible = [True]

        vessel_dynamic_map_list = []
        for row in self.result_departures_df.itertuples():
            port_from = self.ports_dict[row.port_from_id]
            port_from_lon, port_from_lat = port_from['longitude'], port_from['latitude']
            port_to = self.ports_dict[row.port_from_id]
            port_to_lon, port_to_lat = port_to['longitude'], port_to['latitude']

            lon_delta = port_to_lon - port_from_lon
            lan_delta = port_to_lat - port_from_lat
            time_from = int(row.time_from)
            duration = int(row.duration)
            time_to = time_from + duration
            vessel_dynamic_map_list.append((
                row.vessel_name,
                row.is_icebreaker,
                time_from,
                port_from_lon,
                port_from_lat,
            ))
            vessel_dynamic_map_list += [
                (
                    row.vessel_name,
                    row.is_icebreaker,
                    # datetime.strftime(dt, '%Y-%m-%d'),
                    time_from + t,
                    port_from_lon + t * lon_delta / (time_to - time_from),
                    port_from_lat + t * lan_delta / (time_to - time_from),
                )
                for t in range(1, time_to - time_from, 1)
            ]
            vessel_dynamic_map_list.append((
                row.vessel_name,
                row.is_icebreaker,
                time_to,
                port_to_lon,
                port_to_lat,
            ))
        vessel_dynamic_map_df = pd.DataFrame(vessel_dynamic_map_list,
                                             columns=['vessel_name', 'is_icebreaker', 't', 'longitude', 'latitude'])
        # vessel_dynamic_map_df.to_excel('output/dyn.xlsx')
        fig1 = px.scatter_mapbox(
            vessel_dynamic_map_df,
            lat="latitude",
            lon="longitude",
            hover_name="vessel_name",
            zoom=1,
            height=960,
            width=1820,
            animation_frame='t',
            color='is_icebreaker'
        )
        fig1['data'][0]['marker']['size'] = 10

        all_edges = []
        for id, edge in enumerate(self.edges_df.itertuples()):
            all_edges += [
                (id, self.ports_dict[edge.start_point_id]['longitude'], self.ports_dict[edge.start_point_id]['latitude']),
                (id, self.ports_dict[edge.end_point_id]['longitude'], self.ports_dict[edge.end_point_id]['latitude']),
            ]

        plot_edges_df = pd.DataFrame(
            all_edges,
            columns=[
                'id',
                'longitude',
                'latitude',
            ]
        )
        for id in range(len(self.edges_df)):
            edge_df = plot_edges_df[plot_edges_df['id'] == id]
            fig.add_traces(px.line_mapbox(edge_df, lat="latitude", lon="longitude").data)
            fig1.add_traces(px.line_mapbox(edge_df, lat="latitude", lon="longitude").data)
            fig1['data'][1 + id]['line']['color'] = 'grey'
            always_visible.append(True)

        unique_vessels = self.result_departures_df['vessel_name'].unique()
        for v_num, vessel_name in enumerate(unique_vessels):
            vessel_route_df = self.result_departures_df[self.result_departures_df['vessel_name'] == vessel_name]
            vessel_route_port_list = []
            for i, row in enumerate(vessel_route_df.itertuples()):
                port_from_lon, port_from_lat = self.ports_dict[row.port_from_id]['longitude'], self.ports_dict[row.port_from_id]['latitude']
                vessel_route_port_list.append(
                    (port_from_lon, port_from_lat)
                )
                if i == len(vessel_route_df) - 1:
                    port_to_lon, port_to_lat = self.ports_dict[row.port_to_id]['longitude'], self.ports_dict[row.port_to_id]['latitude']
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
            fig['data'][len(always_visible) + v_num]['line']['width'] = 5
            fig['data'][len(always_visible) + v_num]['line']['color'] = 'red'
        vessel_visible = {
            vessel_name: [False] * i + [True] + (len(unique_vessels) - i - 1) * [False]
            for i, vessel_name in enumerate(unique_vessels)
        }

        fig.update_layout(
            updatemenus=[
                dict(
                    active=0,
                    buttons=list(
                        [
                            dict(
                                label='None',
                                method="update",
                                args=[{"visible": always_visible + len(vessel_visible) * [False]},
                                      {
                                          "title": 'Полный граф',
                                          "annotations": []
                                      }
                                      ]
                            )
                        ]
                        + [
                            dict(
                                label=vessel_name,
                                method="update",
                                args=[{"visible": len(always_visible) * [True] + visible_map},
                                      {
                                          "title": vessel_name,
                                          "annotations": []
                                      }
                                      ]
                            )
                            for vessel_name, visible_map in vessel_visible.items()
                        ]
                    ),
                )
            ])

        color_discrete_map = {
            'Перемещение судна': 'DeepSkyBlue',
            'Ожидание': 'red',
            '50 лет Победы': 'brown',
            'Вайгач': 'BlueViolet',
            'Ямал': 'DarkOliveGreen',
            'Таймыр': 'Chocolate',
        }
        vessel_order_list = (
            self.vessels_df.sort_values(by=['date_start'], ascending=False)['vessel_name'].unique().tolist()
            + self.icebreakers_df.sort_values(by=['vessel_id'], ascending=False)['vessel_name'].unique().tolist()
        )
        category_orders = {
            'vessel_name': vessel_order_list
        }
        fig2 = px.timeline(self.result_departures_df, x_start="time_from_dt", x_end="time_to_dt", y="vessel_name",
                           color="edge_type", color_discrete_map=color_discrete_map, category_orders=category_orders)

        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig.show()

        fig1.update_layout(mapbox_style="open-street-map")
        fig1.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig1.show()

        fig2.show()
