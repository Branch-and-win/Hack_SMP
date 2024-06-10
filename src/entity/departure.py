from src.entity.edge import Edge
from src.entity.vessel import Vessel


class Departure:

    def __init__(self, vessel: Vessel, edge: Edge, time: int) -> None:
        self.vessel = vessel
        self.edge = edge
        self.time = time
        self.duration = (1 if self.edge.port_from.id == self.edge.port_to.id else round(edge.distance / 15, 0))
        # Признак: необходим ли ледокол для перемещения
        if (
                vessel.is_icebreaker
                or self.edge.is_fict
                or self.edge.avg_norm >= 19.5
                or (self.edge.avg_norm >= 14.5 and vessel.class_type == 'Arc 7')
        ):
            self.is_icebreaker_assistance = False
        else:
            self.is_icebreaker_assistance = True
        self.possible_icebreaker_departures = []

    def __repr__(self) -> str:
        return f"D({self.vessel, self.edge, self.time})"
    
    def add_possible_icebreaker(self, departure):
        self.possible_icebreaker_departures.append(departure)
        return
