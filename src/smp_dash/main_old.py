import os
from datetime import datetime, timedelta
from typing import List
import plotly.express as px
import pandas as pd


class ModelDash:
    """
    Графическое представление результатов оптимизации
    """

    def __init__(self, input_folder_path: str, output_folder_path: str, scenario_start_dates: List[datetime]):
        self.input_folder_path = input_folder_path
        self.output_folder_path = output_folder_path
        self.scenario_start_dates = scenario_start_dates

        with pd.ExcelFile(os.path.join(input_folder_path, 'model_data.xlsx')) as reader:
            self.ports_df = pd.read_excel(reader, sheet_name='points')
            self.edges_df = pd.read_excel(reader, sheet_name='edges')
            self.icebreakers_df = pd.read_excel(reader, sheet_name='icebreakers')
            self.vessels_df = pd.read_excel(reader, sheet_name='vessels')
        with pd.ExcelFile(os.path.join(output_folder_path, 'departures.xlsx')) as reader:
            self.result_departures_df = pd.read_excel(reader, sheet_name='Sheet1')
            self.collect_kpi(output_folder_path, self.result_departures_df)

        self.ports_dict = self.ports_df.set_index('point_id').to_dict(orient='index')

    def plot_results(self):
        """
        Отрисовка результатов оптимизации
        """
        print('Подготовка картинок с результатами')

        self.result_departures_df.sort_values(by=['time_from_dt'], inplace=True)

        icebreakers_departures = self.result_departures_df[self.result_departures_df['is_icebreaker'] == True]
        icebreakers_departures_dict = icebreakers_departures.groupby(['time_from_dt', 'port_from', 'port_to']).agg(
            {'vessel_name': lambda x: list(x)}).to_dict(orient='index')
        self.result_departures_df['edge_type'] = self.result_departures_df.apply(
            lambda x: icebreakers_departures_dict[(x['time_from_dt'], x['port_from'], x['port_to'])]['vessel_name'][
                0] if (
                    x['need_assistance'] is True or x['is_icebreaker'] is True) else '', axis=1)

        for i, row in self.result_departures_df.iterrows():
            if row['port_from_id'] == row['port_to_id']:
                self.result_departures_df.at[i, 'edge_type'] = 'Ожидание'
            elif row['is_icebreaker']:
                self.result_departures_df.at[i, 'edge_type'] = row['vessel_name']
            elif row['need_assistance']:
                self.result_departures_df.at[i, 'edge_type'] = \
                    icebreakers_departures_dict[(row['time_from_dt'], row['port_from'], row['port_to'])]['vessel_name'][
                        0]
            else:
                self.result_departures_df.at[i, 'edge_type'] = 'Перемещение судна'

        pd.options.mode.chained_assignment = None
        vessel_ends_df = self.result_departures_df[
            (self.result_departures_df['port_to'] == self.result_departures_df['target_port'])
            & ~(self.result_departures_df['is_icebreaker'] == True)
            ]
        vessel_ends_df['edge_type'] = 'Порт назначения'
        vessel_ends_df['port_from'] = vessel_ends_df['port_to']
        vessel_ends_df['time_from_dt'] = vessel_ends_df['time_to_dt']
        vessel_ends_df['time_to_dt'] = vessel_ends_df['time_to_dt'].apply(lambda x: x + timedelta(hours=3))
        self.result_departures_df = pd.concat([self.result_departures_df, vessel_ends_df])

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
                (id, self.ports_dict[edge.start_point_id]['longitude'],
                 self.ports_dict[edge.start_point_id]['latitude']),
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
                port_from_lon, port_from_lat = self.ports_dict[row.port_from_id]['longitude'], \
                self.ports_dict[row.port_from_id]['latitude']
                vessel_route_port_list.append(
                    (port_from_lon, port_from_lat)
                )
                if i == len(vessel_route_df) - 1:
                    port_to_lon, port_to_lat = self.ports_dict[row.port_to_id]['longitude'], \
                    self.ports_dict[row.port_to_id]['latitude']
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
            'Порт назначения': 'Black',
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
        for start_scenario_date in self.scenario_start_dates:
            fig2.add_vline(x=start_scenario_date, line_width=3, line_color="red")

        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig.show()

        fig1.update_layout(mapbox_style="open-street-map")
        fig1.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig1.show()

        fig2.show()

    @staticmethod
    def get_partial_statistic(output_df: pd.DataFrame):
        """Метод вывода статистика результатов в разрезе корабля"""
        statistic_ship = pd.DataFrame()

        df = output_df[output_df['port_to'] != output_df['port_from']]
        statistic_ship['vessel_name'] = df.sort_values(by='vessel_name')['vessel_name'].unique()
        statistic_ship['vessel_id'] = df.sort_values(by='vessel_name')['vessel_id'].unique()

        df1 = df.groupby(['vessel_name'])['duration'].sum().reset_index()
        for v in df1['vessel_name'].unique():
            statistic_ship.loc[statistic_ship['vessel_name'] == v, 'Общее время движения'] = df1[df1['vessel_name'] == v]['duration'].iloc[0]

        df1 = df[
            df['need_assistance'] == 1].groupby(['vessel_name'])['duration'].sum().reset_index()
        statistic_ship['Суммарное время движения под проводкой'] = 0
        for v in df1['vessel_name'].unique():
            statistic_ship.loc[statistic_ship['vessel_name'] == v, 'Суммарное время движения под проводкой'] = \
            df1[df1['vessel_name'] == v]['duration'].iloc[0]


        df1 = df.groupby(['vessel_name'])['speed'].mean().reset_index()
        for v in df1['vessel_name'].unique():
            statistic_ship.loc[statistic_ship['vessel_name'] == v, 'Средняя скорость'] = \
                df1[df1['vessel_name'] == v]['speed'].iloc[0]

        df1 = df.groupby(['vessel_name'])['integer_ice'].mean().reset_index()
        for v in df1['vessel_name'].unique():
            statistic_ship.loc[statistic_ship['vessel_name'] == v, 'Средняя интегральная тяжесть льда'] = \
                df1[df1['vessel_name'] == v]['integer_ice'].iloc[0]

        statistic_ship = statistic_ship.merge(df[['vessel_name', 'is_icebreaker']], on='vessel_name', how='left')
        statistic_ship.rename(columns={'is_icebreaker':'Ледокол'},inplace=True)
        df1 = df[(df['integer_ice'] >= 15) & (df['integer_ice'] <= 19)].groupby(['vessel_name'])[
            'duration'].sum().reset_index()
        for v in statistic_ship['vessel_name'].unique():
            if v not in df1['vessel_name'].unique():
                continue
            statistic_ship.loc[statistic_ship['vessel_name'] == v, 'Суммарное время движения в интервале 15-19'] = \
                df1[df1['vessel_name'] == v]['duration'].iloc[0]

        df1 = df[(df['integer_ice'] >= 10) & (df['integer_ice'] <= 14)].groupby(['vessel_name'])[
            'duration'].sum().reset_index()
        for v in statistic_ship['vessel_name'].unique():
            if v not in df1['vessel_name'].unique():
                continue
            statistic_ship.loc[statistic_ship['vessel_name'] == v, 'Суммарное время движения в интервале 10-14'] = \
                df1[df1['vessel_name'] == v]['duration'].iloc[0]

        df1 = df[(df['integer_ice'] >= 20)].groupby(['vessel_name'])[
            'duration'].sum().reset_index()
        for v in statistic_ship['vessel_name'].unique():
            if v not in df1['vessel_name'].unique():
                continue
            statistic_ship.loc[statistic_ship['vessel_name'] == v, 'Суммарное время движения в интервале 20+'] = \
                df1[df1['vessel_name'] == v]['duration'].iloc[0]

        # собираем статистику по ожиданиям
        df = output_df[output_df['port_to'] == output_df['port_from']]
        df1 = df.groupby(['vessel_name'])['duration'].sum().reset_index()
        statistic_ship['Суммарное время ожидания'] = 0
        for v in statistic_ship['vessel_name'].unique():
            if v not in df1['vessel_name'].unique():
                continue
            statistic_ship.loc[statistic_ship['vessel_name'] == v, 'Суммарное время ожидания'] = \
                df1[df1['vessel_name'] == v]['duration'].iloc[0]

        statistic_ship = statistic_ship.drop_duplicates(subset='vessel_name')
        statistic_ship = statistic_ship.fillna(0)
        statistic_ship.rename(columns={'vessel_name':'название судна','vessel_id':'id судна'},inplace=True)
        return statistic_ship

    @staticmethod
    def get_summary_statistic(df: pd.DataFrame):
        """Метод вывода общей статистика результатов расчета"""
        summary_statistic_ship = {}
        summary_statistic_ice_breaker = {}

        # собираем статистику по кораблям
        ships_df = df[(df['is_icebreaker'] == False) & (df['port_from'] != df['port_to'])]

        # общее время движения по всем кораблям
        sum_time_ship = ships_df['duration'].sum()
        summary_statistic_ship['Общее время движения'] = sum_time_ship

        # суммарное время движения по всем кораблям под проводкой
        sum_time_ship_break = ships_df[ships_df['need_assistance'] == 1]['duration'].sum()
        summary_statistic_ship['Суммарное время движения под проводкой'] = sum_time_ship_break

        # Средняя скорость по всем кораблям
        mean_speed_ship = ships_df['speed'].mean()
        summary_statistic_ship['Средняя скорость'] = mean_speed_ship

        # Средняя интегральная тяжесть льда
        mean_integer_ice_ship = ships_df['integer_ice'].mean()
        summary_statistic_ship['Средняя интегральная тяжесть льда'] = mean_integer_ice_ship

        summary_statistic_ship['Время движения в интегральной тяжести 15-19'] = ships_df[(ships_df['integer_ice'].round() <= 19)&(ships_df['integer_ice'].round() >= 15)]['duration'].sum()
        summary_statistic_ship['Время движения в интегральной тяжести 10-14']= ships_df[(ships_df['integer_ice'].round() <= 14)&(ships_df['integer_ice'].round() >= 10)]['duration'].sum()
        summary_statistic_ship['Время движения в интегральной тяжести 20+']= ships_df[(ships_df['integer_ice'].round() >= 20)]['duration'].sum()

        # собираем статистику по ледоколам
        ice_breakers_df = df[(df['is_icebreaker'] == True) & (df['port_from'] != df['port_to'])]

        summary_statistic_ice_breaker['Суммарное время движения под проводкой'] = None

        # общее время движения по всем ледоколам
        sum_time_ice_breakers = ice_breakers_df['duration'].sum()
        summary_statistic_ice_breaker['Общее время движения'] = sum_time_ice_breakers

        # Средняя скорость по всем ледоколам
        mean_speed_ice_breaker = ice_breakers_df['speed'].mean()
        summary_statistic_ice_breaker['Средняя скорость'] = mean_speed_ice_breaker

        # Средняя интегральная тяжесть льда
        mean_integer_ice_breaker = ice_breakers_df['integer_ice'].mean()
        summary_statistic_ice_breaker['Средняя интегральная тяжесть льда'] = mean_integer_ice_breaker

        summary_statistic_ice_breaker['Время движения в интегральной тяжести 20+'] = ice_breakers_df[(ice_breakers_df['integer_ice'].round() >= 20)]['duration'].sum()
        summary_statistic_ice_breaker['Время движения в интегральной тяжести 15-19'] = ice_breakers_df[(ice_breakers_df['integer_ice'].round() <= 19)&(ice_breakers_df['integer_ice'].round() >= 15)]['duration'].sum()
        summary_statistic_ice_breaker['Время движения в интегральной тяжести 10-14'] = ice_breakers_df[(ice_breakers_df['integer_ice'].round() <= 14)&(ice_breakers_df['integer_ice'].round() >= 10)]['duration'].sum()

        # Статистика по ожиданиям
        ice_breakers_df_w = df[(df['is_icebreaker'] == True) & (df['port_from'] == df['port_to'])]
        ships_df_w = df[(df['is_icebreaker'] == False) & (df['port_from'] == df['port_to'])]
        w_ice_breakers = ice_breakers_df_w['duration'].sum()
        w_ships = ships_df_w['duration'].sum()
        summary_statistic_ice_breaker['Общее время простоя'] = w_ice_breakers
        summary_statistic_ship['Общее время простоя'] = w_ships

        return summary_statistic_ship, summary_statistic_ice_breaker

    @staticmethod
    def collect_kpi(output_path: str, df: pd.DataFrame):
        """Метод сбора статистик по результатам расчета"""
        summary_statistic_ship, summary_statistic_ice_breaker = ModelDash.get_summary_statistic(df)
        summary_df = pd.DataFrame(index=['Корабли', 'Ледоколы'], columns=summary_statistic_ice_breaker.keys())
        for col in summary_df.columns:
            summary_df.loc['Корабли', col] = summary_statistic_ship[col]
            summary_df.loc['Ледоколы', col] = summary_statistic_ice_breaker[col]
        partial_statistic_df = ModelDash.get_partial_statistic(df)
        summary_df.index.name = 'Тип судна'
        summary_df = summary_df.round(3)
        partial_statistic_df = partial_statistic_df.round(3)
        with pd.ExcelWriter(os.path.join(output_path, 'statistics.xlsx')) as writer:
            summary_df.to_excel(writer, sheet_name='Общая статистика')
            partial_statistic_df.to_excel(writer, sheet_name='Частная статистика', index=False)
