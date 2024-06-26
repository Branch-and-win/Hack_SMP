from datetime import datetime
from math import pi, sin, acos, cos

import numpy as np
import pandas as pd
import geopy.distance
from collections import defaultdict
from src.smp_model.input import ModelInput
from typing import List, Tuple
import os
from src.smp_model.utils import choose_week_for_calc


class LengthVelocityCalc:
    # минимально допустимая интегральная тяжесть
    AV_INTEGRAL_ICE = 9.5
    # конвертер номера месяца в название
    converted_month_dict = {
        "01": 'Jan',
        "02": 'Feb',
        "03": 'Mar',
        "04": 'Apr',
        "05": 'May',
        "06": 'Jun',
        "07": 'Jul',
        "08": 'Aug',
        "09": 'Sep',
        "10": 'Oct',
        "11": "Nov",
        "12": 'Dec',
    }
    inversed_converted_month_dict = {v: k for k, v in converted_month_dict.items()}

    def __init__(
            self,
            # input: ModelInput,
            # filename: str = "IntegrVelocity.xlsx",
            data_folder_path: str,
            start_date: datetime,
    ):

        self.data_folder_path = data_folder_path
        self.start_date = start_date

        with pd.ExcelFile(os.path.join(data_folder_path, 'model_data.xlsx')) as reader:
            self.ports_df = pd.read_excel(reader, sheet_name='points')
            self.edges_df = pd.read_excel(reader, sheet_name='edges')
            self.icebreakers_df = pd.read_excel(reader, sheet_name='icebreakers')
            self.vessels_df = pd.read_excel(reader, sheet_name='vessels')
        self.ports_dict = self.ports_df\
            .set_index(['point_id'])\
            .to_dict(orient='index')

        self.input = input
        self.filename = 'IntegrVelocity.xlsx'
        self.lon_arr: pd.DataFrame = pd.read_excel(os.path.join(self.data_folder_path, self.filename), sheet_name='lon', header=None)
        self.lat_arr: pd.DataFrame = pd.read_excel(os.path.join(self.data_folder_path, self.filename), sheet_name='lat', header=None)
        self.date_vel_env, self.vel_arr = self.get_velocity_data(self.start_date)

        self.graph: dict = defaultdict(lambda: {})
        self.nodes: list = []

        self.points_info_df: pd.DataFrame = self.get_full_info_df()

    def get_full_info_df(self):
        """Метод конвертации информации об интегральной тяжести в один датафрейм"""
        lat_arr = []
        lon_arr = []
        vel_arr = []
        idxs = []

        for row in range(self.lon_arr.shape[0]):
            for col in range(self.lon_arr.shape[1]):
                lat_arr.append(self.lat_arr.iloc[row, col])
                lon_arr.append(self.lon_arr.iloc[row, col])
                vel_arr.append(self.vel_arr[row, col])

                idxs.append(f'{row}_{col}')

        return pd.DataFrame({'lon': lon_arr, 'lat': lat_arr, 'vel': vel_arr, "idx": idxs})

    def get_velocity_data(self, date: datetime) -> Tuple[str,np.array]:
        astr_date = date.strftime("%Y-%m-%d").split('-')
        astr_date[1] = self.converted_month_dict.get(astr_date[1], '03')

        velocity_book = pd.ExcelFile(os.path.join(self.data_folder_path, self.filename))
        sheets = velocity_book.sheet_names
        if '-'.join(astr_date) not in sheets:
            dates = [i.replace(i.split('-')[1], self.converted_month_dict.get(i.split('-')[1], '03')) for i in sheets if i not in ['lon','lat']]
            dates = [pd.to_datetime(i, format='%d-%m-%Y') for i in dates]
            sheet = choose_week_for_calc(date, dates)
            str_date = sheet.strftime("%d-%m-%Y").split('-')
            str_date[1] = self.converted_month_dict.get(str_date[1], 'Mar')
            return date.strftime("%Y-%m-%d"), pd.read_excel(
                os.path.join(self.data_folder_path, self.filename), sheet_name='-'.join(str_date), header=None).to_numpy()
        else:
            return '-'.join(astr_date), pd.read_excel(os.path.join(self.data_folder_path, self.filename), sheet_name='-'.join(astr_date), header=None).to_numpy()

    def create_graph(self):

        for row in range(self.lon_arr.shape[0]):
            for col in range(self.lon_arr.shape[1]):

                df = pd.DataFrame()
                filtered_neighbours = self.get_neighbors(1, row, col, self.vel_arr)

                if not filtered_neighbours:
                    continue

                lon_v = self.lon_arr.iloc[row, col]
                lat_v = self.lat_arr.iloc[row, col]

                neigh_lat = []
                neigh_lon = []
                for (i, j) in filtered_neighbours:
                    neigh_lat.append(self.lat_arr.iloc[i, j])
                    neigh_lon.append(self.lon_arr.iloc[i, j])

                df['coords'] = list(zip(neigh_lat, neigh_lon))
                df["distance"] = df["coords"].apply(lambda x: self.spherical_distance(x, (lat_v, lon_v)))
                # df["distance"] = df["coords"].apply(lambda x: geopy.distance.geodesic(x, (lat_v, lon_v)).km)
                self.graph[f'{row}_{col}'] = dict(zip([f"{k[0]}_{k[1]}" for k in filtered_neighbours], df["distance"]))

        for port in self.ports_df.itertuples():
            idx = port.point_id
            lat_v = port.latitude
            lon_v = port.longitude
            self.add_point_around_port(idx, lat_v, lon_v)

        self.nodes = list(self.graph.keys())

    @staticmethod
    def spherical_distance(a1, a2):
        x1 = pi / 180 * float(a1[1])
        y1 = pi / 180 * float(a1[0])
        x2 = pi / 180 * float(a2[1])
        y2 = pi / 180 * float(a2[0])
        a = 20000 / pi  ### length of one radian of arc on earth
        phi = sin(y1) * sin(y2) + cos(y1) * cos(y2) * cos(x1 - x2)
        d = acos(phi) * a
        return d

    def add_point_around_port(self, port, lat_p, lon_p):
        """Поиск соседей для портов"""

        if lat_p < 0:
            lat_p += 359
        if lon_p < 0:
            lon_p += 359

        # находим квадрат порта по левому верхнему углу
        df = self.points_info_df[(self.points_info_df['lat'] >= lat_p) & (self.points_info_df['lon'] <= lon_p)]
        df['coords'] = list(zip(df['lat'].values, df['lon'].values))
        df["distance"] = df["coords"].apply(lambda x: geopy.distance.geodesic(x, (lat_p, lon_p)).km)
        df = df.sort_values(by='distance')
        i, j = list(map(lambda x: int(x), df['idx'].iloc[0].split('_')))

        # ищем соседей
        initial_radius = 1
        neighbours = self.get_neighbors(initial_radius, i, j, self.vel_arr)
        while not neighbours:
            # TODO: граничное значение для увеличения радиуса,
            if initial_radius > 12:
                neighbours = []
                initial_radius = 1
                break
            initial_radius += 1
            neighbours = self.get_neighbors(initial_radius, i, j, self.vel_arr)

        if initial_radius > 1:
            # если точка в зоне непроходимости, то ищем одного ближайшего соседа
            neigh_lat = []
            neigh_lon = []

            fictive_neighbours = pd.DataFrame({'idx': neighbours})
            for (i, j) in neighbours:
                neigh_lat.append(self.lat_arr.iloc[i, j])
                neigh_lon.append(self.lon_arr.iloc[i, j])

            fictive_neighbours['coords'] = list(zip(neigh_lat, neigh_lon))
            fictive_neighbours["distance"] = fictive_neighbours["coords"].apply(
                lambda x: geopy.distance.geodesic(x, (lat_p, lon_p)).km
            )
            fictive_neighbours = fictive_neighbours.sort_values(by='distance')

            idx = fictive_neighbours.iloc[0]['idx']
            dist = fictive_neighbours.iloc[0]['distance']

            self.graph[port].update({f'{idx[0]}_{idx[1]}': dist})
            self.graph[f'{idx[0]}_{idx[1]}'].update({port: dist})

        else:
            for (i, j) in neighbours:
                coord_neighbours_of_port = self.points_info_df[self.points_info_df['idx'] == f'{i}_{j}'][['lat', 'lon']].values[0]
                dist = geopy.distance.geodesic(coord_neighbours_of_port, (lat_p, lon_p)).km

                self.graph[port].update({f'{i}_{j}': dist})
                self.graph[f'{i}_{j}'].update({port: dist})

    @staticmethod
    def get_neighbors(radius: int, row_number: int, column_number: int, matrix):
        """Метод поиска соседей точки"""
        result = []
        for i in range(row_number - radius, row_number + radius + 1):
            if not (0 <= i < len(matrix)):
                continue
            for j in range(column_number - radius, column_number + radius + 1):

                if (
                        not (0 <= j < len(matrix[0]))
                        or (i == row_number and j == column_number)
                        or matrix[i, j] <= LengthVelocityCalc.AV_INTEGRAL_ICE
                ):
                    continue

                result.append((i, j))
        return result

    @staticmethod
    def dijkstra_algorithm(start_node, end_node, nodes, graph) -> Tuple[List[str], float]:
        """Реализация алгоритма Дейкстры для поиска наикратчайшего пути"""
        convert_to_mni = {"km": 0.539957}
        unmarked_nodes = nodes.copy()
        shortest_path = {node: np.inf for node in unmarked_nodes}
        shortest_path[start_node] = 0

        previous_nodes = {}

        while unmarked_nodes:
            current_marked_node = min(unmarked_nodes, key=lambda node: shortest_path.get(node, float('inf')))
            neighbor_nodes = graph[current_marked_node].keys()
            for neighbor in neighbor_nodes:
                value_on_hold = shortest_path[current_marked_node] + graph[current_marked_node][neighbor]
                if value_on_hold < shortest_path.get(neighbor, float('inf')):
                    shortest_path[neighbor] = value_on_hold
                    previous_nodes[neighbor] = current_marked_node

            unmarked_nodes.remove(current_marked_node)
        path = []
        node = end_node
        while node != start_node:
            path.append(node)
            node = previous_nodes[node]
        path.append(start_node)
        path = list(reversed(path))
        return path, shortest_path[end_node] * convert_to_mni['km']


def dump_velocity_length(
        # input: ModelInput,
        # filename: str = 'IntegrVelocity.xlsx'
        data_folder_path: str,
) -> pd.DataFrame:
    """Обновление информации о ледовых условиях"""

    if not os.path.isfile(os.path.join(data_folder_path, 'IntegrVelocity.xlsx')):
        return pd.DataFrame
    if not os.path.isfile(os.path.join(data_folder_path, 'model_data.xlsx')):
        return pd.DataFrame

    velocity_book = pd.ExcelFile(os.path.join(data_folder_path, 'IntegrVelocity.xlsx'))
    sheets = velocity_book.sheet_names
    data = {
        'start_point_id': [],
        'end_point_id': [],
        'avg_norm': [],
        'length': [],
        'date': [],

    }
    for sheet in sheets:
        v_l = sheet.split('-')
        if len(v_l) <= 1:
            continue
        v_l[1] = LengthVelocityCalc.inversed_converted_month_dict.get(v_l[1], v_l[1])
        date = pd.to_datetime('-'.join(v_l), format='%d-%m-%Y')
        print(f'Расчет интегральной тяжести на {date}')
        start_date = date
        graph_creator = LengthVelocityCalc(data_folder_path, start_date)
        graph_creator.create_graph()
        graph, nodes = graph_creator.graph, graph_creator.nodes
        temp_set = set()
        for edge in graph_creator.edges_df.itertuples():
            if (edge.start_point_id, edge.end_point_id) in temp_set:
                continue
            if edge.start_point_id == edge.end_point_id:
                continue
            data['start_point_id'].append(edge.start_point_id)
            data['end_point_id'].append(edge.end_point_id)
            data['date'].append(date)
            temp_set.add((edge.start_point_id, edge.end_point_id))
            try:
                print(edge.start_point_id,'->', edge.end_point_id)
                route, dist = LengthVelocityCalc.dijkstra_algorithm(edge.start_point_id, edge.end_point_id, nodes, graph)
                print(dist)
                num_points = len(route)
                velocity_values = []
                for index, point in enumerate(route):

                    if index in (0, num_points - 1):
                        continue

                    if len(point.split('_')) == 1:
                        continue

                    i, j = int(point.split('_')[0]), int(point.split('_')[1])
                    velocity_values.append(graph_creator.vel_arr[i, j])

                velocity = np.mean(velocity_values)

                data['avg_norm'].append(velocity)
                data['length'].append(dist)

            except Exception as e:
                print(e)
                data['avg_norm'].append(0)
                data['length'].append(1000)
                continue

    data = pd.DataFrame(data)
    # path = os.path.join(input.input_folder_path, 'velocity_env.xlsx')
    # with pd.ExcelWriter(path) as writer:
    #     data.to_excel(writer, index=False)
    return data

if __name__ == '__main__':
    tmp_dir_path = os.path.join('.', 'data', 'tmp', 'test')
    test_df = dump_velocity_length(tmp_dir_path)