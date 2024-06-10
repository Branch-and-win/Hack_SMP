from src.entity.departure import Departure
from src.entity.port import Port
from src.entity.vessel import Vessel
from src.graph.base_graph import BaseGraph


class Location:

    def __init__(self, vessel: Vessel, port: Port, time: int, min_time_to_port_end: float) -> None:
        self.vessel = vessel
        self.port = port
        self.time = time
        self.min_time_to_end_port = min_time_to_port_end

        self.input_departures_by_location = []
        self.output_departures_by_location = []

    def __repr__(self) -> str:
        return 'L(' + ', '.join((self.vessel.name, self.port.name, str(self.time))) + ')'

    def add_input_departure(self, departure: Departure) -> None:
        self.input_departures_by_location.append(departure)

    def add_output_departure(self, departure: Departure) -> None:
        self.output_departures_by_location.append(departure)
