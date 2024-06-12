from typing import List

from src.smp_model.entity.edge import Edge
from src.smp_model.entity.vessel import Vessel


class EdgeTConnection:
    def __init__(self, edge: Edge, t: int):
        self.edge = edge
        self.t = t

        # Ниже параметры, которые заполняются после инициализации
        # Допустимые судна на ребре в момент времени
        self.allowed_vessels: List[Vessel] = []

    def set_allowed_vessels(self, allowed_vessels: List[Vessel]) -> None:
        self.allowed_vessels = allowed_vessels

    def __str__(self) -> str:
        return f"ETc({self.edge, self.t})"

    def __repr__(self):
        return f"ETc({self.edge, self.t})"
