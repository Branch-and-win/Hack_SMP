from Departure import Departure
from Port import Port
from Vessel import Vessel


class Location:

    def __init__(self, vessel: Vessel, port: Port, time: int) -> None:
        self.vessel = vessel
        self.port = port
        self.time = time

        self.input_departures_by_location = []
        self.output_departures_by_location = []

    def __repr__(self) -> str:
        return 'L(' + ', '.join((self.vessel.name, self.port.name, str(self.time))) + ')'

    def add_input_departure(self, departure: Departure) -> None:
        self.input_departures_by_location.append(departure)

    def add_output_departure(self, departure: Departure) -> None:
        self.output_departures_by_location.append(departure)
