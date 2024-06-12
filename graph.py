import pandas as pd
from data_reader import (
    lon,
    lat,
    integer_vel,
    points_info
)
import geopy.distance
from collections import defaultdict
# минимально допустимая интегральная тяжесть
AV_INTEGRAL_ICE = 9.5
# погрешность для
EPS = 1

class Graph:

    def __init__(self, lon_arr, lat_arr, vel_arr, ports):

        self.lon_arr = lon_arr
        self.lat_arr = lat_arr
        self.vel_arr = vel_arr.to_numpy()
        self.ports = ports

        self.graph = defaultdict(lambda: {})
        self.nodes = []

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

        self.all_info_df = pd.DataFrame({'lon': lon_arr, 'lat': lat_arr, 'vel': vel_arr, "idx": idxs})

    def create_graph(self):

        for row in range(self.lon_arr.shape[0]):
            for col in range(self.lon_arr.shape[1]):
                print(row, col)
                df = pd.DataFrame()
                filt_neighbours = self.get_neighbors(1, row, col, self.vel_arr)

                if not filt_neighbours:
                    continue

                lon_v = self.lon_arr.iloc[row, col]
                lat_v = self.lat_arr.iloc[row, col]

                neigh_lat = []
                neigh_lon = []
                for (i,j) in filt_neighbours:

                    neigh_lat.append(self.lat_arr.iloc[i, j])
                    neigh_lon.append(self.lon_arr.iloc[i, j])

                df['coords'] = list(zip(neigh_lat, neigh_lon))
                df["distance"] = df["coords"].apply(lambda x: geopy.distance.geodesic(x, (lat_v, lon_v)).km)
                self.graph[f'{row}_{col}'] = dict(zip([f"{k[0]}_{k[1]}" for k in filt_neighbours], df["distance"]))

        for row in self.ports.itertuples():
            idx = row.point_name
            lat_v = row.latitude
            lon_v = row.longitude
            self.add_point_around_port(idx, lat_v, lon_v)

        self.nodes = list(self.graph.keys())

    def add_point_around_port(self, port, lat_p, lon_p):

        if lat_p < 0:
            lat_p += 359
        if lon_p < 0:
            lon_p += 359

        # находим квадрат порта
        df = self.all_info_df[(self.all_info_df['lat'] >= lat_p) & (self.all_info_df['lon'] <= lon_p)]
        df['coords'] = list(zip(df['lat'].values, df['lon'].values))
        df["distance"] = df["coords"].apply(lambda x: geopy.distance.geodesic(x, (lat_p, lon_p)).km)
        df = df.sort_values(by='distance')
        i, j = list(map(lambda x: int(x), df['idx'].iloc[0].split('_')))

        # ищем соседей
        initial_radius = 1
        neighbours = self.get_neighbors(initial_radius, i, j, self.vel_arr)
        while not neighbours:
            if initial_radius > 12:
                neighbours = []
                initial_radius=1
                break
            initial_radius += 1
            neighbours = self.get_neighbors(initial_radius, i, j, self.vel_arr)
        if initial_radius > 1:

            neigh_lat=[]
            neigh_lon=[]
            df1 = pd.DataFrame({'idx': neighbours})
            for (i, j) in neighbours:
                neigh_lat.append(self.lat_arr.iloc[i, j])
                neigh_lon.append(self.lon_arr.iloc[i, j])
            df1['coords'] = list(zip(neigh_lat, neigh_lon))
            df1["distance"] = df1["coords"].apply(lambda x: geopy.distance.geodesic(x, (lat_p, lon_p)).km)
            df1 = df1.sort_values(by='distance')

            idx = df1.iloc[0]['idx']
            dist = df1.iloc[0]['distance']
            self.graph[port].update({f'{idx[0]}_{idx[1]}': dist})
            self.graph[f'{idx[0]}_{idx[1]}'].update({port: dist})
        else:
            for (i, j) in neighbours:
                a = self.all_info_df[self.all_info_df['idx'] == f'{i}_{j}'][['lat','lon']].values[0]
                dist = geopy.distance.geodesic(a, (lat_p, lon_p)).km
                self.graph[port].update({f'{i}_{j}': dist})
                self.graph[f'{i}_{j}'].update({port: dist})

    @staticmethod
    def get_neighbors(radius, row_number, column_number, a):
        res = []
        for i in range(row_number - radius, row_number + radius + 1):
            if not (0 <= i < len(a)):
                continue
            for j in range(column_number - radius, column_number +1+radius):
                if not (0 <= j < len(a[0])) or (i == row_number and j == column_number) or a[i,j] <= AV_INTEGRAL_ICE:
                    continue

                res.append((i, j))
        return res

if __name__ == "__main__":
    graph = Graph(lon_arr=lon, lat_arr=lat, vel_arr=integer_vel, ports=points_info)
    graph.create_graph()
