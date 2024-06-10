from heapq import heappush, heappop
from itertools import count
from typing import Hashable

import networkx as nx


class BaseGraph(nx.Graph):

    def k_shortest_paths(
        self,
        source: Hashable,
        target: Hashable,
        k: int = 1,
        weight='length'
    ):
        """
        Поиск первых k кратчайших путей из source в target во взвешенном графе

        :param source: node
           Начальная вершина

        :param target: node
           Конечная вершина

        :param k: integer, optional (default=1)
            Количество кратчайших путей из source в target

        :param weight: string, optional (default='weight')
           Ключ ребра для оценки веса

        Returns:
            lengths: list, paths: list - Список весов и последовательностей вершин k кратчайших путей
        """
        
        if source == target:
            return [0], [[source]]

        length, path = nx.single_source_dijkstra(self, source, None, weight=weight)
        if target not in length:
            raise nx.NetworkXNoPath(f"Невозможно построить путь из {source} в {target}")

        lengths = [length[target]]
        paths = [path[target]]
        c = count()
        graph_heap = []
        graph_copy = self.copy()

        i = 0
        while True:
            if i == k - 1:
                break
            for j in range(len(paths[-1]) - 1):
                spur_node = paths[-1][j]
                root_path = paths[-1][:j + 1]

                edges_removed = []
                for c_path in paths:
                    if len(c_path) > j and root_path == c_path[:j + 1]:
                        u = c_path[j]
                        v = c_path[j + 1]
                        if graph_copy.has_edge(u, v):
                            edge_attr = graph_copy.adj[u][v]
                            graph_copy.remove_edge(u, v)
                            edges_removed.append((u, v, edge_attr))

                for n in range(len(root_path) - 1):
                    node = root_path[n]
                    # out-edges
                    edge_list = list(graph_copy.edges(node, data=True))
                    for u, v, edge_attr in edge_list:
                        graph_copy.remove_edge(u, v)
                        edges_removed.append((u, v, edge_attr))

                spur_path_length, spur_path = nx.single_source_dijkstra(graph_copy, spur_node, None, weight=weight)
                if target in spur_path and spur_path[target]:
                    total_path = root_path[:-1] + spur_path[target]
                    total_path_length = self.get_path_length(root_path, weight) + spur_path_length[target]
                    heappush(graph_heap, (total_path_length, next(c), total_path))

                for e in edges_removed:
                    u, v, edge_attr = e
                    graph_copy.add_edge(u, v, length=edge_attr['length'], weight=edge_attr['weight'])

            if graph_heap:
                (l, _, p) = heappop(graph_heap)
                if p not in paths:
                    lengths.append(l)
                    paths.append(p)
                    i += 1
            else:
                break

        return lengths, paths

    def get_path_length(self, path, weight='weight'):
        length = 0
        if len(path) > 1:
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i + 1]

                length += self.adj[u][v].get(weight, 1)

        return length
