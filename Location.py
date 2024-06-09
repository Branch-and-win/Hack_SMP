from collections import defaultdict

class Location:

    def __init__(self, vessel, port, time) -> None:
        self.vessel = vessel
        self.port = port
        self.time = time

        self.input_departures_by_location = []
        self.output_departures_by_location = []

    def __repr__(self) -> str:
        return '(' + ', '.join((self.vessel.name, self.port.name, str(self.time))) + ')'

    def add_input_departure(self, deprature):
        self.input_departures_by_location.append(deprature)

    def add_output_departure(self, deprature):
        self.output_departures_by_location.append(deprature)