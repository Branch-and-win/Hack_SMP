import os
from collections import defaultdict

import pandas as pd
import math
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

from src.smp_model.entity.edge_t_connection import EdgeTConnection
from src.smp_model.entity.port import Port
from src.smp_model.entity.vessel import Vessel
from src.smp_model.entity.edge import Edge
from src.smp_model.entity.speed_decrease import SpeedDecrease
from src.smp_model.entity.departure import Departure
from src.smp_model.entity.location import Location
from src.smp_model.graph.base_graph import BaseGraph
from src.smp_model.model_config import ModelConfig
from src.smp_model.utils import choose_week_for_calc

class ModelInput:
    def __init__(
            self,
            input_folder_path: str,
            output_folder_path: str,

            model_config: ModelConfig
    ):
        print('Подготовка входных данных модели')
        self.input_folder_path: str = input_folder_path
        self.output_folder_path: str = output_folder_path
        self.config: ModelConfig = model_config

        # self.hours_in_interval: int = hours_in_interval
        # self.hours_in_horizon: int = hours_in_horizon
        # self.start_date: datetime = start_date

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

        self.speed_decrease_dict: Dict[Tuple[str, int, bool], SpeedDecrease] = {}

        self.min_time_from_start: Dict[Tuple[Vessel, Port], float] = {}
        self.edges_for_main_graph: List[Edge] = []

        self.read_ports_xlsx()
        self.read_edges_xlsx()
        self.read_vessels_xlsx()
        self.read_icebreakers_xlsx()
        self.speed_decrease_xlsx()
        

        self.create_main_graph()
        self.calculate_min_time_from_start()
        self.fill_best_routes()

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

    def fill_best_routes(self):
        for v in self.vessels:
            if v.is_icebreaker:
                continue
            _, best_routes = self.main_graph.k_shortest_paths(
                v.port_start,
                v.port_end,
                k=5,
            )
            possible_edges = {
                self.edges_dict[port_start.id, port_end.id]
                for best_route in best_routes
                for port_start, port_end in zip(best_route[:-1], best_route[1:])
            }
            possible_ports = set()
            for best_route in best_routes:
                for port in best_route:
                    possible_ports.add(port)
            v.fill_possible_edges(possible_edges, possible_ports)

    def create_main_graph(self) -> None:
        vessel_type_w_max_speed = {v.type_max_speed: v.type_max_speed_str for v in self.vessels}
        graph_edges = []
        for e in self.edges_for_main_graph:
            graph_edges.append((
                e.port_from,
                e.port_to,
                {
                    v_key:
                    self.calculate_edge_time_by_vessel_class_speed(
                        e.distance,
                        e.avg_norm,
                        vessel_type,
                        max_speed
                    )
                    for (vessel_type, max_speed), v_key in vessel_type_w_max_speed.items()
                }
            ))
        self.main_graph.add_edges_from(graph_edges)

    def calculate_min_time_from_start(self):
        for p in self.ports:
            for v in self.vessels:
                self.min_time_from_start[v, p] = (
                    self.main_graph.k_shortest_paths(v.port_start, p, k=1, weight=v.type_max_speed_str)[0][0]
                )

    def generate_time(self) -> List[int]:
        return list(range(math.ceil(self.config.planning_hours / self.config.hours_in_interval)))
    
    def date_to_time(self, date: datetime) -> int:
        return math.ceil((date - self.config.start_date).days * 24 / self.config.hours_in_interval)

    def read_ports_xlsx(self) -> None:
        port_data = pd.read_excel(os.path.join(self.input_folder_path, 'model_data.xlsx'), sheet_name='points')
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
        vessel_data = pd.read_excel(os.path.join(self.input_folder_path, 'model_data.xlsx'), sheet_name='vessels')
        vessel_data = vessel_data[
            (vessel_data['date_start'] < self.config.end_date + timedelta(hours=self.config.hours_in_cross))
            & (vessel_data['date_start'] >= self.config.start_date)
        ]
        for row in vessel_data.itertuples():
            # _, best_routes = self.main_graph.k_shortest_paths(
            #     self.ports_dict[row.start_point_id],
            #     self.ports_dict[row.end_point_id],
            #     k=5,
            # )
            # possible_edges = set()
            # possible_edges = {
            #     self.edges_dict[port_start.id, port_end.id]
            #     for best_route in best_routes
            #     for port_start, port_end in zip(best_route[:-1], best_route[1:])
            # }
            # possible_ports = set()
            # for best_route in best_routes:
            #     for port in best_route:
            #         possible_ports.add(port)

            vessel = Vessel(
                id=row.vessel_id,
                name=row.vessel_name,
                is_icebreaker=False,
                port_start=self.ports_dict[row.start_point_id],
                port_end=self.ports_dict[row.end_point_id],
                time_start=self.date_to_time(row.date_start),
                max_speed=row.max_speed,
                class_type=row.class_type,
            )
            self.vessels.append(vessel)
            self.vessels_dict[vessel.id] = vessel
        return 
    
    def read_icebreakers_xlsx(self) -> None:
        icebreaker_data = pd.read_excel(os.path.join(self.input_folder_path, 'model_data.xlsx'), sheet_name='icebreakers')
        for row in icebreaker_data.itertuples():
            icebreaker = Vessel(
                id=row.vessel_id,
                name=row.vessel_name,
                is_icebreaker=True, 
                port_start=self.ports_dict[row.start_point_id],
                port_end=None,
                time_start=self.date_to_time(row.date_start),
                max_speed=row.max_speed,
                class_type=row.class_type
            )
            self.vessels.append(icebreaker)
            self.vessels_dict[icebreaker.id] = icebreaker
        return 
    
    def read_edges_xlsx(self) -> None:
        edge_data = pd.read_excel(os.path.join(self.input_folder_path, 'model_data.xlsx'), sheet_name='edges')
        acc_vel_dict, acc_len_dict = {}, {}
        if os.path.isfile(os.path.join(self.input_folder_path, 'velocity_env.xlsx')):
            velocity_book = pd.ExcelFile(os.path.join(self.input_folder_path, 'velocity_env.xlsx'))
            sheets = velocity_book.sheet_names
            date = choose_week_for_calc(self.config.start_date, sheets)
            print(f'Для сценария с датой начала {self.config.start_date} используются данные по интегральности за {date}')
            vel_edge_data = pd.read_excel(os.path.join(self.input_folder_path, 'velocity_env.xlsx'), sheet_name=f'{date}')
            acc_vel_dict = dict(
                zip(list(zip(vel_edge_data['start_point_id'], vel_edge_data['end_point_id'])), vel_edge_data['avg_norm'])
            )
            acc_len_dict = dict(
                zip(list(zip(vel_edge_data['start_point_id'], vel_edge_data['end_point_id'])),vel_edge_data['length'])
            )
        for row in edge_data.itertuples():
            edge_1 = Edge(
                port_from=self.ports_dict[row.start_point_id],
                port_to=self.ports_dict[row.end_point_id],
                distance=acc_len_dict.get((row.start_point_id, row.end_point_id), 0),
                avg_norm=acc_vel_dict.get((row.start_point_id, row.end_point_id), 0)
            )
            edge_2 = Edge(
                port_from=self.ports_dict[row.end_point_id],
                port_to=self.ports_dict[row.start_point_id],
                distance=acc_len_dict.get((row.start_point_id, row.end_point_id), 0),
                avg_norm=acc_vel_dict.get((row.start_point_id, row.end_point_id), 0)
            )
            self.edges.append(edge_1)
            self.edges.append(edge_2)
            self.edges_dict[edge_1.port_from.id, edge_1.port_to.id] = edge_1
            self.edges_dict[edge_2.port_from.id, edge_2.port_to.id] = edge_2
            self.edges_for_main_graph.append(edge_1)
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

    def speed_decrease_xlsx(self) -> None:
        speed_decrease_data = pd.read_excel(os.path.join(self.input_folder_path, 'model_data.xlsx'), sheet_name='speed_decrease')
        for row in speed_decrease_data.itertuples():
            for i in range(row.integer_velocity_from, row.integer_velocity_to + 1):
                speed_decrease = SpeedDecrease(  
                    class_type=row.class_type, 
                    integer_velocity= i, 
                    is_icebreaker_assistance=row.is_icebreaker_assistance,
                    is_possible=row.is_possible,
                    speed_decrease_pct=row.speed_decrease_pct,
                    base_speed=row.base_speed
                )
                self.speed_decrease_dict[speed_decrease.class_type, speed_decrease.integer_velocity, speed_decrease.is_icebreaker_assistance] = speed_decrease

    def calculate_edge_time_by_vessel_class_speed(
            self,
            length: float,
            integer_integral_ice: float,
            vessel_class: str,
            max_speed: float,
    ) -> float:
        integer_integral_ice = round(integer_integral_ice, 0)
        if integer_integral_ice < 10:
            return 99999
        possible_speed = 0.1
        for is_icebreaker_assistance in [True, False]:
            if (vessel_class, integer_integral_ice, is_icebreaker_assistance) in self.speed_decrease_dict.keys():
                speed_decrease = self.speed_decrease_dict[vessel_class, integer_integral_ice, is_icebreaker_assistance]
                if speed_decrease.is_possible:
                    if speed_decrease.base_speed == 'max_speed':
                        speed = max_speed * (1 - speed_decrease.speed_decrease_pct / 100)
                    else:
                        speed = min(integer_integral_ice * (1 - speed_decrease.speed_decrease_pct / 100), max_speed)   
                    if speed > possible_speed:
                        possible_speed = speed
        return length / possible_speed

        

    def calculate_ice_depending_values(self, vessel: Vessel, edge: Edge) -> List[Tuple[float, bool, bool]]:
        integer_integral_ice = round(edge.avg_norm, 0)
        if edge.is_fict:
            return [(0, False, True)]
        result = []
        for is_icebreaker_assistance in [True, False]:
            if (vessel.class_type, integer_integral_ice, is_icebreaker_assistance) in self.speed_decrease_dict.keys():
                speed_decrease = self.speed_decrease_dict[vessel.class_type, integer_integral_ice, is_icebreaker_assistance]
                if speed_decrease.base_speed == 'max_speed':
                    speed = vessel.max_speed * (1 - speed_decrease.speed_decrease_pct / 100)
                else:
                    speed = min(integer_integral_ice * (1 - speed_decrease.speed_decrease_pct / 100), vessel.max_speed)
                result.append((speed, is_icebreaker_assistance, speed_decrease.is_possible))
        return result
    
    # Требует умной фильтрации
    def generate_departures(self):
        for e in self.edges:
            for t in self.times:
                self.edge_t_connections[e, t] = EdgeTConnection(e, t)
                allowed_vessels = []
                for v in self.vessels:
                    if (
                         t < v.time_start
                        #t < v.time_start + self.min_time_from_start[v, e.port_from] - 1
                    ):
                        continue
                    for (speed, is_icebreaker_assistance, is_possible) in self.calculate_ice_depending_values(v, e):
                        if is_possible:
                            departure = Departure(
                                vessel=v,
                                edge=e,
                                time=t,
                                speed=speed,
                                is_icebreaker_assistance=is_icebreaker_assistance,
                                hours_in_interval=self.config.hours_in_interval
                            )
                            if (
                                t + departure.duration in self.times
                                and (
                                    v.is_icebreaker
                                    or e in v.possible_edges
                                    or (e.is_fict and e.port_from in v.possible_ports)
                                )
                            ):
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
                if v.port_end:
                    min_time_to_port_end = self.main_graph.k_shortest_paths(p, v.port_end, weight=v.type_max_speed_str)[0][0]
                else:
                    min_time_to_port_end = 0
                for t in self.times:
                    if (
                         t < v.time_start
                        #t < v.time_start + self.min_time_from_start[v, p] - 1
                    ):
                        continue
                    # TODO: Фильтр убивает
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
