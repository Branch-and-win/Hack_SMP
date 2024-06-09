class Departure:

    def __init__(self, vessel, edge, time) -> None:
        self.vessel = vessel
        self.edge = edge
        self.time = time
        self.duration = (1 if self.edge.port_from.id == self.edge.port_to.id else round(edge.distance / 15, 0))
        self.is_icebreaker_assistance = False if (vessel.is_icebreaker or self.edge.port_to.id != 41) else True
        self.possible_icebreaker_departures = []

    def __repr__(self) -> str:
        return '(' + ', '.join((self.vessel.name, self.edge.port_from.name, self.edge.port_to.name, str(self.time))) + ')'
    
    def add_possible_icebreaker(self, departure):
        self.possible_icebreaker_departures.append(departure)
        return