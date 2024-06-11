from src.entity.edge import Edge
from src.entity.vessel import Vessel


class Departure:

    def __init__(self, vessel: Vessel, edge: Edge, time: int) -> None:
        self.vessel = vessel
        self.edge = edge
        self.time = time
        self.speed, self.is_icebreaker_assistance, self.is_possible = self.calculate_ice_depending_values()
        self.duration = (1 if self.edge.is_fict else round(edge.distance / self.speed, 0))
        self.possible_icebreaker_departures = []

    def __repr__(self) -> str:
        return f"D({self.vessel, self.edge, self.time})"
    
    def add_possible_icebreaker(self, departure):
        self.possible_icebreaker_departures.append(departure)
        return

    def calculate_ice_depending_values(self):
        integer_integral_ice = round(self.edge.avg_norm, 0)
        if self.edge.is_fict:
            return (0, False, True)
        if self.vessel.name in ['50 лет Победы', 'Ямал']:
            if integer_integral_ice >= 20:
                return (self.vessel.max_speed, False, True)
            if integer_integral_ice >= 10:
                return (integer_integral_ice, False, True)
            return (1000, False, False)
        if self.vessel.name in ['Вайгач', 'Таймыр']:
            if integer_integral_ice >= 20:
                return (self.vessel.max_speed, False, True)
            if integer_integral_ice >= 15:
                return (integer_integral_ice * 0.9, False, True)
            if integer_integral_ice >= 10:
                return (integer_integral_ice * 0.75, False, True)
            return (1000, False, False)
        if self.vessel.class_type in ['Arc 4', 'Arc 5', 'Arc 6']:
            if integer_integral_ice >= 20:
                return (self.vessel.max_speed, False, True)  
            if integer_integral_ice >= 15:
                return (self.vessel.max_speed * 0.8, True, True)
            if integer_integral_ice >= 10:
                return (self.vessel.max_speed * 0.7, True, True)
            return (1000, False, False)
        if self.vessel.class_type == 'Arc 7':
            if integer_integral_ice >= 20:
                return (self.vessel.max_speed, False, True)  
            if integer_integral_ice >= 15:
                return (integer_integral_ice, False, True)
            if integer_integral_ice >= 10:
                return (integer_integral_ice * 0.8, True, True)
            return (1000, False, False)
                
        
