from src.smp_model.entity.edge import Edge
from src.smp_model.entity.vessel import Vessel


class Departure:

    def __init__(self, vessel: Vessel, edge: Edge, time: int, speed: float, is_icebreaker_assistance: bool, hours_in_interval: int) -> None:
        self.vessel = vessel
        self.edge = edge
        self.time = time
        self.speed = speed
        self.is_icebreaker_assistance = is_icebreaker_assistance
        self.duration = (1 if self.edge.is_fict else round(edge.distance / (self.speed * hours_in_interval), 0))
        self.possible_icebreaker_departures = []

    def __repr__(self) -> str:
        return f"D({self.vessel, self.edge, self.time, self.is_icebreaker_assistance})"
    
    def add_possible_icebreaker(self, departure):
        self.possible_icebreaker_departures.append(departure)
        return


