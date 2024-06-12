import numpy as np
import pandas as pd

from graph import Graph
from data_reader import (
    lon,
    lat,
    integer_vel,
    points_info,
    edges_info
)


def dijkstra_algorithm(start_node, end_node, nodes, graph):
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
    return path, shortest_path[end_node]*0.539957


if __name__ == '__main__':

    data = {'start_point': [], 'end_point': [], 'velocity': [], 'duration, nmi': []}
    graph_creator = Graph(
        lon_arr=lon,
        lat_arr=lat,
        vel_arr=integer_vel,
        ports=points_info,
    )
    graph_creator.create_graph()
    graph, nodes = graph_creator.graph, graph_creator.nodes
    for row in edges_info.itertuples():
        print(row.start_point_name, "->", row.end_point_name)
        data['start_point'].append(row.start_point_name)
        data['end_point'].append(row.end_point_name)
        try:
            path, dist = dijkstra_algorithm(row.start_point_name,  row.end_point_name, nodes, graph)
            velocity_arr = []
            for index, point in enumerate(path):
                if index == 0 or index == len(path)-1:
                    continue
                if len(point.split('_')) == 1:
                    continue
                i, j = int(point.split('_')[0]), int(point.split('_')[1])

                velocity_arr.append(integer_vel.iloc[i, j])

            vel = np.mean(velocity_arr)


            data['velocity'].append(vel)
            data['duration, nmi'].append(dist)
            if row.length > dist:
                print(f'Разница в длине: {row.length-dist}')
            print(f'Интегральная тяжесть:{vel}')
            print(f'Мин дистанция:{dist}')

        except KeyError:
            data['velocity'].append('Не удалось найти путь')
            data['duration, nmi'].append('Не удалось найти путь')

            print('Не удалось найти путь')
            continue

    data = pd.DataFrame(data)
    data.to_excel('Edges.xlsx')