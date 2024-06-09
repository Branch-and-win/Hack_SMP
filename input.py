import os

import pandas as pd
import math
from typing import Dict, List, Tuple
from datetime import datetime

from EdgeTConnection import EdgeTConnection
from Port import Port
from Vessel import Vessel
from Edge import Edge
from Departure import Departure
from Location import Location


class ModelInput:
    def __init__(self, input_folder: str):
        self.hours_in_interval: int = 1
        self.hours_in_horizon: int = 300
        self.start_date: datetime = datetime(2022, 2, 27)
        self.input_folder: str = input_folder

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
        self.read_vessels_xlsx()
        self.read_icebreakers_xlsx()
        self.read_edges_xlsx()
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
        for _, row in vessel_data.iterrows():
            vessel = Vessel(
                id=row['vessel_id'],
                name=row['vessel_name'],
                is_icebreaker=False,
                port_start=self.ports_dict[row['start_point_id']],
                port_end=self.ports_dict[row['end_point_id']],
                time_start=self.date_to_time(row['date_start']),
                max_speed=row['max_speed'],
                class_type=row['class_type']
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
        for _, row in edge_data.iterrows():
            edge_1 = Edge(
                port_from=self.ports_dict[row['start_point_id']], 
                port_to=self.ports_dict[row['end_point_id']], 
                distance=row['length']
            )
            edge_2 = Edge(
                port_from=self.ports_dict[row['end_point_id']], 
                port_to=self.ports_dict[row['start_point_id']], 
                distance=row['length']
            )
            self.edges.append(edge_1)
            self.edges.append(edge_2)
            self.edges_dict[edge_1.port_from.id, edge_1.port_to.id] = edge_1
            self.edges_dict[edge_2.port_from.id, edge_2.port_to.id] = edge_2
        for p in self.ports:
            edge = Edge(
                port_from=p, 
                port_to=p, 
                distance=0
            )
            self.edges.append(edge)
            self.edges_dict[edge.port_from.id, edge.port_to.id] = edge
        return 
    
    # Требует умной фильтрации
    def generate_departures(self):
        for e in self.edges:
            for t in self.times:
                self.edge_t_connections[e, t] = EdgeTConnection(e, t)
                allowed_vessels = []
                for v in self.vessels:
                    # Заплатка, пока нет норм расчета duration
                    if t + (1 if e.port_from.id == e.port_to.id else round(e.distance / 15, 0)) in self.times:
                        departure = Departure(
                            vessel=v,
                            edge=e,
                            time=t
                        )
                        self.departures.append(departure)
                        self.departures_dict[v, e, t] = departure
                        allowed_vessels.append(v)
                self.edge_t_connections[e, t].set_allowed_vessels(allowed_vessels)
        return 
    
    # Требует умной фильтрации
    def generate_locations(self):
        for v in self.vessels:
            for p in self.ports:
                for t in self.times:
                    location = Location(
                        vessel=v, 
                        port=p, 
                        time=t
                    )
                    self.locations.append(location)  
                    self.locations_dict[v, p, t] = location
        return

    def generate_links(self):
        for d in self.departures:
            if d.time + d.duration in self.times:
                self.locations_dict[d.vessel, d.edge.port_to, d.time + d.duration].add_input_departure(d)
                self.locations_dict[d.vessel, d.edge.port_from, d.time].add_output_departure(d)
            for icebreaker in [v for v in self.vessels if v.is_icebreaker and v.id != d.vessel.id]:
                if (icebreaker, d.edge, d.time) in self.departures_dict.keys():
                    d.add_possible_icebreaker(self.departures_dict[icebreaker, d.edge, d.time])

        for l in self.locations:
            self.vessels_dict[l.vessel.id].add_location(l)

        return
