from typing import List, Set

from src.smp_model.entity.edge import Edge
from src.smp_model.entity.port import Port


class Vessel:
    def __init__(
            self,
            id,
            name,
            is_icebreaker,
            port_start,
            port_end,
            time_start,
            max_speed,
            class_type,
    ) -> None:
        self.id = id
        self.name = name
        self.is_icebreaker = is_icebreaker
        self.port_start = port_start
        self.port_end = port_end
        self.time_start = time_start
        self.max_speed = max_speed
        self.class_type = class_type
        # Допустимые ребра для передвижения судна
        self.possible_edges: List[Edge] = []
        self.possible_ports: Set[Port] = set()
        self.locations_by_vessel = []

    def add_location(self, location):
        self.locations_by_vessel.append(location)
        return

    def __str__(self):
        return f"V({self.id}, {self.name})"

    def __repr__(self):
        return f"V({self.id}, {self.name})"

    @property
    def type_max_speed(self):
        return self.class_type, self.max_speed

    @property
    def type_max_speed_str(self):
        return f'{self.class_type}_s{self.max_speed}'

    def fill_possible_edges(self, possible_edges, possible_ports):
        self.possible_edges = possible_edges
        self.possible_ports = possible_ports

