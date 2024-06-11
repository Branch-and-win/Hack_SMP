import os
from datetime import datetime, timedelta

import pandas as pd
from pyomo.core import value
import plotly.express as px
import plotly.figure_factory as ff


class ModelOutput:
    def __init__(self, model, input):
        self.model = model
        self.input = input

        self.result_departures_df = pd.DataFrame(
            columns=[
                'vessel_name',
                'port_from',
                'port_from_id',
                'port_to',
                'port_to_id',
                'time_from',
                'duration',
                'initial_port',
                'initial_time',
                'target_port',
                'need_assistance',
                'is_icebreaker'
            ]
        )
        self.result_locations_df = pd.DataFrame(
            columns=[
                'vessel_name',
                'port',
                'time',
                'initial_port',
                'initial_time',
                'target_port',
                'is_icebreaker',
            ]
        )

    def create_output(self):
        result_departures = [
            [
                d.vessel.name,
                d.edge.port_from.name,
                d.edge.port_from.id,
                d.edge.port_to.name,
                d.edge.port_to.id,
                d.time,
                d.duration,
                d.vessel.port_start.name,
                d.vessel.time_start,
                '-' if d.vessel.is_icebreaker else d.vessel.port_end.name,
                1 if d.is_icebreaker_assistance else 0,
                d.vessel.is_icebreaker
            ]
            for d in self.input.departures
            if value(self.model.departure[d]) > 0.5
        ]
        self.result_departures_df = pd.DataFrame(result_departures, columns=self.result_departures_df.columns)

        result_locations = [
            [
                l.vessel.name,
                l.port.name,
                l.time,
                l.vessel.port_start.name,
                l.vessel.time_start,
                '-' if l.vessel.is_icebreaker else l.vessel.port_end.name,
                l.vessel.is_icebreaker
            ]
            for l in self.input.locations
            if value(self.model.stop_place[l]) > 0.5
        ]

        self.result_locations_df = pd.DataFrame(result_locations, columns=self.result_locations_df.columns)

        self.result_departures_df.to_excel('output/departures.xlsx')
        self.result_locations_df.to_excel('output/locations.xlsx')
        return

    def plot_routes(self):
        self.result_departures_df = pd.read_excel(os.path.join('output', 'departures.xlsx'), sheet_name='Sheet1')
        self.result_departures_df.sort_values(by=['time_from'], inplace=True)
        self.result_departures_df['time_to'] = self.result_departures_df['time_from'] + self.result_departures_df['duration']

        icebreakers_departures = self.result_departures_df[self.result_departures_df['is_icebreaker'] == True]
        icebreakers_departures_dict = icebreakers_departures.groupby(['time_from', 'port_from', 'port_to']).agg(
            {'vessel_name': lambda x: list(x)}).to_dict(orient='index')
        self.result_departures_df['edge_type'] = self.result_departures_df.apply(
            lambda x: icebreakers_departures_dict[(x['time_from'], x['port_from'], x['port_to'])]['vessel_name'][0] if (
                        x['need_assistance'] is True or x['is_icebreaker'] is True) else '', axis=1)
        for i, row in self.result_departures_df.iterrows():

            if row['port_from_id'] == row['port_to_id']:
                self.result_departures_df.at[i, 'edge_type'] = 'Ожидание'
            elif row['is_icebreaker']:
                self.result_departures_df.at[i, 'edge_type'] = row['vessel_name']
            elif row['need_assistance']:
                self.result_departures_df.at[i, 'edge_type'] = icebreakers_departures_dict[(row['time_from'], row['port_from'], row['port_to'])]['vessel_name'][0]
            else:
                self.result_departures_df.at[i, 'edge_type'] = 'Перемещение судна'
        self.result_departures_df['time_from_dt'] = self.result_departures_df['time_from'].apply(lambda x: self.input.start_date + timedelta(hours=x))
        self.result_departures_df['time_to_dt'] = self.result_departures_df['time_to'].apply(lambda x: self.input.start_date + timedelta(hours=x))

        ports_df = pd.DataFrame(
            [(
                p.id,
                p.name,
                p.longitude,
                p.latitude
            ) for p in self.input.ports],
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
            port_from = self.input.ports_dict[row.port_from_id]
            port_to = self.input.ports_dict[row.port_to_id]
            lon_delta = port_to.longitude - port_from.longitude
            lan_delta = port_to.latitude - port_from.latitude
            time_from = int(row.time_from)
            duration = int(row.duration)
            time_to = time_from + duration
            vessel_dynamic_map_list.append((
                row.vessel_name,
                row.is_icebreaker,
                time_from,
                port_from.longitude,
                port_from.latitude,
            ))
            vessel_dynamic_map_list += [
                (
                    row.vessel_name,
                    row.is_icebreaker,
                    # datetime.strftime(dt, '%Y-%m-%d'),
                    # self.input.start_date + timedelta(hours=t),
                    time_from + t,
                    port_from.longitude + t * lon_delta / (time_to - time_from),
                    port_from.latitude + t * lan_delta / (time_to - time_from),
                )
                for t in range(1, time_to - time_from, 1)
            ]
            vessel_dynamic_map_list.append((
                row.vessel_name,
                row.is_icebreaker,
                time_to,
                port_to.longitude,
                port_to.latitude,
            ))
        vessel_dynamic_map_df = pd.DataFrame(vessel_dynamic_map_list, columns=['vessel_name', 'is_icebreaker', 't', 'longitude', 'latitude'])
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
        # fig1['data'][0]['marker']['color'] = 'red'
        # fig1.add_scattermapbox(
        #     ports_df,
        #     lat="latitude",
        #     lon="longitude",
        #     text="name",
        #     zoom=1,
        #     height=1080,
        #     width=1920
        # )

        all_edges = []
        for id, edge in enumerate(self.input.edges):
            all_edges += [
                (id, edge.port_from.longitude, edge.port_from.latitude),
                (id, edge.port_to.longitude, edge.port_to.latitude)
            ]

        edges_df = pd.DataFrame(
            all_edges,
            columns=[
                'id',
                'longitude',
                'latitude',
            ]
        )
        for id in range(len(self.input.edges)):
            edge_df = edges_df[edges_df['id'] == id]
            fig.add_traces(px.line_mapbox(edge_df, lat="latitude", lon="longitude").data)
            fig1.add_traces(px.line_mapbox(edge_df, lat="latitude", lon="longitude").data)
            fig1['data'][1 + id]['line']['color'] = 'grey'
            always_visible.append(True)

        unique_vessels = self.result_departures_df['vessel_name'].unique()
        for v_num, vessel_name in enumerate(unique_vessels):
            vessel_route_df = self.result_departures_df[self.result_departures_df['vessel_name'] == vessel_name]
            vessel_route_port_list = []
            for i, row in enumerate(vessel_route_df.itertuples()):
                port_from = self.input.ports_dict[row.port_from_id]
                vessel_route_port_list.append(
                    (port_from.longitude, port_from.latitude)
                )
                if i == len(vessel_route_df) - 1:
                    port_to = self.input.ports_dict[row.port_to_id]
                    vessel_route_port_list.append(
                        (port_to.longitude, port_to.latitude)
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

        fig2 = px.timeline(self.result_departures_df, x_start="time_from_dt", x_end="time_to_dt", y="vessel_name", color="edge_type")

        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig.show()

        fig1.update_layout(mapbox_style="open-street-map")
        fig1.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig1.show()

        fig2.show()
