import os

import networkx as nx
import pandas as pd
import math
from typing import Dict, List, Tuple
from datetime import datetime

from src.entity.edge_t_connection import EdgeTConnection
from src.entity.port import Port
from src.entity.vessel import Vessel
from src.entity.edge import Edge
from src.entity.departure import Departure
from src.entity.location import Location
from src.graph.base_graph import BaseGraph


class ModelInput:
    def __init__(self, input_folder: str):
        self.hours_in_interval: int = 1
        self.hours_in_horizon: int = 300
        self.start_date: datetime = datetime(2022, 2, 27)
        self.input_folder: str = input_folder

        self.main_graph = BaseGraph()

        self.times: List[int] = self.generate_time()

        self.ports: List[Port] = []
        self.ports_dict: Dict[int, Port] = {}

        self.vessels: List[Vessel] = []
        self.vessels_dict: Dict[int, Vessel] = {}

        self.edges: List[Edge] = []
        self.edges_dict: Dict[Tuple[int, int], Edge] = {}

        self.departures: List[Departure] = []
        self.departures_dict = {}
        self.edge_t_connections: Dict[Tuple[Edge, int], EdgeTConnection] = {}

        self.locations: List[Location] = []
        self.locations_dict = {}

        self.read_ports_xlsx()
        self.read_edges_xlsx()
        self.read_vessels_xlsx()
        self.read_icebreakers_xlsx()
        self.generate_departures()
        self.generate_locations()
        self.generate_links()
        
        # Заплатка, ждем Дейкстру
        for p_from in self.ports:
            for p_to in self.ports:
                if (p_from.id, p_to.id) in self.edges_dict.keys():
                    p_from.add_min_dist(p_to, round(self.edges_dict[p_from.id, p_to.id].distance / 15, 0) * 2)
                else:
                    p_from.add_min_dist(p_to, 300)
    
    def generate_time(self) -> List[int]:
        return list(range(math.ceil(self.hours_in_horizon / self.hours_in_interval)))
    
    def date_to_time(self, date: datetime) -> int:
        return math.ceil((date - self.start_date).days * 24 / self.hours_in_interval)

    def read_ports_xlsx(self) -> None:
        port_data = pd.read_excel(os.path.join(self.input_folder, 'model_data.xlsx'), sheet_name='points')
        for _, row in port_data.iterrows():
            port = Port(
                id=row['point_id'],
                name=row['point_name'],
                longitude=row['longitude'],
                latitude=row['latitude']
            )
            self.ports.append(port)
            self.ports_dict[port.id] = port
        return 
    
    def read_vessels_xlsx(self) -> None:
        vessel_data = pd.read_excel(os.path.join(self.input_folder, 'model_data.xlsx'), sheet_name='vessels')
        vessel_data['date_start'] = pd.to_datetime(vessel_data['date_start'])
        for row in vessel_data.itertuples():
            _, best_routes = self.main_graph.k_shortest_paths(
                self.ports_dict[row.start_point_id],
                self.ports_dict[row.end_point_id],
                k=20,
            )
            possible_edges = {
                self.edges_dict[port_start.id, port_end.id]
                for best_route in best_routes
                for port_start, port_end in zip(best_route[:-1], best_route[1:])
            }
            vessel = Vessel(
                id=row.vessel_id,
                name=row.vessel_name,
                is_icebreaker=False,
                port_start=self.ports_dict[row.start_point_id],
                port_end=self.ports_dict[row.end_point_id],
                time_start=self.date_to_time(row.date_start),
                max_speed=row.max_speed,
                class_type=row.class_type,
                possible_edges=possible_edges,
            )
            self.vessels.append(vessel)
            self.vessels_dict[vessel.id] = vessel
        return 
    
    def read_icebreakers_xlsx(self) -> None:
        icebreaker_data = pd.read_excel(os.path.join(self.input_folder, 'model_data.xlsx'), sheet_name='icebreakers')
        for _, row in icebreaker_data.iterrows():
            icebreaker = Vessel(
                id=row['vessel_id'], 
                name=row['vessel_name'], 
                is_icebreaker=True, 
                port_start=self.ports_dict[row['start_point_id']], 
                port_end=None,
                time_start=0, 
                max_speed=row['max_speed'], 
                class_type=row['class_type']
            )
            self.vessels.append(icebreaker)
            self.vessels_dict[icebreaker.id] = icebreaker
        return 
    
    def read_edges_xlsx(self) -> None:
        edge_data = pd.read_excel(os.path.join(self.input_folder, 'model_data.xlsx'), sheet_name='edges')
        for row in edge_data.itertuples():
            edge_1 = Edge(
                port_from=self.ports_dict[row.start_point_id],
                port_to=self.ports_dict[row.end_point_id],
                distance=row.length,
                avg_norm=row.avg_norm
            )
            edge_2 = Edge(
                port_from=self.ports_dict[row.end_point_id],
                port_to=self.ports_dict[row.start_point_id],
                distance=row.length,
                avg_norm=row.avg_norm
            )
            self.edges.append(edge_1)
            self.edges.append(edge_2)
            self.edges_dict[edge_1.port_from.id, edge_1.port_to.id] = edge_1
            self.edges_dict[edge_2.port_from.id, edge_2.port_to.id] = edge_2
            self.main_graph.add_edge(self.ports_dict[row.start_point_id], self.ports_dict[row.end_point_id], length=row.length, weight=0)
        for p in self.ports:
            edge = Edge(
                port_from=p, 
                port_to=p, 
                distance=0,
                avg_norm=21
            )
            self.edges.append(edge)
            self.edges_dict[edge.port_from.id, edge.port_to.id] = edge
        return 
    
    def calculate_ice_depending_values(vessel: Vessel, edge: Edge) -> List[Tuple[float, bool, bool]]:
        integer_integral_ice = round(edge.avg_norm, 0)
        if edge.is_fict:
            return [(0, False, True)]
        if integer_integral_ice < 10:
            return [(1000, False, False)]
        if integer_integral_ice >= 20:
            return [(vessel.max_speed, False, True)]
        if vessel.name in ['50 лет Победы', 'Ямал']:
            return [(integer_integral_ice, False, True)]
        if vessel.name in ['Вайгач', 'Таймыр']:
            if integer_integral_ice >= 15:
                return [(integer_integral_ice * 0.9, False, True)]
            if integer_integral_ice >= 10:
                return [(integer_integral_ice * 0.75, False, True)]
        if vessel.class_type in ['Arc 4', 'Arc 5', 'Arc 6']:
            if integer_integral_ice >= 15:
                return [(vessel.max_speed * 0.8, True, True)]
            if integer_integral_ice >= 10:
                return [(vessel.max_speed * 0.7, True, True)]
        if vessel.class_type == 'Arc 7':
            if integer_integral_ice >= 15:
                return [(integer_integral_ice, True, True), (vessel.max_speed * 0.6, False, True)]
            if integer_integral_ice >= 10:
                return [(integer_integral_ice * 0.8, True, True), (vessel.max_speed * 0.15, False, True)]  
    
    # Требует умной фильтрации
    def generate_departures(self):
        for e in self.edges:
            for t in self.times:
                self.edge_t_connections[e, t] = EdgeTConnection(e, t)
                allowed_vessels = []
                for v in self.vessels:
                    for (speed, is_icebreaker_assistance, is_possible) in ModelInput.calculate_ice_depending_values(v, e):
                        if is_possible:
                            departure = Departure(
                                vessel=v,
                                edge=e,
                                time=t,
                                speed=speed,
                                is_icebreaker_assistance=is_icebreaker_assistance
                            )
                            if (t + departure.duration in self.times
                            and (v.is_icebreaker or e in v.possible_edges)):
                                self.departures.append(departure)
                                self.departures_dict[v, e, t, is_icebreaker_assistance] = departure
                                allowed_vessels.append(v)
                allowed_vessels = list(set(allowed_vessels))
                self.edge_t_connections[e, t].set_allowed_vessels(allowed_vessels)
        return 
    
    # Требует умной фильтрации
    def generate_locations(self):
        for v in self.vessels:
            for p in self.ports:
                min_time_to_current_port = self.main_graph.k_shortest_paths(v.port_start, p)[0][0] / v.max_speed
                if v.port_end:
                    min_time_to_port_end = self.main_graph.k_shortest_paths(p, v.port_end)[0][0] / v.max_speed
                else:
                    min_time_to_port_end = 0
                for t in self.times:
                    # TODO: Фильтр убивает
                    if True or v.time_start + min_time_to_current_port <= t:
                        location = Location(
                            vessel=v, 
                            port=p, 
                            time=t,
                            min_time_to_port_end=min_time_to_port_end,
                        )
                        self.locations.append(location)  
                        self.locations_dict[v, p, t] = location
        return

    def generate_links(self):
        for d in self.departures:
            if (
                d.time + d.duration in self.times
                and (d.vessel, d.edge.port_from, d.time) in self.locations_dict
                and (d.vessel, d.edge.port_to, d.time + d.duration) in self.locations_dict
            ):
                self.locations_dict[d.vessel, d.edge.port_to, d.time + d.duration].add_input_departure(d)
                self.locations_dict[d.vessel, d.edge.port_from, d.time].add_output_departure(d)
            for icebreaker in [v for v in self.vessels if v.is_icebreaker and v.id != d.vessel.id]:
                if (icebreaker, d.edge, d.time) in self.departures_dict.keys():
                    d.add_possible_icebreaker(self.departures_dict[icebreaker, d.edge, d.time])

        for l in self.locations:
            self.vessels_dict[l.vessel.id].add_location(l)

        return
